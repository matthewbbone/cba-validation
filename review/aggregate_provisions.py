#!/usr/bin/env python3
"""Build the CBA provision-content aggregate from per-document extraction outputs.

Implements the build plan in scripts/README.md §10. Deterministic, no LLM, safe to re-run.

    python scripts/aggregate_provisions.py                       # full build
    python scripts/aggregate_provisions.py --run run200_2026-06  # one run only
    python scripts/aggregate_provisions.py --force               # rebuild every shard
    python scripts/aggregate_provisions.py --cross-check         # verify vs clause_presence_long.csv

Standalone by construction: stdlib only, every taxonomy constant inlined below, no imports from
the wider project. Input paths resolve relative to this file and can be overridden on the CLI.

Phase 1 shards one run at a time into _provisions_shards/<run>.jsonl and skips runs whose shard
already exists; phase 2 concatenates the shards into the two published artifacts. An interrupted
build therefore costs one run, not the whole job.
"""

from __future__ import annotations

import argparse
import csv
import glob
import gzip
import json
import os
import random
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

SCHEMA_VERSION = "provisions_aggregate_v1"

# --------------------------------------------------------------------------------------
# Taxonomy constants (README §2, §3). These are the authoritative copies -- do not import.
# --------------------------------------------------------------------------------------

AREAS = [
    "Compensation",
    "Healthcare",
    "Leave",
    "Job Security",
    "Scheduling",
    "Safety",
    "Union Recognition",
    "Dispute Resolution",
    "Ancillary benefits",
]

# Scheduling's fourth dimension is `workload_cap`. Several scripts elsewhere in the parent
# project misname it `workload_staffing`; that spelling is wrong and appears nowhere in the data.
DIM_TO_AREA = {
    "wage_level": "Compensation",
    "wage_growth": "Compensation",
    "premium_pay": "Compensation",
    "progression_longevity": "Compensation",
    "employer_contribution": "Healthcare",
    "plan_design": "Healthcare",
    "ancillary_coverage": "Healthcare",
    "eligibility_access": "Healthcare",
    "vacation": "Leave",
    "sick_leave": "Leave",
    "holidays": "Leave",
    "other_leave": "Leave",
    "layoff_order": "Job Security",
    "recall": "Job Security",
    "severance": "Job Security",
    "benefit_continuation": "Job Security",
    "seniority_system": "Job Security",
    "subcontracting_work_preservation": "Job Security",
    "schedule_notice": "Scheduling",
    "hours_guarantee": "Scheduling",
    "rest_meal": "Scheduling",
    "workload_cap": "Scheduling",
    "ppe": "Safety",
    "refuse_unsafe": "Safety",
    "joint_committee": "Safety",
    "hazard_assault": "Safety",
    "bargaining_unit": "Union Recognition",
    "union_security": "Union Recognition",
    "union_access": "Union Recognition",
    "hiring_dispatch": "Union Recognition",
    "just_cause": "Dispute Resolution",
    "grievance_process": "Dispute Resolution",
    "arbitration": "Dispute Resolution",
    "investigation_appeal": "Dispute Resolution",
    "pension": "Ancillary benefits",
    "savings_annuity": "Ancillary benefits",
    "training_development": "Ancillary benefits",
    "other_benefits": "Ancillary benefits",
}

# Short labels the raw source mixes with the long canonical ones. Retained for the codebook and
# for auditing `category_as_recorded`; `area` is always derived from `dimension_id`, never read.
AREA_ALIASES = {
    "Security": "Job Security",
    "Recognition": "Union Recognition",
    "Disputes": "Dispute Resolution",
    "Ancillary": "Ancillary benefits",
}

PROVENANCE_LABELS = {
    "cba_contained": {
        "meaning": "Terms are printed in the contract body.",
        "scoring_treatment": "Scored normally.",
    },
    "externalized_recoverable": {
        "meaning": (
            "Delivered via a trust/fund/plan, but a worker-facing magnitude is stated in the "
            "contract ($/hr, 'employer pays 100%', a copay figure)."
        ),
        "scoring_treatment": "Scored on that magnitude -- not zeroed.",
    },
    "externalized_offpage": {
        "meaning": "A trust/plan/SPD is named but no magnitude appears.",
        "scoring_treatment": "Excluded from the denominator. Never zero.",
    },
    "source_gap": {
        "meaning": (
            "An article or appendix is declared (e.g. in the table of contents) but its body is "
            "missing from the scanned text."
        ),
        "scoring_treatment": "Excluded from the denominator. Never zero.",
    },
    "not_applicable": {
        "meaning": (
            "The dimension structurally cannot apply (e.g. hiring-hall referral at a direct-hire "
            "employer)."
        ),
        "scoring_treatment": "Excluded from the denominator.",
    },
    "absent": {
        "meaning": (
            "The provision could apply, but the contract is silent or offers only the statutory "
            "minimum."
        ),
        "scoring_treatment": "Scored 1 on a 1-5 scale -- the floor, not zero.",
    },
}
VALID_PROVENANCE = frozenset(PROVENANCE_LABELS)

# A stray spelling of source_gap that leaks in from `measurement_status`.
PROVENANCE_REWRITES = {"source_or_ocr_gap": "source_gap"}

# Pilot batch: a duplicate subset of a later batch, omitted for reproducibility.
EXCLUDE_RUNS = {"run_sample10_2026-06"}

# Fixed output ordering so a rebuild is byte-identical apart from the timestamp.
RUN_ORDER = [
    "run200_2026-06",
    "run_next50_2026-06",
    "run_next100_2026-06",
    "run_next150_2026-06",
    "run_next498_2026-06",
    "run_cornell_dol_2026-06",
    "run_cornell_dol2_2026-06",
    "run_cornell_dol3_2026-06",
    "run_cornell_dol4_2026-06",
    "run_dol_textlayer_2026-07",
    "run_retailed500_2026-07",
    "run_retailed_tail79_2026-07",
]

