// Types for the chunk span-annotation task.
//
// An annotator reads one *chunk* of one contract beside one provision concept,
// judges whether the passage addresses that concept, and highlights the text
// that is evidence for it. Chunks come from pipeline/runner.py, which splits
// each full.txt with chonkie and scores every (chunk, concept) pair by cosine
// similarity; the UI serves pairs stratified by that score.
//
// Every highlight is stored as a (document, character span) tuple with offsets
// into full.txt, so a downstream consumer can re-slice the exact source text.

// ── Provision concepts ────────────────────────────────────────────────────────

/** One entry of results/concept_similarity/concepts.json, built by the pipeline. */
export interface Concept {
  conceptId: string; // C_LEAVE_HOLIDAYS
  label: string; // "Holidays and holiday pay"
  area: string; // "Leave" — tier_1_concepts.md "Parent area"
  status: string; // "draft calibrated" — its scoring-module status
  description: string; // the plain-language gloss shown to the annotator
}

// ── Percentile bands ──────────────────────────────────────────────────────────

/**
 * Chunks are ranked by similarity *within their own document, for one concept*,
 * and bucketed by percentile from the top. The annotator picks a band, and a
 * unit is drawn uniformly at random from it — stratified sampling, so the same
 * effort yields precision estimates at every level of model confidence rather
 * than only at the top.
 *
 * Per-document ranking is what makes a band comparable across contracts of very
 * different lengths. It has one artifact worth knowing: in a document with only
 * a handful of chunks the top band is close to meaningless (a 1-chunk document
 * ranks that chunk first for all 34 concepts), so `chunkCount` is surfaced in
 * the UI.
 */
export type Band = "0-50" | "50-75" | "75-95" | "95-99" | "99-100";

export const BANDS: { id: Band; lo: number; hi: number; label: string }[] = [
  { id: "0-50", lo: 0, hi: 50, label: "Bottom half" },
  { id: "50-75", lo: 50, hi: 75, label: "50-75th" },
  { id: "75-95", lo: 75, hi: 95, label: "75-95th" },
  { id: "95-99", lo: 95, hi: 99, label: "95-99th" },
  { id: "99-100", lo: 99, hi: 100, label: "Top 1%" },
];

export const DEFAULT_BAND: Band = "99-100";

export function isBand(value: unknown): value is Band {
  return typeof value === "string" && BANDS.some((b) => b.id === value);
}

/** The band a top-percentile value falls in. Bands are (lo, hi], with 0 closed. */
export function bandOf(percentile: number): Band {
  for (const b of BANDS) {
    if (percentile <= b.hi && (percentile > b.lo || b.lo === 0)) return b.id;
  }
  return BANDS[0].id;
}

// ── Chunks ────────────────────────────────────────────────────────────────────

/**
 * Locates one chunk. `engine` is part of the identity, not an implementation
 * detail — the same contract re-OCR'd by a different engine yields different
 * text and therefore different offsets. `chunkId` is the pipeline's own id,
 * stable for a given chunk_size/recipe/tokenizer.
 */
export interface ChunkRef {
  source: string; // "dol_archive"
  engine: string; // "ATH-MaaS_OvisOCR2"
  documentId: string; // "document_1778"
  chunkId: string; // "25"
}

/** One unit of work: a single chunk shown beside a single concept. */
export interface AnnotationUnit {
  chunk: ChunkRef;
  concept: Concept;
  text: string; // verbatim slice of full.txt: full[charStart:charEnd]
  charStart: number; // offset into full.txt
  charEnd: number;
  pageStart: number | null; // printed page range the chunk covers
  pageEnd: number | null;
  chunkIndex: number; // 1-based position of this chunk in its document
  chunkCount: number; // chunks in the document, so a tiny document is obvious
  band: Band; // which stratum this unit was drawn from
  exhausted?: boolean;
}

// ── Spans ─────────────────────────────────────────────────────────────────────

/**
 * A highlighted passage.
 *
 * `start`/`end` are character offsets into the document's **full.txt** decoded
 * as UTF-8: a half-open range, JS UTF-16 code units. These equal Python `str`
 * indices for anything outside the astral planes, and the OCR corpus is
 * effectively ASCII — but `text` is stored redundantly so a consumer can verify
 * or re-locate the passage without trusting the offsets.
 *
 * Invariant, enforced client-side on capture and server-side on submit:
 *   fullText.slice(start, end) === text
 *
 * `page` is the printed page containing `start`, derived from the `--- Page N ---`
 * separators in full.txt.
 */
export interface Span {
  start: number;
  end: number;
  text: string;
  note: string; // annotator's optional note; "" when left blank
  page: number | null;
}

/** Does the passage address the concept at all? Recorded before any highlighting. */
export type Relevance = "yes" | "partly" | "no";

export const RELEVANCE_OPTIONS: { id: Relevance; label: string; hint: string }[] = [
  { id: "yes", label: "Yes", hint: "The passage addresses this concept" },
  { id: "partly", label: "Partly", hint: "Touches on it, or is incomplete/ambiguous" },
  { id: "no", label: "No", hint: "Nothing to do with this concept" },
];

export function isRelevance(value: unknown): value is Relevance {
  return value === "yes" || value === "partly" || value === "no";
}

// ── Wire + storage shapes ─────────────────────────────────────────────────────

export interface SpanSubmitPayload {
  sessionId: string;
  annotator: string;
  chunk: ChunkRef;
  conceptId: string;
  band: Band;
  relevance: Relevance;
  spans: Span[];
}

/** One JSONL row in annotations/chunk_span_annotations.jsonl. */
export interface SpanAnnotationRecord {
  session_id: string;
  timestamp: string;
  annotator: string;
  source: string;
  engine: string;
  document_id: string;
  chunk_id: string;
  /** Repo-relative path to full.txt, so a record is traceable on its own. */
  source_file: string;
  chunk_char_start: number;
  chunk_char_end: number;
  page_start: number | null;
  page_end: number | null;
  concept_id: string;
  concept_label: string;
  /** The stratum the unit was drawn from — needed to weight any precision estimate. */
  band: Band;
  relevance: Relevance;
  spans: Span[];
}

/**
 * Draft held in localStorage so a half-finished unit survives a reload. The whole
 * unit is stored, chunk text included, so a restore needs no round trip; if the
 * corpus has been re-chunked meanwhile the offsets go stale, and the server-side
 * slice check rejects the submission with a clear message.
 */
export interface SpanDraft {
  sessionId: string;
  unit: AnnotationUnit;
  relevance: Relevance | null;
  spans: Span[];
  savedAt: string;
}

// ── Unit identity ─────────────────────────────────────────────────────────────

/**
 * Identifies one unit of work. No part contains a slash, so this round-trips
 * through a path-like string unambiguously. Used for the served/completed
 * exclusion set and for JSONL readback.
 *
 * Note the band is deliberately absent: a (chunk, concept) pair is the same unit
 * of work whichever stratum it was drawn from, so re-serving it under a different
 * band would be a duplicate.
 */
export function unitKey(c: ChunkRef, conceptId: string): string {
  return `${c.source}/${c.engine}/${c.documentId}/${c.chunkId}/${conceptId}`;
}
