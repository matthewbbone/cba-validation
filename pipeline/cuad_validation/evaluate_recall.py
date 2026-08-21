#!/usr/bin/env python3
"""Evaluate CUAD clause retrieval recall with the production chunking pipeline.

The benchmark chunks each contract, embeds the chunks with EmbeddingGemma, and
ranks them independently for all 41 CUAD clause-category queries.  A gold
provision is recalled when at least one selected chunk has positive character
overlap with at least one of its annotated spans.  Majority (at least 50%) and
complete gold-character coverage are reported as stricter diagnostics.

Run from the repository root with::

    uv run python -m pipeline.cuad_validation.evaluate_recall
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.metadata
import io
import json
import math
import os
import platform
import re
import sys
from collections.abc import Iterable, Mapping, Sequence
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "cuad_clause_recall_v1"
CACHE_SCHEMA_VERSION = "cuad_clause_recall_cache_v1"

DATASET_ID = "theatticusproject/cuad"
DATASET_REVISION = "a3c393f5d103fd0c516374e4fdff676c8176dcb1"
MODEL_ID = "google/embeddinggemma-300m"
MODEL_REVISION = "57c266a740f537b4dc058e1b0cda161fd15afa75"
TOKENIZER_ID = MODEL_ID

RECIPE_ID = "markdown"
RECIPE_REPOSITORY = "chonkie-ai/recipes"
RECIPE_REVISION = "bd588a8b1beb3b387ab999f1f86806e7fcea3dd8"
RECIPE_LANGUAGE = "en"

DEFAULT_CHUNK_SIZE = 512
DEFAULT_BATCH_SIZE = 32
DEFAULT_DECIMALS = 4
ALIGNMENT_WINDOW = 64
MIN_TRANSFORMERS = (4, 57)

EXPECTED_CONTRACTS = 510
EXPECTED_CATEGORIES = 41
EXPECTED_QUESTIONS = 20_910
EXPECTED_PROVISIONS = 13_101
EXPECTED_UNIQUE_GOLD_SEGMENTS = 13_823
EXPECTED_POSITIVE_PAIRS = 6_702

# Labels are stable public keys used in all three result artifacts.
CUTOFFS: tuple[tuple[str, float], ...] = (
    ("top_1_percent", 0.01),
    ("top_5_percent", 0.05),
    ("top_25_percent", 0.25),
    ("top_50_percent", 0.50),
)


class OffsetAlignmentError(ValueError):
    """Raised when a chunk cannot be made an exact, ordered source slice."""


def _field(value: Any, name: str, default: Any = None) -> Any:
    """Read a field from either a frozen dataclass/object or a mapping."""

    if isinstance(value, Mapping):
        return value.get(name, default)
    return getattr(value, name, default)


def _as_int(value: Any, *, label: str) -> int:
    try:
        integer = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{label} must be an integer, got {value!r}") from exc
    return integer


# --------------------------------------------------------------------------------------
# Exact source alignment
# --------------------------------------------------------------------------------------


def align_chunk_offset(
    source_text: str,
    chunk_text: str,
    reported_start: int,
    reported_end: int,
    *,
    minimum_start: int = 0,
    window: int = ALIGNMENT_WINDOW,
) -> tuple[int, int]:
    """Return an exact half-open source interval for one Chonkie chunk.

    Chonkie occasionally reports an offset a few characters away from its own
    chunk text.  The reported slice is accepted when exact.  Otherwise all exact
    occurrences within ``window`` characters of both reported endpoints are
    considered, constrained to start at or after ``minimum_start``.  The nearest
    occurrence is selected, with the earliest start as the deterministic tie
    breaker.
    """

    if not isinstance(source_text, str) or not isinstance(chunk_text, str):
        raise TypeError("source_text and chunk_text must be strings")
    if not chunk_text:
        raise OffsetAlignmentError("cannot align an empty chunk")
    if window < 0:
        raise ValueError("window must be non-negative")

    reported_start = _as_int(reported_start, label="reported_start")
    reported_end = _as_int(reported_end, label="reported_end")
    minimum_start = _as_int(minimum_start, label="minimum_start")

    if (
        minimum_start <= reported_start <= reported_end <= len(source_text)
        and source_text[reported_start:reported_end] == chunk_text
    ):
        return reported_start, reported_end

    last_possible_start = len(source_text) - len(chunk_text)
    lower = max(0, minimum_start, reported_start - window)
    upper = min(last_possible_start, reported_start + window)
    if lower > upper:
        raise OffsetAlignmentError(
            "no ordered alignment window remains for chunk "
            f"near [{reported_start}, {reported_end})"
        )

    candidates: list[tuple[int, int, int]] = []
    position = source_text.find(chunk_text, lower, upper + len(chunk_text) + 1)
    while position != -1 and position <= upper:
        end = position + len(chunk_text)
        if abs(end - reported_end) <= window:
            distance = abs(position - reported_start) + abs(end - reported_end)
            candidates.append((distance, position, end))
        position = source_text.find(chunk_text, position + 1, upper + len(chunk_text) + 1)

    if not candidates:
        preview = chunk_text[:80].replace("\n", "\\n")
        raise OffsetAlignmentError(
            f"could not align chunk near [{reported_start}, {reported_end}) within "
            f"±{window} characters: {preview!r}"
        )

    _, start, end = min(candidates, key=lambda item: (item[0], item[1]))
    return start, end


def realign_chunk_offsets(
    source_text: str,
    chunks: Iterable[Any],
    *,
    window: int = ALIGNMENT_WINDOW,
) -> list[tuple[int, int]]:
    """Align a sequence of chunk-like objects while enforcing source order."""

    aligned: list[tuple[int, int]] = []
    minimum_start = 0
    for index, chunk in enumerate(chunks):
        text = _field(chunk, "text")
        start = _field(chunk, "start_index", _field(chunk, "char_start"))
        end = _field(chunk, "end_index", _field(chunk, "char_end"))
        if text is None or start is None or end is None:
            raise OffsetAlignmentError(f"chunk {index} is missing text or reported offsets")
        try:
            exact = align_chunk_offset(
                source_text,
                text,
                start,
                end,
                minimum_start=minimum_start,
                window=window,
            )
        except OffsetAlignmentError as exc:
            raise OffsetAlignmentError(f"chunk {index}: {exc}") from exc
        aligned.append(exact)
        minimum_start = exact[1]
    return aligned


def chunk_contract(
    source_text: str,
    chunker: Any,
    *,
    alignment_window: int = ALIGNMENT_WINDOW,
) -> tuple[list[dict[str, Any]], dict[str, int]]:
    """Chunk one contract and return exact metadata plus alignment statistics."""

    raw_chunks = list(chunker(source_text))
    offsets = realign_chunk_offsets(source_text, raw_chunks, window=alignment_window)
    rows: list[dict[str, Any]] = []
    corrections = 0
    blank_skipped = 0

    for raw, (start, end) in zip(raw_chunks, offsets, strict=True):
        text = _field(raw, "text")
        reported_start = _as_int(_field(raw, "start_index"), label="start_index")
        reported_end = _as_int(_field(raw, "end_index"), label="end_index")
        if (start, end) != (reported_start, reported_end):
            corrections += 1
        if source_text[start:end] != text:
            raise AssertionError("realigned chunk is not an exact source slice")

        embed_text = text.strip()
        if not embed_text:
            blank_skipped += 1
            continue
        token_count = _field(raw, "token_count")
        rows.append(
            {
                "chunk_id": len(rows),
                "char_start": start,
                "char_end": end,
                "token_count": int(token_count) if token_count is not None else None,
                "text": text,
                "embed_text": embed_text,
            }
        )

    if not rows:
        raise ValueError("chunker produced no non-blank chunks for a non-empty contract")
    stats = {
        "n_chars": len(source_text),
        "n_raw_chunks": len(raw_chunks),
        "n_chunks": len(rows),
        "n_offset_corrections": corrections,
        "n_blank_skipped": blank_skipped,
    }
    return rows, stats


def validate_cached_chunks(source_text: str, chunks: Sequence[Mapping[str, Any]]) -> None:
    """Reject cache metadata that no longer describes ordered exact source slices."""

    previous_end = 0
    for expected_id, chunk in enumerate(chunks):
        chunk_id = _as_int(chunk.get("chunk_id"), label="chunk_id")
        start = _as_int(chunk.get("char_start"), label="char_start")
        end = _as_int(chunk.get("char_end"), label="char_end")
        text = chunk.get("text")
        if chunk_id != expected_id:
            raise ValueError(f"cached chunk IDs are not contiguous at {expected_id}")
        if start < previous_end or end <= start or end > len(source_text):
            raise ValueError(f"cached chunk {chunk_id} has invalid or unordered offsets")
        if not isinstance(text, str) or source_text[start:end] != text:
            raise ValueError(f"cached chunk {chunk_id} is not an exact source slice")
        if not str(chunk.get("embed_text", "")).strip():
            raise ValueError(f"cached chunk {chunk_id} has no embedding text")
        previous_end = end


# --------------------------------------------------------------------------------------
# Ranking and interval metrics
# --------------------------------------------------------------------------------------


def cutoff_count(n_chunks: int, fraction: float) -> int:
    """Number of chunks selected at a percentile cutoff (at least one if nonempty)."""

    n_chunks = _as_int(n_chunks, label="n_chunks")
    if n_chunks < 0:
        raise ValueError("n_chunks must be non-negative")
    if not (0 < fraction <= 1):
        raise ValueError("fraction must be in (0, 1]")
    if n_chunks == 0:
        return 0
    return min(n_chunks, max(1, math.ceil(fraction * n_chunks)))


def rank_chunks(
    scores: Sequence[float],
    decimals: int = DEFAULT_DECIMALS,
    chunk_ids: Sequence[int | str] | None = None,
) -> list[int | str]:
    """Rank by rounded score descending, with numeric chunk ID as tie breaker."""

    if decimals < 0:
        raise ValueError("decimals must be non-negative")
    ids: list[int | str] = list(range(len(scores))) if chunk_ids is None else list(chunk_ids)
    if len(ids) != len(scores):
        raise ValueError("scores and chunk_ids must have the same length")
    numeric_ids = [_as_int(chunk_id, label="chunk_id") for chunk_id in ids]
    if len(set(numeric_ids)) != len(numeric_ids):
        raise ValueError("chunk IDs must be numerically unique")
    rounded = [round(float(score), decimals) for score in scores]
    order = sorted(range(len(ids)), key=lambda i: (-rounded[i], numeric_ids[i]))
    return [ids[i] for i in order]


def merge_intervals(intervals: Iterable[tuple[int, int]]) -> list[tuple[int, int]]:
    """Return the sorted union of positive-length half-open intervals."""

    normalized: list[tuple[int, int]] = []
    for raw_start, raw_end in intervals:
        start = _as_int(raw_start, label="interval start")
        end = _as_int(raw_end, label="interval end")
        if end < start:
            raise ValueError(f"interval end precedes start: ({start}, {end})")
        if end > start:
            normalized.append((start, end))
    normalized.sort()

    merged: list[tuple[int, int]] = []
    for start, end in normalized:
        if not merged or start > merged[-1][1]:
            merged.append((start, end))
        else:
            merged[-1] = (merged[-1][0], max(merged[-1][1], end))
    return merged


def interval_union_length(intervals: Iterable[tuple[int, int]]) -> int:
    return sum(end - start for start, end in merge_intervals(intervals))


def interval_intersection_length(
    left: Iterable[tuple[int, int]], right: Iterable[tuple[int, int]]
) -> int:
    """Character length of the intersection between two interval unions."""

    a = merge_intervals(left)
    b = merge_intervals(right)
    i = j = total = 0
    while i < len(a) and j < len(b):
        start = max(a[i][0], b[j][0])
        end = min(a[i][1], b[j][1])
        if end > start:
            total += end - start
        if a[i][1] <= b[j][1]:
            i += 1
        else:
            j += 1
    return total


def interval_coverage(
    gold_intervals: Iterable[tuple[int, int]],
    selected_intervals: Iterable[tuple[int, int]],
) -> float:
    """Fraction of union gold characters covered by selected intervals."""

    gold = merge_intervals(gold_intervals)
    denominator = sum(end - start for start, end in gold)
    if denominator == 0:
        return 0.0
    return interval_intersection_length(gold, selected_intervals) / denominator


def intervals_overlap(left: tuple[int, int], right: tuple[int, int]) -> bool:
    """Whether two half-open intervals share at least one character."""

    return max(left[0], right[0]) < min(left[1], right[1])


def provision_metrics(
    gold_intervals: Sequence[tuple[int, int]],
    chunks: Sequence[Mapping[str, Any]],
    ranked_chunk_ids: Sequence[int | str],
    *,
    cutoffs: Sequence[tuple[str, float]] = CUTOFFS,
) -> dict[str, Any]:
    """Compute overlap and coverage diagnostics for one provision."""

    gold = merge_intervals(gold_intervals)
    gold_char_count = interval_union_length(gold)
    if gold_char_count <= 0:
        raise ValueError("a provision must contain at least one positive-length gold segment")

    chunk_by_numeric_id: dict[int, Mapping[str, Any]] = {}
    for chunk in chunks:
        numeric_id = _as_int(chunk.get("chunk_id"), label="chunk_id")
        if numeric_id in chunk_by_numeric_id:
            raise ValueError(f"duplicate chunk ID: {numeric_id}")
        chunk_by_numeric_id[numeric_id] = chunk
    ranked_numeric_ids = [_as_int(chunk_id, label="ranked chunk ID") for chunk_id in ranked_chunk_ids]
    if set(ranked_numeric_ids) != set(chunk_by_numeric_id):
        raise ValueError("ranked chunk IDs must be a permutation of all chunk IDs")

    rank_by_id = {chunk_id: rank for rank, chunk_id in enumerate(ranked_numeric_ids, start=1)}
    overlapping_ids = [
        chunk_id
        for chunk_id, chunk in chunk_by_numeric_id.items()
        if any(
            intervals_overlap(
                (_as_int(chunk["char_start"], label="char_start"), _as_int(chunk["char_end"], label="char_end")),
                gold_interval,
            )
            for gold_interval in gold
        )
    ]
    overlapping_ids.sort(key=lambda chunk_id: rank_by_id[chunk_id])

    by_cutoff: dict[str, dict[str, Any]] = {}
    previous = {"recalled": False, "coverage": 0.0, "majority": False, "full": False}
    for cutoff_name, fraction in cutoffs:
        selected_count = cutoff_count(len(chunks), fraction)
        selected_ids = ranked_numeric_ids[:selected_count]
        selected_intervals = [
            (
                _as_int(chunk_by_numeric_id[chunk_id]["char_start"], label="char_start"),
                _as_int(chunk_by_numeric_id[chunk_id]["char_end"], label="char_end"),
            )
            for chunk_id in selected_ids
        ]
        covered_chars = interval_intersection_length(gold, selected_intervals)
        coverage = covered_chars / gold_char_count
        metrics = {
            "fraction": fraction,
            "selected_chunk_count": selected_count,
            "recalled": covered_chars > 0,
            "covered_gold_chars": covered_chars,
            "coverage": coverage,
            "majority": covered_chars * 2 >= gold_char_count,
            "full": covered_chars == gold_char_count,
        }
        if (
            metrics["recalled"] < previous["recalled"]
            or metrics["coverage"] < previous["coverage"]
            or metrics["majority"] < previous["majority"]
            or metrics["full"] < previous["full"]
        ):
            raise AssertionError("provision metrics are not monotonic across cutoffs")
        previous = metrics
        by_cutoff[cutoff_name] = metrics

    return {
        "gold_char_count": gold_char_count,
        "overlapping_chunk_ids": overlapping_ids,
        "overlapping_chunk_ranks": [rank_by_id[chunk_id] for chunk_id in overlapping_ids],
        "best_rank": min((rank_by_id[chunk_id] for chunk_id in overlapping_ids), default=None),
        "cutoffs": by_cutoff,
    }


def _matrix_shape(scores: Any) -> tuple[int, int]:
    shape = getattr(scores, "shape", None)
    if shape is not None and len(shape) == 2:
        return int(shape[0]), int(shape[1])
    rows = len(scores)
    columns = len(scores[0]) if rows else 0
    if any(len(row) != columns for row in scores):
        raise ValueError("score matrix rows have inconsistent lengths")
    return rows, columns


def _matrix_value(scores: Any, row: int, column: int) -> float:
    try:
        return float(scores[row, column])
    except (TypeError, IndexError):
        return float(scores[row][column])


def evaluate_contract(
    contract: Any,
    categories: Sequence[Any],
    chunks: Sequence[Mapping[str, Any]],
    scores: Any,
    *,
    decimals: int = DEFAULT_DECIMALS,
    cutoffs: Sequence[tuple[str, float]] = CUTOFFS,
) -> list[dict[str, Any]]:
    """Evaluate every gold provision in one contract against a score matrix."""

    score_shape = _matrix_shape(scores)
    if score_shape != (len(chunks), len(categories)):
        raise ValueError(
            f"score matrix has shape {score_shape}; expected {(len(chunks), len(categories))}"
        )

    chunk_ids = [_field(chunk, "chunk_id") for chunk in chunks]
    category_by_id = {_field(category, "category_id"): category for category in categories}
    if len(category_by_id) != len(categories):
        raise ValueError("category IDs must be unique")

    ranking_by_category: dict[str, list[int | str]] = {}
    rounded_by_category: dict[str, dict[int, float]] = {}
    for category_index, category in enumerate(categories):
        category_id = _field(category, "category_id")
        rounded_scores = [
            round(_matrix_value(scores, chunk_index, category_index), decimals)
            for chunk_index in range(len(chunks))
        ]
        ranking_by_category[category_id] = rank_chunks(
            rounded_scores, decimals=decimals, chunk_ids=chunk_ids
        )
        rounded_by_category[category_id] = {
            _as_int(chunk_id, label="chunk_id"): score
            for chunk_id, score in zip(chunk_ids, rounded_scores, strict=True)
        }

    contract_id = _field(contract, "contract_id")
    detail_rows: list[dict[str, Any]] = []
    for provision in _field(contract, "provisions", ()):
        category_id = _field(provision, "category_id")
        if category_id not in category_by_id:
            raise ValueError(
                f"contract {contract_id!r} has provision with unknown category {category_id!r}"
            )
        category = category_by_id[category_id]
        segments = list(_field(provision, "segments", ()))
        segment_rows = [
            {
                "start": _as_int(_field(segment, "start"), label="segment start"),
                "end": _as_int(_field(segment, "end"), label="segment end"),
                "text": _field(segment, "text"),
            }
            for segment in segments
        ]
        metrics = provision_metrics(
            [(segment["start"], segment["end"]) for segment in segment_rows],
            chunks,
            ranking_by_category[category_id],
            cutoffs=cutoffs,
        )
        rank_by_id = {
            _as_int(chunk_id, label="chunk_id"): rank
            for rank, chunk_id in enumerate(ranking_by_category[category_id], start=1)
        }
        chunk_by_id = {
            _as_int(chunk["chunk_id"], label="chunk_id"): chunk for chunk in chunks
        }
        overlapping_chunks = [
            {
                "chunk_id": chunk_id,
                "rank": rank_by_id[chunk_id],
                "score": rounded_by_category[category_id][chunk_id],
                "char_start": _as_int(chunk_by_id[chunk_id]["char_start"], label="char_start"),
                "char_end": _as_int(chunk_by_id[chunk_id]["char_end"], label="char_end"),
            }
            for chunk_id in metrics["overlapping_chunk_ids"]
        ]
        detail_rows.append(
            {
                "contract_id": contract_id,
                "category_id": category_id,
                "category_label": _field(
                    provision, "category_label", _field(category, "label")
                ),
                "provision_id": _field(provision, "provision_id"),
                "provision_index": _field(provision, "provision_index"),
                "provision_text": _field(provision, "text"),
                "segments": segment_rows,
                "gold_char_count": metrics["gold_char_count"],
                "n_chunks": len(chunks),
                "overlapping_chunk_ids": metrics["overlapping_chunk_ids"],
                "overlapping_chunk_ranks": metrics["overlapping_chunk_ranks"],
                "overlapping_chunks": overlapping_chunks,
                "best_rank": metrics["best_rank"],
                "cutoffs": metrics["cutoffs"],
            }
        )
    return detail_rows


# --------------------------------------------------------------------------------------
# Aggregation and atomic result writing
# --------------------------------------------------------------------------------------


def _rate(numerator: int, denominator: int) -> dict[str, int | float]:
    return {
        "numerator": numerator,
        "denominator": denominator,
        "percent": (100.0 * numerator / denominator) if denominator else 0.0,
    }


def aggregate_evaluation(
    detail_rows: Sequence[Mapping[str, Any]],
    categories: Sequence[Any],
    *,
    cutoffs: Sequence[tuple[str, float]] = CUTOFFS,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Create micro-average and all-category aggregates from provision rows."""

    category_meta = {
        _field(category, "category_id"): {
            "category_id": _field(category, "category_id"),
            "category_label": _field(category, "label"),
            "description": _field(category, "description"),
            "query_text": _field(category, "query_text"),
        }
        for category in categories
    }
    if len(category_meta) != len(categories):
        raise ValueError("category IDs must be unique")

    rows_by_category: dict[str, list[Mapping[str, Any]]] = {
        category_id: [] for category_id in category_meta
    }
    for row in detail_rows:
        category_id = row["category_id"]
        if category_id not in rows_by_category:
            raise ValueError(f"detail row has unknown category {category_id!r}")
        rows_by_category[category_id].append(row)

    def aggregate_rows(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
        denominator = len(rows)
        result: dict[str, Any] = {"denominator": denominator, "cutoffs": {}}
        previous = {"any_overlap": 0, "majority_coverage": 0, "full_coverage": 0}
        for cutoff_name, fraction in cutoffs:
            counters = {
                "any_overlap": sum(bool(row["cutoffs"][cutoff_name]["recalled"]) for row in rows),
                "majority_coverage": sum(bool(row["cutoffs"][cutoff_name]["majority"]) for row in rows),
                "full_coverage": sum(bool(row["cutoffs"][cutoff_name]["full"]) for row in rows),
            }
            for metric, numerator in counters.items():
                if numerator < previous[metric]:
                    raise AssertionError(
                        f"aggregate {metric} is not monotonic at {cutoff_name}"
                    )
                previous[metric] = numerator
            result["cutoffs"][cutoff_name] = {
                "fraction": fraction,
                "any_overlap": _rate(counters["any_overlap"], denominator),
                "majority_coverage": _rate(counters["majority_coverage"], denominator),
                "full_coverage": _rate(counters["full_coverage"], denominator),
            }
        return result

    headline = aggregate_rows(detail_rows)
    headline["assertions"] = {
        "provision_metrics_monotonic": True,
        "aggregate_metrics_monotonic": True,
    }

    per_category: list[dict[str, Any]] = []
    for category_id, meta in category_meta.items():
        aggregate = aggregate_rows(rows_by_category[category_id])
        flat: dict[str, Any] = {**meta, "denominator": aggregate["denominator"]}
        for cutoff_name, _ in cutoffs:
            for metric in ("any_overlap", "majority_coverage", "full_coverage"):
                rate = aggregate["cutoffs"][cutoff_name][metric]
                flat[f"{cutoff_name}_{metric}_numerator"] = rate["numerator"]
                flat[f"{cutoff_name}_{metric}_percent"] = rate["percent"]
        per_category.append(flat)
    return headline, per_category


# Friendly alias for callers that use the plan's terminology.
aggregate_results = aggregate_evaluation


def _atomic_write_bytes(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    partial = path.with_name(f".{path.name}.{os.getpid()}.partial")
    try:
        with partial.open("wb") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(partial, path)
    except BaseException:
        partial.unlink(missing_ok=True)
        raise


def _atomic_write_json(path: Path, value: Any) -> None:
    body = json.dumps(value, ensure_ascii=False, indent=2) + "\n"
    _atomic_write_bytes(path, body.encode("utf-8"))


def _atomic_write_jsonl(path: Path, rows: Iterable[Mapping[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    partial = path.with_name(f".{path.name}.{os.getpid()}.partial")
    try:
        with partial.open("w", encoding="utf-8", newline="\n") as handle:
            for row in rows:
                handle.write(json.dumps(row, ensure_ascii=False, separators=(",", ":")))
                handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(partial, path)
    except BaseException:
        partial.unlink(missing_ok=True)
        raise


def write_results(
    out_dir: str | Path,
    summary: Mapping[str, Any],
    per_category: Sequence[Mapping[str, Any]],
    detail_rows: Sequence[Mapping[str, Any]],
) -> tuple[Path, Path, Path]:
    """Atomically write the three public result artifacts."""

    out_path = Path(out_dir)
    summary_path = out_path / "recall_summary.json"
    category_path = out_path / "per_category.csv"
    detail_path = out_path / "provision_recall.jsonl"

    _atomic_write_json(summary_path, summary)
    _atomic_write_jsonl(detail_path, detail_rows)

    fieldnames = list(per_category[0].keys()) if per_category else [
        "category_id",
        "category_label",
        "description",
        "query_text",
        "denominator",
    ]
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=fieldnames, lineterminator="\n")
    writer.writeheader()
    writer.writerows(per_category)
    _atomic_write_bytes(category_path, buffer.getvalue().encode("utf-8"))
    return summary_path, category_path, detail_path


# --------------------------------------------------------------------------------------
# Model, chunker, and cache plumbing
# --------------------------------------------------------------------------------------


def _installed_version(distribution: str) -> str | None:
    try:
        return importlib.metadata.version(distribution)
    except importlib.metadata.PackageNotFoundError:
        return None


def library_versions() -> dict[str, str | None]:
    return {
        "python": platform.python_version(),
        "numpy": _installed_version("numpy"),
        "torch": _installed_version("torch"),
        "transformers": _installed_version("transformers"),
        "sentence_transformers": _installed_version("sentence-transformers"),
        "chonkie": _installed_version("chonkie"),
        "tokie": _installed_version("tokie"),
        "huggingface_hub": _installed_version("huggingface-hub"),
    }


def check_transformers_version() -> str:
    import transformers

    version = transformers.__version__
    numeric = tuple(int(part) for part in re.findall(r"\d+", version)[:2])
    if numeric < MIN_TRANSFORMERS:
        required = ".".join(str(part) for part in MIN_TRANSFORMERS)
        raise RuntimeError(
            f"transformers {version} silently degrades EmbeddingGemma; need >= {required}"
        )
    return version


def resolve_device(requested: str) -> str:
    import torch

    if requested != "auto":
        return requested
    if torch.backends.mps.is_available():
        return "mps"
    if torch.cuda.is_available():
        return "cuda"
    return "cpu"


def build_chunker(
    *,
    tokenizer_id: str,
    model_revision: str,
    recipe: str,
    recipe_revision: str,
    chunk_size: int,
) -> Any:
    """Build Chonkie with the runner's Tokie backend and pinned inputs."""

    from chonkie import RecursiveChunker
    from huggingface_hub import hf_hub_download
    from tokie import Tokenizer as TokieTokenizer

    # Passing a model ID to Chonkie (as runner.py does) selects its Tokie
    # backend. Loading the pinned tokenizer.json explicitly preserves those
    # exact token counts while making the otherwise mutable Hub lookup
    # reproducible. A Transformers tokenizer object is not interchangeable
    # here: Chonkie chooses slightly different chunk boundaries for it.
    tokenizer_path = hf_hub_download(
        repo_id=tokenizer_id,
        filename="tokenizer.json",
        revision=model_revision,
    )
    tokenizer = TokieTokenizer.from_json(tokenizer_path)
    if recipe == "none":
        return RecursiveChunker(tokenizer=tokenizer, chunk_size=chunk_size)

    recipe_path = hf_hub_download(
        repo_id=RECIPE_REPOSITORY,
        repo_type="dataset",
        subfolder="recipes",
        filename=f"{recipe}_{RECIPE_LANGUAGE}.json",
        revision=recipe_revision,
    )
    return RecursiveChunker.from_recipe(
        name=None,
        lang=None,
        path=recipe_path,
        tokenizer=tokenizer,
        chunk_size=chunk_size,
    )


def load_embedding_model(model_id: str, model_revision: str, device: str) -> Any:
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(model_id, revision=model_revision, device=device)


def embed_chunks(model: Any, chunks: Sequence[Mapping[str, Any]], batch_size: int) -> Any:
    import numpy as np

    vectors = model.encode_document(
        [chunk["embed_text"] for chunk in chunks],
        batch_size=batch_size,
        normalize_embeddings=True,
        show_progress_bar=False,
    )
    return np.asarray(vectors, dtype="float32")


def embed_queries(model: Any, query_texts: Sequence[str], batch_size: int) -> Any:
    import numpy as np

    vectors = model.encode_query(
        list(query_texts),
        batch_size=batch_size,
        normalize_embeddings=True,
        show_progress_bar=False,
    )
    return np.asarray(vectors, dtype="float32")


def make_cache_identity(
    contract_id: str,
    source_text: str,
    params: Mapping[str, Any],
) -> tuple[str, str]:
    """Return ``(source_sha256, cache_key)`` using canonical JSON input."""

    source_sha256 = hashlib.sha256(source_text.encode("utf-8")).hexdigest()
    identity = {
        "contract_id": contract_id,
        "source_sha256": source_sha256,
        "params": params,
    }
    canonical = json.dumps(identity, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    cache_key = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    return source_sha256, cache_key


def load_contract_cache(
    cache_dir: str | Path,
    cache_key: str,
    *,
    contract_id: str,
    source_text: str,
    source_sha256: str,
    params: Mapping[str, Any],
) -> tuple[list[dict[str, Any]], Any, dict[str, int]] | None:
    """Load and fully validate one atomic cache entry, or return ``None``."""

    import numpy as np

    path = Path(cache_dir) / f"{cache_key}.npz"
    if not path.is_file():
        return None
    try:
        with np.load(path, allow_pickle=False) as archive:
            vectors = np.asarray(archive["vectors"], dtype="float32")
            metadata = json.loads(str(archive["metadata"].item()))
        if metadata.get("cache_schema_version") != CACHE_SCHEMA_VERSION:
            return None
        if metadata.get("contract_id") != contract_id:
            return None
        if metadata.get("source_sha256") != source_sha256:
            return None
        if metadata.get("params") != dict(params):
            return None
        chunks = metadata.get("chunks")
        stats = metadata.get("stats")
        if not isinstance(chunks, list) or not isinstance(stats, dict):
            return None
        if vectors.ndim != 2 or vectors.shape[0] != len(chunks):
            return None
        validate_cached_chunks(source_text, chunks)
        return chunks, vectors, stats
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError):
        return None


def save_contract_cache(
    cache_dir: str | Path,
    cache_key: str,
    *,
    contract_id: str,
    source_sha256: str,
    params: Mapping[str, Any],
    chunks: Sequence[Mapping[str, Any]],
    vectors: Any,
    stats: Mapping[str, int],
) -> Path:
    """Atomically save chunk metadata and normalized vectors in one NPZ file."""

    import numpy as np

    cache_path = Path(cache_dir) / f"{cache_key}.npz"
    public_chunks = [
        {key: value for key, value in chunk.items() if key != "embed_text"} | {
            "embed_text": chunk["embed_text"]
        }
        for chunk in chunks
    ]
    metadata = {
        "cache_schema_version": CACHE_SCHEMA_VERSION,
        "contract_id": contract_id,
        "source_sha256": source_sha256,
        "params": dict(params),
        "stats": dict(stats),
        "chunks": public_chunks,
    }
    buffer = io.BytesIO()
    np.savez(
        buffer,
        vectors=np.asarray(vectors, dtype="float32"),
        metadata=np.asarray(json.dumps(metadata, ensure_ascii=False, separators=(",", ":"))),
    )
    _atomic_write_bytes(cache_path, buffer.getvalue())
    return cache_path


def _corpus_count(corpus: Any, property_name: str, fallback: int) -> int:
    value = getattr(corpus, property_name, None)
    return int(value) if value is not None else fallback


def enforce_corpus_integrity(corpus: Any) -> dict[str, int]:
    """Enforce the published CUAD corpus invariants before model scoring."""

    contracts = list(corpus.contracts)
    categories = list(corpus.categories)
    provisions = [provision for contract in contracts for provision in contract.provisions]
    segment_references = [segment for provision in provisions for segment in provision.segments]
    fallback_unique_segments = len(
        {
            (
                provision.category_id,
                segment.start,
                segment.end,
                segment.text,
                contract.contract_id,
            )
            for contract in contracts
            for provision in contract.provisions
            for segment in provision.segments
        }
    )
    counts = {
        "contracts": _corpus_count(corpus, "contract_count", len(contracts)),
        "categories": _corpus_count(corpus, "category_count", len(categories)),
        "questions": _corpus_count(
            corpus, "question_count", len(contracts) * len(categories)
        ),
        "provisions": _corpus_count(corpus, "provision_count", len(provisions)),
        "unique_gold_segments": _corpus_count(
            corpus, "gold_segment_count", fallback_unique_segments
        ),
        "segment_references": _corpus_count(
            corpus, "segment_reference_count", len(segment_references)
        ),
        "positive_pairs": _corpus_count(
            corpus,
            "positive_pair_count",
            len(
                {
                    (contract.contract_id, provision.category_id)
                    for contract in contracts
                    for provision in contract.provisions
                }
            ),
        ),
    }
    expected = {
        "contracts": EXPECTED_CONTRACTS,
        "categories": EXPECTED_CATEGORIES,
        "questions": EXPECTED_QUESTIONS,
        "provisions": EXPECTED_PROVISIONS,
        "unique_gold_segments": EXPECTED_UNIQUE_GOLD_SEGMENTS,
        "positive_pairs": EXPECTED_POSITIVE_PAIRS,
    }
    mismatches = {
        key: (counts[key], expected_value)
        for key, expected_value in expected.items()
        if counts[key] != expected_value
    }
    if mismatches:
        formatted = ", ".join(
            f"{key}={actual} (expected {wanted})"
            for key, (actual, wanted) in mismatches.items()
        )
        raise ValueError(f"CUAD corpus integrity check failed: {formatted}")
    return counts


def _cache_params(args: argparse.Namespace, device: str, versions: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "cache_schema_version": CACHE_SCHEMA_VERSION,
        "dataset_id": DATASET_ID,
        "dataset_revision": args.revision,
        "model_id": args.model,
        "model_revision": args.model_revision,
        "tokenizer_id": args.tokenizer,
        # The CLI intentionally has one HF model revision: the default tokenizer
        # belongs to the same repository and is pinned to that exact commit.
        "tokenizer_revision": args.model_revision,
        "tokenizer_backend": "tokie",
        "tokenizer_backend_version": versions.get("tokie"),
        "recipe_id": args.recipe,
        "recipe_repository": RECIPE_REPOSITORY if args.recipe != "none" else None,
        "recipe_revision": args.recipe_revision if args.recipe != "none" else None,
        "recipe_language": RECIPE_LANGUAGE if args.recipe != "none" else None,
        "chunk_size_tokens": args.chunk_size,
        "alignment_window_chars": ALIGNMENT_WINDOW,
        "batch_size": args.batch_size,
        "device": device,
        "libraries": {
            name: versions.get(name)
            for name in (
                "numpy",
                "torch",
                "transformers",
                "sentence_transformers",
                "chonkie",
                "tokie",
            )
        },
    }


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--revision", default=DATASET_REVISION, help="pinned CUAD dataset revision")
    parser.add_argument("--model", default=MODEL_ID)
    parser.add_argument("--model-revision", default=MODEL_REVISION)
    parser.add_argument("--tokenizer", default=TOKENIZER_ID)
    parser.add_argument("--recipe", default=RECIPE_ID, help="Chonkie recipe name, or 'none'")
    parser.add_argument("--recipe-revision", default=RECIPE_REVISION)
    parser.add_argument("--chunk-size", type=int, default=DEFAULT_CHUNK_SIZE)
    parser.add_argument("--batch-size", type=int, default=DEFAULT_BATCH_SIZE)
    parser.add_argument("--device", default="auto", help="auto | mps | cuda | cpu")
    parser.add_argument("--decimals", type=int, default=DEFAULT_DECIMALS)
    parser.add_argument("--data-dir", default="results/cuad_validation/data")
    parser.add_argument("--out-dir", default="results/cuad_validation")
    parser.add_argument("--cache-dir", default="results/cuad_validation/cache")
    parser.add_argument("--force", action="store_true", help="ignore valid contract caches")
    return parser


def _validate_args(parser: argparse.ArgumentParser, args: argparse.Namespace) -> None:
    if args.chunk_size <= 0:
        parser.error("--chunk-size must be positive")
    if args.batch_size <= 0:
        parser.error("--batch-size must be positive")
    if args.decimals < 0:
        parser.error("--decimals must be non-negative")
    if args.device not in {"auto", "mps", "cuda", "cpu"}:
        parser.error("--device must be one of: auto, mps, cuda, cpu")


def _print_final_table(headline: Mapping[str, Any]) -> None:
    print("\nCUAD provision recall (micro-average)")
    print("cutoff   any overlap            >=50% coverage         full coverage")
    for cutoff_name, fraction in CUTOFFS:
        metrics = headline["cutoffs"][cutoff_name]
        values = []
        for key in ("any_overlap", "majority_coverage", "full_coverage"):
            rate = metrics[key]
            values.append(
                f"{rate['numerator']:5d}/{rate['denominator']:<5d} ({rate['percent']:6.2f}%)"
            )
        print(f"top {fraction * 100:>2.0f}%  " + "  ".join(values))


def main(argv: Sequence[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    _validate_args(parser, args)

    from .prepare_cuad_data import load_cuad

    data_dir = Path(args.data_dir).resolve()
    out_dir = Path(args.out_dir).resolve()
    cache_dir = Path(args.cache_dir).resolve()

    print(f"loading CUAD {DATASET_ID}@{args.revision}", flush=True)
    corpus = load_cuad(data_dir, revision=args.revision, download=True)
    corpus_counts = enforce_corpus_integrity(corpus)
    categories = list(corpus.categories)
    contracts = list(corpus.contracts)
    print(
        f"corpus: {corpus_counts['contracts']} contracts, {corpus_counts['categories']} categories, "
        f"{corpus_counts['provisions']:,} provisions, "
        f"{corpus_counts['unique_gold_segments']:,} unique segments",
        flush=True,
    )

    transformers_version = check_transformers_version()
    device = resolve_device(args.device)
    versions = library_versions()
    versions["transformers"] = transformers_version
    print(f"device: {device} | transformers: {transformers_version}", flush=True)

    model = load_embedding_model(args.model, args.model_revision, device)
    print(
        f"model: {args.model}@{args.model_revision} "
        f"(dimension {model.get_embedding_dimension()}, window {model.max_seq_length})",
        flush=True,
    )
    if args.chunk_size > int(model.max_seq_length):
        raise ValueError(
            f"chunk size {args.chunk_size} exceeds model window {model.max_seq_length}"
        )

    query_vectors = embed_queries(
        model, [_field(category, "query_text") for category in categories], args.batch_size
    )
    if query_vectors.shape[0] != EXPECTED_CATEGORIES:
        raise AssertionError(
            f"query matrix has {query_vectors.shape[0]} rows, expected {EXPECTED_CATEGORIES}"
        )

    params = _cache_params(args, device, versions)
    chunker = None
    all_detail_rows: list[dict[str, Any]] = []
    cache_hits = 0
    cache_misses = 0
    total_chunks = 0
    total_scores = 0
    chunking_totals: dict[str, int] = {}

    for contract_index, contract in enumerate(contracts, start=1):
        source_sha256, cache_key = make_cache_identity(contract.contract_id, contract.text, params)
        cached = None
        if not args.force:
            cached = load_contract_cache(
                cache_dir,
                cache_key,
                contract_id=contract.contract_id,
                source_text=contract.text,
                source_sha256=source_sha256,
                params=params,
            )

        if cached is not None:
            chunks, vectors, stats = cached
            cache_hits += 1
            cache_status = "cached"
        else:
            cache_misses += 1
            if chunker is None:
                print(
                    f"chunker: RecursiveChunker {args.recipe}@{args.recipe_revision}, "
                    f"{args.chunk_size} tokens",
                    flush=True,
                )
                chunker = build_chunker(
                    tokenizer_id=args.tokenizer,
                    model_revision=args.model_revision,
                    recipe=args.recipe,
                    recipe_revision=args.recipe_revision,
                    chunk_size=args.chunk_size,
                )
            chunks, stats = chunk_contract(contract.text, chunker)
            vectors = embed_chunks(model, chunks, args.batch_size)
            if vectors.shape[0] != len(chunks):
                raise AssertionError("embedding row count does not match chunk count")
            save_contract_cache(
                cache_dir,
                cache_key,
                contract_id=contract.contract_id,
                source_sha256=source_sha256,
                params=params,
                chunks=chunks,
                vectors=vectors,
                stats=stats,
            )
            cache_status = "rebuilt" if args.force else "miss"

        validate_cached_chunks(contract.text, chunks)
        scores = vectors @ query_vectors.T
        expected_shape = (len(chunks), len(categories))
        if scores.shape != expected_shape:
            raise AssertionError(f"score matrix has shape {scores.shape}, expected {expected_shape}")
        detail_rows = evaluate_contract(
            contract,
            categories,
            chunks,
            scores,
            decimals=args.decimals,
        )
        all_detail_rows.extend(detail_rows)
        total_chunks += len(chunks)
        total_scores += int(scores.size)
        for name, value in stats.items():
            chunking_totals[name] = chunking_totals.get(name, 0) + int(value)

        display_id = contract.contract_id.replace("\n", " ")
        if len(display_id) > 62:
            display_id = display_id[:59] + "..."
        print(
            f"[{contract_index:3d}/{len(contracts)}] {display_id:<62} "
            f"{len(chunks):4d} chunks, {len(detail_rows):3d} provisions ({cache_status})",
            flush=True,
        )

    if len(all_detail_rows) != EXPECTED_PROVISIONS:
        raise AssertionError(
            f"evaluated {len(all_detail_rows):,} provisions, expected {EXPECTED_PROVISIONS:,}"
        )
    expected_scores = total_chunks * EXPECTED_CATEGORIES
    if total_scores != expected_scores:
        raise AssertionError(f"computed {total_scores:,} scores, expected {expected_scores:,}")

    headline, per_category = aggregate_evaluation(all_detail_rows, categories)
    if headline["denominator"] != EXPECTED_PROVISIONS:
        raise AssertionError("micro-average denominator changed during aggregation")

    generated_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    summary = {
        "schema_version": SCHEMA_VERSION,
        "generated_at": generated_at,
        "dataset": {
            "id": DATASET_ID,
            "revision": args.revision,
            "data_dir": str(data_dir),
        },
        "model": {
            "id": args.model,
            "revision": args.model_revision,
            "embedding_dimension": int(query_vectors.shape[1]),
            "device": device,
        },
        "chunking": {
            "library": "chonkie",
            "chunker": "RecursiveChunker",
            "recipe": args.recipe,
            "recipe_repository": RECIPE_REPOSITORY,
            "recipe_revision": args.recipe_revision,
            "recipe_language": RECIPE_LANGUAGE,
            "chunk_size_tokens": args.chunk_size,
            "tokenizer": args.tokenizer,
            "tokenizer_revision": args.model_revision,
            "tokenizer_backend": "tokie",
            "tokenizer_backend_version": versions.get("tokie"),
            "alignment_window_chars": ALIGNMENT_WINDOW,
            "stats": chunking_totals,
        },
        "scoring": {
            "similarity": "cosine (dot product of L2-normalized embeddings)",
            "round_before_ranking_decimals": args.decimals,
            "tie_breaker": "numeric chunk_id ascending",
            "query_template": "{category}. {official description}",
            "cutoff_chunk_count": "max(1, ceil(fraction * document_chunks))",
            "primary_recall": "positive character overlap with any gold segment",
        },
        "versions": versions,
        "counts": {
            **corpus_counts,
            "chunks": total_chunks,
            "scores": total_scores,
        },
        "cache": {
            "directory": str(cache_dir),
            "hits": cache_hits,
            "misses": cache_misses,
            "force": bool(args.force),
            "cache_schema_version": CACHE_SCHEMA_VERSION,
        },
        "recall": headline,
        "assertions": {
            "corpus_integrity": True,
            "all_chunk_offsets_exact": True,
            "score_dimensions": True,
            "micro_denominator_13101": True,
            "recall_monotonic": True,
        },
    }
    paths = write_results(out_dir, summary, per_category, all_detail_rows)
    _print_final_table(headline)
    for path in paths:
        print(f"wrote {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
