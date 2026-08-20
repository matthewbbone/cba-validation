/**
 * Mirror everything the annotation UI reads into S3, under the same paths it uses
 * on local disk.
 *
 *   S3_BUCKET_NAME=my-bucket npx tsx scripts/upload-corpus.ts
 *   S3_BUCKET_NAME=my-bucket S3_PREFIX=cba npx tsx scripts/upload-corpus.ts
 *   ... --force            re-upload objects that already exist
 *   ... --dry-run          list what would be uploaded and stop
 *
 * Uploads:
 *   stg_01_ocr/{source}/{engine}/{doc}/full.txt      (one per document)
 *   results/concept_similarity/chunks.jsonl
 *   results/concept_similarity/lookup.json
 *   results/concept_similarity/concepts.json
 *
 * Only full.txt is uploaded from the OCR tree: the per-page .md/.txt files are what
 * full.txt was built from, and nothing in the app reads them any more.
 *
 * Existing objects are skipped unless --force, so a re-run after a partial upload
 * costs only the missing objects.
 */

import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";
import {
  HeadObjectCommand,
  PutObjectCommand,
  S3Client,
} from "@aws-sdk/client-s3";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const REPO_ROOT = path.resolve(__dirname, "../..");

const BUCKET = process.env.S3_BUCKET_NAME;
const REGION = process.env.AWS_REGION ?? "us-east-1";
const PREFIX = (process.env.S3_PREFIX ?? "").replace(/^\/+|\/+$/g, "");
const FORCE = process.argv.includes("--force");
const DRY_RUN = process.argv.includes("--dry-run");

if (!BUCKET) {
  console.error("S3_BUCKET_NAME is required.\n  S3_BUCKET_NAME=my-bucket npx tsx scripts/upload-corpus.ts");
  process.exit(1);
}

const s3 = new S3Client({ region: REGION });
const key = (rel: string) => (PREFIX ? `${PREFIX}/${rel}` : rel);

// Text so a browser or `aws s3 cp -` shows it readably; JSON where it is JSON.
function contentType(rel: string): string {
  if (rel.endsWith(".json")) return "application/json";
  if (rel.endsWith(".jsonl")) return "application/x-ndjson";
  return "text/plain; charset=utf-8";
}

async function alreadyThere(rel: string, size: number): Promise<boolean> {
  try {
    const head = await s3.send(new HeadObjectCommand({ Bucket: BUCKET, Key: key(rel) }));
    // Same byte length is a good enough identity check for immutable artifacts.
    return head.ContentLength === size;
  } catch {
    return false;
  }
}

function collect(): string[] {
  const rels: string[] = [];

  const ocrRoot = path.join(REPO_ROOT, "stg_01_ocr");
  if (!fs.existsSync(ocrRoot)) {
    console.error(`missing ${path.relative(REPO_ROOT, ocrRoot)} — nothing to upload`);
    process.exit(1);
  }
  for (const source of fs.readdirSync(ocrRoot).sort()) {
    if (source.startsWith(".")) continue;
    const sourceDir = path.join(ocrRoot, source);
    if (!fs.statSync(sourceDir).isDirectory()) continue;
    for (const engine of fs.readdirSync(sourceDir).sort()) {
      if (engine.startsWith(".")) continue;
      const engineDir = path.join(sourceDir, engine);
      if (!fs.statSync(engineDir).isDirectory()) continue;
      for (const doc of fs.readdirSync(engineDir).sort()) {
        if (doc.startsWith(".")) continue;
        const full = path.join(engineDir, doc, "full.txt");
        if (fs.existsSync(full)) rels.push(`stg_01_ocr/${source}/${engine}/${doc}/full.txt`);
      }
    }
  }

  for (const name of ["chunks.jsonl", "lookup.json", "concepts.json"]) {
    const rel = `results/concept_similarity/${name}`;
    if (!fs.existsSync(path.join(REPO_ROOT, rel))) {
      console.error(`missing ${rel} — run \`uv run python pipeline/runner.py\` first`);
      process.exit(1);
    }
    rels.push(rel);
  }

  return rels;
}

async function main() {
  const rels = collect();
  const totalBytes = rels.reduce((n, r) => n + fs.statSync(path.join(REPO_ROOT, r)).size, 0);
  console.log(`target : s3://${BUCKET}/${PREFIX ? PREFIX + "/" : ""}`);
  console.log(`objects: ${rels.length} (${(totalBytes / 1e6).toFixed(2)} MB)`);

  if (DRY_RUN) {
    for (const rel of rels) console.log(`  would upload ${key(rel)}`);
    return;
  }

  let uploaded = 0;
  let skipped = 0;
  let bytes = 0;
  for (const rel of rels) {
    const abs = path.join(REPO_ROOT, rel);
    const size = fs.statSync(abs).size;
    if (!FORCE && (await alreadyThere(rel, size))) {
      skipped++;
      continue;
    }
    await s3.send(
      new PutObjectCommand({
        Bucket: BUCKET,
        Key: key(rel),
        Body: fs.readFileSync(abs),
        ContentType: contentType(rel),
      })
    );
    uploaded++;
    bytes += size;
    if (uploaded % 5 === 0 || size > 1e6) {
      console.log(`  ${uploaded + skipped}/${rels.length}  ${rel} (${(size / 1000).toFixed(0)} KB)`);
    }
  }

  console.log(`uploaded ${uploaded} object(s), ${(bytes / 1e6).toFixed(2)} MB; skipped ${skipped} already present`);
  if (skipped && !FORCE) console.log("pass --force to re-upload unchanged objects");
}

main().catch((err) => {
  console.error("upload failed:", err);
  process.exit(1);
});
