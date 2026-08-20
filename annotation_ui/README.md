# CBA provision span annotation

An annotator reads one **chunk** of a collective bargaining agreement beside one
provision concept, judges whether the passage addresses that concept, and highlights the
text that is evidence for it. Each highlight is stored as a `(document, character span)`
tuple with offsets into `full.txt`, so it can be traced back to the exact source text.

Chunks and their concept scores come from [pipeline/runner.py](../pipeline/runner.py).
Run that first — this tool reads its artifacts and will refuse to start without them.

## Running it

```bash
uv run python pipeline/runner.py   # once, from the repo root — builds the artifacts
cd annotation_ui && npm install && npm run dev   # http://localhost:3000
```

There is no build step for data — the app reads the pipeline's output directly:

| Input | What it provides |
|---|---|
| `results/concept_similarity/chunks.jsonl` | chunk text, offsets, page range |
| `results/concept_similarity/lookup.json` | the (chunk × concept) similarity scores |
| `results/concept_similarity/concepts.json` | the 34 concepts and their descriptions |
| `stg_01_ocr/{source}/{engine}/{doc}/full.txt` | re-read at submit to verify every span |

## Storage: local disk or S3

Those four paths are read through [lib/storage.ts](lib/storage.ts), which has two
backends selected by one environment variable:

| | `S3_BUCKET_NAME` unset | `S3_BUCKET_NAME` set |
|---|---|---|
| reads | repo working tree | `s3://$S3_BUCKET_NAME/[$S3_PREFIX/]<same path>` |
| writes | append to `annotations/chunk_span_annotations.jsonl` | one object per judgement |

**The path vocabulary is identical in both modes** — a path like
`stg_01_ocr/dol_archive/ATH-MaaS_OvisOCR2/document_549/full.txt` is the file on disk,
the S3 key, *and* the `source_file` recorded on every row. There is no mapping table to
drift out of sync.

To populate a bucket:

```bash
S3_BUCKET_NAME=my-bucket npm run upload-corpus            # --dry-run to preview
S3_BUCKET_NAME=my-bucket npm run dev                      # read from S3
```

`upload-corpus` uploads the 20 `full.txt` files plus the three pipeline artifacts (~14 MB)
and skips objects already present at the same size, so a re-run after a partial upload
costs only what is missing. It deliberately does **not** upload the per-page `.md`/`.txt`
files: `full.txt` was built from them and nothing in the app reads them.

In S3 mode each judgement is written to its own object:

```
chunk_annotations/{annotator-slug}/{band}/{source}/{engine}/{document}/{chunk}/{concept}.json
```

One object per unit, so a re-annotation overwrites instead of appending a duplicate and
two annotators cannot clobber each other — S3 has no append, so a shared JSONL would mean
read-modify-write of the whole object per submission. The band sits in the key so progress
readback is a single `ListObjectsV2` on the annotator's prefix: both the unit identity and
its stratum come out of the key, with no object fetches.

**Cost of a cold process:** the first request fetches ~9.5 MB of artifacts
(`chunks.jsonl` + `lookup.json`), about 6–7 s. Everything after that is served from
memory — measured 0.27 s per session and 0.28 s per submit against a production build.
`full.txt` is fetched whole and cached per document; it is never range-read, because span
offsets are *character* offsets and the corpus contains 21 distinct non-ASCII characters,
so a byte range would silently return the wrong slice.

For hosted deployment see the header of [amplify.yml](../amplify.yml), which lists the
three environment variables and the three IAM actions the SSR role needs.

URL parameters, all optional:

- `?annotator=mb` — skip the name prompt
- `?band=95-99` — start in a given percentile band (also set by the selector, which
  writes it back to the URL so a reload keeps it)
- `?doc=document_1778` — only chunks of one document
- `?concept=C_LEAVE_HOLIDAYS` — only one concept

## How units are chosen

Every (chunk, concept) pair is ranked **within its own document, for that concept**, and
bucketed by percentile from the top. The annotator picks a band; within it the draw is
uniform at random.

| Band | Units | What it is |
|---|---|---|
| Top 1% (99–100th) | 1,428 | the model's best guesses |
| 95–99th | 4,386 | strong but not top |
| 75–95th | 21,692 | plausible |
| 50–75th | 27,166 | weak |
| Bottom half (0–50th) | 54,298 | near-certain negatives |

This is stratified sampling, not a work queue: the same effort yields a precision
estimate at every level of model confidence, so you can find where the score stops being
informative rather than only confirming the top of the list. The `band` is recorded on
every row, which is what makes those estimates weightable.

Ranking per document, rather than corpus-wide, keeps a band comparable across contracts
of very different lengths — a 401-page contract and a 26-page one each contribute their
own top 1%. One artifact follows from that: in a document with only a handful of chunks
the top band is close to meaningless (`243Abby` has a single chunk, so it ranks first for
all 34 concepts), which is why the header always shows `chunk N of M`.

