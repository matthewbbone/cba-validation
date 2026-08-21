#!/usr/bin/env python3
"""Run and summarize the locked CUAD recall benchmark for three embedding models."""

from __future__ import annotations

import argparse
import csv
import io
import json
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Sequence

from .evaluate_recall import (
    CUTOFFS,
    DATASET_REVISION,
    DEFAULT_BATCH_SIZE,
    DEFAULT_CHUNK_SIZE,
    DEFAULT_DECIMALS,
    EXPECTED_PROVISIONS,
    RECIPE_ID,
    RECIPE_REVISION,
    TOKENIZER_ID,
    TOKENIZER_REVISION,
    _atomic_write_bytes,
    _atomic_write_json,
)


SCHEMA_VERSION = "cuad_model_comparison_v1"


@dataclass(frozen=True)
class ModelProfile:
    model_id: str
    revision: str
    query_prompt_name: str
    document_prompt_name: str

    @property
    def slug(self) -> str:
        return self.model_id.casefold().replace("/", "__").replace(".", "_")


MODEL_PROFILES: tuple[ModelProfile, ...] = (
    ModelProfile(
        "google/embeddinggemma-300m",
        "57c266a740f537b4dc058e1b0cda161fd15afa75",
        "query",
        "document",
    ),
    ModelProfile(
        "microsoft/harrier-oss-v1-0.6b",
        "f9b9dc8d367d443f2479d27aa5d8d2850c0774ee",
        "web_search_query",
        "none",
    ),
    ModelProfile(
        "Qwen/Qwen3-Embedding-0.6B",
        "97b0c614be4d77ee51c0cef4e5f07c00f9eb65b3",
        "query",
        "none",
    ),
)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--revision", default=DATASET_REVISION)
    parser.add_argument("--data-dir", default="results/cuad_validation/data")
    parser.add_argument("--out-root", default="results/cuad_validation/model_comparison")
    parser.add_argument("--cache-root", default="results/cuad_validation/model_cache")
    parser.add_argument("--tokenizer", default=TOKENIZER_ID)
    parser.add_argument("--tokenizer-revision", default=TOKENIZER_REVISION)
    parser.add_argument("--recipe", default=RECIPE_ID)
    parser.add_argument("--recipe-revision", default=RECIPE_REVISION)
    parser.add_argument("--chunk-size", type=int, default=DEFAULT_CHUNK_SIZE)
    parser.add_argument("--batch-size", type=int, default=DEFAULT_BATCH_SIZE)
    parser.add_argument("--device", default="auto")
    parser.add_argument("--decimals", type=int, default=DEFAULT_DECIMALS)
    parser.add_argument("--force", action="store_true")
    parser.add_argument(
        "--summarize-only",
        action="store_true",
        help="do not run models; rebuild comparison files from existing summaries",
    )
    return parser


def evaluator_command(
    profile: ModelProfile,
    args: argparse.Namespace,
    out_dir: Path,
    cache_dir: Path,
) -> list[str]:
    command = [
        sys.executable,
        "-m",
        "pipeline.cuad_validation.evaluate_recall",
        "--revision",
        args.revision,
        "--data-dir",
        str(Path(args.data_dir)),
        "--out-dir",
        str(out_dir),
        "--cache-dir",
        str(cache_dir),
        "--model",
        profile.model_id,
        "--model-revision",
        profile.revision,
        "--tokenizer",
        args.tokenizer,
        "--tokenizer-revision",
        args.tokenizer_revision,
        "--query-prompt-name",
        profile.query_prompt_name,
        "--document-prompt-name",
        profile.document_prompt_name,
        "--recipe",
        args.recipe,
        "--recipe-revision",
        args.recipe_revision,
        "--chunk-size",
        str(args.chunk_size),
        "--batch-size",
        str(args.batch_size),
        "--device",
        args.device,
        "--decimals",
        str(args.decimals),
    ]
    if args.force:
        command.append("--force")
    return command


def load_model_result(profile: ModelProfile, out_dir: Path) -> dict[str, Any]:
    summary_path = out_dir / "recall_summary.json"
    try:
        summary = json.loads(summary_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"could not read completed result {summary_path}: {exc}") from exc
    expected = {
        "model id": (summary["model"]["id"], profile.model_id),
        "model revision": (summary["model"]["revision"], profile.revision),
        "query prompt": (
            summary["scoring"]["query_prompt_name"],
            None if profile.query_prompt_name == "none" else profile.query_prompt_name,
        ),
        "document prompt": (
            summary["scoring"]["document_prompt_name"],
            None if profile.document_prompt_name == "none" else profile.document_prompt_name,
        ),
        "denominator": (summary["recall"]["denominator"], EXPECTED_PROVISIONS),
    }
    mismatches = [
        f"{name}={actual!r}, expected {wanted!r}"
        for name, (actual, wanted) in expected.items()
        if actual != wanted
    ]
    if mismatches:
        raise RuntimeError(f"invalid result in {summary_path}: " + "; ".join(mismatches))
    return summary


