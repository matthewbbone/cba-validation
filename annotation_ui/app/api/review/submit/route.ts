import { NextRequest, NextResponse } from "next/server";
import { submitReview } from "@/lib/data";
import { REVIEW_ISSUES, REVIEW_QUALITIES } from "@/lib/types";
import type { ReviewSubmitPayload, ExtractionReviewRecord } from "@/lib/types";

/**
 * Validate one toggle row: must be an array, every member known. Returns the
 * members de-duplicated and in the canonical order so the same judgement always
 * serialises identically and downstream tallies stay stable.
 */
function normaliseFlags<T extends string>(
  value: unknown,
  allowed: T[],
  name: string
): { ok: true; flags: T[] } | { ok: false; error: string } {
  if (!Array.isArray(value)) {
    return { ok: false, error: `${name} must be an array (empty means none selected)` };
  }
  const unknown = value.filter((v) => !allowed.includes(v as T));
  if (unknown.length) {
    return { ok: false, error: `unknown ${name}: ${unknown.join(", ")}` };
  }
  return { ok: true, flags: allowed.filter((a) => value.includes(a)) };
}

export async function POST(req: NextRequest) {
  let body: ReviewSubmitPayload;
  try {
    body = await req.json();
  } catch {
    return NextResponse.json({ ok: false, error: "Invalid JSON body" }, { status: 400 });
  }

  const { sessionId, reviewer, unit, quality, issues, comment } = body;
  if (!reviewer?.trim() || !unit) {
    return NextResponse.json(
      { ok: false, error: "reviewer and unit are required" },
      { status: 400 }
    );
  }

  const q = normaliseFlags(quality ?? [], REVIEW_QUALITIES, "quality");
  if (!q.ok) return NextResponse.json({ ok: false, error: q.error }, { status: 400 });
  const i = normaliseFlags(issues ?? [], REVIEW_ISSUES, "issues");
  if (!i.ok) return NextResponse.json({ ok: false, error: i.error }, { status: 400 });

  const record: ExtractionReviewRecord = {
    session_id: sessionId,
    timestamp: new Date().toISOString(),
    reviewer: reviewer.trim(),
    cba_source: unit.source,
    cba_filename: unit.filename,
    run: unit.run,
    document_id: unit.documentId,
    concept_id: unit.conceptId,
    quality: q.flags,
    issues: i.flags,
    comment: comment ?? "",
    n_records: unit.nRecords,
    n_fields: unit.nFields,
  };

  try {
    await submitReview(record);
  } catch (err) {
    console.error("[review/submit] Failed to persist review:", err);
    return NextResponse.json({ ok: false, error: "Failed to persist review." }, { status: 500 });
  }

  return NextResponse.json({ ok: true });
}
