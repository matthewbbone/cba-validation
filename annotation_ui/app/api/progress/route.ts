import { NextRequest, NextResponse } from "next/server";
import { getCompletedCBAsForPID, isS3Configured } from "@/lib/data";

export async function GET(req: NextRequest) {
  const pid = new URL(req.url).searchParams.get("pid");
  if (!pid) return NextResponse.json({ error: "pid required" }, { status: 400 });
  if (!isS3Configured()) return NextResponse.json({ completed: [] });
  const completed = await getCompletedCBAsForPID(pid);
  return NextResponse.json({ completed });
}
