import { NextRequest, NextResponse } from "next/server";
import { getRandomCBAExcluding, getRandomProvisions } from "@/lib/data";

export function GET(req: NextRequest) {
  const url = new URL(req.url);
  const excludeParam = url.searchParams.get("exclude");
  let excludeKeys: string[] = [];
  if (excludeParam) {
    try {
      excludeKeys = JSON.parse(decodeURIComponent(excludeParam));
    } catch {
      // ignore malformed param
    }
  }

  const cba = getRandomCBAExcluding(excludeKeys);
  if (!cba) return NextResponse.json({ exhausted: true });

  const provisions = getRandomProvisions(5);
  return NextResponse.json({ cba, provisions });
}
