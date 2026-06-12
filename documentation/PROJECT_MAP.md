# CBA generosity project — where everything is

Orientation map for coauthors (and their agents). **All paths are relative to the
`1_CBAs/` directory** (the shared working root). The active project lives under
`codex_PG/`; the website and source archives are siblings of it.

Current state: one unified **996-agreement** dataset on a single extraction-and-scoring
pipeline, with a refreshed paper (v2) and the coauthor data deliverables. The headline
intermediary data and code are all under one run folder (see §3).

---

## 1. The paper

| Path | What it is |
|---|---|
| `codex_PG/scalable_v4/notes/paper_draft_v2_996.tex` | **The manuscript** (current, 996-doc). Compiles clean. |
| `codex_PG/scalable_v4/notes/paper_draft_v2_996.pdf` | Compiled PDF. |
| `codex_PG/scalable_v4/notes/paper_archive/` | Archived v1 (100-doc pilot draft). |
| `codex_PG/scalable_v4/notes/PILOT_VS_FULL_COMPARISON.md` | What changed moving pilot → 996 (method vs sample decomposition). |

**Figures and tables are generated, not hand-made.** To rebuild them:

| Path | What it is |
|---|---|
| `codex_PG/scalable_v4/scripts/make_paper_v2_artifacts.py` | Generates all 4 figures + 3 tables from the final-scores CSVs. |
| `codex_PG/scalable_v4/runs/2026-05-30_v5_wave2_reextract/figures/` | Output: `fig1`–`fig4` (PDF + PNG). The `.tex` pulls from here via `\graphicspath`. |
| `codex_PG/scalable_v4/runs/2026-05-30_v5_wave2_reextract/tables/` | Output: `table1`–`table3` (`\input` into the `.tex`). |

Run `python scripts/make_paper_v2_artifacts.py` from `codex_PG/scalable_v4/`, then
`pdflatex paper_draft_v2_996.tex` (twice) from `notes/`.

---

## 2. The data deliverables (what was asked for)

In `codex_PG/deliverables/` — coauthor-facing CSVs, each with a README. This folder is
**only** the requested outputs, kept clean; the raw pipeline data is in §3.

| File | What it is |
|---|---|
| `cba_generosity_scores_996doc_reextract.csv` (+ `_wide`, `_subcriteria`) | Per (agreement × area) 0–1 scores. |
| `cba_generosity_summaries_996doc_reextract.csv` | The LLM judge summaries per CBA × category. |
| `cba_extracted_wages_996_occupation.csv` (+ `_doclevel`) | Directly-extracted wage ladders (occupation × step), USD/hr, with state/NAICS/year. |
| `cba_provision_presence_996.csv` | Contract × 99 provision-presence flags + metadata (prevalence-over-time). |
| `cba_provision_records_996.csv` | Long: one row per extracted provision, with evidence pointers. |
| `cba_provision_dictionary.csv` | The 99 provision types and how common each is. |
| `README_996doc_reextract.md`, `README_extracted_wages.md`, `README_provision_summary.md` | Per-deliverable guides (filters, join keys, caveats). |
| `COAUTHOR_UPDATE_2026-06-07.md` | Memo summarizing the package. |
| `_superseded/` | Older 898/900/100-doc files, archived. |

---

## 3. The pipeline and all intermediary data

Everything from extraction → scoring → calibration → validation lives in **one run folder**:

`codex_PG/scalable_v4/runs/2026-05-30_v5_wave2_reextract/`

### Core intermediary tables