RUN_NOTES = {
    "run_dol_textlayer_2026-07": (
        "Extracted over a different API transport; its logs record a material number of parse "
        "failures. Failed documents are simply missing, so attrition is not missing-at-random. "
        "Include `run` as a control and test sensitivity by excluding this batch."
    ),
    "run_retailed500_2026-07": "Model attribution unrecorded for this batch.",
    "run_retailed_tail79_2026-07": "Model attribution unrecorded for this batch.",
    "run200_2026-06": (
        "Earliest batch. `provenance` was absent on ~92% of its dimension rows and is backfilled "
        "from `coverage`; `wrong_object_check` appears only here."
    ),
}

# --------------------------------------------------------------------------------------
# Alias coalescing (README §10 rules 2 and 4). Ordered by precedence, first non-null wins.
# --------------------------------------------------------------------------------------

DOCUMENT_ALIASES = {
    "employer": [
        "employer",
        "employer_name",
        "employer_or_association",
        "employer_or_sector",
        "employer_party",
        "employer_or_industry",
        "parties",
    ],
    "union": ["union", "union_name", "unions"],
    "title": ["title", "agreement_title", "document_type", "contract_type"],
    "sector": ["sector", "sector_guess", "industry", "industry_sector"],
    "effective_date": [
        "effective_date",
        "agreement_effective_date",
        "agreement_effective",
        "term_start",
        "contract_start",
        "contract_term_start",
        "effective_dates",
        "agreement_dates",
        "agreement_period",
        "agreement_term",
        "term",
    ],
    "expiration_date": [
        "expiration_date",
        "agreement_expiration_date",
        "agreement_expiration",
        "agreement_expires",
        "term_end",
        "contract_end",
        "contract_term_end",
    ],
    "agreement_type": ["agreement_type", "document_type", "contract_type"],
}

FIELD_ALIASES = {
    "field_value": ["field_value", "value", "raw_value"],
    "concept_id": ["concept_id", "record_concept_id"],
    "field_name": ["field_name", "field"],
    "field_class": [
        "field_class",
        "classification",
        "field_category",
        "category",
        "category_class",
        "field_classification",
        "field_classify",
    ],
    "note": ["note", "notes", "field_note", "field_notes", "description"],
}

# Every alias that gets folded into a canonical key, so the coalesced copies can be dropped
# from the passthrough without losing the value.
FIELD_ALIAS_MEMBERS = {a for aliases in FIELD_ALIASES.values() for a in aliases}

CONCEPT_RECORD_CORE = [
    "concept_id",
    "concept_label",
    "subobject_type",
    "concept_reporting_class",
    "measurement_status",
    "status_reason",
    "status_flags",
    "evidence_pointer",
]

METADATA_SOURCE_NAME = "harmonized_cba_metadata.csv"

# Row-identity columns: per-part by construction, so they are reported separately rather than
# consensus-folded across the parts of a multi-row RetailEd base.
METADATA_IDENTITY_COLS = {"cba_id"}

RETAILED_PART_SUFFIX = re.compile(r"_\d+\.pdf$")


# --------------------------------------------------------------------------------------
# Small helpers
# --------------------------------------------------------------------------------------


def strip_keys(row):
    """Strip whitespace from a row dict's keys. Two padded keys exist in the corpus."""
    if not isinstance(row, dict):
        return row
    return {(k.strip() if isinstance(k, str) else k): v for k, v in row.items()}


def first_present(row, aliases):
    """First non-null value among `aliases`, in precedence order."""
    for key in aliases:
        if row.get(key) is not None:
            return row[key]
    return None


def derive_cba_id(document_id):
    """README §10: `DoL_` + id when the id is all digits, else the id verbatim."""
    return "DoL_" + document_id if document_id.isdigit() else document_id


def blank_to_none(value):
    return None if value == "" else value


# --------------------------------------------------------------------------------------
# Metadata
# --------------------------------------------------------------------------------------


class MetadataIndex:
    """Two-way lookup over harmonized_cba_metadata.csv.

    Non-RetailEd ids join exactly. RetailEd ids do not: the metadata splits each agreement into
    per-part rows (`..._01.pdf`, `..._02.pdf`, ...), so those join on the base id with the part
    suffix stripped. Where the parts of one base disagree on a column the consensus is null and
    the column is named in `_conflict_fields` -- picking one part would fabricate agreement.
    """

    def __init__(self, path):
        self.path = Path(path)
        self.columns = []
        self.exact = {}
        self.without_pdf = {}
        self.by_base = defaultdict(list)
        self.n_rows = 0
        self._load()

    def _load(self):
        with open(self.path, encoding="utf-8-sig", newline="") as fh:
            reader = csv.DictReader(fh)
            self.columns = [c for c in (reader.fieldnames or []) if c]
            for row in reader:
                row = {k: blank_to_none(v) for k, v in row.items() if k}
                cba_id = row.get("cba_id")
                if not cba_id:
                    continue
                self.n_rows += 1
                self.exact[cba_id] = row
                if cba_id.lower().endswith(".pdf"):
                    # Verified collision-free over this CSV: no two ids collapse together and no
                    # stripped key shadows an existing exact id.
                    self.without_pdf[cba_id[:-4]] = row
                base = RETAILED_PART_SUFFIX.sub("", cba_id)
                if base != cba_id:
                    self.by_base[base].append(row)

    def _empty(self, cba_id):
        block = {c: None for c in self.columns if c not in METADATA_IDENTITY_COLS}
        block.update(
            {
                "_source": METADATA_SOURCE_NAME,
                "_cba_id": cba_id,
                "_join": None,
                "_n_metadata_rows": 0,
                "_conflict_fields": [],
            }
        )
        return block

    def lookup(self, cba_id):
        """Return (metadata block, join kind).

        Tried in order: the id verbatim, the id against metadata ids with a trailing `.pdf`
        stripped, then the RetailEd base id. Join kind is `exact`, `exact_no_pdf_suffix`,
        `retailed_base`, or None.
        """
        for kind, index in (("exact", self.exact), ("exact_no_pdf_suffix", self.without_pdf)):
            row = index.get(cba_id)
            if row is None:
                continue
            block = {c: row.get(c) for c in self.columns if c not in METADATA_IDENTITY_COLS}
            block.update(
                {
                    "_source": METADATA_SOURCE_NAME,
                    "_cba_id": row["cba_id"],
                    "_join": kind,
                    "_n_metadata_rows": 1,
                    "_conflict_fields": [],
                }
            )
            return block, kind

        parts = self.by_base.get(cba_id)
        if parts:
            block = {}
            conflicts = []
            for col in self.columns:
                if col in METADATA_IDENTITY_COLS:
                    continue
                values = {p.get(col) for p in parts}
                if len(values) == 1:
                    block[col] = values.pop()
                else:
                    block[col] = None
                    conflicts.append(col)
            block.update(
                {
                    "_source": METADATA_SOURCE_NAME,
                    "_cba_id": cba_id,
                    "_join": "retailed_base",
                    "_n_metadata_rows": len(parts),
                    "_conflict_fields": conflicts,
                    "_member_cba_ids": sorted(p["cba_id"] for p in parts),
                }
            )
            return block, "retailed_base"

        return self._empty(cba_id), None


