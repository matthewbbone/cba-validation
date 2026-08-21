#!/usr/bin/env python3
"""Score every chunk of the OCR'd CBA corpus against the tier-1 provision concepts.

Deterministic given the same inputs and parameters, and safe to re-run: chunking and
embedding are cached per document, so an interrupted run costs one document, not the corpus.

    uv run python pipeline/runner.py                       # full build, local files
    uv run python pipeline/runner.py --doc 243Abby         # one document (smoke test)
    uv run python pipeline/runner.py --stage chunk         # chunk only, no model load
    uv run python pipeline/runner.py --force               # ignore the cache and rebuild
    S3_BUCKET_NAME=my-bucket uv run python pipeline/runner.py    # read and write S3

Four stages:
  1. chunk each stg_01_ocr/**/full.txt with chonkie's RecursiveChunker (markdown recipe)
  2. embed each chunk with google/embeddinggemma-300m via sentence-transformers
  3. cosine-similarity every chunk against every tier-1 concept description
  4. write a document > chunk > concept > score lookup, plus the cached artifacts

Storage: every path below is **repo-relative**, and resolves either against the repo
working tree or against an S3 bucket when S3_BUCKET_NAME is set -- the same two-backend,
one-vocabulary arrangement as annotation_ui/lib/storage.ts, so a path means the same thing
to the pipeline, to the UI, and in the bucket. Inputs read:

    stg_01_ocr/{source}/{engine}/{document}/full.txt
    results/tier_1_concepts.md
    annotation_ui/lib/provision-schemas.json      (the concept descriptions)

and everything under results/concept_similarity/ is written back, including the per-document
cache -- so a run interrupted on one machine can be resumed on another.

Note this script cannot run on the Amplify SSR runtime: it is Python, needs torch, and
loads a 1.2 GB model. S3 support is for running it on a machine that has no checkout of
the corpus (an EC2 box, a colleague's laptop) and for landing the artifacts straight in the
bucket instead of uploading them afterwards.

Unlike review/aggregate_provisions.py and review/report_extraction_diagnostics.py, this script
is NOT stdlib-only -- it cannot be. It needs chonkie, sentence-transformers, transformers,
torch, numpy and boto3, declared in pyproject.toml. Install with:

    uv add chonkie "sentence-transformers>=5.0" "transformers>=4.57" torch numpy jsonschema boto3
"""

from __future__ import annotations

import argparse
import bisect
import io
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

# v2: chunks.jsonl `source_file` is repo-relative rather than an absolute local
# path, so the artifact is portable between a checkout and the bucket.
SCHEMA_VERSION = "concept_similarity_v2"

MODEL_ID = "google/embeddinggemma-300m"

# EmbeddingGemma silently falls back to causal instead of bidirectional attention on
# transformers < 4.57, producing materially degraded embeddings with no warning at all.
# See https://github.com/huggingface/sentence-transformers/issues/3725 -- this is asserted
# at runtime rather than left to the lockfile precisely because it fails quietly.
MIN_TRANSFORMERS = (4, 57)

# full.txt is a concatenation of the page_N.md files joined by this line, in numeric order.
# Its offsets give every chunk an exact page range with no matching heuristics.
PAGE_SEP_RE = re.compile(r"^--- Page (\d+) ---[ \t]*$", re.MULTILINE)

# The OCR emits this literal string as the entire content of a blank/unreadable page.
# 7 pages corpus-wide. Only dropped under --drop-filler.
OCR_FILLER = "The quick brown fox jumps over the lazy dog."


# --------------------------------------------------------------------------------------
# Storage -- local working tree or S3, behind one repo-relative path vocabulary
# --------------------------------------------------------------------------------------


