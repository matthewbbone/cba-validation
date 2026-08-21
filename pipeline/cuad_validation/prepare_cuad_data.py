#!/usr/bin/env python3
"""Download and exactly align CUAD master provisions to SQuAD source spans.

No network access occurs at import time. ``master_clauses.csv`` supplies the
13,101 provision groupings, while ``CUAD_v1.json`` supplies all contract text
and authoritative answer offsets.
"""

from __future__ import annotations

import argparse
import ast
import csv
import json
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

DATASET_ID = "theatticusproject/cuad"
DATASET_REVISION = "a3c393f5d103fd0c516374e4fdff676c8176dcb1"
MASTER_CLAUSES_FILENAME = "CUAD_v1/master_clauses.csv"
SQUAD_JSON_FILENAME = "CUAD_v1/CUAD_v1.json"

EXPECTED_CONTRACTS = 510
EXPECTED_CATEGORIES = 41
EXPECTED_QUESTIONS = 20_910
EXPECTED_PROVISIONS = 13_101
EXPECTED_GOLD_SEGMENTS = 13_823
EXPECTED_POSITIVE_PAIRS = 6_702

_QUESTION_RE = re.compile(
    r'^Highlight the parts \(if any\) of this contract related to "(?P<label>.*?)" '
    r"that should be reviewed by a lawyer\. Details: (?P<description>.*)$",
    re.DOTALL,
)


class CuadDataError(ValueError):
    """The pinned CUAD files violate their expected schema or counts."""


@dataclass(frozen=True)
class GoldSegment:
    text: str
    start: int
    end: int


@dataclass(frozen=True)
class Provision:
    provision_id: str
    category_id: str
    category_label: str
    provision_index: int
    text: str
    segments: tuple[GoldSegment, ...]


@dataclass(frozen=True)
class Category:
    category_id: str
    label: str
    description: str
    query_text: str


@dataclass(frozen=True)
class Contract:
    contract_id: str
    text: str
    provisions: tuple[Provision, ...]


@dataclass(frozen=True)
class CuadCorpus:
    contracts: tuple[Contract, ...]
    categories: tuple[Category, ...]

    @property
    def contract_count(self) -> int:
        return len(self.contracts)

    @property
    def category_count(self) -> int:
        return len(self.categories)

    @property
    def question_count(self) -> int:
        return self.contract_count * self.category_count

    @property
    def provision_count(self) -> int:
        return sum(len(contract.provisions) for contract in self.contracts)

    @property
    def segment_reference_count(self) -> int:
        return sum(
            len(provision.segments)
            for contract in self.contracts
            for provision in contract.provisions
        )

    @property
    def gold_segment_count(self) -> int:
        """Unique spans, scoped by contract and category.

        Eight exact JSON spans are reused by distinct master provisions, so
        references number 13,831 while unique gold spans number 13,823.
        """
        return len(
            {
                (
                    contract.contract_id,
                    provision.category_id,
                    segment.start,
                    segment.end,
                    segment.text,
                )
                for contract in self.contracts
                for provision in contract.provisions
                for segment in provision.segments
            }
        )

    @property
    def positive_pair_count(self) -> int:
        return sum(
            len({provision.category_id for provision in contract.provisions})
            for contract in self.contracts
        )


def parse_csv_list(value: str) -> tuple[str, ...]:
    """Safely parse a Python-list-valued master CSV context cell."""
    if not isinstance(value, str):
        raise CuadDataError(f"context cell must be a string, got {type(value).__name__}")
    try:
        parsed = ast.literal_eval(value)
    except (SyntaxError, ValueError) as exc:
        raise CuadDataError(f"invalid context-list literal: {value!r}") from exc
    if not isinstance(parsed, list):
        raise CuadDataError(f"context cell must contain a list, got {type(parsed).__name__}")
    if any(not isinstance(item, str) for item in parsed):
        raise CuadDataError("context list contains a non-string item")
    return tuple(parsed)


def normalize_key(value: str) -> str:
    """Normalize a title/category for a collision-checked join.

    The CSV has PDF suffixes while JSON titles do not; one pinned CSV filename
    also has a stray apostrophe after ``.PDF``.
    """
    if not isinstance(value, str):
        raise CuadDataError(f"join key must be a string, got {type(value).__name__}")
    cleaned = re.sub(r"[\s'\"]+$", "", value.strip().casefold())
    cleaned = re.sub(r"\.pdf$", "", cleaned, flags=re.IGNORECASE)
    normalized = re.sub(r"[^a-z0-9]+", "", cleaned)
    if not normalized:
        raise CuadDataError(f"join key normalizes to empty: {value!r}")
    return normalized