# --------------------------------------------------------------------------------------
# Per-document normalization
# --------------------------------------------------------------------------------------


def normalize_document(raw, run, document_id, source_file, metadata_index, stats):
    """Normalize one per-document extraction file into an aggregate record."""
    document_raw = strip_keys(raw.get("document") or {})

    recorded_id = document_raw.get("document_id")
    recorded_id = str(recorded_id) if recorded_id is not None else None

    document = {
        key: first_present(document_raw, aliases) for key, aliases in DOCUMENT_ALIASES.items()
    }

    # --- concept_records ---------------------------------------------------------------
    concept_records = []
    has_score_ready = False
    for row in raw.get("concept_records") or []:
        row = strip_keys(row)
        stats.key_presence["concept_records"].update(row.keys())
        stats.rows["concept_records"] += 1
        record = {key: row.get(key) for key in CONCEPT_RECORD_CORE}
        # Preserve unrecognized keys rather than dropping them (README §10 rule 3).
        for key, value in row.items():
            if key not in record:
                record[key] = value
        status = record.get("measurement_status")
        stats.measurement_status[status] += 1
        if status == "score_ready":
            has_score_ready = True
            stats.score_ready += 1
        concept_records.append(record)

    # --- concept_fields ----------------------------------------------------------------
    concept_fields = []
    for row in raw.get("concept_fields") or []:
        row = strip_keys(row)
        stats.key_presence["concept_fields"].update(row.keys())
        stats.rows["concept_fields"] += 1
        field = {
            canonical: first_present(row, aliases) for canonical, aliases in FIELD_ALIASES.items()
        }
        field["field_unit"] = row.get("field_unit")
        field["support_status"] = row.get("support_status")
        field["evidence_pointer"] = row.get("evidence_pointer")
        # Never cast the value; record what was found instead (README §10 rule 4).
        field["value_type"] = type(field["field_value"]).__name__
        for key, value in row.items():
            if key not in field and key not in FIELD_ALIAS_MEMBERS:
                field[key] = value
        stats.support_status[field["support_status"]] += 1
        concept_fields.append(field)

    # --- dimension_coverage ------------------------------------------------------------
    dimension_coverage = []
    unknown_dimension_ids = []
    provenance_backfilled = False
    n_invalid_provenance = 0
    for row in raw.get("dimension_coverage") or []:
        row = strip_keys(row)
        stats.key_presence["dimension_coverage"].update(row.keys())
        stats.rows["dimension_coverage"] += 1

        dimension_id = row.get("dimension_id")
        area = DIM_TO_AREA.get(dimension_id)
        if area is None:
            unknown_dimension_ids.append(dimension_id)
            stats.unknown_dimension_ids[dimension_id] += 1

        recorded_provenance = row.get("provenance")
        coverage = row.get("coverage")
        if recorded_provenance is None:
            provenance_backfilled = True

        provenance = PROVENANCE_REWRITES.get(recorded_provenance, recorded_provenance)
        if provenance not in VALID_PROVENANCE:
            if recorded_provenance is not None:
                n_invalid_provenance += 1
                stats.invalid_provenance[recorded_provenance] += 1
            fallback = PROVENANCE_REWRITES.get(coverage, coverage)
            provenance = fallback if fallback in VALID_PROVENANCE else None
        stats.provenance[provenance] += 1

        entry = {
            "dimension_id": dimension_id,
            "area": area,
            "provenance": provenance,
            "coverage": coverage,
            "category_as_recorded": row.get("category"),
            "provenance_as_recorded": recorded_provenance,
            "evidence_pointer": row.get("evidence_pointer"),
            "note": row.get("note"),
        }
        for key, value in row.items():
            if key not in entry and key not in {"category", "document_id"}:
                entry[key] = value
        dimension_coverage.append(entry)

    stats.ndc_dist[len(dimension_coverage)] += 1

    # --- quality -----------------------------------------------------------------------
    truncated = bool(raw.get("truncated")) or bool(document_raw.get("truncated"))
    quality = {
        "n_dimension_coverage": len(dimension_coverage),
        "unknown_dimension_ids": unknown_dimension_ids,
        "provenance_backfilled": provenance_backfilled,
        "has_truncated_flag": truncated,
        "has_score_ready": has_score_ready,
        "n_invalid_provenance": n_invalid_provenance,
        "document_id_as_recorded": recorded_id if recorded_id != document_id else None,
    }
    if quality["document_id_as_recorded"] is not None:
        stats.document_id_mismatches += 1
    if provenance_backfilled:
        stats.provenance_backfilled_docs += 1
    if truncated:
        stats.truncated_docs += 1

    # --- metadata ----------------------------------------------------------------------
    cba_id = derive_cba_id(document_id)
    metadata, join_kind = metadata_index.lookup(cba_id)
    if join_kind is None:
        stats.metadata_unmatched.append(cba_id)
    else:
        stats.metadata_joins[join_kind] += 1

    return {
        "document_id": document_id,
        "run": run,
        "source_file": source_file,
        "document": document,
        "document_raw": document_raw,
        "metadata": metadata,
        "quality": quality,
        "concept_records": concept_records,
        "concept_fields": concept_fields,
        "dimension_coverage": dimension_coverage,
    }


# --------------------------------------------------------------------------------------
# Per-run statistics
# --------------------------------------------------------------------------------------


