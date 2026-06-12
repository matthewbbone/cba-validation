import { NextRequest, NextResponse } from "next/server";
import { appendAnnotationRecord } from "@/lib/data";
import type { SubmitPayload, AnnotationRecord } from "@/lib/types";

export async function POST(req: NextRequest) {
  const body: SubmitPayload = await req.json();
  const { sessionId, cba, provisions } = body;

  const record: AnnotationRecord = {
    session_id: sessionId,
    timestamp: new Date().toISOString(),
    cba_source: cba.source,
    cba_filename: cba.filename,
    provisions,
  };

  appendAnnotationRecord(record);
  return NextResponse.json({ ok: true });
}
