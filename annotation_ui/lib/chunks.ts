import fs from "fs";
import path from "path";
import { bandOf, type Band, type ChunkRef, type Concept } from "./types";

// The pipeline's artifacts and the OCR corpus both live outside annotation_ui and
// are gitignored, so this tool only runs against a local checkout that has them.
const REPO_ROOT = path.resolve(process.cwd(), "..");
const PIPELINE_DIR = path.join(REPO_ROOT, "results", "concept_similarity");
const CHUNKS_PATH = path.join(PIPELINE_DIR, "chunks.jsonl");
const LOOKUP_PATH = path.join(PIPELINE_DIR, "lookup.json");
const CONCEPTS_PATH = path.join(PIPELINE_DIR, "concepts.json");

const BUILD_HINT =
  "Build it with: uv run python pipeline/runner.py";

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

function requireFile(p: string, what: string): void {
  if (!fs.existsSync(p)) {
    throw new Error(`${what} not found at ${p}. ${BUILD_HINT}`);
  }
}

// ── Chunks ────────────────────────────────────────────────────────────────────

let chunkCache: ChunkRow[] | null = null;
let chunkByKey: Map<string, ChunkRow> | null = null;
let chunkOrder: Map<string, string[]> | null = null; // document_key -> chunk ids, in order

function loadChunks(): ChunkRow[] {
  if (chunkCache) return chunkCache;
  requireFile(CHUNKS_PATH, "chunks.jsonl");

  const rows: ChunkRow[] = [];
  for (const line of fs.readFileSync(CHUNKS_PATH, "utf-8").split("\n")) {
    if (!line.trim()) continue;
    try {
      rows.push(JSON.parse(line) as ChunkRow);
    } catch {
      // Skip a malformed line rather than failing the whole corpus load.
    }
  }

  chunkByKey = new Map(rows.map((r) => [`${r.document_key}/${r.chunk_id}`, r]));
  chunkOrder = new Map();
  for (const r of rows) {
    const list = chunkOrder.get(r.document_key) ?? [];
    list.push(r.chunk_id);
    chunkOrder.set(r.document_key, list);
  }

  chunkCache = rows;
  return rows;
}

export function getChunks(): ChunkRow[] {
  return loadChunks();
}

export function documentKey(c: ChunkRef): string {
  return `${c.source}/${c.engine}/${c.documentId}`;
}

export function findChunk(c: ChunkRef): ChunkRow | null {
  loadChunks();
  return chunkByKey!.get(`${documentKey(c)}/${c.chunkId}`) ?? null;
}

/** 1-based position of a chunk in its document, and the document's chunk count. */
export function chunkPosition(c: ChunkRef): { index: number; count: number } {
  loadChunks();
  const ids = chunkOrder!.get(documentKey(c)) ?? [];
  return { index: ids.indexOf(c.chunkId) + 1, count: ids.length };
}

// ── Concepts ──────────────────────────────────────────────────────────────────

let conceptCache: Concept[] | null = null;

export function getConcepts(): Concept[] {
  if (conceptCache) return conceptCache;
  requireFile(CONCEPTS_PATH, "concepts.json");

  const raw = JSON.parse(fs.readFileSync(CONCEPTS_PATH, "utf-8")) as Record<
    string,
    { concept_id: string; label: string; area: string; status?: string; description?: string }
  >;
  conceptCache = Object.values(raw).map((c) => ({
    conceptId: c.concept_id,
    label: c.label,
    area: c.area,
    status: c.status ?? "",
    description: c.description ?? "",
  }));
  if (conceptCache.length === 0) throw new Error(`no concepts in ${CONCEPTS_PATH}. ${BUILD_HINT}`);
  return conceptCache;
}

export function findConcept(conceptId: string): Concept | null {
  return getConcepts().find((c) => c.conceptId === conceptId) ?? null;
}

// ── Percentile bands ──────────────────────────────────────────────────────────

/** One servable unit: a (chunk, concept) pair and the stratum it belongs to. */
export interface PoolUnit {
  documentKey: string;
  chunkId: string;
  conceptId: string;
  band: Band;
}

let poolCache: PoolUnit[] | null = null;

/**
 * Every (chunk, concept) pair, labelled with its percentile band.
 *
 * Ranking is per (document, concept): a document's own chunks are sorted by that
 * concept's score, and each chunk's top-percentile is 100 * (1 - rank/n). So the
 * best-scoring chunk sits at 100 and the worst at 100/n, which puts roughly 1% of
 * each document's chunks in the 99-100 band regardless of document length.
 *
 * Ties break on numeric chunk id so the assignment is deterministic across
 * restarts — otherwise a unit could drift between bands and be served twice.
 */
export function getPool(): PoolUnit[] {
  if (poolCache) return poolCache;
  requireFile(LOOKUP_PATH, "lookup.json");

  const lookup = JSON.parse(fs.readFileSync(LOOKUP_PATH, "utf-8")) as {
    documents: Record<string, Record<string, Record<string, number>>>;
  };

  const pool: PoolUnit[] = [];
  for (const [documentKey, chunks] of Object.entries(lookup.documents)) {
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
          documentKey,
          chunkId: ranked[rank],
          conceptId,
          band: bandOf(100 * (1 - rank / n)),
        });
      }
    }
  }

  poolCache = pool;
  return pool;
}

/** Pool size per band, for the band selector. */
export function bandCounts(): Record<string, number> {
  const counts: Record<string, number> = {};
  for (const unit of getPool()) counts[unit.band] = (counts[unit.band] ?? 0) + 1;
  return counts;
}

// ── full.txt access ───────────────────────────────────────────────────────────

/**
 * Absolute path to a document's full.txt, guarded: `source`, `engine` and
 * `documentId` arrive from client JSON.
 */
export function fullTextPath(c: ChunkRef): string {
  const root = path.join(REPO_ROOT, "stg_01_ocr");
  const resolved = path.resolve(root, c.source, c.engine, c.documentId, "full.txt");
  if (!resolved.startsWith(root + path.sep)) throw new Error("Invalid path");
  return resolved;
}

export function fullTextRelPath(c: ChunkRef): string {
  return path.relative(REPO_ROOT, fullTextPath(c));
}

export function readFullText(c: ChunkRef): string {
  return fs.readFileSync(fullTextPath(c), "utf-8");
}

const PAGE_SEP_RE = /^--- Page (\d+) ---[ \t]*$/gm;

/**
 * The printed page containing `offset`, from the `--- Page N ---` separators —
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