class RunStats:
    """Counters accumulated while sharding one run, persisted alongside the shard.

    Held in a sidecar so a resumed build can assemble the codebook without re-reading shards.
    """

    ARRAYS = ("concept_records", "concept_fields", "dimension_coverage")

    def __init__(self, run):
        self.run = run
        self.n_documents = 0
        self.files_skipped = 0
        self.skipped_paths = []
        self.rows = Counter()
        self.key_presence = {name: Counter() for name in self.ARRAYS}
        self.unknown_dimension_ids = Counter()
        self.invalid_provenance = Counter()
        self.provenance = Counter()
        self.measurement_status = Counter()
        self.support_status = Counter()
        self.ndc_dist = Counter()
        self.score_ready = 0
        self.provenance_backfilled_docs = 0
        self.truncated_docs = 0
        self.document_id_mismatches = 0
        self.duplicate_document_ids = []
        self.metadata_joins = Counter()
        self.metadata_unmatched = []

    def to_dict(self):
        return {
            "run": self.run,
            "n_documents": self.n_documents,
            "files_skipped": self.files_skipped,
            "skipped_paths": self.skipped_paths,
            "rows": dict(self.rows),
            "key_presence": {k: dict(v) for k, v in self.key_presence.items()},
            "unknown_dimension_ids": dict(self.unknown_dimension_ids),
            "invalid_provenance": dict(self.invalid_provenance),
            "provenance": {str(k): v for k, v in self.provenance.items()},
            "measurement_status": {str(k): v for k, v in self.measurement_status.items()},
            "support_status": {str(k): v for k, v in self.support_status.items()},
            "ndc_dist": {str(k): v for k, v in self.ndc_dist.items()},
            "score_ready": self.score_ready,
            "provenance_backfilled_docs": self.provenance_backfilled_docs,
            "truncated_docs": self.truncated_docs,
            "document_id_mismatches": self.document_id_mismatches,
            "duplicate_document_ids": self.duplicate_document_ids,
            "metadata_joins": dict(self.metadata_joins),
            "metadata_unmatched": self.metadata_unmatched,
        }


# --------------------------------------------------------------------------------------
# Phase 1 -- shard one run
# --------------------------------------------------------------------------------------


def shard_path(shards_dir, run):
    return shards_dir / f"{run}.jsonl"


def stats_path(shards_dir, run):
    return shards_dir / f"{run}.stats.json"


def discover_runs(runs_dir):
    """Run directories holding at least one per-document file, in fixed output order.

    run_nlrbedge_2026-07 has a per_document/ directory that is empty, so it must be dropped on
    the file count rather than on the directory's existence -- otherwise it lands in the output
    as a thirteenth run contributing zero documents.
    """
    found = []
    for entry in sorted(os.listdir(runs_dir)):
        if entry in EXCLUDE_RUNS or not entry.startswith("run"):
            continue
        if not (Path(runs_dir) / entry / "per_document").is_dir():
            continue
        if glob.glob(os.path.join(runs_dir, entry, "per_document", "*.json")):
            found.append(entry)
    ordered = [r for r in RUN_ORDER if r in found]
    return ordered + sorted(set(found) - set(ordered))


def build_run(run, runs_dir, shards_dir, metadata_index, force=False):
    """Normalize one run into `_provisions_shards/<run>.jsonl`. Returns its stats dict."""
    shard = shard_path(shards_dir, run)
    stats_file = stats_path(shards_dir, run)
    if shard.exists() and stats_file.exists() and not force:
        print(f"  {run:32s} shard exists, skipping (--force to rebuild)")
        return json.loads(stats_file.read_text(encoding="utf-8"))

    # Glob on *.json: a raw listdir also picks up abandoned atomic-write temp files
    # (143.json.tmp.51616.8271c4a8e348 and two more), which is the 7,057-vs-7,054 discrepancy.
    paths = sorted(glob.glob(os.path.join(runs_dir, run, "per_document", "*.json")))

    stats = RunStats(run)
    seen_ids = set()
    partial = shard.with_suffix(".jsonl.partial")

    with open(partial, "w", encoding="utf-8") as out:
        for path in paths:
            document_id = os.path.basename(path)[:-5]
            try:
                with open(path, encoding="utf-8-sig") as fh:
                    raw = json.load(fh)
            except (json.JSONDecodeError, OSError) as exc:
                # Insurance, not a live path: the corpus currently parses 7,054/7,054. Dropbox
                # may re-evict these files to cloud-only, which surfaces here as OSError.
                stats.files_skipped += 1
                stats.skipped_paths.append(f"{path}: {type(exc).__name__}")
                continue

            if document_id in seen_ids:
                stats.duplicate_document_ids.append(document_id)
            seen_ids.add(document_id)

            record = normalize_document(
                raw,
                run=run,
                document_id=document_id,
                source_file=os.path.relpath(path, Path(runs_dir).parent),
                metadata_index=metadata_index,
                stats=stats,
            )
            stats.n_documents += 1
            out.write(json.dumps(record, ensure_ascii=False, separators=(",", ":")))
            out.write("\n")

    # Atomic promote: a half-written shard must never be mistaken for a finished one.
    os.replace(partial, shard)
    payload = stats.to_dict()
    stats_file.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    print(
        f"  {run:32s} {stats.n_documents:5d} docs  "
        f"{stats.rows['concept_records']:7d} records  "
        f"{stats.rows['concept_fields']:7d} fields  "
        f"{stats.rows['dimension_coverage']:7d} dim rows  "
        f"skipped {stats.files_skipped}"
    )
    return payload


# --------------------------------------------------------------------------------------
# Phase 2 -- merge shards into the published artifacts
# --------------------------------------------------------------------------------------


def merge_counter(target, source):
    for key, value in source.items():
        target[key] += value


