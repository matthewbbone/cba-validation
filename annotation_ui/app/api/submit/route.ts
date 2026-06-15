import { NextRequest, NextResponse } from "next/server";
import { appendAnnotationRecord, isS3Configured, writeAnnotationToS3 } from "@/lib/data";
import type { SubmitPayload, AnnotationRecord } from "@/lib/types";

export async function POST(req: NextRequest) {
  const body: SubmitPayload = await req.json();
  const { sessionId, cba, provisions, prolific } = body;

  const record: AnnotationRecord = {
    session_id: sessionId,
    timestamp: new Date().toISOString(),
    cba_source: cba.source,
    cba_filename: cba.filename,
    prolific_pid: prolific.prolific_pid,
    study_id: prolific.study_id,
    prolific_session_id: prolific.prolific_session_id,
    provisions,
  };

  try {
    if (isS3Configured()) {
      await writeAnnotationToS3(prolific.prolific_pid, record);
    } else {
      appendAnnotationRecord(record);
    }
  } catch (err) {
    console.error("[submit] Failed to persist annotation:", err);
    return NextResponse.json(
      { ok: false, error: "Failed to persist annotation." },
      { status: 500 }
    );
  }

  return NextResponse.json({ ok: true });
}
