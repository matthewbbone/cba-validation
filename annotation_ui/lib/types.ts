// ── Provision metadata ────────────────────────────────────────────────────────

export interface Provision {
  conceptId: string;
  category: string;
  label: string;
}

export type ProvisionFormat = "binary" | "quantitative" | "complex";

export type PriorityTier = "core" | "conditional_core" | "advanced" | "standard";

export interface ProvisionMeta {
  priority_tier?: PriorityTier;
  rank?: number | null;
  priority_score?: number | null;
  difficulty?: "low" | "medium" | "high" | null;
  core_family?: string | null;
  notes?: string[];
}

export interface ProvisionSchema {
  format: ProvisionFormat;
  title?: string; // short, human-friendly heading shown in bold to raters
  description?: string; // plain-language explanation shown as card subtext
  flags: string[]; // boolean flag field names (complex only)
  string_fields?: string[]; // typed string-list attribute names (all formats)
  meta?: ProvisionMeta; // tier/rank metadata
}

// ── CBA ───────────────────────────────────────────────────────────────────────

export interface CBA {
  source: string;
  filename: string;
}

export interface SessionData {
  cba: CBA;
  provisions: Provision[];
  exhausted?: boolean;
}

// ── Prolific identifiers ──────────────────────────────────────────────────────

export interface ProlificContext {
  prolific_pid: string;
  study_id: string;
  prolific_session_id: string;
}

// ── Annotation value types (mirror Python QuantitativeValue) ──────────────────

export interface AnnotationDuration {
  hours: number | null;
  days: number | null;
  weeks: number | null;
  months: number | null;
  years: number | null;
}

export interface AnnotationValue {
  money: { amount: number } | null;
  percent: { value: number } | null; // stored as decimal, e.g. 0.05 for 5%
  duration: AnnotationDuration | null;
  number: number | null;
  multiplier: number | null;
  included: boolean | null;
  employer_paid: boolean | null;
  employee_paid: boolean | null;
}

// ── Per-provision annotation ──────────────────────────────────────────────────

export interface ProvisionAnnotation {
  concept_id: string;
  category: string;
  format: ProvisionFormat;
  exists: boolean | null; // null = no decision made yet
  summarize: string;
  // binary: none of the below
  // quantitative: single value or null
  value?: AnnotationValue | null;
  // complex: list of values + flag map
  values?: AnnotationValue[];
  flags?: Record<string, boolean | null>;
  // typed string-list attributes (named source terms), keyed by attribute name
  string_fields?: Record<string, string[]>;
}

// ── Submit payload ────────────────────────────────────────────────────────────

export interface SubmitPayload {
  sessionId: string;
  cba: CBA;
  provisions: ProvisionAnnotation[];
  prolific: ProlificContext;
}

// ── Storage (JSONL row / S3 object) ───────────────────────────────────────────

export interface AnnotationRecord {
  session_id: string;
  timestamp: string;
  cba_source: string;
  cba_filename: string;
  prolific_pid: string;
  study_id: string;
  prolific_session_id: string;
  provisions: ProvisionAnnotation[];
}

// ── Draft (localStorage) ──────────────────────────────────────────────────────

export interface DraftState {
  sessionId: string;
  cba: CBA;
  provisions: Provision[];
  annotations: ProvisionAnnotation[];
  savedAt: string;
}

// ── Extraction review ─────────────────────────────────────────────────────────
// A reviewer reads the source PDF beside everything the extractor recorded for
// one concept in one document, and judges it. Distinct from the rater-facing
// annotation flow above: this audits the machine output rather than coding the
// contract from scratch.

/**
 * Independent problem flags, not a scale. A reviewer sets any combination —
 * an extraction can be both hallucinating and confusing — and an empty set is a
 * meaningful, common answer: no problems found.
 */
export type ReviewIssue = "missing" | "hallucinating" | "confusing";

export const REVIEW_ISSUES: ReviewIssue[] = ["missing", "hallucinating", "confusing"];

/**
 * Overall assessment flags. Recorded as a set rather than a single value so the
 * buttons behave as toggles like the issue row. Note these are not logically
 * independent — good and bad together is contradictory — but nothing enforces
 * that, so treat a multi-flag row as reviewer ambivalence, not as a scale point.
 */
export type ReviewQuality = "good" | "okay" | "bad";

export const REVIEW_QUALITIES: ReviewQuality[] = ["good", "okay", "bad"];

/**
 * One reviewable slice of the corpus: a single (extraction document, concept_id)
 * pair. `run` is carried because a PDF can be extracted by more than one batch,
 * and those extractions must never be merged.
 */
export interface ReviewUnit {
  source: string; // data/cbas/<source>/ directory
  filename: string; // the PDF
  run: string; // extraction batch
  documentId: string;
  conceptId: string;
  category: string;
  label: string;
  nRecords: number;
  nFields: number;
  offDictionary: boolean; // concept_id absent from the provision dictionary
}

// Extraction rows, kept loose on purpose: the source arrays carry ~500 distinct
// keys across batches and unrecognised ones are passed through by the builder.
export interface ExtractionRecordRow {
  concept_id: string;
  concept_label?: string | null;
  measurement_status?: string | null;
  status_reason?: string | null;
  status_flags?: string[] | null;
  evidence_pointer?: string | null;
  [key: string]: unknown;
}

export interface ExtractionFieldRow {
  concept_id: string;
  field_name?: string | null;
  field_value?: unknown;
  field_unit?: string | null;
  value_type?: string | null;
  support_status?: string | null;
  note?: string | null;
  evidence_pointer?: string | null;
  [key: string]: unknown;
}

export interface DimensionRow {
  dimension_id: string | null;
  area: string | null;
  provenance: string | null;
  note?: string | null;
  evidence_pointer?: string | null;
  [key: string]: unknown;
}

export interface ExtractionDetail {
  run: string;
  documentId: string;
  document: Record<string, unknown>;
  metadata: Record<string, unknown>;
  quality: Record<string, unknown>;
  concept_records: ExtractionRecordRow[];
  concept_fields: ExtractionFieldRow[];
  dimension_coverage: DimensionRow[];
}

/** Persisted judgement — one row per (reviewer, run, document, concept). */
export interface ExtractionReviewRecord {
  session_id: string;
  timestamp: string;
  reviewer: string;
  cba_source: string;
  cba_filename: string;
  run: string;
  document_id: string;
  concept_id: string;
  /** Overall assessment flags. Empty means the reviewer did not rate it. */
  quality: ReviewQuality[];
  /** Specific problem flags. Empty means reviewed with no problems found. */
  issues: ReviewIssue[];
  comment: string;
  // What the reviewer was actually shown, so a judgement stays interpretable
  // even after the aggregate is rebuilt.
  n_records: number;
  n_fields: number;
}

export interface ReviewSubmitPayload {
  sessionId: string;
  reviewer: string;
  unit: ReviewUnit;
  quality: ReviewQuality[];
  issues: ReviewIssue[];
  comment: string;
}

export interface ReviewDraft {
  unitKey: string;
  quality: ReviewQuality[];
  issues: ReviewIssue[];
  comment: string;
  savedAt: string;
}