def build_codebook(all_stats, metadata_index, concept_tally, field_name_cardinality):
    key_presence = {}
    for run, stats in all_stats.items():
        row_totals = stats["rows"]
        key_presence[run] = {
            array: {
                "n_rows": row_totals.get(array, 0),
                "keys": {
                    key: {
                        "n_rows": count,
                        "pct_of_rows": (
                            round(100.0 * count / row_totals[array], 3)
                            if row_totals.get(array)
                            else 0.0
                        ),
                    }
                    for key, count in sorted(
                        stats["key_presence"].get(array, {}).items(),
                        key=lambda kv: (-kv[1], kv[0]),
                    )
                },
            }
            for array in RunStats.ARRAYS
        }

    provenance = Counter()
    measurement_status = Counter()
    support_status = Counter()
    unknown_dimension_ids = Counter()
    invalid_provenance = Counter()
    ndc_dist = Counter()
    for stats in all_stats.values():
        merge_counter(provenance, stats["provenance"])
        merge_counter(measurement_status, stats["measurement_status"])
        merge_counter(support_status, stats["support_status"])
        merge_counter(unknown_dimension_ids, stats["unknown_dimension_ids"])
        merge_counter(invalid_provenance, stats["invalid_provenance"])
        merge_counter(ndc_dist, stats["ndc_dist"])

    def tally(counter):
        return dict(sorted(counter.items(), key=lambda kv: (-kv[1], str(kv[0]))))

    score_ready = sum(s["score_ready"] for s in all_stats.values())
    score_ready_runs = sorted(r for r, s in all_stats.items() if s["score_ready"])

    return {
        "provenance_labels": PROVENANCE_LABELS,
        "areas": AREAS,
        "area_aliases_short_to_long": AREA_ALIASES,
        "dimensions": {
            dim: {"area": area} for dim, area in sorted(DIM_TO_AREA.items(), key=lambda kv: kv[0])
        },
        "concepts": {
            concept: {
                "n_records": count,
                "n_distinct_field_names": field_name_cardinality.get(concept, 0),
            }
            for concept, count in sorted(
                concept_tally.items(), key=lambda kv: (-kv[1], str(kv[0]))
            )
        },
        "concepts_note": (
            f"{len(concept_tally)} distinct concept_ids were observed, against the ~58 controlled "
            "objects the vocabulary defines. The distribution is strongly bimodal and the "
            "controlled vocabulary is intact: "
            f"{sum(1 for n in concept_tally.values() if n >= 50)} ids account for essentially all "
            "the mass (>=50 records each) and appear in nearly every run -- that is the real "
            f"vocabulary. The remaining {sum(1 for n in concept_tally.values() if n < 50)} are a "
            "drift tail confined to a single run apiece, "
            f"{sum(1 for n in concept_tally.values() if n == 1)} of them appearing exactly once: "
            "ad-hoc renamings of concepts that already exist (C_BASE_WAGE for C_WAGE_BASE_RATE, "
            "C_BARGAINING_UNIT for C_RECOGNITION_COVERAGE_SCOPE), not new measurement objects. "
            "Threshold on n_records -- at >=50 the vocabulary matches its specification. "
            "n_distinct_field_names is the number of distinct field_name spellings recorded under "
            "the concept: it runs into the tens of thousands for the common ones because "
            "field_name frequently carries a job classification rather than a stable slot name. "
            "That is the concrete reason concept_fields is a semi-structured supplement and not a "
            "comparable panel."
        ),
        "presence_rule": {
            "description": (
                "README §7. cba_contained / externalized_recoverable / externalized_offpage -> 1 "
                "(the provision exists); absent -> 0 (the contract is silent); source_gap / "
                "not_applicable / null -> None (unknown -- never fillna(0))."
            ),
            "present": [
                "cba_contained",
                "externalized_recoverable",
                "externalized_offpage",
            ],
            "zero": ["absent"],
            "unknown": ["source_gap", "not_applicable", None],
        },
        "key_presence_by_run": key_presence,
        "key_presence_note": (
            "Measured on the source keys after whitespace stripping and BEFORE alias coalescing, "
            "so a consumer can tell 'this batch spelled the key differently' apart from 'this "
            "contract did not have the provision'. The coalesced canonical keys are listed under "
            "normalizations_applied."
        ),
        "value_tallies": {
            "provenance": tally(provenance),
            "measurement_status": tally(measurement_status),
            "support_status": tally(support_status),
            "n_dimension_coverage": tally(ndc_dist),
            "unknown_dimension_ids": tally(unknown_dimension_ids),
            "invalid_provenance_as_recorded": tally(invalid_provenance),
        },
        "metadata_source": {
            "file": METADATA_SOURCE_NAME,
            "n_rows": metadata_index.n_rows,
            "columns": metadata_index.columns,
            "join_rule": (
                "cba_id = 'DoL_' + document_id when the id is all digits, else the id verbatim. "
                "Tried in order: the id verbatim (`exact`); the id against metadata ids with a "
                "trailing '.pdf' stripped (`exact_no_pdf_suffix`); then, for RetailEd ids, which "
                "have no single matching row because the metadata splits each agreement into "
                "per-part rows (..._01.pdf, ..._02.pdf, ...), the base id with the part suffix "
                "stripped (`retailed_base`). `metadata._join` records which rule fired. For a "
                "`retailed_base` match the value of each column is the consensus across the "
                "parts; where the parts disagree the value is null and the column is named in "
                "`_conflict_fields`, with the contributing rows listed in `_member_cba_ids`."
            ),
            "value_types": (
                "All columns are carried verbatim as strings; empty cells become null. Coerce "
                "before arithmetic -- state_fips and naics carry significant leading zeros."
            ),
        },
        "normalizations_applied": [
            "document_id taken from the filename stem; the in-file value is str on most documents "
            "but int on 109 and null on 2, and case-mismatched on 7. Where it differs it is kept "
            "at quality.document_id_as_recorded.",
            "Whitespace stripped from every source key (two padded keys exist in the corpus).",
            "document aliases coalesced first-non-null into employer, union, title, sector, "
            "effective_date, expiration_date, agreement_type; the original kept as document_raw.",
            "concept_fields aliases coalesced: field_value|value|raw_value -> field_value; "
            "concept_id|record_concept_id -> concept_id; field_name|field -> field_name; "
            "field_class|classification|field_category|category|category_class|"
            "field_classification|field_classify -> field_class; "
            "note|notes|field_note|field_notes|description -> note. value_type records the Python "
            "type of the value as found; the value itself is never cast.",
            "dimension_coverage area derived from dimension_id (1:1); the recorded category label "
            "is ignored for area and retained as category_as_recorded.",
            "provenance = provenance if it is one of the six labels, else coverage if that is, "
            "else null; source_or_ocr_gap rewritten to source_gap. The raw value is retained as "
            "provenance_as_recorded.",
            "Unrecognized keys on all three arrays are passed through rather than dropped.",
            f"Runs excluded: {sorted(EXCLUDE_RUNS)}.",
        ],
        "known_caveats": [
            "`absent` is a substantive finding (the contract is silent) and scores 1 on a 1-5 "
            "scale. `source_gap` and `not_applicable` are epistemic and score nothing -- blank is "
            "not zero, and neither is `absent`.",
            "`externalized_offpage` means the benefit almost certainly exists and only its "
            "magnitude is unknown. Coding it as absence reproduces the exact bias this dataset "
            "was built to remove.",
            "dimension_coverage is the only layer with a guaranteed-stable schema; build "
            "comparative measures from it. concept_fields drifts badly across batches -- consult "
            "key_presence_by_run before filtering on any key or field_name spelling.",
            f"measurement_status == 'score_ready' appears on {score_ready} concept records in "
            f"{score_ready_runs}. README §6 states the extractor never emits it, so these are "
            "scorer write-back into the extraction files. Carried verbatim; flagged per document "
            "at quality.has_score_ready.",
            f"{sum(invalid_provenance.values())} dimension rows carried a non-provenance value in "
            "the provenance slot (measurement_status labels such as needs_external_source). Those "
            "resolve via coverage where possible and are null otherwise, with the original at "
            "provenance_as_recorded.",
            "support_status is far more heterogeneous than the two documented values; see "
            "value_tallies.support_status before filtering. Trust nothing above "
            "directly_supported as a printed fact.",
            "field_value is heterogeneously typed by construction (int, float, str, null, bool, "
            "list, dict). Always coerce; value_type records what was found.",
            "Evidence pointers reference source OCR text that is not shipped here. They are for "
            "auditing against the originals, not for reconstructing quotes.",
            "Model attribution is not recorded anywhere in the run state files, so runs[*].models "
            "is null throughout rather than inferred.",
            "This is LLM-extracted data. The extraction layer has not been exhaustively validated "
            "against human coding -- hand-check any small subsample an argument leans on.",
        ],
    }


