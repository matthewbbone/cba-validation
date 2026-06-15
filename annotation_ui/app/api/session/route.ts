import { NextRequest, NextResponse } from "next/server";
import {
  getRandomCBAExcluding,
  getRandomProvisions,
  getCompletedCBAsForPID,
  isS3Configured,
} from "@/lib/data";

interface SessionRequest {
  pid?: string;
  // Session-local keys to exclude (completed in this client session + skipped).
  exclude?: string[];
}

export async function POST(req: NextRequest) {
  let body: SessionRequest;
  try {
    body = await req.json();
  } catch {
    return NextResponse.json({ error: "Invalid JSON body" }, { status: 400 });
  }

  const excludeSet = new Set(Array.isArray(body.exclude) ? body.exclude : []);

  // When S3 is configured, fold in the authoritative completed list for this
  // PID server-side so the client never has to serialize its full history.
  if (isS3Configured() && body.pid) {
    try {
      for (const key of await getCompletedCBAsForPID(body.pid)) excludeSet.add(key);
    } catch (err) {
      console.error("[session] Could not load completed CBAs:", err);
    }
  }

  const cba = getRandomCBAExcluding(Array.from(excludeSet));
  if (!cba) return NextResponse.json({ exhausted: true });

  const provisions = getRandomProvisions(5);
  return NextResponse.json({ cba, provisions });
}