class Store:
    """Reads and writes repo-relative paths against the working tree or a bucket.

    S3 mode is selected purely by a bucket being configured, so a local checkout with no
    AWS credentials keeps behaving exactly as before.
    """

    def __init__(self, repo_root, bucket=None, prefix="", region=None):
        self.repo_root = Path(repo_root)
        self.bucket = bucket or None
        self.prefix = (prefix or "").strip("/")
        self.region = region or os.environ.get("AWS_REGION") or "us-east-1"
        self._client = None

    # -- plumbing ------------------------------------------------------------------

    @property
    def client(self):
        if self._client is None:
            import boto3  # imported lazily so local runs need no AWS SDK at all

            self._client = boto3.client("s3", region_name=self.region)
        return self._client

    def describe(self):
        if not self.bucket:
            return f"local:{self.repo_root}"
        return f"s3://{self.bucket}/{self.prefix + '/' if self.prefix else ''}"

    def key(self, rel):
        return f"{self.prefix}/{rel}" if self.prefix else rel

    def local(self, rel):
        """Resolve a repo-relative path, refusing anything that escapes the repo."""
        resolved = (self.repo_root / rel).resolve()
        if not str(resolved).startswith(str(self.repo_root) + os.sep):
            raise ValueError(f"path escapes the repo: {rel}")
        return resolved

    # -- reads ---------------------------------------------------------------------

    def read_bytes(self, rel):
        if not self.bucket:
            return self.local(rel).read_bytes()
        return self.client.get_object(Bucket=self.bucket, Key=self.key(rel))["Body"].read()

    def read_text(self, rel):
        return self.read_bytes(rel).decode("utf-8")

    def exists(self, rel):
        if not self.bucket:
            try:
                return self.local(rel).is_file()
            except ValueError:
                return False
        from botocore.exceptions import ClientError

        try:
            # HEAD, not GET: the cache probe would otherwise pull the whole object.
            self.client.head_object(Bucket=self.bucket, Key=self.key(rel))
            return True
        except ClientError:
            return False

    def list_paths(self, rel_prefix):
        """Repo-relative paths under `rel_prefix`, sorted, in both backends."""
        if not self.bucket:
            root = self.local(rel_prefix)
            if not root.is_dir():
                return []
            return sorted(
                str(p.relative_to(self.repo_root))
                for p in root.rglob("*")
                if p.is_file() and not p.name.startswith(".")
            )

        paginator = self.client.get_paginator("list_objects_v2")
        strip = len(self.prefix) + 1 if self.prefix else 0
        out = []
        for page in paginator.paginate(Bucket=self.bucket, Prefix=self.key(rel_prefix)):
            for obj in page.get("Contents", []):
                out.append(obj["Key"][strip:])
        return sorted(out)

    # -- writes --------------------------------------------------------------------
    # Locally: write a .partial then os.replace, so a half-written artifact is never
    # mistaken for a finished one. On S3: a PutObject is already atomic per object.

    def write_bytes(self, rel, data, content_type=None):
        if not self.bucket:
            target = self.local(rel)
            target.parent.mkdir(parents=True, exist_ok=True)
            partial = target.with_suffix(target.suffix + ".partial")
            partial.write_bytes(data)
            os.replace(partial, target)
            return
        extra = {"ContentType": content_type} if content_type else {}
        self.client.put_object(Bucket=self.bucket, Key=self.key(rel), Body=data, **extra)

    def write_text(self, rel, text, content_type="text/plain; charset=utf-8"):
        self.write_bytes(rel, text.encode("utf-8"), content_type)

    def write_json(self, rel, obj, indent=2):
        separators = (",", ":") if indent is None else None
        body = json.dumps(obj, ensure_ascii=False, indent=indent, separators=separators)
        self.write_text(rel, body, "application/json")

    def write_jsonl(self, rel, rows):
        body = "".join(
            json.dumps(r, ensure_ascii=False, separators=(",", ":")) + "\n" for r in rows
        )
        self.write_text(rel, body, "application/x-ndjson")

    def write_npy(self, rel, array):
        import numpy as np

        buf = io.BytesIO()
        np.save(buf, array)
        self.write_bytes(rel, buf.getvalue(), "application/octet-stream")


# --------------------------------------------------------------------------------------
# Environment
# --------------------------------------------------------------------------------------

def check_transformers(parser):
    """Abort if transformers is old enough to silently degrade the model. Returns its version."""
    import transformers

    version = transformers.__version__
    parts = re.findall(r"\d+", version)[:2]
    if tuple(int(p) for p in parts) < MIN_TRANSFORMERS:
        parser.error(
            f"transformers {version} silently uses causal attention with {MODEL_ID}, which "
            f"produces wrong embeddings without warning. Need >= "
            f"{'.'.join(str(p) for p in MIN_TRANSFORMERS)}.\n"
            f'Fix with: uv add "transformers>=4.57"'
        )
    return version