def merge_shards(all_stats, shards_dir, out_dir, metadata_index):
    runs = [r for r in RUN_ORDER if r in all_stats] + sorted(
        set(all_stats) - set(RUN_ORDER)
    )

    # Concept frequency for the codebook needs one pass over the shards; do it before writing so
    # the header can be emitted up front and the documents streamed after it. The same pass
    # collects field_name cardinality per concept, which is what shows concept_fields is not a
    # comparable panel: field_name frequently holds a job classification, not a stable slot name.
    concept_tally = Counter()
    field_names = defaultdict(set)
    for run in runs:
        with open(shard_path(shards_dir, run), encoding="utf-8") as fh:
            for line in fh:
                doc = json.loads(line)
                for record in doc["concept_records"]:
                    concept_tally[record.get("concept_id")] += 1
                for field in doc["concept_fields"]:
                    field_names[field.get("concept_id")].add(field.get("field_name"))
    field_name_cardinality = {k: len(v) for k, v in field_names.items()}

    counts = {
        "documents": sum(all_stats[r]["n_documents"] for r in runs),
        "runs": len(runs),
        "concept_records": sum(all_stats[r]["rows"].get("concept_records", 0) for r in runs),
        "concept_fields": sum(all_stats[r]["rows"].get("concept_fields", 0) for r in runs),
        "dimension_coverage_rows": sum(
            all_stats[r]["rows"].get("dimension_coverage", 0) for r in runs
        ),
        "files_skipped": sum(all_stats[r]["files_skipped"] for r in runs),
    }

    header = {
        "schema_version": SCHEMA_VERSION,
        "generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "counts": counts,
        "codebook": build_codebook(
            all_stats, metadata_index, concept_tally, field_name_cardinality
        ),
        "runs": {
            run: {
                "n_documents": all_stats[run]["n_documents"],
                "models": None,
                "notes": RUN_NOTES.get(run),
            }
            for run in runs
        },
    }

    json_path = out_dir / "cba_provisions_aggregate.json"
    gz_path = out_dir / "cba_provisions_aggregate.jsonl.gz"

    # Stream both artifacts: the monolith is ~290 MB, far too large to hold as one string.
    prefix = json.dumps(header, ensure_ascii=False, separators=(",", ":"))[:-1]
    with open(json_path, "w", encoding="utf-8") as mono, gzip.open(
        gz_path, "wt", encoding="utf-8"
    ) as gz:
        mono.write(prefix)
        mono.write(',"documents":[')
        first = True
        for run in runs:
            with open(shard_path(shards_dir, run), encoding="utf-8") as fh:
                for line in fh:
                    line = line.rstrip("\n")
                    if not line:
                        continue
                    gz.write(line)
                    gz.write("\n")
                    if not first:
                        mono.write(",")
                    mono.write(line)
                    first = False
        mono.write("]}")

    return counts, json_path, gz_path


# --------------------------------------------------------------------------------------
# Reporting
# --------------------------------------------------------------------------------------


