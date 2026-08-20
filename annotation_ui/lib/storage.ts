import fs from "fs";
import path from "path";
import {
  GetObjectCommand,
  HeadObjectCommand,
  ListObjectsV2Command,
  PutObjectCommand,
  S3Client,
} from "@aws-sdk/client-s3";

/**
 * Two backends behind one path vocabulary.
 *
 * Every caller names things by their **repo-relative path** --
 * "stg_01_ocr/dol_archive/.../full.txt", "results/concept_similarity/lookup.json".
 * Locally that resolves against the repo root; on S3 it becomes the object key,
 * optionally under S3_PREFIX. Keeping one vocabulary means there is no mapping
 * table to drift, and a path in a stored record means the same thing either way.
 *
 * S3 mode is selected purely by S3_BUCKET_NAME being set, so a local checkout with
 * no AWS configured keeps working exactly as before.
 */

const BUCKET = process.env.S3_BUCKET_NAME;
const REGION = process.env.AWS_REGION ?? "us-east-1";
// Optional key prefix, e.g. "cba/" — normalised to end with exactly one slash.
const PREFIX = (process.env.S3_PREFIX ?? "").replace(/^\/+|\/+$/g, "");

const REPO_ROOT = path.resolve(process.cwd(), "..");

export function isS3Configured(): boolean {
  return !!BUCKET;
}

export function describeStorage(): string {
  return BUCKET ? `s3://${BUCKET}/${PREFIX ? PREFIX + "/" : ""}` : `local:${REPO_ROOT}`;
}

let client: S3Client | null = null;
function s3(): S3Client {
  if (!client) client = new S3Client({ region: REGION });
  return client;
}

export function objectKey(relPath: string): string {
  return PREFIX ? `${PREFIX}/${relPath}` : relPath;
}

/**
 * Resolves a repo-relative path on local disk, refusing anything that escapes the
 * repo -- callers pass values that originate in client JSON.
 */
export function localPath(relPath: string): string {
  const resolved = path.resolve(REPO_ROOT, relPath);
  if (!resolved.startsWith(REPO_ROOT + path.sep)) throw new Error("Invalid path");
  return resolved;
}

async function bodyToString(body: unknown): Promise<string> {
  // The SDK v3 stream exposes transformToString in Node; fall back to chunks if not.
  const b = body as { transformToString?: () => Promise<string> } | null;
  if (b && typeof b.transformToString === "function") return b.transformToString();
  const chunks: Buffer[] = [];
  for await (const chunk of body as AsyncIterable<Buffer>) chunks.push(chunk);
  return Buffer.concat(chunks).toString("utf-8");
}

/**
 * Whole-object read, decoded as UTF-8.
 *
 * Deliberately not a byte-range read. Span offsets are *character* offsets, and
 * the corpus contains 21 distinct non-ASCII characters (smart quotes, en/em
 * dashes, section signs, bullets), so a byte range would silently return the
 * wrong slice on any document containing one.
 */
export async function readText(relPath: string): Promise<string> {
  if (!BUCKET) return fs.promises.readFile(localPath(relPath), "utf-8");
  const res = await s3().send(
    new GetObjectCommand({ Bucket: BUCKET, Key: objectKey(relPath) })
  );
  return bodyToString(res.Body);
}

export async function exists(relPath: string): Promise<boolean> {
  if (!BUCKET) {
    try {
      return fs.existsSync(localPath(relPath));
    } catch {
      return false;
    }
  }
  try {
    // HEAD, not GET: a GetObject here would download the whole object just to
    // learn that it is there, doubling the transfer on every submit.
    await s3().send(new HeadObjectCommand({ Bucket: BUCKET, Key: objectKey(relPath) }));
    return true;
  } catch {
    return false;
  }
}

/** Writes JSON at `relPath`. S3: one object. Local: a file, parent dirs created. */
export async function writeJson(relPath: string, obj: unknown): Promise<void> {
  const body = JSON.stringify(obj);
  if (!BUCKET) {
    const target = localPath(relPath);
    await fs.promises.mkdir(path.dirname(target), { recursive: true });
    await fs.promises.writeFile(target, body, "utf-8");
    return;
  }
  await s3().send(
    new PutObjectCommand({
      Bucket: BUCKET,
      Key: objectKey(relPath),
      Body: body,
      ContentType: "application/json",
    })
  );
}

/** Appends a line to a local file. S3 has no append, so this is local-only. */
export async function appendLine(relPath: string, line: string): Promise<void> {
  if (BUCKET) throw new Error("appendLine is not available in S3 mode");
  const target = localPath(relPath);
  await fs.promises.mkdir(path.dirname(target), { recursive: true });
  await fs.promises.appendFile(target, line + "\n", "utf-8");
}

/**
 * Every path under `relPrefix`, returned repo-relative (prefix-stripped so the
 * caller sees the same strings in both modes). Paginates.
 */
export async function listPaths(relPrefix: string): Promise<string[]> {
  if (!BUCKET) {
    let dir: string;
    try {
      dir = localPath(relPrefix);
    } catch {
      return [];
    }
    if (!fs.existsSync(dir)) return [];
    const out: string[] = [];
    const walk = (d: string) => {
      for (const e of fs.readdirSync(d, { withFileTypes: true })) {
        if (e.name.startsWith(".")) continue;
        const p = path.join(d, e.name);
        if (e.isDirectory()) walk(p);
        else out.push(path.relative(REPO_ROOT, p));
      }
    };
    walk(dir);
    return out.sort();
  }

  const keyPrefix = objectKey(relPrefix);
  const strip = PREFIX ? PREFIX.length + 1 : 0;
  const out: string[] = [];
  let token: string | undefined;
  do {
    const res = await s3().send(
      new ListObjectsV2Command({ Bucket: BUCKET, Prefix: keyPrefix, ContinuationToken: token })
    );
    for (const obj of res.Contents ?? []) {
      if (obj.Key) out.push(obj.Key.slice(strip));
    }
    token = res.IsTruncated ? res.NextContinuationToken : undefined;
  } while (token);
  return out.sort();
}