def resolve_device(requested):
    """Prefer Apple Silicon's MPS, then CUDA, then CPU. EmbeddingGemma has no float16 path."""
    import torch

    if requested and requested != "auto":
        return requested
    if torch.backends.mps.is_available():
        return "mps"
    if torch.cuda.is_available():
        return "cuda"
    return "cpu"


# --------------------------------------------------------------------------------------
# Concepts
# --------------------------------------------------------------------------------------

def parse_tier1(store, rel, parser):
    """Rows of the pipe table in results/tier_1_concepts.md, in file order.

    Hand-maintained, so the parse is forgiving: rows are taken only after the |---| row and
    short rows are skipped. The file has no trailing newline on its last row.
    """
    try:
        raw_text = store.read_text(rel)
    except Exception as exc:  # noqa: BLE001 -- missing locally or in the bucket
        parser.error(f"could not read the concept list {rel} from {store.describe()}: {exc}")

    concepts = []
    past_separator = False
    for raw in raw_text.split("\n"):
        line = raw.strip()
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if cells and all(re.fullmatch(r":?-{2,}:?", c) for c in cells):
            past_separator = True
            continue
        if not past_separator or len(cells) < 3:
            continue
        concept_id = cells[0].strip("`").strip()
        if not concept_id:
            continue
        concepts.append({
            "concept_id": concept_id,
            "label": cells[1],
            "area": cells[2],
            "status": cells[3] if len(cells) > 3 else "",
        })
    if not concepts:
        parser.error(f"no concept rows parsed from {rel}")
    return concepts


def load_concepts(store, concepts_rel, schemas_rel, parser):
    """Compose the query text for each tier-1 concept.

    tier_1_concepts.md is the authority on which concepts exist and supplies the label and
    parent area; provision-schemas.json supplies the hand-written plain-language description.
    That file is the older 99-concept dictionary whose own tier/category vocabulary differs, so
    only `description` is read from it -- and a missing one is a hard error rather than a
    silently shorter query string.
    """
    concepts = parse_tier1(store, concepts_rel, parser)

    try:
        schemas = json.loads(store.read_text(schemas_rel))
    except Exception as exc:  # noqa: BLE001
        parser.error(f"could not read the provision schemas {schemas_rel} from {store.describe()}: {exc}")

    missing = [c["concept_id"] for c in concepts if not schemas.get(c["concept_id"], {}).get("description")]
    if missing:
        parser.error(
            f"{len(missing)} tier-1 concept(s) have no description in {schemas_rel}: "
            f"{', '.join(missing[:5])}"
        )

    for c in concepts:
        c["description"] = schemas[c["concept_id"]]["description"].strip()
        c["query_text"] = f"{c['label']} ({c['area']}). {c['description']}"
    return concepts


# --------------------------------------------------------------------------------------
# Documents and page provenance
# --------------------------------------------------------------------------------------

def discover_documents(store, ocr_root, parser):
    """Every stg_01_ocr/{source}/{engine}/{document_id}/full.txt, sorted for stable chunk ids.

    Only full.txt is looked for. The per-page .md/.txt files it was built from are not read
    by anything here, and on S3 they may not have been uploaded at all.
    """
    docs = []
    for rel in store.list_paths(ocr_root.rstrip("/") + "/"):
        parts = rel.split("/")
        # stg_01_ocr / source / engine / document / full.txt
        if len(parts) != 5 or parts[-1] != "full.txt":
            continue
        _, source, engine, document_id, _ = parts
        if any(x.startswith(".") for x in (source, engine, document_id)):
            continue
        docs.append({
            "key": f"{source}/{engine}/{document_id}",
            "source": source,
            "engine": engine,
            "document_id": document_id,
            "rel": rel,
        })
    if not docs:
        parser.error(f"no full.txt files under {ocr_root} in {store.describe()}")
    return sorted(docs, key=lambda d: d["rel"])


