# CBA Provision Content — aggregated extraction data

This directory holds a single JSON file describing the **provision content of ~7,044 U.S. collective
bargaining agreements (CBAs)**, extracted from the agreements' own text by large language models, plus
the script that builds it.

- `cba_provisions_aggregate.json` — the canonical artifact (331 MB, one JSON object)
- `cba_provisions_aggregate.jsonl.gz` — same records, one document per line, gzipped (66 MB).
  **Prefer this one** if you are streaming, memory-constrained, or receiving the data by transfer.
- `aggregate_provisions.py` — the builder (see [§10](#10-build-plan-for-aggregate_provisionspy)
  and [§11](#11-build-results))
- [`REPORT.md`](REPORT.md) — measured structural consistency across the 12 runs: what drifts, how
  far the taxonomy moves, and what is missing. **Read it before building any cross-run measure.**

This README is written to be **self-sufficient**: you should be able to use the data without access to
the wider project it came from.

---

## 1. What this data is

Each record is one collective bargaining agreement. For each agreement the data reports:

| Layer | What it holds |
|---|---|
| `document` | The agreement's identity as read off its own first pages: employer, union, title, sector, effective/expiration dates, agreement type. |
| `dimension_coverage` | **The backbone.** One row for each of 38 standard provision dimensions, recording whether that provision is present in the contract, delivered off-page, or genuinely absent — see [§3](#3-the-provenance-labels). |
| `concept_records` | The individual provisions the model actually found, mapped to a controlled vocabulary of 58 "concepts", each citing where in the document it was found. |
| `concept_fields` | The quantities pulled out of those provisions — wage rates, employer contributions, vacation weeks, notice periods — with units and a support status. |
| `metadata` | External harmonized metadata joined in by document id: state, NAICS industry, worker counts, contract year. |

This is **content data, not outcome data**. It tells you what agreements say, not what happened
under them.

### What is deliberately *not* here

The parent project also produces 0–1 *generosity scores* per provision area, plus calibration
adjustments. **Those are excluded.** This file is the extraction layer only — the observations, not
the valuations. That keeps it free of scoring and calibration assumptions, and means you can build
your own index. [§7](#7-recipes) shows how.

---

## 2. Minimal project context

A **collective bargaining agreement** is the contract between an employer (or an association of
employers) and a union, governing wages, benefits, and working conditions for a bargaining unit of
workers. In the U.S. these are typically 3–5 year contracts, tens to hundreds of pages, and are not
collected in any systematic public database of their *contents*. Researchers have historically been
able to count union coverage far more easily than they could read what unions actually won.

This project addresses that gap. It takes scanned and digital CBAs, converts them to text, and has an
LLM read each one to record what provisions it contains, in a fixed comparative structure: **nine
provision areas, subdivided into 38 dimensions.**

### The nine areas and 38 dimensions

Note the two label conventions you will meet in the wild — the aggregate normalizes to the **long**
form, but the raw source data mixes both:

| Area (canonical, long) | Short alias | Dimensions |
|---|---|---|
| Compensation | *(same)* | `wage_level`, `wage_growth`, `premium_pay`, `progression_longevity` |
| Healthcare | *(same)* | `employer_contribution`, `plan_design`, `ancillary_coverage`, `eligibility_access` |
| Leave | *(same)* | `vacation`, `sick_leave`, `holidays`, `other_leave` |
| Job Security | `Security` | `layoff_order`, `recall`, `severance`, `benefit_continuation`, `seniority_system`, `subcontracting_work_preservation` |
| Scheduling | *(same)* | `schedule_notice`, `hours_guarantee`, `rest_meal`, `workload_cap` |
| Safety | *(same)* | `ppe`, `refuse_unsafe`, `joint_committee`, `hazard_assault` |
| Union Recognition | `Recognition` | `bargaining_unit`, `union_security`, `union_access`, `hiring_dispatch` |
| Dispute Resolution | `Disputes` | `just_cause`, `grievance_process`, `arbitration`, `investigation_appeal` |
| Ancillary benefits | `Ancillary` | `pension`, `savings_annuity`, `training_development`, `other_benefits` |

Eight areas have four dimensions; Job Security has six. Total 38.

---

## 3. The provenance labels

**This is the single most important thing to understand about the data.**

A large share of what a union contract delivers is not *described* in the contract. Health insurance
and pensions are frequently delivered through multiemployer trusts, with the contract naming the fund
and stating a contribution rate but the plan details living in a separate summary plan description.
Wage schedules sometimes sit in appendices that were never scanned.

A naive reading codes all of that as "no provision" — converting a real benefit into a false zero.
Those errors run **one direction only** (always downward) and concentrate in exactly the sectors that
bargain through trusts: construction, autos, grocery, hospitality, utilities. A controlled comparison
in the parent project measured the correction at **+0.21 on Healthcare** overall and **+0.31 on
agreements with off-page benefits**, with in-contract provisions unchanged.

So every dimension carries a **provenance** label distinguishing *absent* from *not visible here*:

| Label | Meaning | How the project's scorer treats it |
|---|---|---|
| `cba_contained` | Terms are printed in the contract body. | Scored normally. |
| `externalized_recoverable` | Delivered via a trust/fund/plan, **but a worker-facing magnitude is stated** in the contract ($/hr, "employer pays 100%", a copay figure). | Scored on that magnitude — **not** zeroed. |
| `externalized_offpage` | A trust/plan/SPD is named but no magnitude appears. | **Excluded** from the denominator. Never zero. |
| `source_gap` | An article or appendix is declared (e.g. in the table of contents) but its body is missing from the scanned text. | **Excluded** from the denominator. Never zero. |
| `not_applicable` | The dimension structurally cannot apply (e.g. hiring-hall referral at a direct-hire employer). | **Excluded** from the denominator. |
| `absent` | The provision could apply, but the contract is silent or offers only the statutory minimum. | Scored **1** on a 1–5 scale — the floor, not zero. |

**Read that last row twice.** `absent` is a substantive finding (the contract is silent) and scores 1.
The excluded labels are epistemic (we cannot see) and score nothing at all.

### The most common mistake

Treating `externalized_offpage` as absence. It means **the benefit almost certainly exists** — a
pension fund is named — and only its size is unknown. If you code it as zero you will systematically
understate exactly the union sectors that bargain hardest for benefits, and you will reproduce the bias
this dataset was built to remove.

---

## 4. Concepts vs. dimensions

Two nested vocabularies, easily confused:

- A **dimension** is one of the 38 fixed scoring sub-criteria above. Every document has a row for
  every dimension, whether or not the provision exists. Use these for **comparison across
  agreements** — the frame is constant.
- A **concept** is one of 58 controlled `C_*` measurement objects (`C_WAGE_BASE_RATE`,
  `C_HEALTH_MEDICAL_ACTIVE_CONTRIBUTION`, `C_LEAVE_VACATION`, `C_SUBCONTRACTING_WORK_PRESERVATION`,
  …). Concepts appear only when the model actually found the provision, and they carry the evidence.
  Use these for **finer-grained presence and magnitudes** than the 38 dimensions allow.

Roughly: dimensions are the fixed grid; concepts are what was found and where. A document typically
carries 33–38 concept records and 43–66 concept fields.

Two caveats on concepts. `C_HEALTH_MEDICAL_ACTIVE` is a deprecated umbrella superseded by
`..._CONTRIBUTION` and `..._PLAN_DESIGN` — do not mix it with its own children. And about 20 concepts
are flagged `required_core`, meaning the extractor was instructed to search for them in every
contract; the rest were recorded opportunistically, so **absence of a non-core concept is weaker
evidence than absence of a core one.**

A third caveat, measured at build time: the corpus contains **314 distinct `concept_id` values, not
58** — but the controlled vocabulary itself is intact. The distribution is sharply bimodal: **57
ids carry ≥50 records each and appear in 11 or 12 of the 12 runs**, which is the documented
vocabulary, essentially exactly. The other **257 are a drift tail confined to one run apiece** (175
appear exactly once), and they are ad-hoc renamings of concepts that already exist — `C_BASE_WAGE`
for `C_WAGE_BASE_RATE`, `C_BARGAINING_UNIT` for `C_RECOGNITION_COVERAGE_SCOPE` — not new
measurement objects. **Threshold on `codebook.concepts[id].n_records` at ≥50** and the taxonomy
matches its specification.

### Which layer is comparable across the corpus

**`dimension_coverage` is the only layer with a guaranteed-stable schema.** Its seven keys are
identical across all 13 extraction batches, and every document carries a row for all 38 dimensions
whether or not the provision exists. That fixed frame is what makes cross-agreement and cross-batch
comparison sound. **Build your comparative measures from it.**

`concept_records` has a stable core but drifts at the edges. `concept_fields` drifts badly — the
full build counts **over 380 distinct key names** across the corpus (not the ~35 estimated earlier),
with up to seven incompatible names for the same slot in different batches (see
[§9](#9-data-quality-caveats)). The aggregate coalesces the known collisions, but **treat
`concept_fields` as a rich semi-structured supplement, not a comparable panel.** A field's absence
for a given agreement may mean the provision was absent — or merely that that batch spelled the key
differently.

The decisive number is in `codebook.concepts[id].n_distinct_field_names`: `C_WAGE_BASE_RATE` carries
**37,131 distinct `field_name` values** across 6,957 records. `field_name` frequently holds a job
classification (`journeyman_hourly_rate`, `foreman_differential`, `rate_eff_7_1_79`) rather than a
stable slot name. No filter on a single `field_name` spelling will generalize.

---

## 5. How the data was produced

```
PDF  →  text  →  one LLM agent reads one contract  →  per-document JSON  →  this aggregate
```

1. **Text extraction.** Digital text layers were pulled with `pymupdf`. Scanned documents went
   through OCR — Mistral `mistral-ocr-3` for ~390 documents (~22,900 pages), and a Claude
   vision-transcription path for a smaller set.
2. **Provision extraction.** One LLM agent per contract, reading the full text in a single pass, with
   instructions that shape how you should read the output:
   - *"Work only from the files given to you; do not use outside knowledge of the employer."* The
     model was forbidden from filling gaps with what it might know about the company or industry.
   - **Every concept record must cite a location** in the source text. Headings, tables of contents,
     and page numbers were explicitly designated retrieval leads, **not evidence**.
   - A dimension row is required for all 38 dimensions **even when the provision is absent**.
   - Where the contract states a worker-facing value, it must be emitted as a `concept_fields` row —
     "the evidence pointer is the citation, not a substitute for a field."
   - Scanning the whole document was required before declaring anything missing; summarizing later
     articles from the table of contents was prohibited.
3. **Aggregation.** The deterministic, no-LLM merge described in [§10](#10-build-plan-for-aggregate_provisionspy).

### Models used

Extraction ran on Anthropic Claude models — **Sonnet 4.6** for the earlier batches and **Sonnet 5**
for the later and larger ones. Some documents were extracted by one and scored by the other. Model
attribution is recorded per document where known, but **covers only about 60% of the corpus**
(~4,266 of 7,054 source files); the two RetailEd batches and a majority of the largest batch are
unattributed. Treat model identity as a **partially observed covariate** — usable as a robustness
check, not as a clean instrument.

---

## 6. Structure of the JSON

One top-level object. The `codebook` block makes the file self-describing — the taxonomy, label
definitions, and the exact normalizations applied all travel *inside* the data.

```json
{
  "schema_version": "provisions_aggregate_v1",
  "generated_utc": "2026-08-17T...",
  "counts": { "documents": 7044, "runs": 12, "concept_records": 0, "concept_fields": 0,
              "dimension_coverage_rows": 0, "files_skipped": 0 },
  "codebook": {
    "provenance_labels": { "cba_contained": {"meaning": "...", "scoring_treatment": "..."}, "...": {} },
    "areas": ["Compensation", "Healthcare", "Leave", "Job Security", "Scheduling",
              "Safety", "Union Recognition", "Dispute Resolution", "Ancillary benefits"],
    "dimensions": { "wage_level": {"area": "Compensation", "label": "Base wage level ..."} },
    "concepts":   { "C_WAGE_BASE_RATE": {"subcategory": "Wages"} },
    "normalizations_applied": ["..."],
    "known_caveats": ["..."]
  },
  "runs": { "run200_2026-06": {"n_documents": 200, "models": "...", "notes": "..."} },
  "documents": [
    {
      "document_id": "102",
      "run": "run200_2026-06",
      "source_file": "data/runs/run200_2026-06/per_document/102.json",

      "document": {
        "employer": "Multiemployer embroidery/cutting association: ...",
        "union": "UFCW Local 1245",
        "title": "Memorandum of Agreement",
        "sector": "manufacturing_textile_embroidery",
        "effective_date": "2005-05-01",
        "expiration_date": null,
        "agreement_type": "multiemployer_association_memorandum_of_agreement"
      },
      "document_raw": { "...": "the untouched original block, before alias coalescing" },

      "metadata": { "state_abbrev": null, "naics": null, "n_workers": null,
                    "mistral_contract_year": null, "_source": "harmonized_cba_metadata.csv" },

      "quality": { "n_dimension_coverage": 38, "provenance_backfilled": true,
                   "unknown_dimension_ids": [], "has_truncated_flag": false },

      "concept_records": [
        { "concept_id": "C_HEALTH_MEDICAL_ACTIVE_CONTRIBUTION",
          "concept_label": "Employer health-fund monthly contribution",
          "measurement_status": "needs_common_units",
          "status_reason": "Employer contribution increased 15%: $133.00/month to $153.00/month ...",
          "status_flags": ["multiemployer_health_fund", "plan_design_external"],
          "evidence_pointer": "102.txt line 43" }
      ],

      "concept_fields": [
        { "concept_id": "C_HEALTH_MEDICAL_ACTIVE_CONTRIBUTION",
          "field_name": "employer_contribution_rate",
          "field_value": "153.00", "field_unit": "USD/month",
          "value_type": "str", "support_status": "directly_supported",
          "evidence_pointer": "102.txt line 43", "note": "eff 2006-03-01" }
      ],

      "dimension_coverage": [
        { "dimension_id": "employer_contribution", "area": "Healthcare",
          "provenance": "externalized_recoverable", "coverage": "externalized_recoverable",
          "category_as_recorded": "Healthcare", "provenance_as_recorded": "externalized_recoverable",
          "evidence_pointer": "102.txt line 43",
          "note": "Employer health-fund contribution stated with magnitude: $153.00/month ..." }
      ]
    }
  ]
}
```

### Field notes

- **`document_id`** is the only identifier present in every source file. Ids are bare numerals
  (`"102"`) for the original batch, and prefixed (`Cornell_DoL_…`, `Cornell_RetailEd_…`, `DoL_…`) for
  later ones. Some Cornell ids retain a `.pdf` suffix. **Ids are unique within a run**; treat
  `(run, document_id)` as the primary key.
- **`measurement_status`** on a concept record is documented as six values: `profile_only`,
  `needs_common_units`, `needs_external_source`, `source_or_ocr_gap`, `rejected`, and `score_ready`.
  In practice roughly 30 spellings occur; see `codebook.value_tallies.measurement_status`.
  `score_ready` was expected to be absent — only the downstream scorer sets it — but **483 records
  carry it**, all in `run_next50/100/150/498`, i.e. scorer write-back into the extraction files.
  They are carried verbatim and flagged per document at `quality.has_score_ready`.
- **`support_status`** on a concept field is `directly_supported` when the value is printed in the
  text; rejected candidates carry `unsupported_rejected`. Trust nothing above `directly_supported` as
  a printed fact.
- **`coverage` vs `provenance`** are duplicates in ~99.99% of rows. `provenance` is authoritative;
  where it was missing in the source, it was backfilled from `coverage` and `quality.provenance_backfilled`
  is set.
- **`document_raw`** preserves the original, un-coalesced `document` block, because the source field
  names drifted heavily (see [§9](#9-data-quality-caveats)). If a field you need is missing from the
  normalized `document`, look here.

---

## 7. Recipes

Stream the gzipped JSONL rather than loading the monolith — the single JSON peaks at 2–4 GB of RAM.

```python
import gzip, json

def documents(path="cba_provisions_aggregate.jsonl.gz"):
    with gzip.open(path, "rt", encoding="utf-8") as fh:
        for line in fh:
            yield json.loads(line)
```

**Build a presence table.** Mind the coding rule — and note the parent project is not internally
consistent about it, so choose deliberately:

```python
import pandas as pd

PRESENT = {"cba_contained", "externalized_recoverable", "externalized_offpage"}

def presence(prov):
    if prov in PRESENT:  return 1      # provision exists
    if prov == "absent": return 0      # contract is silent
    return None                        # source_gap / not_applicable: UNKNOWN, not zero

rows = []
for d in documents():
    r = {"document_id": d["document_id"], "run": d["run"]}
    for dc in d["dimension_coverage"]:
        r[dc["dimension_id"]] = presence(dc["provenance"])
    rows.append(r)
pres = pd.DataFrame(rows)     # NaN means unknown -- never fillna(0)
```

> **Convention warning.** The parent project contains two incompatible rules for
> `externalized_offpage`: its main workbook builder codes it **1** (the benefit exists), while one
> decomposition script codes it **blank** (its magnitude is unobserved). The rule above follows the
> former. If you are measuring *whether workers have a benefit*, code it 1. If you are measuring
> *what the contract specifies*, code it blank. State which you chose.

**Measure the off-page share by area** — the quantity that motivated the whole provenance scheme:

```python
from collections import Counter
c = Counter()
for d in documents():
    for dc in d["dimension_coverage"]:
        c[(dc["area"], dc["provenance"])] += 1
```

**Count concept frequency** (finer than the 38 dimensions):

```python
concepts = Counter(cr["concept_id"] for d in documents() for cr in d["concept_records"])
```

**Pull quantities.** `field_value` is heterogeneously typed *and* the surrounding keys are
batch-dependent, so coerce and never assume a key exists:

```python
def field_value(f):
    for k in ("field_value", "value", "raw_value"):   # coalesced at build; be defensive anyway
        if f.get(k) is not None:
            return f[k]
    return None

HOURLY = {"usd/hr", "usd/hour", "usd_per_hour", "$/hr"}   # not exhaustive -- see below

wages = [(d["document_id"], field_value(f), f.get("field_unit"))
         for d in documents() for f in d["concept_fields"]
         if f.get("concept_id") == "C_WAGE_BASE_RATE"          # filter on the concept...
         and (f.get("field_unit") or "").strip().lower() in HOURLY   # ...and the unit
         and f.get("support_status") == "directly_supported"]
```

**Filter on `concept_id`, never on `field_name`.** Field names are not standardized across batches
and frequently carry a job classification rather than a slot name — `C_WAGE_BASE_RATE` alone spans
37,131 distinct `field_name` values, so any single spelling matches almost nothing. (An earlier
draft of this recipe filtered on `field_name == "base_wage_rate_usd_hr"`, which returns **zero
rows** against the built corpus.) Units drift too: the eight commonest spellings of "per hour"
above cover most but not all of the hourly rows. Always inspect
`Counter(f["field_unit"] for f in ...)` for your concept first, and cross-check your yield by `run`
— a spelling that appears in only some batches will silently produce a biased subsample.

**Analyze by place and time** using the joined `metadata` (`state_abbrev`, `naics`,
`mistral_contract_year`) — but read the caveat on year coverage in [§9](#9-data-quality-caveats)
first.

---

## 8. Interpretation warnings

1. **Blank is not zero.** `source_gap` and `not_applicable` mean *unknown*. `fillna(0)` on a presence
   table silently converts missing scans into absent provisions and will bias every result downward.
2. **`absent` is not zero either** — it scores 1 in the project's rubric, as the floor of a 1–5 scale.
3. **`externalized_offpage` means the benefit exists.** See [§3](#3-the-provenance-labels).
4. **Thin coverage ≠ a stingy contract.** Memoranda of agreement and amendments legitimately contain
   only a few provisions; the rest is `source_gap`. Documents with fewer than ~2 readable dimensions
   in an area are `unmeasured` in the parent project and excluded from its rollups. Filter on
   `quality.n_dimension_coverage` and on per-area provenance counts before ranking anything.
5. **Evidence pointers reference text not shipped here.** `"102.txt line 43"` points into the source
   OCR, which is not part of this distribution. Pointers are for auditing against the originals, not
   for reconstructing quotes.
6. **This is LLM-extracted data.** It has been calibrated and spot-checked against an independent
   scoring pipeline at the *score* level, but the extraction layer in this file has **not** been
   exhaustively validated against human coding. Treat it as high-quality machine reading with a real
   error rate, and hand-check any small subsample your argument leans on.
7. **Do not compare raw counts across runs** without accounting for model and provenance
   differences. See [§9](#9-data-quality-caveats).

---

## 9. Data quality caveats

| Issue | What to do |
|---|---|
| **`document` field names drift.** Employer appeared as `employer_name`/`employer`/`employer_party`/`employer_or_industry`; dates in seven different shapes. All coalesced into canonical keys. | Use the normalized fields; fall back to `document_raw` when something is missing. |
| **`concept_fields` drifts badly** — over 380 distinct keys across the corpus. **Eight** appear in all 13 batches, not six: `concept_id`, `field_name`, `field_value`, `field_unit`, `support_status`, `evidence_pointer`, and also `note` and `effective_date`. Coalesced collisions — value: `field_value`/`value`/`raw_value` (mixed *within* single files); object-class: `field_class`/`classification`/`field_category`/`category`/`category_class`/`field_classification`/`field_classify`; note: `note`/`notes`/`field_note`/`field_notes`/`description`. Batch-specific one-offs (`step`, `period`, `frequency`, `trigger`, `field_max`, `active_health_class`, …) pass through untouched. | Rely on the six-key core. Anything else may be absent because of batch provenance rather than contract content. Expect a wide sparse frame from `json_normalize`. See `codebook.key_presence_by_run`. |
| **`concept_records` drifts at the edges.** Stable core everywhere (`concept_id`, `concept_label`, `measurement_status`, `status_reason`, `status_flags`, `subobject_type`, `evidence_pointer`), but `concept_reporting_class` is missing from `run_cornell_dol2_2026-06`, and `run_next498_2026-06` leaks ad-hoc domain keys into records (`dispatch_type`, `geographic_scope`, `referral_groups_count`, …). | Build no cross-corpus measure on any key outside the stable core. |
| **`field_value` types are heterogeneous** — `int`, `float`, `str`, `None`, `bool`, and occasionally `list`/`dict`. | Always coerce. `value_type` records what was found. |
| **Category labels were mixed** short/long, sometimes within one file. The aggregate derives `area` from `dimension_id` (a 1:1 map) and ignores the recorded label. | Use `area`. `category_as_recorded` is retained for auditing only. |
| **`provenance` was missing** on ~92% of the earliest batch's rows; backfilled from `coverage`. | Check `quality.provenance_backfilled` if this matters to you. |
| **Row counts vary.** Measured over the 7,044 included documents: 7,021 have exactly 38 dimension rows, 20 have 34 (the Dispute Resolution block omitted), **2 have 26**, and one has 39 (a spurious `Miscellany` row — the only `dimension_id` in the corpus outside the 38). | Filter on `quality.n_dimension_coverage`; check `unknown_dimension_ids`. |
| **`wrong_object_check`** appears only in the earliest batch (`run200_2026-06`, ~6,101 rows, observed value always `"ok"`) and is **not** in the documented output contract — a legacy self-audit flag asserting the value was attached to the correct measurement object, dropped after that batch. | Carried through verbatim. Not a reliable filter; never compare across batches. |
| **One batch had extraction attrition.** The largest batch (`run_dol_textlayer_2026-07`, 3,564 docs) was extracted over a different API transport and its logs record a material number of parse failures. Failed documents are simply missing, so attrition is **not** missing-at-random. | Include `run` as a control; test sensitivity by excluding this batch. |
| **Model heterogeneity**, only ~60% attributed. | See [§5](#5-how-the-data-was-produced). |
| **Contract year is partly imputed.** The metadata's `mistral_contract_year` is itself model-derived, and the parent project falls back through several sources to date a contract. | Do not treat year as exact; check coverage before running trends. |
| **A pilot batch is excluded.** `run_sample10_2026-06` (10 docs) is omitted as a duplicate subset of a later batch. | Nothing to do — noted for reproducibility. |

---

## 10. Build plan for `aggregate_provisions.py`

**Implemented.** This section specifies it; [§11](#11-build-results) records what the build actually
produced.

```
python scripts/aggregate_provisions.py               # full build (~10 min cold)
python scripts/aggregate_provisions.py --run RUN     # one run only
python scripts/aggregate_provisions.py --force       # rebuild every shard
python scripts/aggregate_provisions.py --verify      # build, then run the verification suite
python scripts/aggregate_provisions.py --verify-only # verify the artifacts already on disk
```

### Hard constraint: standalone

The script reads **only**:

1. `runs/run*/per_document/*.json` — the extraction outputs
2. `harmonized_cba_metadata.csv` — the harmonized metadata, alongside the script

Both resolve relative to the script's own location and are overridable with `--runs-dir` /
`--metadata`. (Earlier drafts of this section gave the parent project's paths,
`data/runs/…` and `../metadata_harmonization/data/output/…`; those are not the layout here.)

It must **not** import from `pipeline/scripts/` nor read `pipeline/config/`. Every constant it needs
is inlined in the script itself, so it remains runnable if lifted out of the project. The constants
to inline are all documented above and are the authoritative copies:

- the 9 canonical area names ([§2](#2-minimal-project-context))
- the 38 `dimension_id → area` map ([§2](#2-minimal-project-context)) — note Scheduling's fourth
  dimension is **`workload_cap`**; several scripts elsewhere in the project misname it
  `workload_staffing`
- the short→long alias map `{Security: Job Security, Recognition: Union Recognition,
  Disputes: Dispute Resolution, Ancillary: Ancillary benefits}`
- the six provenance labels and their treatments ([§3](#3-the-provenance-labels))
- `EXCLUDE_RUNS = {"run_sample10_2026-06"}`
- the id join rule: `cba_id = "DoL_" + id` if the id is all digits, else the id verbatim

Dependencies: standard library plus `pandas` for the metadata CSV only (or `csv` to stay
dependency-free).

### Expected inputs

| Run | Docs | | Run | Docs |
|---|---|---|---|---|
| `run200_2026-06` | 200 | | `run_cornell_dol3_2026-06` | 400 |
| `run_next50_2026-06` | 50 | | `run_cornell_dol4_2026-06` | 595 |
| `run_next100_2026-06` | 100 | | `run_dol_textlayer_2026-07` | 3,564 |
| `run_next150_2026-06` | 150 | | `run_retailed500_2026-07` | 500 |
| `run_next498_2026-06` | 498 | | `run_retailed_tail79_2026-07` | 78 |
| `run_cornell_dol_2026-06` | 500 | | `run_cornell_dol2_2026-06` | 409 |

Total **7,044**. Excluded: `run_sample10_2026-06` (10). `run_nlrbedge_2026-07` has an empty
`per_document/` and drops out naturally — guard against the directory being absent.

### Source corpus is verified clean

A full `json.load` pass over every `data/runs/*/per_document/*.json` returned:

```
total 7054   zero-byte 0   unparseable 0   no dimension_coverage 0
```

So error handling is **insurance, not a live code path**. Keep the `try/except (json.JSONDecodeError,
OSError): continue` idiom the project uses, but **count and print the skips** — every existing script
swallows them silently, which is why nobody knew the corpus was clean. A `skipped: 0` line in the
summary makes the next person's audit unnecessary. Do not build a `getsize(p) == 0` pre-check on the
assumption that cloud-only placeholders exist; keep the `OSError` catch, which is what such a read
would raise if the sync state changes again.

**Glob on `*.json`, not `os.listdir`.** `run200_2026-06/per_document/` contains an abandoned
atomic-write temp file, `143.json.tmp.51616.8271c4a8e348`, which is why a raw directory listing counts
7,057 where the glob counts 7,054. Derive ids with `os.path.basename(p)[:-5]` *only* after a `*.json`
glob has guaranteed the extension.

### Should still be resumable

Part of the corpus initially reported the macOS `dataless` (cloud-only) flag. A bulk re-check now
reports **0 dataless across all 7,054 files**, and the verification pass completed in **~6 minutes
cold** — I/O-bound on first touch, not pathological.

> `du` **cannot** be used to test hydration here. On macOS Dropbox File Provider paths it
> under-reports, showing 0 KB for directories whose files are demonstrably readable. The
> authoritative signal is the `dataless` flag from `stat -f "%Sf"`.

Dropbox re-evicts over time, so tolerate `OSError` per file rather than assuming availability — and
shard, as insurance.

So: process **one run at a time**, writing `_provisions_shards/<run>.jsonl` on completion, and skip
runs whose shard already exists unless `--force`. Merge shards in a second pass. A stall then costs one
run, not the whole job. Accept an optional run-name argument to process a single run.

**Single streaming pass.** Harvest all three arrays in one visit per file; never re-open a file.

### Normalization rules

1. `document_id` → `str()` (some are typed `int`). Verify it matches the filename stem.
2. `document` → coalesce aliases into `employer`, `union`, `title`, `sector`, `effective_date`,
   `expiration_date`, `agreement_type`; retain the original as `document_raw`.
3. `concept_records` → keep `concept_id`, `concept_label`, `measurement_status`, `status_reason`,
   `status_flags`, `evidence_pointer`; pass through `subobject_type` / `concept_reporting_class` when
   present (they are optional and usually absent). Preserve unrecognized keys rather than dropping
   them.
4. `concept_fields` → coalesce, in this precedence order:
   `field_value | value | raw_value` → **`field_value`**;
   `concept_id | record_concept_id` → **`concept_id`**;
   `field_name | field` → **`field_name`**;
   `field_class | classification | field_category | category | category_class | field_classification | field_classify`
   → **`field_class`**;
   `note | notes | field_note | field_notes | description` → **`note`**.
   Record `value_type`. **Never cast the value** — preserve it as found. Pass batch-specific one-off
   keys through untouched rather than dropping them.
5. `dimension_coverage` → derive `area` from `dimension_id`; keep `category_as_recorded`. Set
   `provenance = provenance or coverage`; normalize the stray `source_or_ocr_gap` → `source_gap`,
   keeping `provenance_as_recorded`.
6. Join metadata on the derived `cba_id`; prefix or namespace the joined fields so their external
   origin stays visible.
7. Populate `quality`: `n_dimension_coverage`, `unknown_dimension_ids`, `provenance_backfilled`,
   `has_truncated_flag`.
8. Read with `encoding="utf-8-sig"` (BOM tolerance). On `json.JSONDecodeError` / `OSError`, skip and
   **count** — report the tally rather than failing silently, as existing project scripts do.
9. **Union the keys; never assume a fixed schema.** Emit a per-run key-presence table into
   `codebook.key_presence_by_run` for all three arrays, so a consumer can see at a glance which
   batches carried which optional keys — and can tell "this batch didn't record it" apart from "this
   contract didn't have it." This is the single most useful thing the aggregate can add over the raw
   files.

### Outputs

`cba_provisions_aggregate.json` (compact separators, **331 MB** as built) and
`cba_provisions_aggregate.jsonl.gz` (**66 MB**), both in this directory, plus a summary to stdout.
Deterministic, no LLM, safe to re-run. Both are streamed out document by document, so the build
never holds the corpus in memory.

The artifacts came out roughly double the 290 MB / 30 MB estimated here, because the aggregate
carries all 25 metadata columns, the untouched `document_raw` block, and every unrecognized
passthrough key rather than a documented subset.

> Both artifacts sit inside a Dropbox folder and are ~145× larger than anything else in the project.
> Dropbox re-uploads the monolithic JSON in full on every rebuild and may evict it back to cloud-only.
> Hand recipients the `.jsonl.gz`.

### Verification

1. **One run first:** build `run200_2026-06` alone. Document `102` should yield 2 concept records and
   7 concept fields, and its `Disputes` rows must emerge as area `Dispute Resolution`.
2. **In-script assertions:** every `dimension_id` resolves (report unknowns, don't crash); no
   `measurement_status == "score_ready"`; every `provenance` is one of the six labels after
   normalization; `document_id` unique within a run.
3. **Resume works:** interrupt a full run, relaunch, confirm completed shards are skipped and the
   final count is 7,044.
4. **Round-trip:** stream the `.jsonl.gz`, assert the line count equals `counts.documents`, and
   deep-compare three random documents against their source files.
5. **Cross-check against an existing artifact.** `data/analysis/master/master_presence_wide.csv`
   does not exist in this repo. Every run instead ships `outputs/clause_presence_long.csv`, whose
   coding is exactly the [§7](#7-recipes) presence rule — but it is built from `cell_scores/`, the
   **scoring** stage, not from `per_document/`. It is therefore an agreement measure against the
   layer downstream of this one, not an identity test; see [§11](#11-build-results).

The identity test is instead **fidelity against the source files**: every document in the aggregate
must reproduce its own `per_document/*.json` — row counts, the `dimension_id` and `concept_id`
sequences, every recorded `provenance`/`coverage`, every coalesced `field_value`, and
`document_raw`. `--verify` runs this over all 7,044 documents. A failure here is a hard error.

---

## 11. Build results

Built and verified 2026-08-17. Reproduce with
`python scripts/aggregate_provisions.py --force --verify` (~10 minutes cold).

```
documents 7044   runs 12   concept_records 228252   concept_fields 331582
dimension_coverage_rows 267569   files_skipped 0
```

`files_skipped 0` over 7,054 globbed files, of which 7,044 are included and 10 are the excluded
`run_sample10_2026-06` pilot. The corpus is clean; the error path never fired.
`run_nlrbedge_2026-07` has an empty `per_document/`, so it is dropped on the file count rather
than on the directory's existence — it would otherwise land in the output as a thirteenth run
contributing zero documents.

### Verification outcome

| Test | Result |
|---|---|
| Single run (`run200_2026-06`), document `102` | 2 concept records, 7 concept fields, 38 dimension rows; `Disputes` rows resolve to area `Dispute Resolution` |
| Fidelity vs source files | **7,044 / 7,044 documents reproduce their `per_document/*.json` exactly** |
| Round-trip | `.jsonl.gz` line count 7,044 == `counts.documents` |
| Resume | Removing one shard rebuilds only that run; a stale `.jsonl.partial` is never consumed |
| Metadata join | 7,044 / 7,044 matched — 6,466 `exact`, 577 `retailed_base`, 1 `exact_no_pdf_suffix` |
| Cross-check vs scoring layer | 99.9585% agreement over 267,500 cells (see below) |

### The cross-check is an agreement measure, not an identity test

`clause_presence_long.csv` is built from `cell_scores/` — the scoring stage — not from
`per_document/`. The scorer sits downstream of this aggregate and repairs what the extractor
missed. Of the 111 divergences:

- **86 are `row_absent_from_extraction`** — the scorer emits all 38 dimensions even for the 23
  documents whose extraction omitted a block (the 34-row and 26-row cases). The aggregate has no
  row to report because the extractor wrote none.
- **25 are `provenance_revised_by_scorer`** — the scorer changed the label outright, in both
  directions (e.g. `DoL_1199/severance`: extraction says `absent`, scoring says `cba_contained`).

Both are the extraction/scoring boundary the aggregate deliberately sits on the near side of, not
normalization error. Agreement below 99.9% would indicate something structurally wrong.

### Departures from the §10 spec, and why

| §10 said | What the data required |
|---|---|
| Assert no `measurement_status == "score_ready"` | 483 records carry it, in `run_next50/100/150/498`. Carried verbatim, flagged at `quality.has_score_ready`, tallied in the summary. The build does not abort. |
| Every `provenance` is one of the six labels | 10 rows carry a `measurement_status` value in the provenance slot. Resolved via `coverage` where valid (1 of 10), null otherwise, original always kept at `provenance_as_recorded`. |
| `document_id` → `str()`, verify against the filename stem | The filename stem is treated as **authoritative** instead: the in-file value is `int` on 109 documents, `null` on 2, and case-mismatched on 5 of the included ones (`DOL_2133` vs `DoL_2133`). Divergences are kept at `quality.document_id_as_recorded`. |
| Join rule: `DoL_`+id if digits, else verbatim | Matches 6,466 / 7,044. All 578 RetailEd documents miss, because the metadata splits each agreement into per-part rows. Two further tiers were added — `.pdf`-suffix strip (verified collision-free, resolves 1) and RetailEd base id with per-column consensus across parts (resolves 577). |
| Metadata: the four fields in the §6 example | All 25 columns are carried, namespaced under `metadata` with `_source`, `_cba_id`, `_join`, `_n_metadata_rows`, `_conflict_fields`, and `_member_cba_ids`. Values stay verbatim strings, empty cells become null — `state_fips` and `naics` carry significant leading zeros, so coerce before arithmetic. |

On the RetailEd consensus rule: 468 of 578 bases have 2–10 parts, and those parts disagree often —
`effective_date` on 451 bases, `employer` on 347, `state_abbrev` on 139. Where parts disagree the
value is **null** and the column is named in `_conflict_fields`. Taking the first part would have
fabricated agreement across genuinely different sub-agreements.

### What the aggregate adds over the raw files

`codebook.key_presence_by_run` reports, per run and per array, how many rows carried each key and
what share of that run's rows that is. Fractions rather than booleans, because the interesting
cases are partial: `concept_reporting_class` is present in all 13 batches but on only **1.8%** of
`run_cornell_dol2_2026-06`'s concept records. That is what lets a consumer tell *"this batch didn't
record it"* apart from *"this contract didn't have it"* — the distinction the raw files cannot
support.