def print_summary(all_stats, counts, json_path, gz_path):
    def total(key):
        return sum(s[key] for s in all_stats.values())

    unknown = Counter()
    invalid = Counter()
    ndc = Counter()
    joins = Counter()
    unmatched = []
    for stats in all_stats.values():
        merge_counter(unknown, stats["unknown_dimension_ids"])
        merge_counter(invalid, stats["invalid_provenance"])
        merge_counter(ndc, stats["ndc_dist"])
        merge_counter(joins, stats["metadata_joins"])
        unmatched.extend(stats["metadata_unmatched"])

    print()
    print("=" * 78)
    print(
        f"documents {counts['documents']}  runs {counts['runs']}  "
        f"concept_records {counts['concept_records']}  "
        f"concept_fields {counts['concept_fields']}  "
        f"dimension_coverage_rows {counts['dimension_coverage_rows']}  "
        f"files_skipped {counts['files_skipped']}"
    )
    print("=" * 78)
    print(f"  metadata joined      : exact {joins['exact']}, "
          f"exact_no_pdf_suffix {joins['exact_no_pdf_suffix']}, "
          f"retailed_base {joins['retailed_base']}, unmatched {len(unmatched)}")
    if unmatched:
        print(f"                         unmatched ids: {sorted(unmatched)}")
    print(f"  n_dimension_coverage : {dict(sorted((int(k), v) for k, v in ndc.items()))}")
    print(f"  unknown dimension_ids: {dict(unknown) or 'none'}")
    print(f"  invalid provenance   : {dict(invalid) or 'none'} "
          f"(resolved via coverage where possible, else null)")
    print(f"  score_ready records  : {total('score_ready')} "
          f"in {sorted(r for r, s in all_stats.items() if s['score_ready']) or 'none'}")
    print(f"  provenance backfilled: {total('provenance_backfilled_docs')} documents")
    print(f"  truncated documents  : {total('truncated_docs')}")
    print(f"  document_id mismatch : {total('document_id_mismatches')} "
          f"(filename stem is authoritative)")
    dupes = [d for s in all_stats.values() for d in s["duplicate_document_ids"]]
    print(f"  duplicate ids in run : {dupes or 'none'}")
    if json_path:
        print(f"  wrote {json_path} ({json_path.stat().st_size / 1e6:.1f} MB)")
        print(f"  wrote {gz_path} ({gz_path.stat().st_size / 1e6:.1f} MB)")


# --------------------------------------------------------------------------------------
# Verification
# --------------------------------------------------------------------------------------

PRESENT = {"cba_contained", "externalized_recoverable", "externalized_offpage"}


def presence(prov):
    """README §7. Returns 1, 0, or None -- None means unknown, never zero."""
    if prov in PRESENT:
        return 1
    if prov == "absent":
        return 0
    return None


def fidelity(gz_path, runs_dir, expected_documents, sample=None):
    """The real normalization test: every document must reproduce its own source file.

    Checks row counts, the dimension_id and concept_id sequences, and that every recorded
    provenance/coverage and coalesced field_value survived the normalization unchanged. A failure
    here means the aggregate lost or reordered something and is a hard error.
    """
    print()
    print("fidelity vs runs/<run>/per_document/*.json")
    lines = 0
    with gzip.open(gz_path, "rt", encoding="utf-8") as fh:
        for _ in fh:
            lines += 1
    ok = lines == expected_documents
    print(f"  {'OK ' if ok else 'FAIL'} jsonl.gz lines {lines} == counts.documents "
          f"{expected_documents}")

    picks = None
    if sample is not None and sample < lines:
        picks = set(random.Random(0).sample(range(lines), sample))

    checked = 0
    failures = []
    with gzip.open(gz_path, "rt", encoding="utf-8") as fh:
        for index, line in enumerate(fh):
            if picks is not None and index not in picks:
                continue
            doc = json.loads(line)
            source = Path(runs_dir).parent / doc["source_file"]
            try:
                with open(source, encoding="utf-8-sig") as sfh:
                    raw = json.load(sfh)
            except (json.JSONDecodeError, OSError) as exc:
                failures.append(f"{doc['run']}/{doc['document_id']}: unreadable source ({exc})")
                continue

            src_dims = [strip_keys(r) for r in raw.get("dimension_coverage") or []]
            src_recs = [strip_keys(r) for r in raw.get("concept_records") or []]
            src_flds = [strip_keys(r) for r in raw.get("concept_fields") or []]

            problems = []
            if len(src_recs) != len(doc["concept_records"]):
                problems.append("concept_records length")
            if len(src_flds) != len(doc["concept_fields"]):
                problems.append("concept_fields length")
            if len(src_dims) != len(doc["dimension_coverage"]):
                problems.append("dimension_coverage length")
            if [r.get("dimension_id") for r in src_dims] != [
                r["dimension_id"] for r in doc["dimension_coverage"]
            ]:
                problems.append("dimension_id sequence")
            if [r.get("provenance") for r in src_dims] != [
                r["provenance_as_recorded"] for r in doc["dimension_coverage"]
            ]:
                problems.append("provenance_as_recorded")
            if [r.get("coverage") for r in src_dims] != [
                r["coverage"] for r in doc["dimension_coverage"]
            ]:
                problems.append("coverage")
            if [r.get("concept_id") for r in src_recs] != [
                r["concept_id"] for r in doc["concept_records"]
            ]:
                problems.append("concept_id sequence")
            if [first_present(r, FIELD_ALIASES["field_value"]) for r in src_flds] != [
                r["field_value"] for r in doc["concept_fields"]
            ]:
                problems.append("field_value sequence")
            if strip_keys(raw.get("document") or {}) != doc["document_raw"]:
                problems.append("document_raw")

            checked += 1
            if problems:
                failures.append(f"{doc['run']}/{doc['document_id']}: {', '.join(problems)}")

    scope = "all documents" if picks is None else f"{checked} sampled documents"
    if failures:
        ok = False
        print(f"  FAIL {len(failures)} of {checked} documents diverge from source ({scope})")
        for failure in failures[:10]:
            print(f"        {failure}")
    else:
        print(f"  OK  {checked} documents reproduce their source files exactly ({scope})")
    return ok


# Agreement below this against the downstream scoring layer means something is structurally
# wrong; small divergence is expected because the scorer corrects the extractor (see below).
CROSS_CHECK_MIN_AGREEMENT = 99.9


