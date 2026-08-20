# Structural consistency of the CBA extraction corpus

What varies across the 12 extraction runs and 7,044 documents, what stays fixed, and what is
missing. Every number here is measured from `cba_provisions_aggregate.jsonl.gz` and its embedded
`codebook`; reproduce with `python scripts/aggregate_provisions.py --force --verify`.

Companion to [README.md](README.md) — that file tells you how to *use* the data, this one tells you
how far you can trust it to be the same shape from one batch to the next.

---

## The headline

**One layer is stable and three are not.** `dimension_coverage` is a fixed 38-row grid with 7 keys,
identical in all 12 runs. `concept_records` and especially `concept_fields` drift so hard that most
of their key space exists in a single batch. The `document` block is worse still.

| Layer | Distinct keys corpus-wide | Present in all 12 runs | Present in exactly 1 run |
|---|---:|---:|---:|
| `dimension_coverage` | 9 | **7** (78%) | 2 |
| `concept_records` | 108 | 8 (7%) | **61** (56%) |
| `concept_fields` | **497** | 9 (2%) | **364** (73%) |
| `document` | **1,268** | — | — |

Read that bottom row twice. Of 497 key names ever used in `concept_fields`, 364 were used by one
batch and never again. **Any cross-corpus measure built on a `concept_fields` key other than the
core nine is measuring batch provenance, not contract content.**