def page_offsets(full_text):
    """(page numbers, their separator-line start offsets) -- both ascending, index-aligned."""
    numbers, starts = [], []
    for match in PAGE_SEP_RE.finditer(full_text):
        numbers.append(int(match.group(1)))
        starts.append(match.start())
    return numbers, starts


def page_range(numbers, starts, start, end):
    """The page numbers containing `start` and `end - 1`.

    A chunk is attributed to the last page whose separator begins at or before it, so a chunk
    opening on a separator line belongs to the page it introduces. Returns (None, None) when
    the document has no separators at all.
    """
    if not starts:
        return None, None
    first = bisect.bisect_right(starts, start) - 1
    last = bisect.bisect_right(starts, max(start, end - 1)) - 1
    first = max(first, 0)
    last = max(last, 0)
    return numbers[first], numbers[last]


def embed_text_of(chunk_text):
    """The string actually handed to the encoder.

    Page separators are stripped here and only here: the stored chunk text and its offsets stay
    verbatim slices of full.txt, so traceability is untouched, while `--- Page 42 ---` never
    reaches the model as content.
    """
    return PAGE_SEP_RE.sub("", chunk_text).strip()


def is_filler(embed_text):
    """True when a chunk carries nothing but the OCR's blank-page placeholder."""
    return bool(embed_text) and not embed_text.replace(OCR_FILLER, "").strip()


# --------------------------------------------------------------------------------------
# Stage 1 -- chunking
# --------------------------------------------------------------------------------------

def build_chunker(chunk_size, tokenizer, recipe, parser):
    from chonkie import RecursiveChunker

    if recipe == "none":
        return RecursiveChunker(tokenizer=tokenizer, chunk_size=chunk_size)
    try:
        return RecursiveChunker.from_recipe(
            recipe, lang="en", tokenizer=tokenizer, chunk_size=chunk_size
        )
    except Exception as exc:  # noqa: BLE001 -- recipe loading reaches the network and HF hub
        parser.error(
            f"could not load the chonkie '{recipe}' recipe: {type(exc).__name__}: {exc}\n"
            f"Pass --recipe none to fall back to the default recursive rules."
        )


def chunk_document(store, doc, chunker, drop_filler):
    """Chunk one full.txt into rows carrying text, exact offsets and a page range."""
    full_text = store.read_text(doc["rel"])
    numbers, starts = page_offsets(full_text)

    rows = []
    n_mismatch = n_blank = n_filler = 0
    for chunk in chunker(full_text):
        start, end = chunk.start_index, chunk.end_index
        # Everything downstream -- page attribution, any later citation -- rests on the chunk
        # being a verbatim slice, so check rather than assume.
        verified = full_text[start:end] == chunk.text
        if not verified:
            n_mismatch += 1

        embed_text = embed_text_of(chunk.text)
        if not embed_text:
            n_blank += 1
            continue
        if drop_filler and is_filler(embed_text):
            n_filler += 1
            continue

        first_page, last_page = page_range(numbers, starts, start, end)
        rows.append({
            "chunk_id": str(len(rows)),
            "document_key": doc["key"],
            "source": doc["source"],
            "engine": doc["engine"],
            "document_id": doc["document_id"],
            # Repo-relative, so the row resolves against a checkout or the bucket.
            "source_file": doc["rel"],
            "char_start": start,
            "char_end": end,
            "page_start": first_page,
            "page_end": last_page,
            "token_count": chunk.token_count,
            "offsets_verified": verified,
            "text": chunk.text,
            "embed_text": embed_text,
        })

    stats = {
        "n_pages": len(numbers),
        "n_chunks": len(rows),
        "n_offset_mismatches": n_mismatch,
        "n_blank_skipped": n_blank,
        "n_filler_dropped": n_filler,
        "n_chars": len(full_text),
    }
    return rows, stats


# --------------------------------------------------------------------------------------
# Stage 2 -- embedding, with a per-document cache
# --------------------------------------------------------------------------------------

def cache_slug(document_key):
    return document_key.replace("/", "__")


def cache_params(args, model_id):
    """Everything that changes the cached vectors. A mismatch invalidates the entry."""
    return {
        "schema_version": SCHEMA_VERSION,
        "model": model_id,
        "chunk_size": args.chunk_size,
        "tokenizer": args.tokenizer,
        "recipe": args.recipe,
        "drop_filler": bool(args.drop_filler),
    }