def cross_check(gz_path, runs_dir):
    """Compare the derived presence table against the downstream scoring layer.

    The README names data/analysis/master/master_presence_wide.csv, which does not exist in this
    repo. Every run instead ships outputs/clause_presence_long.csv, but that file is built from
    `cell_scores/` -- the *scoring* stage -- not from `per_document/`. This aggregate is the
    extraction layer, and the scorer sits downstream of it and repairs what the extractor missed:
    it emits all 38 dimensions even for the documents whose extraction omitted a block, and it
    revises individual labels. So exact equality is the wrong expectation. Divergence is reported
    and classified; only a collapse in agreement is treated as a failure.
    """
    derived = {}
    with gzip.open(gz_path, "rt", encoding="utf-8") as fh:
        for line in fh:
            doc = json.loads(line)
            derived[(doc["run"], doc["document_id"])] = {
                row["dimension_id"]: row["provenance"] for row in doc["dimension_coverage"]
            }

    runs = sorted({run for run, _ in derived})
    total = diverged = 0
    kinds = Counter()
    print()
    print("cross-check vs runs/<run>/outputs/clause_presence_long.csv (scoring layer)")
    for run in runs:
        path = Path(runs_dir) / run / "outputs" / "clause_presence_long.csv"
        if not path.exists():
            print(f"       {run:32s} no clause_presence_long.csv -- skipped")
            continue
        compared = run_diverged = 0
        with open(path, encoding="utf-8-sig", newline="") as fh:
            for row in csv.DictReader(fh):
                dims = derived.get((run, row["document_id"]))
                if dims is None:
                    continue
                compared += 1
                expected = row["present"]
                expected = None if expected == "" else int(float(expected))
                if row["clause"] not in dims:
                    got, kind = None, "row_absent_from_extraction"
                else:
                    got, kind = presence(dims[row["clause"]]), "provenance_revised_by_scorer"
                if got != expected:
                    run_diverged += 1
                    kinds[kind] += 1
        total += compared
        diverged += run_diverged
        rate = 100.0 * (1 - run_diverged / compared) if compared else 100.0
        print(f"       {run:32s} compared {compared:7d}  diverged {run_diverged:4d}  "
              f"agreement {rate:8.4f}%")

    rate = 100.0 * (1 - diverged / total) if total else 100.0
    ok = rate >= CROSS_CHECK_MIN_AGREEMENT
    print(f"  {'OK ' if ok else 'FAIL'} overall: compared {total}  diverged {diverged}  "
          f"agreement {rate:.4f}%  (threshold {CROSS_CHECK_MIN_AGREEMENT}%)")
    for kind, count in kinds.most_common():
        print(f"        {count:4d}  {kind}")
    print("        Divergence is expected: clause_presence_long.csv is built from cell_scores/,")
    print("        the scoring stage, which fills in dimensions the extractor omitted and revises")
    print("        individual labels. This aggregate is the extraction layer only.")
    return ok


def run_verification(gz_path, runs_dir, expected_documents, sample=None):
    """Fidelity against the source files, then agreement against the scoring layer."""
    fidelity_ok = fidelity(gz_path, str(runs_dir), expected_documents, sample)
    cross_ok = cross_check(gz_path, str(runs_dir))
    print()
    print(f"verification: fidelity {'PASS' if fidelity_ok else 'FAIL'}, "
          f"cross-check {'PASS' if cross_ok else 'FAIL'}")
    return 0 if (fidelity_ok and cross_ok) else 1


# --------------------------------------------------------------------------------------
# Entry point
# --------------------------------------------------------------------------------------


def main(argv=None):
    here = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--runs-dir", default=str(here.parent / "runs"))
    parser.add_argument("--metadata", default=str(here / METADATA_SOURCE_NAME))
    parser.add_argument("--out-dir", default=str(here))
    parser.add_argument("--shards-dir", default=None, help="default: <out-dir>/_provisions_shards")
    parser.add_argument("--run", action="append", help="process only this run (repeatable)")
    parser.add_argument("--force", action="store_true", help="rebuild shards that already exist")
    parser.add_argument("--shards-only", action="store_true", help="skip the merge phase")
    parser.add_argument("--verify", action="store_true", help="run the verification suite")
    parser.add_argument(
        "--verify-only",
        action="store_true",
        help="verify the artifacts already on disk without rebuilding",
    )
    parser.add_argument(
        "--verify-sample",
        type=int,
        default=None,
        help="check only N documents against source (default: all)",
    )
    args = parser.parse_args(argv)

    runs_dir = Path(args.runs_dir)
    out_dir = Path(args.out_dir)
    shards_dir = Path(args.shards_dir) if args.shards_dir else out_dir / "_provisions_shards"
    shards_dir.mkdir(parents=True, exist_ok=True)

    if not runs_dir.is_dir():
        parser.error(f"runs directory not found: {runs_dir}")
    if not Path(args.metadata).is_file():
        parser.error(f"metadata csv not found: {args.metadata}")

    if args.verify_only:
        gz_path = out_dir / "cba_provisions_aggregate.jsonl.gz"
        json_path = out_dir / "cba_provisions_aggregate.json"
        if not gz_path.exists():
            parser.error(f"nothing to verify: {gz_path} not found")
        # `counts` is a flat object near the head of the monolith; parse it without loading 331 MB.
        with open(json_path, encoding="utf-8") as fh:
            match = re.search(r'"counts":(\{[^}]*\})', fh.read(8192))
        if not match:
            parser.error(f"could not read counts from {json_path}")
        expected = json.loads(match.group(1))["documents"]
        return run_verification(gz_path, runs_dir, expected, args.verify_sample)

    metadata_index = MetadataIndex(args.metadata)
    print(f"metadata: {metadata_index.n_rows} rows, {len(metadata_index.columns)} columns")

    available = discover_runs(runs_dir)
    runs = args.run or available
    unknown = [r for r in runs if r not in available]
    if unknown:
        parser.error(f"unknown run(s): {unknown}. available: {available}")

    print(f"runs: {len(runs)}")
    all_stats = {}
    for run in runs:
        all_stats[run] = build_run(run, str(runs_dir), shards_dir, metadata_index, args.force)

    if args.shards_only:
        print_summary(all_stats, {
            "documents": sum(s["n_documents"] for s in all_stats.values()),
            "runs": len(all_stats),
            "concept_records": sum(s["rows"].get("concept_records", 0) for s in all_stats.values()),
            "concept_fields": sum(s["rows"].get("concept_fields", 0) for s in all_stats.values()),
            "dimension_coverage_rows": sum(
                s["rows"].get("dimension_coverage", 0) for s in all_stats.values()
            ),
            "files_skipped": sum(s["files_skipped"] for s in all_stats.values()),
        }, None, None)
        return 0

    counts, json_path, gz_path = merge_shards(all_stats, shards_dir, out_dir, metadata_index)
    print_summary(all_stats, counts, json_path, gz_path)

    if args.verify:
        return run_verification(gz_path, runs_dir, counts["documents"], args.verify_sample)
    return 0


if __name__ == "__main__":
    sys.exit(main())