def split_provision(value: str) -> tuple[str, ...]:
    """Split literal ``<omitted>`` pieces, dropping empties and repeated text."""
    if not isinstance(value, str):
        raise CuadDataError(f"provision must be a string, got {type(value).__name__}")
    seen: set[str] = set()
    result: list[str] = []
    for raw in value.split("<omitted>"):
        piece = raw.strip()
        if piece and piece not in seen:
            seen.add(piece)
            result.append(piece)
    return tuple(result)


def align_gold_segments(
    context: str,
    segment_texts: Sequence[str],
    answers: Sequence[Mapping[str, Any]],
) -> tuple[GoldSegment, ...]:
    """Map master pieces to exact JSON answers; never fall back to fuzzy search."""
    if not isinstance(context, str):
        raise CuadDataError("contract context must be a string")
    by_text: dict[str, GoldSegment] = {}
    for index, answer in enumerate(answers):
        if not isinstance(answer, Mapping):
            raise CuadDataError(f"answer {index} is not an object")
        text = answer.get("text")
        start = answer.get("answer_start")
        if not isinstance(text, str) or not isinstance(start, int) or isinstance(start, bool):
            raise CuadDataError(f"answer {index} needs string text and integer answer_start")
        end = start + len(text)
        if start < 0 or end > len(context) or context[start:end] != text:
            raise CuadDataError(
                f"answer {index} does not exactly slice context at [{start}:{end}]"
            )
        segment = GoldSegment(text, start, end)
        previous = by_text.get(text)
        if previous is not None and previous != segment:
            raise CuadDataError(f"identical answer text occurs at ambiguous offsets: {text!r}")
        by_text[text] = segment

    aligned: list[GoldSegment] = []
    seen: set[GoldSegment] = set()
    for index, text in enumerate(segment_texts):
        if not isinstance(text, str):
            raise CuadDataError(f"segment {index} is not a string")
        if text not in by_text:
            raise CuadDataError(f"master segment has no exact JSON answer: {text!r}")
        segment = by_text[text]
        if segment not in seen:
            seen.add(segment)
            aligned.append(segment)
    return tuple(aligned)


def _slugify(label: str) -> str:
    value = re.sub(r"[^a-z0-9]+", "_", label.casefold()).strip("_")
    if not value:
        raise CuadDataError(f"empty category id for {label!r}")
    return value


def _unique_index(values: Sequence[str], *, kind: str) -> dict[str, str]:
    result: dict[str, str] = {}
    for value in values:
        key = normalize_key(value)
        if key in result:
            raise CuadDataError(
                f"normalized {kind} collision for {key!r}: {result[key]!r}, {value!r}"
            )
        result[key] = value
    return result


def _artifact_paths(data_dir: str | Path) -> tuple[Path, Path]:
    root = Path(data_dir).expanduser()
    return root / MASTER_CLAUSES_FILENAME, root / SQUAD_JSON_FILENAME


def acquire_cuad(
    data_dir: str | Path,
    revision: str = DATASET_REVISION,
) -> tuple[Path, Path]:
    """Download only the master CSV and complete SQuAD JSON into ``data_dir``."""
    if not revision:
        raise ValueError("dataset revision must be non-empty")
    try:
        from huggingface_hub import hf_hub_download
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError("huggingface-hub is required to acquire CUAD") from exc
    root = Path(data_dir).expanduser()
    root.mkdir(parents=True, exist_ok=True)
    paths = [
        Path(
            hf_hub_download(
                repo_id=DATASET_ID,
                filename=filename,
                repo_type="dataset",
                revision=revision,
                local_dir=root,
            )
        )
        for filename in (MASTER_CLAUSES_FILENAME, SQUAD_JSON_FILENAME)
    ]
    return paths[0], paths[1]


def _load_json(path: Path) -> list[dict[str, Any]]:
    try:
        with path.open(encoding="utf-8") as handle:
            payload = json.load(handle)
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise CuadDataError(f"could not read CUAD JSON {path}: {exc}") from exc
    if not isinstance(payload, dict) or not isinstance(payload.get("data"), list):
        raise CuadDataError("CUAD JSON must contain a top-level data list")
    documents = payload["data"]
    if any(not isinstance(document, dict) for document in documents):
        raise CuadDataError("CUAD JSON data contains a non-object document")
    return documents


