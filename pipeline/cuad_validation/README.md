# CUAD clause-retrieval recall benchmark

This benchmark applies the chunking and embedding retrieval method in
[`pipeline/runner.py`](../runner.py) to the CUAD contract dataset. It asks a retrieval
question rather than re-running clause extraction: for every annotated clause, does at
least one of the highest-scoring chunks for that clause category overlap the gold text?

## Corpus and denominator

The inputs are downloaded from
[`theatticusproject/cuad`](https://huggingface.co/datasets/theatticusproject/cuad) at the
pinned dataset revision
`a3c393f5d103fd0c516374e4fdff676c8176dcb1`:

- `CUAD_v1/CUAD_v1.json` supplies the complete contract text and exact answer offsets for
  all 510 contracts and all 41 clause categories. The Hugging Face repository contains
  only 200 standalone `.txt` contract files, so those files cannot support a complete
  benchmark. For the files that do exist, their text is byte-identical to the JSON
  contexts.
- `CUAD_v1/master_clauses.csv` defines the paper's 13,101 annotated provisions. This is
  the denominator for the headline micro recall.

The two counts commonly associated with CUAD are intentionally different. A single
provision can contain non-contiguous text separated by the literal `<omitted>` marker.
After splitting such provisions, the 13,101 provisions contain 13,831 segment references
to 13,823 unique gold spans (eight exact spans are reused by distinct master provisions).
A provision counts once in the headline result, regardless of how many segments it
contains.

Preparation validates the published corpus invariants before any model work begins:
510 contracts, 41 categories, 20,910 contract-category questions, 13,101 provisions,
13,823 unique segments, unique normalized contract/category mappings, and exact source
text for every mapped segment. A mismatch is an error rather than a silently shortened
benchmark.

## Retrieval method

For each CUAD category, the query is exactly:

```text
{category}. {official description}
```

Each contract is independently split with Chonkie's markdown `RecursiveChunker`, using
the same Tokie tokenizer backend selected by `runner.py` and a 512-token chunk size.
The tokenizer JSON is downloaded at its pinned revision rather than from a mutable Hub
branch. The defaults pin:

- model: `google/embeddinggemma-300m`, revision
  `57c266a740f537b4dc058e1b0cda161fd15afa75`
- Chonkie recipe repository: `chonkie-ai/recipes`, revision
  `bd588a8b1beb3b387ab999f1f86806e7fcea3dd8`
- recipe: `markdown`

As in `runner.py`, contract chunks and category queries use the model's asymmetric
document/query prompt profiles, both sides are L2-normalized, and their dot product is
cosine similarity.
Chonkie-reported offsets are checked against the exact source slice. A locally shifted
offset is realigned to the nearest nearby exact match, with the earliest start breaking
an equal-distance tie; out-of-order or unresolved chunks fail the run.

Scores are rounded to four decimals before ranking. Ranking happens separately within
each `(contract, category)` pair, descending by score and then ascending by numeric chunk
ID to make ties deterministic. At percentile `p`, the evaluator selects
`ceil(p * number_of_contract_chunks)` chunks, with at least one selected for every
non-empty contract. The reported thresholds are 1%, 5%, 25%, and 50%.

The primary metric is **any-overlap recall**: a provision is recalled if a selected chunk
overlaps at least one character of any of its gold segments. Two stricter diagnostics use
the union of all selected overlaps so overlapping chunks are not double-counted:

- **majority coverage:** selected chunks cover at least 50% of the provision's annotated
  characters;
- **full coverage:** selected chunks cover all annotated characters across every segment.

All three metrics are micro-averaged over provisions, not contracts, categories, or
segments.

## Running the benchmark

Install the locked environment, then run the complete benchmark:

```bash
uv sync
uv run python -m pipeline.cuad_validation.evaluate_recall
```

The first run downloads the two pinned CUAD files and the pinned model/recipe snapshots.
It then creates resumable per-contract caches. A later run reuses a cache only when its
source-text hash and every material chunking/model parameter match, including the
Chonkie and Tokie backend versions. Use `--force` to ignore valid caches and rebuild
them.

Useful overrides are visible with:

```bash
uv run python -m pipeline.cuad_validation.evaluate_recall --help
```

They include dataset, model, and tokenizer revisions; query/document prompt names;
local input/output paths; model; tokenizer; recipe and recipe revision; chunk size;
batch size; device; score decimals; cache directory; and `--force`. Changing an
override makes the resulting run a different benchmark; the resolved values and
installed library versions are recorded in output metadata.

## Three-model comparison

Run the locked comparison for the three Hugging Face models with:

```bash
uv run python -m pipeline.cuad_validation.evaluate_models
```

The driver runs each evaluator in a separate process so accelerator memory is released
between models. Dataset, category queries, 512-token chunks, EmbeddingGemma tokenizer,
recipe, ranking, and recall definitions remain fixed. Only the embedding model and its
official query/document prompt profile change:

| Model | Pinned revision | Query prompt | Document prompt |
| --- | --- | --- | --- |
| `google/embeddinggemma-300m` | `57c266a740f537b4dc058e1b0cda161fd15afa75` | `query` | `document` |
| `microsoft/harrier-oss-v1-0.6b` | `f9b9dc8d367d443f2479d27aa5d8d2850c0774ee` | `web_search_query` | none |
| `Qwen/Qwen3-Embedding-0.6B` | `97b0c614be4d77ee51c0cef4e5f07c00f9eb65b3` | `query` | none |

Outputs and caches are isolated by model under `model_comparison/` and `model_cache/`.
The driver also writes `model_comparison.json` and `model_comparison.csv` at the
comparison root. Use `--summarize-only` to rebuild those comparison files from completed
model summaries without loading model weights.

The standard-library test suite is offline and does not load model weights:

```bash
uv run python -m unittest discover -s tests -p 'test_cuad_validation.py' -v
```

## Outputs

Generated files live under the ignored `results/cuad_validation/` directory by default:

| Artifact | Contents |
| --- | --- |
| `recall_summary.json` | Schema/run metadata, validated corpus counts, cutoff definitions, and any-overlap, majority, and full-coverage numerators, denominator, and percentages. |
| `per_category.csv` | One row per CUAD category, with its provision denominator and all three recall metrics at every cutoff. |
| `provision_recall.jsonl` | One audit row per master provision: contract/category identity, source segments, overlapping chunk IDs and ranks, coverage fractions, and Boolean results at each cutoff. |
| `cache/<cache-key>.npz` | Exact aligned chunks, normalized document embeddings, source hash, and all parameters needed to decide whether the per-contract cache can be reused. |

The provision audit rows are the source for both aggregate artifacts. The run is accepted
only if it writes exactly 13,101 rows, produces a `chunks x 41` score matrix for every
contract, and every metric is monotonically non-decreasing from the 1% through 50%
cutoffs. Generated data and model artifacts are intentionally not committed; the pinned
revisions, lockfile, cache metadata, and summary metadata make the computation
reproducible.
