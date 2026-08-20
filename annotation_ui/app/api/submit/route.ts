import { NextRequest, NextResponse } from "next/server";
import {
  findChunk,
  findConcept,
  fullTextPath,
  fullTextRelPath,
  pageAtOffset,
  readFullText,
} from "@/lib/chunks";
import { appendSpanRecord } from "@/lib/data";
import { isBand, isRelevance } from "@/lib/types";
import type { ChunkRef, Span, SpanAnnotationRecord, SpanSubmitPayload } from "@/lib/types";
import fs from "fs";

function isChunkRef(v: unknown): v is ChunkRef {
  if (!v || typeof v !== "object") return false;
  const c = v as Record<string, unknown>;
  return (
    typeof c.source === "string" &&
    typeof c.engine === "string" &&
    typeof c.documentId === "string" &&
    typeof c.chunkId === "string"
  );
}

function bad(error: string) {
  return NextResponse.json({ ok: false, error }, { status: 400 });
}

/**
 * Persists one chunk-concept judgement: a relevance verdict plus any evidence spans.
 *
 * Every span is re-verified against the document's full.txt before anything is
 * written -- the server re-reads the source and re-slices, so a row can never land
 * in the JSONL claiming a passage the file does not contain. Spans are also
 * required to fall inside the chunk that was actually shown, which catches a
 * client that has drifted out of sync with the pipeline's chunking.
 */
export async function POST(req: NextRequest) {
  let body: SpanSubmitPayload;
  try {
    body = await req.json();
  } catch {
    return bad("Malformed JSON body.");
  }

  const annotator = typeof body.annotator === "string" ? body.annotator.trim() : "";
  if (!annotator) return bad("An annotator name is required.");
  if (typeof body.sessionId !== "string" || !body.sessionId) return bad("Missing sessionId.");
  if (!isChunkRef(body.chunk)) return bad("Missing or malformed chunk reference.");
  if (!isBand(body.band)) return bad(`Unknown band "${String(body.band)}".`);
  if (!isRelevance(body.relevance)) {
    return bad("A relevance verdict (yes / partly / no) is required.");
  }

  const concept = findConcept(body.conceptId);
  if (!concept) return bad(`Unknown concept "${body.conceptId}".`);

  const row = findChunk(body.chunk);
  if (!row) {
    return bad(
      `No such chunk: ${body.chunk.documentId} chunk ${body.chunk.chunkId}. ` +
        `The corpus may have been re-chunked since this unit was served.`
    );
  }

  let filePath: string;
  try {
    filePath = fullTextPath(body.chunk);
  } catch {
    return bad("Invalid document path.");
  }
  if (!fs.existsSync(filePath)) return bad(`No full.txt for ${body.chunk.documentId}.`);

  const spans: unknown = body.spans;
  if (!Array.isArray(spans)) return bad("`spans` must be an array.");

  // "No" means the passage has nothing to do with the concept, so evidence for it
  // is a contradiction. "Yes"/"partly" with no spans is allowed and meaningful:
  // relevant, but the annotator could not delimit a clean passage.
  if (body.relevance === "no" && spans.length > 0) {
    return bad('A "no" verdict cannot carry evidence spans.');
  }

  const fullText = readFullText(body.chunk);
  const verified: Span[] = [];

  for (let i = 0; i < spans.length; i++) {
    const s = spans[i] as Partial<Span>;
    const label = `Span ${i + 1}`;

    if (!Number.isInteger(s.start) || !Number.isInteger(s.end)) {
      return bad(`${label}: start and end must be integers.`);
    }
    const start = s.start as number;
    const end = s.end as number;
    if (start < 0 || end <= start || end > fullText.length) {
      return bad(
        `${label}: offsets [${start},${end}) are outside full.txt (length ${fullText.length}).`
      );
    }
    if (start < row.char_start || end > row.char_end) {
      return bad(
        `${label}: offsets [${start},${end}) fall outside the chunk that was shown ` +
          `([${row.char_start},${row.char_end})).`
      );
    }
    if (typeof s.text !== "string") return bad(`${label}: missing text.`);
    if (fullText.slice(start, end) !== s.text) {
      return bad(
        `${label}: text does not match the source at [${start},${end}). ` +
          `The document may have been re-OCR'd since it was loaded.`
      );
    }

    verified.push({
      start,
      end,
      text: s.text,
      note: typeof s.note === "string" ? s.note.trim() : "",
      page: pageAtOffset(fullText, start),
    });
  }

  const record: SpanAnnotationRecord = {
    session_id: body.sessionId,
    timestamp: new Date().toISOString(),
    annotator,
    source: body.chunk.source,
    engine: body.chunk.engine,
    document_id: body.chunk.documentId,
    chunk_id: body.chunk.chunkId,
    source_file: fullTextRelPath(body.chunk),
    chunk_char_start: row.char_start,
    chunk_char_end: row.char_end,
    page_start: row.page_start,
    page_end: row.page_end,
    concept_id: concept.conceptId,
    concept_label: concept.label,
    band: body.band,
    relevance: body.relevance,
    spans: verified,
  };

  try {
    appendSpanRecord(record);
  } catch (err) {
    console.error("[submit] Failed to persist annotation:", err);
    return NextResponse.json(
      { ok: false, error: "Failed to persist annotation." },
      { status: 500 }
    );
  }

  return NextResponse.json({ ok: true });
}
