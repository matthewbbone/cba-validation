import type { Band, SpanAnnotationRecord } from "./types";
import { isBand, unitKey } from "./types";
import { appendLine, isS3Configured, listPaths, readText, writeJson } from "./storage";

// Repo-relative, so the same strings work on disk and as S3 keys.
const JSONL_PATH = "annotations/chunk_span_annotations.jsonl";
const S3_ROOT = "chunk_annotations";

export function outputLocation(): string {
  return isS3Configured() ? `${S3_ROOT}/` : JSONL_PATH;
}

/**
 * Annotator names are free text typed by a person. Compare them loosely -- "MB",
 * "mb" and " mb " are the same annotator -- and slugify before putting one in a
 * key path.
 */
export function normaliseAnnotator(annotator: string): string {
  return annotator.trim().toLowerCase().replace(/\s+/g, " ");
}

export function annotatorSlug(annotator: string): string {
  return normaliseAnnotator(annotator)
    .replace(/[^a-z0-9._-]+/g, "-")
    .replace(/^-+|-+$/g, "");
}

/**
 * Where one judgement lives in S3 mode.
 *
 * The band is part of the path so a ListObjectsV2 on the annotator's prefix yields
 * both the unit identity and its stratum without fetching a single object -- which
 * is what makes the per-band tally cheap. A unit belongs to exactly one band for a
 * given pipeline run, so this never splits one unit across two keys.
 *
 * One object per unit, so a re-annotation overwrites rather than appending a
 * duplicate, and two annotators submitting at once cannot clobber each other.
 */
export function recordKey(record: SpanAnnotationRecord): string {
  return (
    `${S3_ROOT}/${annotatorSlug(record.annotator)}/${record.band}/` +
    `${record.source}/${record.engine}/${record.document_id}/` +
    `${record.chunk_id}/${record.concept_id}.json`
  );
}

export async function appendSpanRecord(record: SpanAnnotationRecord): Promise<void> {
  // Let write failures propagate -- the caller must surface them so a submission
  // is never silently lost.
  if (isS3Configured()) {
    await writeJson(recordKey(record), record);
    return;
  }
  await appendLine(JSONL_PATH, JSON.stringify(record));
}

interface DoneUnit {
  key: string;
  band: Band | null;
}

/**
 * Distinct units this annotator has submitted, with the band each was drawn from.
 *
 * S3: parsed straight out of the keys, no object reads. Local: read back from the
 * append-only JSONL, where a re-annotated unit appears more than once, so the last
 * row wins.
 */
async function getDoneUnits(annotator: string): Promise<DoneUnit[]> {
  if (isS3Configured()) {
    const prefix = `${S3_ROOT}/${annotatorSlug(annotator)}/`;
    const paths = await listPaths(prefix);
    const out: DoneUnit[] = [];
    for (const p of paths) {
      if (!p.endsWith(".json")) continue;
      // band/source/engine/documentId/chunkId/conceptId.json
      const parts = p.slice(prefix.length, -".json".length).split("/");
      if (parts.length !== 6) continue;
      const [band, source, engine, documentId, chunkId, conceptId] = parts;
      out.push({
        key: unitKey({ source, engine, documentId, chunkId }, conceptId),
        band: isBand(band) ? band : null,
      });
    }
    return out;
  }

  let raw: string;
  try {
    raw = await readText(JSONL_PATH);
  } catch {
    return []; // nothing submitted yet
  }

  const who = normaliseAnnotator(annotator);
  const latest = new Map<string, Band | null>();
  for (const line of raw.split("\n")) {
    if (!line.trim()) continue;
    let r: SpanAnnotationRecord;
    try {
      r = JSON.parse(line) as SpanAnnotationRecord;
    } catch {
      continue; // skip malformed lines rather than failing the whole lookup
    }
    if (normaliseAnnotator(r.annotator) !== who) continue;
    latest.set(
      unitKey(
        { source: r.source, engine: r.engine, documentId: r.document_id, chunkId: r.chunk_id },
        r.concept_id
      ),
      isBand(r.band) ? r.band : null
    );
  }

  const out: DoneUnit[] = [];
  latest.forEach((band, key) => out.push({ key, band }));
  return out;
}

/** Unit keys this annotator has already submitted, de-duplicated. */
export async function getCompletedUnits(annotator: string): Promise<string[]> {
  const seen = new Set<string>();
  for (const u of await getDoneUnits(annotator)) seen.add(u.key);
  return Array.from(seen);
}

/** How many distinct units this annotator has done in each band. */
export async function getBandTally(annotator: string): Promise<Record<string, number>> {
  const byKey = new Map<string, Band | null>();
  for (const u of await getDoneUnits(annotator)) byKey.set(u.key, u.band);

  const tally: Record<string, number> = {};
  byKey.forEach((band) => {
    if (band) tally[band] = (tally[band] ?? 0) + 1;
  });
  return tally;
}
