import { NextResponse } from "next/server";
import { getRandomCBA, getRandomProvisions } from "@/lib/data";

export function GET() {
  const cba = getRandomCBA();
  const provisions = getRandomProvisions(5);
  return NextResponse.json({ cba, provisions });
}