def _load_master_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    try:
        with path.open(encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            fields = reader.fieldnames
            if fields is None:
                raise CuadDataError("master CSV has no header")
            rows = list(reader)
    except (OSError, UnicodeError, csv.Error) as exc:
        raise CuadDataError(f"could not read CUAD master CSV {path}: {exc}") from exc
    if not fields or fields[0] != "Filename" or (len(fields) - 1) % 2:
        raise CuadDataError("master CSV must start with Filename then context/answer pairs")
    contexts, answer_fields = fields[1::2], fields[2::2]
    for label, answer_label in zip(contexts, answer_fields, strict=True):
        if normalize_key(answer_label) != normalize_key(f"{label} Answer"):
            raise CuadDataError(f"unpaired context/answer columns: {label!r}, {answer_label!r}")
    if any(None in row or any(value is None for value in row.values()) for row in rows):
        raise CuadDataError("master CSV has an extra-column or short row")
    return contexts, rows


def _parse_question(value: Any, location: str) -> tuple[str, str]:
    if not isinstance(value, str) or (match := _QUESTION_RE.fullmatch(value)) is None:
        raise CuadDataError(f"{location} has an unrecognized CUAD question: {value!r}")
    label, description = match.group("label").strip(), match.group("description").strip()
    if not label or not description:
        raise CuadDataError(f"{location} has an empty label or description")
    return label, description


def _document_parts(
    document: Mapping[str, Any], index: int
) -> tuple[str, str, list[Mapping[str, Any]]]:
    title, paragraphs = document.get("title"), document.get("paragraphs")
    if not isinstance(title, str) or not title:
        raise CuadDataError(f"JSON document {index} has no title")
    if not isinstance(paragraphs, list) or len(paragraphs) != 1:
        raise CuadDataError(f"JSON document {title!r} must have exactly one paragraph")
    paragraph = paragraphs[0]
    if not isinstance(paragraph, dict):
        raise CuadDataError(f"JSON document {title!r} paragraph is not an object")
    context, qas = paragraph.get("context"), paragraph.get("qas")
    if not isinstance(context, str):
        raise CuadDataError(f"JSON document {title!r} context is not a string")
    if not isinstance(qas, list) or any(not isinstance(qa, dict) for qa in qas):
        raise CuadDataError(f"JSON document {title!r} qas is not a list of objects")
    return title, context, qas


def _answers(context: str, qa: Mapping[str, Any], location: str) -> list[Mapping[str, Any]]:
    answers = qa.get("answers")
    impossible = qa.get("is_impossible")
    if not isinstance(answers, list) or any(not isinstance(a, dict) for a in answers):
        raise CuadDataError(f"{location} answers is not a list of objects")
    if not isinstance(impossible, bool) or impossible == bool(answers):
        raise CuadDataError(f"{location} has inconsistent answers/is_impossible")
    align_gold_segments(context, (), answers)  # validates every exact slice
    return answers


def load_cuad(
    data_dir: str | Path,
    revision: str = DATASET_REVISION,
    download: bool = True,
) -> CuadCorpus:
    """Load and join CUAD, failing unless all published invariants hold."""
    if download:
        master_path, json_path = acquire_cuad(data_dir, revision)
    else:
        master_path, json_path = _artifact_paths(data_dir)
        missing = [str(path) for path in (master_path, json_path) if not path.is_file()]
        if missing:
            raise FileNotFoundError("missing CUAD artifact(s): " + ", ".join(missing))

    documents = _load_json(json_path)
    context_headers, master_rows = _load_master_csv(master_path)
    for name, observed, expected in (
        ("JSON contracts", len(documents), EXPECTED_CONTRACTS),
        ("master contracts", len(master_rows), EXPECTED_CONTRACTS),
        ("master categories", len(context_headers), EXPECTED_CATEGORIES),
    ):
        if observed != expected:
            raise CuadDataError(f"expected {expected} {name}, found {observed}")

    parts = [_document_parts(document, i) for i, document in enumerate(documents)]
    json_titles = _unique_index([title for title, _, _ in parts], kind="JSON title")
    filenames: list[str] = []
    for row_number, row in enumerate(master_rows, 2):
        filename = row.get("Filename")
        if not isinstance(filename, str) or not filename:
            raise CuadDataError(f"master row {row_number} has no Filename")
        filenames.append(filename)
    master_titles = _unique_index(filenames, kind="master filename")
    if json_titles.keys() != master_titles.keys():
        raise CuadDataError("normalized JSON/master contract-title sets differ")
    master_by_filename = {row["Filename"]: row for row in master_rows}
    master_categories = _unique_index(context_headers, kind="master category")

    _, first_context, first_qas = parts[0]
    category_specs: list[tuple[str, str]] = []
    first_keys: set[str] = set()
    for index, qa in enumerate(first_qas):
        label, description = _parse_question(qa.get("question"), f"first-document QA {index}")
        key = normalize_key(label)
        if key in first_keys:
            raise CuadDataError(f"first document repeats category {label!r}")
        first_keys.add(key)
        _answers(first_context, qa, f"first-document category {label!r}")
        category_specs.append((label, description))
    if len(category_specs) != EXPECTED_CATEGORIES:
        raise CuadDataError(f"expected {EXPECTED_CATEGORIES} JSON categories, found {len(category_specs)}")
    json_categories = _unique_index([label for label, _ in category_specs], kind="JSON category")
    if json_categories.keys() != master_categories.keys():
        raise CuadDataError("normalized JSON/master category sets differ")

    categories: list[Category] = []
    category_by_key: dict[str, Category] = {}
    description_by_key: dict[str, str] = {}
    ids: set[str] = set()
    for label, description in category_specs:
        category_id = _slugify(label)
        if category_id in ids:
            raise CuadDataError(f"category ID collision: {category_id!r}")
        ids.add(category_id)
        category = Category(category_id, label, description, f"{label}. {description}")
        categories.append(category)
        category_by_key[normalize_key(label)] = category
        description_by_key[normalize_key(label)] = description

    contracts: list[Contract] = []
    question_count = 0
    for title, context, qas in parts:
        row = master_by_filename[master_titles[normalize_key(title)]]
        qa_by_key: dict[str, Mapping[str, Any]] = {}
        for index, qa in enumerate(qas):
            location = f"document {title!r} QA {index}"
            label, description = _parse_question(qa.get("question"), location)
            key = normalize_key(label)
            if key in qa_by_key:
                raise CuadDataError(f"document {title!r} repeats category {label!r}")
            if key not in description_by_key or description != description_by_key[key]:
                raise CuadDataError(f"document {title!r} has unknown/changed category {label!r}")
            _answers(context, qa, location)
            qa_by_key[key] = qa
            question_count += 1
        if qa_by_key.keys() != category_by_key.keys():
            raise CuadDataError(f"document {title!r} does not contain exactly all categories")

        provisions: list[Provision] = []
        for category in categories:
            key = normalize_key(category.label)
            master_label = master_categories[key]
            try:
                raw_provisions = parse_csv_list(row[master_label])
            except CuadDataError as exc:
                raise CuadDataError(f"invalid {title!r}/{master_label!r} context: {exc}") from exc
            answers = qa_by_key[key]["answers"]
            expected = {
                GoldSegment(a["text"], a["answer_start"], a["answer_start"] + len(a["text"]))
                for a in answers
            }
            used: set[GoldSegment] = set()
            for provision_index, raw_provision in enumerate(raw_provisions):
                pieces = split_provision(raw_provision)
                if not pieces:
                    raise CuadDataError(
                        f"provision {title!r}/{master_label!r}/{provision_index} is empty"
                    )
                try:
                    segments = align_gold_segments(context, pieces, answers)
                except CuadDataError as exc:
                    raise CuadDataError(
                        f"cannot align {title!r}/{master_label!r}/{provision_index}: {exc}"
                    ) from exc
                used.update(segments)
                provisions.append(
                    Provision(
                        f"{title}::{category.category_id}::{provision_index}",
                        category.category_id,
                        category.label,
                        provision_index,
                        raw_provision,
                        segments,
                    )
                )
            if used != expected:
                raise CuadDataError(f"master/JSON span sets differ for {title!r}/{category.label!r}")
        contracts.append(Contract(title, context, tuple(provisions)))

    corpus = CuadCorpus(tuple(contracts), tuple(categories))
    checks = (
        ("contracts", corpus.contract_count, EXPECTED_CONTRACTS),
        ("categories", corpus.category_count, EXPECTED_CATEGORIES),
        ("questions", question_count, EXPECTED_QUESTIONS),
        ("rectangular questions", corpus.question_count, EXPECTED_QUESTIONS),
        ("provisions", corpus.provision_count, EXPECTED_PROVISIONS),
        ("unique gold segments", corpus.gold_segment_count, EXPECTED_GOLD_SEGMENTS),
        ("positive pairs", corpus.positive_pair_count, EXPECTED_POSITIVE_PAIRS),
    )
    failures = [
        f"{name}: expected {expected}, found {actual}"
        for name, actual, expected in checks
        if actual != expected
    ]
    if failures:
        raise CuadDataError("corpus invariant failure(s): " + "; ".join(failures))
    return corpus


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Download and validate pinned CUAD data")
    parser.add_argument("--data-dir", type=Path, default=Path("results/cuad_validation/data"))
    parser.add_argument("--revision", default=DATASET_REVISION)
    parser.add_argument("--no-download", action="store_true")
    args = parser.parse_args(argv)
    corpus = load_cuad(args.data_dir, args.revision, not args.no_download)
    for label, count in (
        ("contracts", corpus.contract_count),
        ("categories", corpus.category_count),
        ("questions", corpus.question_count),
        ("provisions", corpus.provision_count),
        ("unique gold segments", corpus.gold_segment_count),
        ("segment references", corpus.segment_reference_count),
        ("positive contract/category pairs", corpus.positive_pair_count),
    ):
        print(f"{label}: {count:,}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
