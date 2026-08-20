import { NextRequest, NextResponse } from "next/server";
import { getExtractionDetail } from "@/lib/data";

/** Everything the extractor recorded for one document, for the review panel. */
export async function GET(req: NextRequest) {
  const run = req.nextUrl.searchParams.get("run");
  const documentId = req.nextUrl.searchParams.get("documentId");
  if (!run || !documentId) {
    return NextResponse.json({ error: "run and documentId are required" }, { status: 400 });
  }

  const detail = getExtractionDetail(run, documentId);
  if (!detail) {
    return NextResponse.json(
      {
        error:
          "No extraction found. Run `npm run prepare-data` after building " +
          "scripts/cba_provisions_aggregate.jsonl.gz.",
      },
      { status: 404 }
    );
  }

  return NextResponse.json(detail);
}
