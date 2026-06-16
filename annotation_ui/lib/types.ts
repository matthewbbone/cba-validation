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
