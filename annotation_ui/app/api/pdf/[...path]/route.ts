import { NextRequest, NextResponse } from "next/server";
import fs from "fs";
import { getCBAFilePath, getPDFPresignedUrl, isS3Configured } from "@/lib/data";

export async function GET(
  _req: NextRequest,
  { params }: { params: { path: string[] } }
) {
  if (!params.path || params.path.length < 2) {
    return new NextResponse("Bad request", { status: 400 });
  }
  const [source, ...rest] = params.path;
  const filename = rest.join("/");

  // S3 mode: redirect to a presigned URL
  if (isS3Configured()) {
    try {
      const url = await getPDFPresignedUrl(source, filename);
      return NextResponse.redirect(url);
    } catch (err) {
      console.error("[pdf] S3 error:", err);
      return new NextResponse("Failed to fetch PDF from S3", { status: 502 });
    }
  }

  // Local dev fallback: serve from disk
  let filePath: string;
  try {
    filePath = getCBAFilePath(source, filename);
  } catch {
    return new NextResponse("Forbidden", { status: 403 });
  }
  if (!fs.existsSync(filePath)) {
    return new NextResponse("Not found", { status: 404 });
  }
  const buffer = fs.readFileSync(filePath);
  return new NextResponse(buffer, {
    headers: {
      "Content-Type": "application/pdf",
      "Content-Disposition": `inline; filename="${filename}"`,
    },
  });
}
