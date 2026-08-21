import { NextRequest, NextResponse } from "next/server";
import { getCompletedReviews, getReviewUnits } from "@/lib/data";

/**
 * The review unit index, plus (when a reviewer is named) the unit keys that
 * reviewer has already judged — resolved server-side so the client never has to
 * carry its full history, matching the annotation flow's progress lookup.
 */
export async function GET(req: NextRequest) {
  const reviewer = req.nextUrl.searchParams.get("reviewer")?.trim() ?? "";

  let completed: string[] = [];
  if (reviewer) {
    try {
      completed = await getCompletedReviews(reviewer);
    } catch (err) {
      // Non-fatal: the reviewer can still work, they just lose progress marks.
      console.error("[review/units] Could not load completed reviews:", err);
    }
  }

  return NextResponse.json({ units: getReviewUnits(), completed });
}