**The similarity score itself is never shown.** The band is the only signal the annotator
gets, and even that is their own choice; a visible `0.61` would invite confirming the
model's guess, contaminating exactly the data you would use to evaluate it.

## Output format

One JSON object per line:

```json
{
  "session_id": "m9x2k4a1b",
  "timestamp": "2026-08-20T19:12:03.512Z",
  "annotator": "mb",
  "source": "dol_archive",
  "engine": "ATH-MaaS_OvisOCR2",
  "document_id": "document_1778",
  "chunk_id": "25",
  "source_file": "stg_01_ocr/dol_archive/ATH-MaaS_OvisOCR2/document_1778/full.txt",
  "chunk_char_start": 36063,
  "chunk_char_end": 38010,
  "page_start": 11,
  "page_end": 12,
  "concept_id": "C_LEAVE_HOLIDAYS",
  "concept_label": "Holidays and holiday pay",
  "band": "99-100",
  "relevance": "yes",
  "spans": [
    { "start": 37534, "end": 38008, "text": "23.18 In addition to the holidays…",
      "note": "part-time personal day", "page": 12 }
  ]
}
```

`relevance` is `yes` / `partly` / `no` and is always required. `no` with zero spans is the
negative label; `yes` or `partly` with zero spans is also meaningful — relevant, but with
no cleanly delimitable passage. A `no` carrying spans is rejected as a contradiction.

`source_file` is the repo-relative path that is also the S3 key, so a row is resolvable
against either backend.

`start`/`end` are half-open character offsets into `source_file` — JS UTF-16 code units,
which equal Python `str` indices for anything outside the astral planes. The invariant
every consumer can rely on:

```python
import json, pathlib
for line in open('annotations/chunk_span_annotations.jsonl'):
    r = json.loads(line)
    src = pathlib.Path(r['source_file']).read_text()
    for s in r['spans']:
        assert src[s['start']:s['end']] == s['text']
        assert r['chunk_char_start'] <= s['start'] and s['end'] <= r['chunk_char_end']
```

`/api/submit` enforces both of those before writing, by re-reading `full.txt` and
re-slicing it. So a row can never claim a passage the file does not contain, nor one
outside the chunk that was actually on screen.

## How the offsets survive markdown rendering

[lib/md-blocks.ts](lib/md-blocks.ts) is a block-level tokenizer, not a markdown parser. It
emits *leaves*, each a contiguous slice of the source, and
[ChunkText.tsx](app/components/ChunkText.tsx) renders every leaf as an element carrying
its start offset. So a `##` heading renders as a heading whose text begins after the
hashes, a pipe table renders as a real table with one leaf per cell, and resolving a
browser selection to a source offset is arithmetic rather than estimation.

Two details specific to chunks:

- The tokenizer necessarily indexes the chunk from 0, while spans are recorded in
  `full.txt` coordinates. Leaves are shifted by the chunk's `char_start` immediately after
  parsing, so there is exactly one place where the two coordinate systems meet.
- `--- Page N ---` separators, which the concatenation added rather than the contract,
  render as page-break rules and are given **no** selectable leaf, so they can never land
  inside a highlighted span. A span may still *cover* one when a selection crosses a page
  boundary, because the recorded range is a source range — re-slicing returns the
  separator exactly as it appears in the file.

Inline emphasis is deliberately not parsed: dropping `*` from the displayed text would
break the invariant, and the OCR barely uses inline markup.

```bash
npm run check-blocks   # asserts the invariant over every page in stg_01_ocr
```

## Notes for annotators

- A chunk is not a page. 63% of chunks span two or more printed pages, which is the point:
  a provision cut across a page boundary now arrives intact. The header shows the page
  range and page-break rules mark the turns.
- Chunks are capped at 512 tokens, so a long article can still be split. Judge the passage
  in front of you, not the article you infer around it.
- Multi-column lists are flattened in a reading order that does not always match the
  visual columns — a parenthetical can land after the wrong item. That is the OCR's doing.
- Repeated OCR boilerplate (running footers, letter templates) is chunked and scored like
  any other text. It accounts for ~3% of top-20 matches, so it will occasionally appear;
  `no` is the right verdict.

## Dormant

`scripts/prepare-data.ts` and `lib/{provisions,provision-schemas,cba-manifest}.json` belong
to the earlier PDF-and-structured-form task. Nothing in the app imports them any more —
the concept descriptions now come from the pipeline's `concepts.json`, which composes
`tier_1_concepts.md` with `provision-schemas.json` at build time. They are kept because
`provision-schemas.json` carries hand-edited rater copy. The extraction-review tab and the
Prolific plumbing were removed earlier; the S3 layer is unrelated to the old PDF-serving
code and shares none of it.