def load_cached(store, cache_dir, document_key, params):
    """Cached (rows, vectors, stats) for one document, or None.

    The meta file is the commit marker. Stats come back with the vectors so a warm re-run
    reports the same chunk counts and offset-mismatch count as the run that built the cache.
    """
    import numpy as np

    slug = cache_slug(document_key)
    meta_rel = f"{cache_dir}/{slug}.meta.json"
    npz_rel = f"{cache_dir}/{slug}.npz"
    try:
        meta = json.loads(store.read_text(meta_rel))
    except Exception:  # noqa: BLE001 -- absent, unreadable or malformed: treat as a miss
        return None
    if meta.get("params") != params:
        return None
    try:
        vectors = np.load(io.BytesIO(store.read_bytes(npz_rel)))["vectors"]
    except Exception:  # noqa: BLE001
        return None
    if len(meta.get("rows", [])) != len(vectors):
        return None
    return meta["rows"], vectors, meta.get("stats", {})


def save_cached(store, cache_dir, document_key, params, rows, vectors, stats):
    """Write vectors then meta. Meta last: it is what marks the entry usable."""
    import numpy as np

    slug = cache_slug(document_key)
    buf = io.BytesIO()
    np.savez(buf, vectors=vectors)
    store.write_bytes(f"{cache_dir}/{slug}.npz", buf.getvalue(), "application/octet-stream")
    store.write_json(
        f"{cache_dir}/{slug}.meta.json", {"params": params, "stats": stats, "rows": rows}, indent=None
    )


def embed_rows(model, rows, batch_size):
    """Chunk vectors, L2-normalized so stage 3 is a plain dot product."""
    import numpy as np

    if not rows:
        return np.zeros((0, model.get_embedding_dimension()), dtype="float32")
    vectors = model.encode_document(
        [r["embed_text"] for r in rows],
        batch_size=batch_size,
        normalize_embeddings=True,
        show_progress_bar=False,
    )
    return np.asarray(vectors, dtype="float32")


# --------------------------------------------------------------------------------------
# Output
# --------------------------------------------------------------------------------------

# --------------------------------------------------------------------------------------
# main
# --------------------------------------------------------------------------------------