| File | What it is |
|---|---|
| `v5_1_final_scores_calibrated.csv` | **Canonical output**: 7,828 scored cells / 996 docs, post-calibration. (The deliverable CSVs derive from this.) |
| `v5_1_final_scores.csv`, `v5_1_by_sector.csv`, `v5_1_by_state.csv`, `v5_1_document_index.csv` | Pre-calibration scores and rollups. |
| `concept_records.csv` / `concept_records_normalized.csv` | Extracted provisions (Step 1 output). |
| `concept_fields.csv` | Typed numeric/categorical fields per provision. |
| `category_briefs_rich.json` | The deterministic "provision summaries" fed to the LLM scorer (Step 3 input). |
| `documents_enriched.csv` | Doc metadata: state, NAICS, harmonized_sector, contract_year, length_stratum. |
| `absolute_scores.csv`, `score_inputs.csv` | Scoring intermediates. |
| `anchor_calibration/` + `anchor_calibration_summary.csv` | Step 4 intercept calibration (per-area shifts). |

### Validation / stylized-fact data

| File | Feeds which validation |
|---|---|
| `oews/` + `oews_wage_validation.csv` | BLS OEWS survey-wage check (median ratio 1.03). |
| `cola_by_document.csv`, `cola_by_year.csv` | COLA-decline stylized fact (6.7% by 2020–23). |
| `extraction_richness_comparison.csv` | The ~38% quantitative-field increase vs old extraction. |
| `manifest_ocr_audit.csv`, `misaligned_doc_corrections.csv` | OCR/manifest audit + the 4 relabeled docs. |
| `davidson_rerun/` | Pairwise Davidson check (ρ=0.84). Key files: `judged_pairs_all.csv`, `davidson_strengths_all.csv`, `davidson_vs_absolute_by_category.csv`; refit with `fit_final.py` / `consolidate_and_fit.py`. |
| `reliability_run/` | Cross-model + test-retest reliability (Opus ρ=0.90, ICC 0.89). `reliability_results.json`, `compute_reliability.py`. |
| `codex_PG/scalable_v4/runs/2026-05-17_v4_native_wave1/hand_ratings/` | Careful page-by-page re-read (ρ=0.81). `hand_ratings.csv` + `hand_ratings_extended.csv` (9 areas). |

### Builder scripts (how each output was made)

In the same run folder: `_build_scores_deliverable.py`, `_build_extracted_wages_deliverable.py`,
`_build_provision_summary_deliverable.py`, `_build_documents_enriched.py`,
`_build_harmonized_sector.py`, `_cola_stylized_fact.py`, `_manifest_ocr_audit.py`,
`_backfill_concept_record_ids.py`, `finish_step_d.py` (Step D driver).

### Findings write-ups (the reasoning behind each number)

`.md` files in the run folder: `WAGE_CROSSCHECK_FINDINGS.md`, `OEWS_VALIDATION_FINDINGS.md`,
`COLA_STYLIZED_FACT_FINDINGS.md`, `EXTRACTION_RICHNESS_FINDINGS.md`,
`MANIFEST_OCR_AUDIT_FINDINGS.md`, `RELIABILITY_FINDINGS.md`, `SECTOR_HARMONIZATION.md`,
`GAP_DIAGNOSIS_FINDINGS.md`, `MISALIGNED_DOC_SALVAGE.md`, `ANCHOR_CALIBRATION_REFRESH.md`,
`RUN_STATUS.md`.

---

## 4. The companion website

| Path | What it is |
|---|---|
| `cba-pilot-site/` | Vite/npm site (interactive explorer). |
| `cba-pilot-site/scripts/export_v5_1_data_996.py` | Regenerates the 996-doc data layer the site reads. |

Build with `npm run build` from `cba-pilot-site/`.

---

## Quick "I want to…" index

- **See the scores** → `deliverables/cba_generosity_scores_996doc_reextract.csv`
- **See the raw wages** → `deliverables/cba_extracted_wages_996_occupation.csv`
- **Track a specific provision (COLA, pension, …)** → `deliverables/cba_provision_presence_996.csv` (+ `README_provision_summary.md` for caveats)
- **Regenerate a paper figure** → `scalable_v4/scripts/make_paper_v2_artifacts.py`
- **Re-fit Davidson** → `…/2026-05-30_v5_wave2_reextract/davidson_rerun/fit_final.py`
- **Understand a validation number** → the matching `*_FINDINGS.md` in the run folder
