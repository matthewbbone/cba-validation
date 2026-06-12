/**
 * Uploads all CBA PDFs from data/cbas/ to S3.
 * Requires S3_BUCKET_NAME and AWS_REGION env vars (or ~/.aws/credentials).
 *
 * Usage:  npx tsx scripts/upload-pdfs.ts
 */

import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";
import { S3Client, PutObjectCommand, HeadObjectCommand } from "@aws-sdk/client-s3";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const REPO_ROOT = path.resolve(__dirname, "../..");
const CBAS_DIR = path.join(REPO_ROOT, "data", "cbas");

const BUCKET = process.env.S3_BUCKET_NAME;
const REGION = process.env.AWS_REGION ?? "us-east-1";

if (!BUCKET) {
  console.error("Set S3_BUCKET_NAME before running this script.");
  process.exit(1);
}

const s3 = new S3Client({ region: REGION });

async function exists(key: string): Promise<boolean> {
  try {
    await s3.send(new HeadObjectCommand({ Bucket: BUCKET!, Key: key }));
    return true;
  } catch {
    return false;
  }
}

let uploaded = 0;
let skipped = 0;

for (const entry of fs.readdirSync(CBAS_DIR, { withFileTypes: true })) {
  if (!entry.isDirectory()) continue;
  const sourceDir = path.join(CBAS_DIR, entry.name);
  for (const filename of fs.readdirSync(sourceDir)) {
    if (!filename.endsWith(".pdf")) continue;
    const key = `cbas/${entry.name}/${filename}`;
    if (await exists(key)) {
      skipped++;
      continue;
    }
    const body = fs.readFileSync(path.join(sourceDir, filename));
    await s3.send(
      new PutObjectCommand({ Bucket: BUCKET!, Key: key, Body: body, ContentType: "application/pdf" })
    );
    console.log(`  uploaded ${key}`);
    uploaded++;
  }
}

console.log(`\n✓ Done — ${uploaded} uploaded, ${skipped} already present.`);