This is the single most important structural fact about the corpus, and it is why
[README §4](README.md#4-concepts-vs-dimensions) directs comparative work to `dimension_coverage`.

---

## 1. Structural drift

### 1.1 Key-space size per run

Source keys, counted before the aggregate's alias coalescing (`codebook.key_presence_by_run`).

| Run | Docs | `concept_records` keys | `concept_fields` keys | `dimension_coverage` keys | `document` keys |
|---|---:|---:|---:|---:|---:|
| `run200_2026-06` | 200 | 13 | 17 | 7 | 155 |
| `run_next50_2026-06` | 50 | 9 | 15 | 7 | 77 |
| `run_next100_2026-06` | 100 | 11 | 20 | 7 | 101 |
| `run_next150_2026-06` | 150 | 20 | 23 | 7 | 112 |
| `run_next498_2026-06` | 498 | 22 | 93 | 7 | 263 |
| `run_cornell_dol_2026-06` | 500 | 35 | **132** | 7 | 227 |
| `run_cornell_dol2_2026-06` | 409 | 28 | 32 | 7 | 98 |
| `run_cornell_dol3_2026-06` | 400 | 16 | 28 | 7 | 116 |
| `run_cornell_dol4_2026-06` | 595 | 23 | 56 | 8 | 243 |
| `run_dol_textlayer_2026-07` | 3,564 | **78** | **188** | 7 | **570** |
| `run_retailed500_2026-07` | 500 | 27 | **218** | 8 | 514 |
| `run_retailed_tail79_2026-07` | 78 | 11 | 68 | 7 | 184 |

The `dimension_coverage` column is the point: **7, in every run, without exception.** The two
extra keys are single strays — `correction_note` (`run_cornell_dol4`) and `subtext`
(`run_retailed500`).

Everywhere else, key count scales with batch size and with nothing else. `run_retailed500_2026-07`
invented 122 `concept_fields` keys used nowhere else; `run_dol_textlayer_2026-07` invented 101.

### 1.2 The stable cores

These are the keys you can rely on. Everything outside them is batch-conditional.

- **`dimension_coverage`** (7 keys, all 12 runs): `dimension_id`, `category`, `coverage`, `provenance`,
  `evidence_pointer`, `note`, `document_id`
- **`concept_records`** (8 keys, all 12 runs): `concept_id`, `concept_label`, `subobject_type`,
  `concept_reporting_class`, `measurement_status`, `status_reason`, `status_flags`,
  `evidence_pointer`
- **`concept_fields`** (9 keys, all 12 runs): `concept_id`, `field_name`, `field_value`, `field_unit`,
  `support_status`, `evidence_pointer`, `note`, `effective_date`, `subobject_type`

Universality is not the same as density. `concept_reporting_class` appears in all 12 runs but on
only **1.8%** of `run_cornell_dol2_2026-06`'s concept records, against near-100% elsewhere. Consult
`codebook.key_presence_by_run`, which reports `pct_of_rows` per key per run for exactly this reason
— it is what distinguishes *"this batch didn't record it"* from *"this contract didn't have it."*

### 1.3 The same slot under different names

Coalesced by the builder, listed here so you know what was merged:

| Canonical | Source spellings encountered |
|---|---|
| `field_value` | `field_value`, `value`, `raw_value` — **mixed within single files** |
| `field_class` | `field_class`, `classification`, `field_category`, `category`, `category_class`, `field_classification`, `field_classify` |
| `note` | `note`, `notes`, `field_note`, `field_notes`, `description` |
| `concept_id` | `concept_id`, `record_concept_id` |
| `field_name` | `field_name`, `field` |
| `employer` | `employer`, `employer_name`, `employer_or_association`, `employer_or_sector`, `employer_party`, `parties` |
| `effective_date` | 11 spellings, including `agreement_dates`, `agreement_period`, `term_start`, `contract_start` |

Two source keys carried literal leading whitespace (`' support_status'`, `' note'`) and are stripped
on load.

---

## 2. Taxonomy stability

### 2.1 The 38-dimension grid does not move

**Every one of the 38 `dimension_id` values appears in every one of the 12 runs.** Corpus-wide,
exactly one row out of 267,569 falls outside the vocabulary: a single `miscellany` row in
`run_next100_2026-06`. The `dimension_id → area` map is 1:1 and total.

This is the strongest result in the report. Whatever else drifted, the comparative frame did not.

### 2.2 Concept vocabulary: intact core, 257-id drift tail

314 distinct `concept_id` values against a documented vocabulary of ~58. The distribution is
bimodal, and the split is clean:

| Band | Ids | Median runs appearing in | Interpretation |
|---|---:|---:|---|
| ≥1,000 records | 48 | 12 | The controlled vocabulary |
| 50–999 records | 9 | 11 | Genuine opportunistic concepts |
| 2–49 records | 82 | **1** | Drift |
| exactly 1 record | 175 | **1** | Drift |

**57 ids carry ≥50 records and appear in essentially every run** — that is the documented
vocabulary, recovered almost exactly. The other 257 sit in one run apiece and are ad-hoc renamings
of concepts that already exist: `C_BASE_WAGE` for `C_WAGE_BASE_RATE`, `C_BARGAINING_UNIT` for
`C_RECOGNITION_COVERAGE_SCOPE`, `C_401K_SAVINGS` for `C_ANCILLARY_SAVINGS_ANNUITY`. One id is
literally `"C_CHILD_DEPENDENT_CARE / novelty (Build New Mexico fund)"`.

**Threshold `codebook.concepts[id].n_records` at ≥50 and the taxonomy matches its specification.**

Two runs are drift hotspots — `run200_2026-06` (174 distinct ids, 126 off-core) and
`run_cornell_dol_2026-06` (180, 132) — so raw concept counts are not comparable across runs without
that threshold.

### 2.3 Category labels are mixed, and mixed *within* runs

The source records each dimension's area as either a short (`Security`) or long (`Job Security`)
label. **7 of 12 runs use both conventions**, sometimes in the same file:

| Run | Short | Long | Mixed |
|---|---:|---:|:--:|
| `run200_2026-06` | 3,596 | 0 | |
| `run_next50_2026-06` | 900 | 0 | |
| `run_next100_2026-06` | 1,800 | 0 | |
| `run_next150_2026-06` | 2,696 | 0 | |
| `run_next498_2026-06` | 7,774 | 1,186 | ✓ |
| `run_cornell_dol_2026-06` | 8,512 | 476 | ✓ |
| `run_cornell_dol2_2026-06` | 7,336 | 18 | ✓ |
| `run_cornell_dol3_2026-06` | 7,188 | 0 | |
| `run_cornell_dol4_2026-06` | 10,102 | 600 | ✓ |
| `run_dol_textlayer_2026-07` | 62,312 | 1,816 | ✓ |
| `run_retailed500_2026-07` | 6,080 | 2,912 | ✓ |
| `run_retailed_tail79_2026-07` | 802 | 594 | ✓ |

The aggregate ignores the recorded label entirely and derives `area` from `dimension_id`. Use
`area`; `category_as_recorded` is retained for auditing only.

### 2.4 Status vocabularies drift badly

Documented value counts versus observed distinct values per run:

| Run | `measurement_status` (6 documented) | `support_status` (2 documented) | `field_unit` | `field_name` |
|---|---:|---:|---:|---:|
| `run200_2026-06` | 5 | 3 | 3,475 | 7,716 |
| `run_next50_2026-06` | 5 | 6 | 563 | 2,353 |
| `run_next100_2026-06` | 5 | 6 | 1,009 | 5,110 |
| `run_next150_2026-06` | 5 | 7 | 827 | 5,478 |
| `run_next498_2026-06` | 10 | 22 | 4,031 | 21,187 |
| `run_cornell_dol_2026-06` | 12 | 27 | 4,029 | 19,685 |
| `run_cornell_dol2_2026-06` | 14 | 25 | 3,091 | 13,941 |
| `run_cornell_dol3_2026-06` | 13 | 18 | 3,013 | 13,701 |
| `run_cornell_dol4_2026-06` | 15 | 25 | 4,740 | 18,551 |
| `run_dol_textlayer_2026-07` | 19 | **116** | 18,555 | 94,621 |
| `run_retailed500_2026-07` | 8 | 13 | 3,752 | 23,901 |
| `run_retailed_tail79_2026-07` | 5 | 5 | 825 | 3,834 |

`support_status` is documented as two values and reaches **116 distinct spellings** in the largest
batch — `not_supported_external_trust`, `not_stated_appendix_missing`, `ocr_illegible`, and a long
tail of one-offs. `directly_supported` still covers 99.54% of rows corpus-wide, so a
`== "directly_supported"` filter is safe; anything more specific is not portable across runs.

**`field_name` is not a vocabulary at all.** `C_WAGE_BASE_RATE` alone spans **37,131 distinct
`field_name` values** across 6,957 records, because the field name frequently carries a job
classification (`journeyman_hourly_rate`, `foreman_differential`, `rate_eff_7_1_79`). Filter on
`concept_id` and `field_unit`; never on a single `field_name` spelling.

---

## 3. What is missing

### 3.1 Missing *rows*: the grid is 99.7% complete

| Rows per document | Documents |
|---:|---:|
| 38 (complete) | 7,021 |
| 34 (Dispute Resolution block omitted) | 20 |
| 26 | 2 |
| 39 (spurious `miscellany` row) | 1 |

Per-run completeness runs 97.4%–100%; `run_retailed_tail79_2026-07` is lowest at 97.4%. Filter on
`quality.n_dimension_coverage` before any ranking.

### 3.2 Missing *knowledge*: 9.2% of the grid is epistemically blank

Across all 267,569 dimension rows, **9.22% (24,682) is unknown** — `source_gap`, `not_applicable`, or null —
and must never be read as zero. The rate varies more than twofold by run:

| Run | `cba_contained` | `absent` | off-page | recoverable | `source_gap` | `not_applicable` | **unknown** |
|---|---:|---:|---:|---:|---:|---:|---:|
| `run200_2026-06` | 66.1% | 15.4% | 6.7% | 2.7% | 5.9% | 3.2% | 9.1% |
| `run_next50_2026-06` | 71.0% | 8.7% | 8.2% | 3.1% | 5.9% | 3.2% | 9.1% |
| `run_next100_2026-06` | 70.6% | 13.8% | 4.3% | 5.4% | 2.7% | 3.2% | 5.9% |
| `run_next150_2026-06` | 57.1% | 23.9% | 6.8% | 8.6% | 1.5% | 2.1% | 3.7% |
| `run_next498_2026-06` | 67.4% | 18.4% | 4.9% | 3.5% | 2.8% | 3.1% | 5.9% |
| `run_cornell_dol_2026-06` | 67.7% | 16.5% | 4.8% | 3.1% | 4.2% | 3.8% | 7.9% |
| `run_cornell_dol2_2026-06` | 67.3% | 16.3% | 4.3% | 3.4% | 3.7% | 5.0% | 8.7% |
| `run_cornell_dol3_2026-06` | 66.6% | 16.7% | 4.4% | 3.3% | 3.9% | 5.0% | 9.0% |
| `run_cornell_dol4_2026-06` | 64.1% | 16.2% | 3.5% | 0.7% | **9.8%** | 5.8% | **15.5%** |
| `run_dol_textlayer_2026-07` | 64.9% | 17.7% | 4.3% | 3.1% | 5.0% | 5.0% | 10.1% |
| `run_retailed500_2026-07` | 61.9% | **28.1%** | 3.6% | 2.2% | 1.3% | 2.9% | 4.2% |
| `run_retailed_tail79_2026-07` | 59.4% | **28.3%** | 4.0% | 4.1% | 1.8% | 2.5% | 4.3% |

Two cross-run hazards here:

- **`run_cornell_dol4_2026-06` has 9.8% `source_gap`**, triple the corpus norm, and the lowest
  `externalized_recoverable` rate at 0.7%. Its scans are materially more incomplete.
- **The RetailEd batches code 28% `absent`** against 8.7%–24% elsewhere. Since `absent` scores 1
  and unknown scores nothing, a batch that resolves ambiguity toward `absent` will look
  systematically stingier. **Do not compare raw presence rates across runs without controlling for
  `run`.**

### 3.3 Off-page delivery is real and concentrated

The phenomenon the provenance scheme exists to capture, by area:

| Area | `externalized_offpage` | `externalized_recoverable` | `not_applicable` | `absent` |
|---|---:|---:|---:|---:|
| **Healthcare** | **30.22%** | 11.84% | 0.18% | 10.49% |
| **Ancillary benefits** | **9.25%** | 14.90% | 0.21% | 28.43% |
| Leave | 1.14% | 1.41% | 1.23% | 17.17% |
| Compensation | 0.50% | 0.05% | 0.21% | 3.51% |
| Job Security | 0.37% | 0.25% | 1.04% | 26.97% |
| Dispute Resolution | 0.11% | 0.00% | 0.10% | 9.78% |
| Safety | 0.07% | 0.02% | 8.68% | 46.01% |
| Scheduling | 0.03% | 0.01% | 12.16% | 15.06% |
| Union Recognition | 0.01% | 0.01% | 18.66% | 1.91% |

**Nearly a third of all Healthcare dimension rows are off-page**, plus another 12% recoverable only
via a stated magnitude. Coding `externalized_offpage` as absence would zero out 42% of the observed
Healthcare signal, concentrated in the trust-bargaining sectors. This is the bias the dataset was
built to remove — see [README §3](README.md#3-the-provenance-labels).

### 3.4 Missing *citations*

`evidence_pointer` is null on **11.10%** of dimension rows corpus-wide, ranging from 0.5%
(`run_next100`) to **21.1%** (`run200_2026-06`). Concept records are near-universally cited
(0.01% null corpus-wide, <0.2% in every run). If your argument depends on auditing pointers back to source text, check
the null rate for your runs first.

`provenance` itself was absent from the source on 8,921 rows and backfilled from `coverage`. This
is overwhelmingly one batch: **90.5% of `run200_2026-06` documents** are backfilled, against 0–1.7%
everywhere else. `quality.provenance_backfilled` flags it per document.

### 3.5 Missing *identity*

Percentage of documents where the normalized `document` block has a non-null value:

| Run | employer | union | title | sector | effective | expiration | agreement_type |
|---|---:|---:|---:|---:|---:|---:|---:|
| `run200_2026-06` | 96.0 | 96.0 | 34.0 | 95.0 | 95.5 | 68.5 | 31.5 |
| `run_next50_2026-06` | 96.0 | 84.0 | 28.0 | 88.0 | 84.0 | 62.0 | 8.0 |
| `run_next100_2026-06` | 95.0 | 97.0 | 45.0 | 98.0 | 97.0 | 61.0 | 8.0 |
| `run_next150_2026-06` | 95.3 | 72.7 | 68.7 | 99.3 | 96.0 | 58.0 | 45.3 |
| `run_next498_2026-06` | 98.8 | 97.2 | 37.1 | 98.2 | 89.2 | 70.5 | 22.1 |
| `run_cornell_dol_2026-06` | 99.2 | 99.0 | 39.4 | 96.0 | 96.6 | 85.6 | 14.6 |
| `run_cornell_dol2_2026-06` | 99.5 | 98.3 | 44.0 | 98.0 | 97.8 | 80.4 | 6.4 |
| `run_cornell_dol3_2026-06` | 99.0 | 98.0 | 41.0 | 97.2 | 95.8 | 79.0 | 9.0 |
| `run_cornell_dol4_2026-06` | 95.8 | 92.3 | 11.8 | 83.9 | 87.2 | 32.4 | 18.2 |
| `run_dol_textlayer_2026-07` | 95.4 | 91.9 | 28.8 | 92.4 | 93.3 | 51.3 | 10.0 |
| `run_retailed500_2026-07` | 86.2 | 87.8 | 14.6 | 87.0 | 62.8 | 57.2 | 15.8 |
| `run_retailed_tail79_2026-07` | 91.0 | 94.9 | 19.2 | 92.3 | 69.2 | 62.8 | 20.5 |

Employer and union are reliable (86–99.5%). **`title` and `agreement_type` are not usable as
covariates** — 11.8%–68.7% and 6.4%–45.3% respectively, and the variation tracks the batch, not the
contracts. `expiration_date` swings from 32.4% to 85.6%. Prefer the joined `metadata` block for
identity fields wherever it is populated.

### 3.6 Missing *metadata*

All 7,044 documents join to `harmonized_cba_metadata.csv`, but the columns are unevenly filled:

| Coverage | Columns |
|---|---|
| 100% | `source`, `metadata_source`, `multi_state`, `also_in_dol`, `also_in_cornell` |
| 86–94% | `filename`, `filepath`, `state_abbrev`/`state_name`/`state_fips` (89.9%), `employer` (88.9%), `union` (88.7%), `naics` (87.4%), `sector` (86.0%) |
| 65–72% | `effective_date` (72.4%), `expiration_date` (64.7%) |
| 47–50% | `mistral_contract_year` (50.4%), `mistral_naics`, `mistral_*_wage` (46.7%) |
| <40% | `n_workers` (39.6%), `naics_description` (14.8%) |

**Time-series work is capped at ~50% of the corpus** by `mistral_contract_year`, which is itself
model-derived. Worker-weighted analysis is capped at ~40%.

Joins by kind: 6,466 `exact`, 577 `retailed_base`, 1 `exact_no_pdf_suffix`.

### 3.7 RetailEd metadata is partly unresolvable

The metadata splits each RetailEd agreement into per-part rows; the aggregate joins on the base id
and takes the consensus across parts, nulling any column where the parts disagree. Of the 577 base
joins:

| Column | Nulled by disagreement |
|---|---:|
| `effective_date` | 451 (78.2%) |
| `union` | 359 (62.2%) |
| `employer` | 347 (60.1%) |
| `state_abbrev` / `state_name` / `state_fips` | 139 (24.1%) |
| `naics` | 129 (22.4%) |
| `sector` | 93 (16.1%) |

So for the 578 RetailEd documents, **employer, union and effective date are unavailable ~60–78% of
the time**, and state/NAICS ~22–24%. `_conflict_fields` names the affected columns per document and
`_member_cba_ids` lists the contributing rows. Taking the first part instead would have supplied
confident values that the source does not support.

---

## 4. What is included that shouldn't be

- **`score_ready` contamination.** 483 concept records carry
  `measurement_status == "score_ready"`, which only the downstream scorer sets. All are in
  `run_next50/100/150/498` — scorer write-back into the extraction files. Flagged at
  `quality.has_score_ready`.
- **Non-provenance values in the provenance slot.** 10 dimension rows carry `needs_external_source`
  (6), `profile_only` (3), or `needs_common_units` (1). Resolved via `coverage` where valid (1 of
  10), null otherwise; the original is always at `provenance_as_recorded`.
- **`wrong_object_check`.** A legacy self-audit flag present only in `run200_2026-06`, on **all
  13,552 of that batch's `concept_fields` rows** (value always `"ok"`), and never part of the
  output contract. (README §9 puts it at ~6,101 rows; the measured figure is 100% of the batch.) Carried verbatim. Never compare across
  batches on it.
- **Abandoned temp files.** Three `*.json.tmp.*` files sit in `per_document/` directories and are
  excluded by globbing `*.json` rather than listing the directory — the difference between 7,057
  listed entries and 7,054 real ones.
- **A duplicate pilot batch.** `run_sample10_2026-06` (10 documents) is a subset of a later batch
  and is excluded.

---

## 5. Practical guidance

1. **Build comparative measures from `dimension_coverage`.** It is the only layer with a
   guaranteed-stable schema and a complete 38-row grid.
2. **Never `fillna(0)` a presence table.** 9.2% of the grid is epistemically unknown and the rate
   varies fourfold by run (3.7%–15.5%).
3. **Always include `run` as a control.** Unknown share, `absent` share, citation coverage, concept
   vocabulary size and identity-field completeness all vary more by batch than plausible contract
   heterogeneity would explain.
4. **Threshold `concept_id` at ≥50 records** before treating it as a real measurement object.
5. **Filter `concept_fields` on `concept_id` and `field_unit`, never on `field_name`.**
6. **Check `codebook.key_presence_by_run` before using any key outside the stable cores** — a key
   absent from a batch means that batch didn't record it, not that the contracts lacked it.
7. **Test sensitivity by excluding `run_dol_textlayer_2026-07`.** It is half the corpus, has
   non-random extraction attrition, and leads every drift metric in this report.
