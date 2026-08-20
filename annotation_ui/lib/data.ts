import fs from "fs";
import path from "path";
import type { SpanAnnotationRecord } from "./types";
import { unitKey } from "./types";

// Append-only JSONL at the repo root. Deliberately not gitignored: these
// judgements are the deliverable, unlike the OCR text and pipeline artifacts
// they point at.
const REPO_ROOT = path.resolve(process.cwd(), "..");
const SPANS_PATH = path.join(REPO_ROOT, "annotations", "chunk_span_annotations.jsonl");

export function spansFilePath(): string {
  return SPANS_PATH;
}

/**
 * Annotator names are free text typed by a person, so compare them loosely --
 * "MB", "mb" and " mb " are the same annotator for progress purposes.
 */
export function normaliseAnnotator(annotator: string): string {
  return annotator.trim().toLowerCase().replace(/\s+/g, " ");
}

export function appendSpanRecord(record: SpanAnnotationRecord): void {
  // Let write failures propagate -- the caller must surface them so a submission
  // is never silently lost.
  const dir = path.dirname(SPANS_PATH);
  if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });
  fs.appendFileSync(SPANS_PATH, JSON.stringify(record) + "\n", "utf-8");
}

function readRecords(): SpanAnnotationRecord[] {
  if (!fs.existsSync(SPANS_PATH)) return [];
  const out: SpanAnnotationRecord[] = [];
  for (const line of fs.readFileSync(SPANS_PATH, "utf-8").split("\n")) {
    if (!line.trim()) continue;
    try {
      out.push(JSON.parse(line) as SpanAnnotationRecord);
    } catch {
      // Skip malformed lines rather than failing the whole progress lookup.
    }
  }
  return out;
}

/**
 * Unit keys this annotator has already submitted. The file is append-only, so a
 * re-annotated unit appears more than once; de-duplicate.
 */
export function getCompletedUnits(annotator: string): string[] {
  const who = normaliseAnnotator(annotator);
  const keys = new Set<string>();

  for (const r of readRecords()) {
    if (normaliseAnnotator(r.annotator) !== who) continue;
    keys.add(
      unitKey(
        {
          source: r.source,
          engine: r.engine,
          documentId: r.document_id,
          chunkId: r.chunk_id,
        },
        r.concept_id
      )
    );
  }

  return Array.from(keys);
}

/**
 * How many distinct units this annotator has done in each band, so the selector
 * can show progress per stratum. Counts unique units, not rows.
 */
export function getBandTally(annotator: string): Record<string, number> {
  const who = normaliseAnnotator(annotator);
  const seen = new Map<string, string>(); // unit key -> band of its latest row

  for (const r of readRecords()) {
    if (normaliseAnnotator(r.annotator) !== who) continue;
    const key = unitKey(
      { source: r.source, engine: r.engine, documentId: r.document_id, chunkId: r.chunk_id },
      r.concept_id
    );
    seen.set(key, r.band);
  }

  const tally: Record<string, number> = {};
  seen.forEach((band) => {
    tally[band] = (tally[band] ?? 0) + 1;
  });
  return tally;
}
