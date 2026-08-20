import { bandOf, type Band, type ChunkRef, type Concept } from "./types";
import { exists, readText } from "./storage";

// Repo-relative paths, identical in local and S3 mode (see lib/storage.ts).
const PIPELINE_DIR = "results/concept_similarity";
const CHUNKS_PATH = `${PIPELINE_DIR}/chunks.jsonl`;
const LOOKUP_PATH = `${PIPELINE_DIR}/lookup.json`;
const CONCEPTS_PATH = `${PIPELINE_DIR}/concepts.json`;

const BUILD_HINT =
  "Build it with `uv run python pipeline/runner.py`, then upload with " +
  "`npm run upload-corpus` if the app is reading from S3.";

/** One row of chunks.jsonl. */
export interface ChunkRow {
  chunk_id: string;
  document_key: string;
  source: string;
  engine: string;
  document_id: string;
  source_file: string;
  char_start: number;
  char_end: number;
  page_start: number | null;
  page_end: number | null;
  token_count: number;
  offsets_verified: boolean;
  text: string;
}

async function readArtifact(relPath: string, what: string): Promise<string> {
  try {
    return await readText(relPath);
  } catch (err) {
    throw new Error(
      `Could not read ${what} at ${relPath}. ${BUILD_HINT} ` +
        `(${err instanceof Error ? err.message : String(err)})`
    );
  }
}

// The artifacts are ~10 MB in total and immutable for a given pipeline run, so each
// is fetched once per process and held. The promise itself is cached, not the value,
// so concurrent first requests share one fetch instead of racing.

// ── Chunks ────────────────────────────────────────────────────────────────────

interface ChunkIndex {
  rows: ChunkRow[];
  byKey: Map<string, ChunkRow>;
  order: Map<string, string[]>; // document_key -> chunk ids, in document order
}

let chunkPromise: Promise<ChunkIndex> | null = null;

function loadChunks(): Promise<ChunkIndex> {
  if (!chunkPromise) {
    chunkPromise = (async () => {
      const raw = await readArtifact(CHUNKS_PATH, "chunks.jsonl");
      const rows: ChunkRow[] = [];
      for (const line of raw.split("\n")) {
        if (!line.trim()) continue;
        try {
          rows.push(JSON.parse(line) as ChunkRow);
        } catch {
          // Skip a malformed line rather than failing the whole corpus load.
        }
      }
      const byKey = new Map(rows.map((r) => [`${r.document_key}/${r.chunk_id}`, r]));
      const order = new Map<string, string[]>();
      for (const r of rows) {
        const list = order.get(r.document_key) ?? [];
        list.push(r.chunk_id);
        order.set(r.document_key, list);
      }
      return { rows, byKey, order };
    })().catch((err) => {
      chunkPromise = null; // let a later request retry a transient S3 failure
      throw err;
    });
  }
  return chunkPromise;
}

export async function getChunks(): Promise<ChunkRow[]> {
  return (await loadChunks()).rows;
}

export function documentKey(c: ChunkRef): string {
  return `${c.source}/${c.engine}/${c.documentId}`;
}

export async function findChunk(c: ChunkRef): Promise<ChunkRow | null> {
  const idx = await loadChunks();
  return idx.byKey.get(`${documentKey(c)}/${c.chunkId}`) ?? null;
}

/** 1-based position of a chunk in its document, and the document's chunk count. */
export async function chunkPosition(c: ChunkRef): Promise<{ index: number; count: number }> {
  const idx = await loadChunks();
  const ids = idx.order.get(documentKey(c)) ?? [];
  return { index: ids.indexOf(c.chunkId) + 1, count: ids.length };
}

// ── Concepts ──────────────────────────────────────────────────────────────────

let conceptPromise: Promise<Concept[]> | null = null;

export function getConcepts(): Promise<Concept[]> {
  if (!conceptPromise) {
    conceptPromise = (async () => {
      const raw = JSON.parse(await readArtifact(CONCEPTS_PATH, "concepts.json")) as Record<
        string,
        { concept_id: string; label: string; area: string; status?: string; description?: string }
      >;
      const concepts = Object.values(raw).map((c) => ({
        conceptId: c.concept_id,
        label: c.label,
        area: c.area,
        status: c.status ?? "",
        description: c.description ?? "",
      }));
      if (concepts.length === 0) throw new Error(`no concepts in ${CONCEPTS_PATH}. ${BUILD_HINT}`);
      return concepts;
    })().catch((err) => {
      conceptPromise = null;
      throw err;
    });
  }
  return conceptPromise;
}

export async function findConcept(conceptId: string): Promise<Concept | null> {
  return (await getConcepts()).find((c) => c.conceptId === conceptId) ?? null;
}