def build_comparison(
    results: Sequence[tuple[ModelProfile, Path, dict[str, Any], float | None]],
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    models: list[dict[str, Any]] = []
    rows: list[dict[str, Any]] = []
    for profile, out_dir, summary, elapsed_seconds in results:
        entry = {
            "model": summary["model"],
            "query_prompt_name": summary["scoring"]["query_prompt_name"],
            "document_prompt_name": summary["scoring"]["document_prompt_name"],
            "elapsed_seconds_this_invocation": elapsed_seconds,
            "counts": summary["counts"],
            "recall": summary["recall"],
            "result_directory": str(out_dir.resolve()),
        }
        models.append(entry)
        row: dict[str, Any] = {
            "model_id": profile.model_id,
            "revision": profile.revision,
            "embedding_dimension": summary["model"]["embedding_dimension"],
            "query_prompt_name": summary["scoring"]["query_prompt_name"],
            "document_prompt_name": summary["scoring"]["document_prompt_name"],
        }
        for cutoff_name, _ in CUTOFFS:
            for metric in ("any_overlap", "majority_coverage", "full_coverage"):
                rate = summary["recall"]["cutoffs"][cutoff_name][metric]
                row[f"{cutoff_name}_{metric}_numerator"] = rate["numerator"]
                row[f"{cutoff_name}_{metric}_percent"] = rate["percent"]
        rows.append(row)
    comparison = {
        "schema_version": SCHEMA_VERSION,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "method": {
            "fixed_dataset_revision": results[0][2]["dataset"]["revision"],
            "fixed_tokenizer": results[0][2]["chunking"]["tokenizer"],
            "fixed_tokenizer_revision": results[0][2]["chunking"]["tokenizer_revision"],
            "fixed_recipe": results[0][2]["chunking"]["recipe"],
            "fixed_recipe_revision": results[0][2]["chunking"]["recipe_revision"],
            "fixed_chunk_size_tokens": results[0][2]["chunking"]["chunk_size_tokens"],
            "round_before_ranking_decimals": results[0][2]["scoring"][
                "round_before_ranking_decimals"
            ],
            "denominator": EXPECTED_PROVISIONS,
        },
        "models": models,
    }
    return comparison, rows


def write_comparison(out_root: Path, comparison: dict[str, Any], rows: list[dict[str, Any]]) -> None:
    _atomic_write_json(out_root / "model_comparison.json", comparison)
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=list(rows[0]))
    writer.writeheader()
    writer.writerows(rows)
    _atomic_write_bytes(
        out_root / "model_comparison.csv",
        buffer.getvalue().encode("utf-8"),
    )


def print_comparison(rows: Sequence[dict[str, Any]]) -> None:
    print("\nCUAD any-overlap provision recall by embedding model")
    print("model                                      top 1%   top 5%  top 25%  top 50%")
    for row in rows:
        values = [
            row[f"{cutoff_name}_any_overlap_percent"]
            for cutoff_name, _ in CUTOFFS
        ]
        print(
            f"{row['model_id']:<42} "
            + "  ".join(f"{value:7.2f}%" for value in values)
        )


def main(argv: Sequence[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    out_root = Path(args.out_root)
    cache_root = Path(args.cache_root)
    results: list[tuple[ModelProfile, Path, dict[str, Any], float | None]] = []
    for index, profile in enumerate(MODEL_PROFILES, start=1):
        out_dir = out_root / profile.slug
        cache_dir = cache_root / profile.slug
        elapsed: float | None = None
        if not args.summarize_only:
            print(f"\n=== [{index}/{len(MODEL_PROFILES)}] {profile.model_id} ===", flush=True)
            started = time.monotonic()
            subprocess.run(
                evaluator_command(profile, args, out_dir, cache_dir),
                check=True,
            )
            elapsed = time.monotonic() - started
        summary = load_model_result(profile, out_dir)
        results.append((profile, out_dir, summary, elapsed))

    comparison, rows = build_comparison(results)
    write_comparison(out_root, comparison, rows)
    print_comparison(rows)
    print(f"wrote {out_root / 'model_comparison.json'}")
    print(f"wrote {out_root / 'model_comparison.csv'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
