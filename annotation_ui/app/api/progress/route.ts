import { NextRequest, NextResponse } from "next/server";
import { getCompletedUnits, getBandTally } from "@/lib/data";
import { bandCounts } from "@/lib/chunks";

/**
 * What this annotator has already submitted: the unit keys (for the exclusion
 * set) plus a per-band done/total tally, so the band selector can show how much
 * of each stratum is left.
 */
export async function GET(req: NextRequest) {
  const annotator = req.nextUrl.searchParams.get("annotator") ?? "";
  if (!annotator.trim()) {
    return NextResponse.json({ completed: [], count: 0, done: {}, pool: {} });
  }

  const completed = getCompletedUnits(annotator);
  let pool: Record<string, number> = {};
  try {
    pool = bandCounts();
  } catch {
    // The tally is a convenience; a missing pipeline artifact is reported by /api/session.
  }

  return NextResponse.json({
    completed,
    count: completed.length,
    done: getBandTally(annotator),
    pool,
  });
}
