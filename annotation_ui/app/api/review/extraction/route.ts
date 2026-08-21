import { NextRequest, NextResponse } from "next/server";
import { getExtractionDetail } from "@/lib/data";

/** Everything the extractor recorded for one document, for the review panel. */
export async function GET(req: NextRequest) {
  const run = req.nextUrl.searchParams.get("run");
  const documentId = req.nextUrl.searchParams.get("documentId");
  if (!run || !documentId) {
    return NextResponse.json({ error: "run and documentId are required" }, { status: 400 });
  }

  let detail;
  try {
    detail = await getExtractionDetail(run, documentId);
  } catch (err) {
    console.error("[review/extraction] Could not load extraction detail:", err);
    detail = null;
  }
  if (!detail) {
    return NextResponse.json(
      {
        error:
          "No extraction found. Build it with `npm run prepare-data` (needs " +
          "review/cba_provisions_aggregate.jsonl.gz), and `npm run upload-corpus` " +
          "if the app is reading from S3.",
      },
      { status: 404 }
    );
  }

  return NextResponse.json(detail);
}
