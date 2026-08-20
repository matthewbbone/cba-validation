import { NextRequest, NextResponse } from "next/server";
import {
  bandCounts,
  chunkPosition,
  findChunk,
  findConcept,
  getPool,
} from "@/lib/chunks";
import { getCompletedUnits } from "@/lib/data";
import { DEFAULT_BAND, isBand, unitKey } from "@/lib/types";
import type { AnnotationUnit, Band, ChunkRef } from "@/lib/types";

/**
 * Serves one unit of work: a (chunk, concept) pair drawn uniformly at random
 * from one percentile band, excluding what this annotator has already done.
 *
 * Body: { annotator, band?, exclude?: string[], doc?: string, concept?: string }
 *
 * The band is the stratum, not a ranking: within it the draw is uniform, so an
 * annotator does not work down a score-ordered list and the sample stays usable
 * for estimating precision inside that stratum.
 */
export async function POST(req: NextRequest) {
  let body: {
    annotator?: unknown;
    band?: unknown;
    exclude?: unknown;
    doc?: unknown;
    concept?: unknown;
  };
  try {
    body = await req.json();
  } catch {
    return NextResponse.json({ error: "Malformed JSON body." }, { status: 400 });
  }

  const annotator = typeof body.annotator === "string" ? body.annotator.trim() : "";
  if (!annotator) {
    return NextResponse.json({ error: "An annotator name is required." }, { status: 400 });
  }
  if (body.band !== undefined && !isBand(body.band)) {
    return NextResponse.json({ error: `Unknown band "${String(body.band)}".` }, { status: 400 });
  }
  const band: Band = isBand(body.band) ? body.band : DEFAULT_BAND;

  const exclude = Array.isArray(body.exclude)
    ? body.exclude.filter((k): k is string => typeof k === "string")
    : [];
  const docFilter = typeof body.doc === "string" && body.doc ? body.doc : null;
  const conceptFilter = typeof body.concept === "string" && body.concept ? body.concept : null;

  let pool;
  try {
    pool = await getPool();
  } catch (err) {
    console.error("[session] Failed to read the pipeline artifacts:", err);
    return NextResponse.json(
      { error: err instanceof Error ? err.message : "Failed to read pipeline artifacts." },
      { status: 500 }
    );
  }

  let candidates = pool.filter((u) => u.band === band);
  if (docFilter) candidates = candidates.filter((u) => u.documentKey.endsWith(`/${docFilter}`));
  if (conceptFilter) candidates = candidates.filter((u) => u.conceptId === conceptFilter);

  if (candidates.length === 0) {
    const known = docFilter && !pool.some((u) => u.documentKey.endsWith(`/${docFilter}`));
    if (known) {
      return NextResponse.json({ error: `No chunked document named "${docFilter}".` }, { status: 404 });
    }
    if (conceptFilter && !pool.some((u) => u.conceptId === conceptFilter)) {
      return NextResponse.json({ error: `"${conceptFilter}" is not a scored concept.` }, { status: 404 });
    }
    // A filter combination can be legitimately empty in a narrow band — a short
    // document has no 99-100 units to spare once its handful are done.
    return NextResponse.json({ exhausted: true, band, poolSize: 0 });
  }

  const done = new Set<string>([...(await getCompletedUnits(annotator)), ...exclude]);
  const poolSize = candidates.length;

  const remaining = candidates.filter((u) => {
    const [source, engine, documentId] = u.documentKey.split("/");
    return !done.has(
      unitKey({ source, engine, documentId, chunkId: u.chunkId }, u.conceptId)
    );
  });

  if (remaining.length === 0) {
    return NextResponse.json({ exhausted: true, band, poolSize });
  }

  // Retry so one unreadable chunk cannot wedge the queue.
  const shortlist = remaining.slice();
  for (let attempt = 0; attempt < 5 && shortlist.length > 0; attempt++) {
    const i = Math.floor(Math.random() * shortlist.length);
    const picked = shortlist[i];
    const [source, engine, documentId] = picked.documentKey.split("/");
    const chunk: ChunkRef = { source, engine, documentId, chunkId: picked.chunkId };

    const row = await findChunk(chunk);
    const concept = await findConcept(picked.conceptId);
    if (!row || !concept) {
      console.error("[session] Pool references a missing chunk or concept:", picked);
      shortlist.splice(i, 1);
      continue;
    }

    const position = await chunkPosition(chunk);
    const unit: AnnotationUnit = {
      chunk,
      concept,
      text: row.text,
      charStart: row.char_start,
      charEnd: row.char_end,
      pageStart: row.page_start,
      pageEnd: row.page_end,
      chunkIndex: position.index,
      chunkCount: position.count,
      band,
    };
    return NextResponse.json({ ...unit, poolSize, bandCounts: await bandCounts() });
  }

  return NextResponse.json({ error: "Failed to load a chunk." }, { status: 500 });
}
