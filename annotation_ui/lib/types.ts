// ── Provision metadata ────────────────────────────────────────────────────────

export interface Provision {
  conceptId: string;
  category: string;
  label: string;
}

export type ProvisionFormat = "binary" | "quantitative" | "complex";

export interface ProvisionSchema {
  format: ProvisionFormat;
  flags: string[]; // flag field names for complex provisions
}

// ── CBA ───────────────────────────────────────────────────────────────────────

export interface CBA {
  source: string;
  filename: string;
}

export interface SessionData {
  cba: CBA;
  provisions: Provision[];
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
  exists: boolean;
  summarize: string;
  // binary: none of the below
  // quantitative: single value or null
  value?: AnnotationValue | null;
  // complex: list of values + flag map
  values?: AnnotationValue[];
  flags?: Record<string, boolean | null>;
}

// ── Submit payload ────────────────────────────────────────────────────────────

export interface SubmitPayload {
  sessionId: string;
  cba: CBA;
  provisions: ProvisionAnnotation[];
}

// ── Storage (JSONL row) ───────────────────────────────────────────────────────

export interface AnnotationRecord {
  session_id: string;
  timestamp: string;
  cba_source: string;
  cba_filename: string;
  provisions: ProvisionAnnotation[];
}