// ── Percentile bands ──────────────────────────────────────────────────────────

/** One servable unit: a (chunk, concept) pair and the stratum it belongs to. */
export interface PoolUnit {
  documentKey: string;
  chunkId: string;
  conceptId: string;
  band: Band;
}

let poolPromise: Promise<PoolUnit[]> | null = null;

/**
 * Every (chunk, concept) pair, labelled with its percentile band.
 *
 * Ranking is per (document, concept): a document's own chunks are sorted by that
 * concept's score, and each chunk's top-percentile is 100 * (1 - rank/n). So the
 * best-scoring chunk sits at 100 and the worst at 100/n, which puts roughly 1% of
 * each document's chunks in the 99-100 band regardless of document length.
 *
 * Ties break on numeric chunk id so the assignment is deterministic across
 * restarts -- otherwise a unit could drift between bands and be served twice.
 */
export function getPool(): Promise<PoolUnit[]> {
  if (!poolPromise) {
    poolPromise = (async () => {
      const lookup = JSON.parse(await readArtifact(LOOKUP_PATH, "lookup.json")) as {
        documents: Record<string, Record<string, Record<string, number>>>;
      };

      const pool: PoolUnit[] = [];
      for (const [docKey, chunks] of Object.entries(lookup.documents)) {
        const chunkIds = Object.keys(chunks);
        const n = chunkIds.length;
        if (n === 0) continue;

        const conceptIds = Object.keys(chunks[chunkIds[0]] ?? {});
        for (const conceptId of conceptIds) {
          const ranked = chunkIds.slice().sort((a, b) => {
            const diff = (chunks[b][conceptId] ?? 0) - (chunks[a][conceptId] ?? 0);
            return diff !== 0 ? diff : Number(a) - Number(b);
          });
          for (let rank = 0; rank < ranked.length; rank++) {
            pool.push({
              documentKey: docKey,
              chunkId: ranked[rank],
              conceptId,
              band: bandOf(100 * (1 - rank / n)),
            });
          }
        }
      }
      return pool;
    })().catch((err) => {
      poolPromise = null;
      throw err;
    });
  }
  return poolPromise;
}

/** Pool size per band, for the band selector. */
export async function bandCounts(): Promise<Record<string, number>> {
  const counts: Record<string, number> = {};
  for (const unit of await getPool()) counts[unit.band] = (counts[unit.band] ?? 0) + 1;
  return counts;
}

// ── full.txt access ───────────────────────────────────────────────────────────

/**
 * Repo-relative path to a document's full.txt. Also the stored `source_file` on
 * every record, and the S3 key suffix -- one string that means the same thing in
 * the record, on disk and in the bucket.
 */
export function fullTextPath(c: ChunkRef): string {
  for (const part of [c.source, c.engine, c.documentId]) {
    if (!part || part.includes("/") || part.includes("..")) throw new Error("Invalid path");
  }
  return `stg_01_ocr/${c.source}/${c.engine}/${c.documentId}/full.txt`;
}

// Only 20 documents, ~4.6 MB in total, and each is re-read on every submit for the
// same document. Cache them whole; the cap is a backstop, not a tuning knob.
const FULL_TEXT_CACHE_MAX = 25;
const fullTextCache = new Map<string, Promise<string>>();

export function readFullText(c: ChunkRef): Promise<string> {
  const rel = fullTextPath(c);
  const hit = fullTextCache.get(rel);
  if (hit) return hit;

  const p = readText(rel).catch((err) => {
    fullTextCache.delete(rel);
    throw err;
  });
  fullTextCache.set(rel, p);
  if (fullTextCache.size > FULL_TEXT_CACHE_MAX) {
    const oldest = fullTextCache.keys().next().value;
    if (oldest !== undefined) fullTextCache.delete(oldest);
  }
  return p;
}

export function fullTextExists(c: ChunkRef): Promise<boolean> {
  try {
    return exists(fullTextPath(c));
  } catch {
    return Promise.resolve(false);
  }
}

const PAGE_SEP_RE = /^--- Page (\d+) ---[ \t]*$/gm;

/**
 * The printed page containing `offset`, from the `--- Page N ---` separators --
 * the same derivation the pipeline uses, so a span's page agrees with its chunk's
 * page range. Returns null for a document with no separators.
 */
export function pageAtOffset(fullText: string, offset: number): number | null {
  PAGE_SEP_RE.lastIndex = 0;
  let page: number | null = null;
  let match: RegExpExecArray | null;
  while ((match = PAGE_SEP_RE.exec(fullText)) !== null) {
    if (match.index > offset) break;
    page = Number(match[1]);
  }
  return page;
}