def main(argv=None):
    here = Path(__file__).resolve().parent
    repo = here.parent

    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    # All paths are repo-relative and resolve against the working tree or the bucket.
    parser.add_argument("--ocr-root", default="stg_01_ocr")
    parser.add_argument("--concepts", default="results/tier_1_concepts.md")
    parser.add_argument(
        "--schemas",
        default="annotation_ui/lib/provision-schemas.json",
        help="source of the plain-language concept descriptions",
    )
    parser.add_argument(
        "--out-dir",
        default=None,
        help="default: results/concept_similarity (a --doc run writes to its _partial subdir)",
    )
    parser.add_argument("--cache-dir", default=None, help="default: <out-dir>/_cache")
    parser.add_argument(
        "--s3-bucket",
        default=os.environ.get("S3_BUCKET_NAME"),
        help="read and write S3 instead of the working tree (env: S3_BUCKET_NAME)",
    )
    parser.add_argument(
        "--s3-prefix",
        default=os.environ.get("S3_PREFIX", ""),
        help="optional key prefix within the bucket (env: S3_PREFIX)",
    )
    parser.add_argument("--model", default=MODEL_ID)
    parser.add_argument("--tokenizer", default=MODEL_ID, help="chonkie counts chunk_size in these tokens")
    parser.add_argument("--recipe", default="markdown", help="chonkie recursive recipe, or 'none'")
    parser.add_argument("--chunk-size", type=int, default=512, help="tokens per chunk (model window is 2048)")
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--device", default="auto", help="auto | mps | cuda | cpu")
    parser.add_argument("--doc", action="append", help="only this document_id (repeatable)")
    parser.add_argument("--force", action="store_true", help="ignore the cache and re-embed")
    parser.add_argument(
        "--drop-filler",
        action="store_true",
        help=f"skip chunks that are only the OCR placeholder {OCR_FILLER!r}",
    )
    parser.add_argument(
        "--stage",
        choices=["all", "chunk", "embed", "score"],
        default="all",
        help="chunk: no model load. embed: fill the cache. score: use the cache only.",
    )
    parser.add_argument("--decimals", type=int, default=4, help="rounding for stored scores")
    args = parser.parse_args(argv)

    store = Store(repo, bucket=args.s3_bucket, prefix=args.s3_prefix)
    print(f"storage: {store.describe()}")

    default_out = "results/concept_similarity"
    out_dir = args.out_dir.rstrip("/") if args.out_dir else default_out
    # The cache is always the shared one, so a --doc run still warms it for the full build.
    cache_dir = args.cache_dir.rstrip("/") if args.cache_dir else f"{default_out}/_cache"

    concepts = load_concepts(store, args.concepts, args.schemas, parser)
    concept_ids = [c["concept_id"] for c in concepts]
    print(f"concepts: {len(concepts)} tier-1 (descriptions from {args.schemas})")

    documents = discover_documents(store, args.ocr_root, parser)
    if args.doc:
        wanted = set(args.doc)
        documents = [d for d in documents if d["document_id"] in wanted]
        unknown = wanted - {d["document_id"] for d in documents}
        if unknown:
            parser.error(f"unknown document(s): {sorted(unknown)}")
    print(f"documents: {len(documents)}")

    if args.doc and not args.out_dir:
        out_dir = f"{default_out}/_partial"
        print(f"partial run (--doc): writing to {out_dir} so the full-corpus artifacts stay intact")

    params = cache_params(args, args.model)

    # ---- stage 1 only: chunk without touching the model weights --------------------
    if args.stage == "chunk":
        chunker = build_chunker(args.chunk_size, args.tokenizer, args.recipe, parser)
        all_rows, totals = [], {}
        for doc in documents:
            rows, stats = chunk_document(store, doc, chunker, args.drop_filler)
            all_rows.extend(rows)
            for k, v in stats.items():
                totals[k] = totals.get(k, 0) + v
            print(f"  {doc['key']:56s} {stats['n_pages']:4d}p {stats['n_chunks']:5d} chunks")
        store.write_jsonl(f"{out_dir}/chunks.jsonl", [strip_embed_text(r) for r in all_rows])
        print(f"chunks: {len(all_rows):,}  (offset mismatches: {totals.get('n_offset_mismatches', 0)})")
        print(f"wrote {out_dir}/chunks.jsonl")
        return 0

    transformers_version = check_transformers(parser)
    device = resolve_device(args.device)
    print(f"transformers {transformers_version} | device {device}")

    from sentence_transformers import SentenceTransformer
    import numpy as np
    import sentence_transformers as st

    model = SentenceTransformer(args.model, device=device)
    print(f"model: {args.model} (dim {model.get_embedding_dimension()}, window {model.max_seq_length})")

    chunker = None  # built lazily -- a fully cached run never needs it

    all_rows, all_vectors, totals = [], [], {}
    n_cached = 0
    for doc in documents:
        cached = None if args.force else load_cached(store, cache_dir, doc["key"], params)
        if cached is not None:
            rows, vectors, stats = cached
            n_cached += 1
            suffix = "  (cached)"
        else:
            if args.stage == "score":
                parser.error(
                    f"--stage score needs a cache entry for {doc['key']}.\n"
                    f"Build it first with: uv run python pipeline/runner.py --stage embed"
                )
            if chunker is None:
                chunker = build_chunker(args.chunk_size, args.tokenizer, args.recipe, parser)
            rows, stats = chunk_document(store, doc, chunker, args.drop_filler)
            vectors = embed_rows(model, rows, args.batch_size)
            save_cached(
                store, cache_dir, doc["key"], params, [strip_embed_text(r) for r in rows], vectors, stats
            )
            suffix = ""

        for k, v in stats.items():
            totals[k] = totals.get(k, 0) + v
        if stats.get("n_offset_mismatches"):
            suffix += f"  !! {stats['n_offset_mismatches']} offset mismatches"
        print(
            f"  {doc['key']:56s} {stats.get('n_pages', 0):4d}p {stats.get('n_chunks', len(rows)):5d} chunks"
            f"  {stats.get('n_chars', 0)/1000:6.0f}k chars{suffix}"
        )
        all_rows.extend(rows)
        all_vectors.append(vectors)

    chunk_vectors = np.concatenate(all_vectors) if all_vectors else np.zeros((0, 768), dtype="float32")
    print(f"chunks: {len(all_rows):,} ({n_cached}/{len(documents)} documents from cache)")

    if args.stage == "embed":
        print("stage=embed: cache filled, stopping before scoring")
        return 0

    # ---- stage 2b -- concept vectors ------------------------------------------------
    # encode_query / encode_document apply EmbeddingGemma's two different prompt templates.
    # A bare encode() on both sides would quietly cost accuracy: this model is asymmetric.
    concept_vectors = np.asarray(
        model.encode_query(
            [c["query_text"] for c in concepts],
            batch_size=args.batch_size,
            normalize_embeddings=True,
            show_progress_bar=False,
        ),
        dtype="float32",
    )

    # ---- stage 3 -- cosine similarity ----------------------------------------------
    # Both sides are L2-normalized, so the dot product *is* cosine similarity.
    scores = chunk_vectors @ concept_vectors.T
    print(f"scores: {scores.shape[0]:,} chunks x {scores.shape[1]} concepts = {scores.size:,}")

    # ---- stage 4 -- the lookup dictionary ------------------------------------------
    documents_out = {}
    for i, row in enumerate(all_rows):
        per_chunk = documents_out.setdefault(row["document_key"], {})
        per_chunk[row["chunk_id"]] = {
            cid: round(float(scores[i, j]), args.decimals) for j, cid in enumerate(concept_ids)
        }

    generated = datetime.now(timezone.utc).isoformat(timespec="seconds")
    meta = {
        "model": args.model,
        "chunk_size": args.chunk_size,
        "tokenizer": args.tokenizer,
        "recipe": args.recipe,
        "drop_filler": bool(args.drop_filler),
        "n_documents": len(documents_out),
        "n_chunks": len(all_rows),
        "n_concepts": len(concepts),
    }
    store.write_json(f"{out_dir}/lookup.json", {
        "schema_version": SCHEMA_VERSION,
        "meta": meta,
        "documents": documents_out,
    }, indent=None)

    store.write_jsonl(f"{out_dir}/chunks.jsonl", [strip_embed_text(r) for r in all_rows])
    store.write_npy(f"{out_dir}/chunk_embeddings.npy", chunk_vectors)
    store.write_npy(f"{out_dir}/concept_embeddings.npy", concept_vectors)
    store.write_json(f"{out_dir}/concepts.json", {c["concept_id"]: c for c in concepts})
    store.write_json(f"{out_dir}/manifest.json", {
        "schema_version": SCHEMA_VERSION,
        "generated": generated,
        "model": args.model,
        "embedding_dim": int(chunk_vectors.shape[1]) if len(chunk_vectors) else None,
        "device": device,
        "storage": store.describe(),
        "versions": {
            "transformers": transformers_version,
            "sentence_transformers": st.__version__,
            "numpy": np.__version__,
        },
        "chunking": {
            "library": "chonkie",
            "chunker": "RecursiveChunker",
            "recipe": args.recipe,
            "chunk_size_tokens": args.chunk_size,
            "tokenizer": args.tokenizer,
        },
        "counts": {
            "documents": len(documents_out),
            "chunks": len(all_rows),
            "concepts": len(concepts),
            "scores": int(scores.size),
            "documents_from_cache": n_cached,
        },
        "chunking_stats": totals,
        "decimals": args.decimals,
    })

    mismatches = totals.get("n_offset_mismatches", 0)
    if mismatches:
        print(f"  !! {mismatches} chunk(s) were not verbatim slices -- their page ranges are suspect")
    for name in ("lookup.json", "chunks.jsonl", "chunk_embeddings.npy",
                 "concept_embeddings.npy", "concepts.json", "manifest.json"):
        print(f"wrote {out_dir}/{name}")
    return 0


def strip_embed_text(row):
    """`embed_text` is derivable from `text`; keep it out of the artifacts."""
    return {k: v for k, v in row.items() if k != "embed_text"}


if __name__ == "__main__":
    sys.exit(main())
