/**
 * DORMANT — kept for the recipe, not part of the current workflow.
 *
 * Live: the review-data stage at the bottom, which the extraction-review tab needs.
 * Run it once, then `npm run upload-corpus` if the app reads from S3.
 *
 * Dormant, and skipped with a notice unless their inputs come back:
 *   lib/cba-manifest.json      — { source, filename } for every PDF in data/cbas/
 *   lib/provisions.json        — the provision dictionary, from CSV
 *   lib/provision-schemas.json — format + flags per concept_id, via Python
 *
 * Their input trees (data/cbas, data/cba_meta, structures/) were removed from the
 * repo, so those stages skip with a notice rather than crashing. provisions.json
 * and cba-manifest.json remain committed, which is why the review stage can still
 * resolve concept labels and PDF filenames without them.
 *
 * Usage:  npx tsx scripts/prepare-data.ts
 */

import fs from "fs";
import path from "path";
import readline from "readline";
import zlib from "zlib";
import { fileURLToPath } from "url";
import { execSync } from "child_process";
import Papa from "papaparse";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const REPO_ROOT = path.resolve(__dirname, "../..");
const CBAS_DIR = path.join(REPO_ROOT, "data", "cbas");
const DICT_PATH = path.join(REPO_ROOT, "data", "cba_meta", "cba_provision_dictionary.csv");
const LIB_DIR = path.join(__dirname, "..", "lib");
const DATA_DIR = path.join(__dirname, "..", "data");
// The aggregate lives in review/, not scripts/ -- the old default pointed at a
// path that has never existed in this repo, so the stage always skipped.
const AGGREGATE_PATH = path.join(REPO_ROOT, "review", "cba_provisions_aggregate.jsonl.gz");

// ── CBA manifest ──────────────────────────────────────────────────────────────
if (!fs.existsSync(CBAS_DIR)) {
  console.log(`• cba-manifest.json — skipped (no ${path.relative(REPO_ROOT, CBAS_DIR)})`);
} else {
  const cbas: { source: string; filename: string }[] = [];
  for (const entry of fs.readdirSync(CBAS_DIR, { withFileTypes: true })) {
    if (!entry.isDirectory()) continue;
    const sourceDir = path.join(CBAS_DIR, entry.name);
    for (const filename of fs.readdirSync(sourceDir)) {
      if (filename.endsWith(".pdf")) cbas.push({ source: entry.name, filename });
    }
  }
  fs.writeFileSync(path.join(LIB_DIR, "cba-manifest.json"), JSON.stringify(cbas, null, 2));
  console.log(`✓ cba-manifest.json  — ${cbas.length} CBAs`);
}

// ── Provision dictionary ──────────────────────────────────────────────────────
if (!fs.existsSync(DICT_PATH)) {
  console.log(`• provisions.json — skipped (no ${path.relative(REPO_ROOT, DICT_PATH)})`);
} else {
  const csv = fs.readFileSync(DICT_PATH, "utf-8");
  const { data } = Papa.parse<{
    concept_id: string;
    category: string;
    concept_label_example: string;
  }>(csv, { header: true, skipEmptyLines: true });

  const provisions = data.map((row) => ({
    conceptId: row.concept_id,
    category: row.category,
    label: row.concept_label_example,
  }));
  fs.writeFileSync(path.join(LIB_DIR, "provisions.json"), JSON.stringify(provisions, null, 2));
  console.log(`✓ provisions.json    — ${provisions.length} provisions`);
}

// ── Provision schemas (format + flags per concept_id) ─────────────────────────
// The committed provision-schemas.json carries rater-facing `title` and
// `description` copy that was edited by hand *after* generation (commit 5cc70e0)
// and that generate_ui_schema.py does not reproduce. Regenerating unconditionally
// silently reverts that copy, so this step is opt-in.
const schemaPath = path.join(LIB_DIR, "provision-schemas.json");
const schemaScript = path.join(REPO_ROOT, "structures", "generate_ui_schema.py");
const forceSchemas = process.argv.includes("--force-schemas");

if (fs.existsSync(schemaPath) && !forceSchemas) {
  const schemaCount = Object.keys(JSON.parse(fs.readFileSync(schemaPath, "utf-8"))).length;
  console.log(
    `• provision-schemas.json — kept existing (${schemaCount} provisions). ` +
      `Pass --force-schemas to regenerate; it will drop the hand-edited rater copy.`
  );
} else if (!fs.existsSync(schemaScript)) {
  console.log(`• provision-schemas.json — skipped (no ${path.relative(REPO_ROOT, schemaScript)})`);
} else {
  const schemaJson = execSync(`python3 "${schemaScript}"`, { cwd: REPO_ROOT }).toString();
  fs.writeFileSync(schemaPath, schemaJson);
  const schemaCount = Object.keys(JSON.parse(schemaJson)).length;
  console.log(`✓ provision-schemas.json — ${schemaCount} provisions (regenerated)`);
}

// The review stage needs the provision dictionary and the PDF manifest. Both are
// committed, so read them back rather than depending on the stages above having run.
const cbas: { source: string; filename: string }[] = JSON.parse(
  fs.readFileSync(path.join(LIB_DIR, "cba-manifest.json"), "utf-8")
);
const provisions: { conceptId: string; category: string; label: string }[] = JSON.parse(
  fs.readFileSync(path.join(LIB_DIR, "provisions.json"), "utf-8")
);

// ── Review data ───────────────────────────────────────────────────────────────
// Links each local PDF to its extraction(s) in the provisions aggregate, then
// emits one review unit per (extraction document × concept_id).
// (Invoked at the bottom of the file — it reads consts declared below.)

/**
 * Directory name under data/cbas/ → the `source` value used in the harmonized
 * metadata, which is what the aggregate's cba_id prefix is built from.
 */
const SOURCE_PREFIX: Record<string, string> = {
  dol_archive: "DoL",
  cornell_dol: "Cornell_DoL",
  cornell_retail_educ: "Cornell_RetailEd",
};

interface AggregateDoc {
  document_id: string;
  run: string;
  document: Record<string, unknown>;
  metadata: Record<string, unknown> & {
    filename?: string | null;
    _member_cba_ids?: string[] | null;
  };
  quality: Record<string, unknown>;
  concept_records: { concept_id: string; concept_label?: string | null }[];
  concept_fields: { concept_id: string }[];
  dimension_coverage: Record<string, unknown>[];
}

async function buildReviewData(): Promise<void> {
  if (!fs.existsSync(AGGREGATE_PATH)) {
    console.log(
      `• review-units.json — skipped (no ${path.relative(REPO_ROOT, AGGREGATE_PATH)}; ` +
        `build it with \`python scripts/aggregate_provisions.py\`)`
    );
    return;
  }

  // Two lookup keys per PDF. `metadata.filename` resolves almost everything;
  // RetailEd rows null that column whenever the per-part metadata rows disagree,
  // so those fall back to matching a member cba_id.
  const byFilename = new Map<string, { source: string; filename: string }>();
  const byMemberId = new Map<string, { source: string; filename: string }>();
  for (const cba of cbas) {
    const prefix = SOURCE_PREFIX[cba.source];
    if (!prefix) continue;
    byFilename.set(cba.filename, cba);
    byMemberId.set(`${prefix}_${cba.filename}`, cba);
  }

  // concept_id → dictionary entry, for category/label on known concepts.
  const dict = new Map(provisions.map((p) => [p.conceptId, p]));

  const units: Record<string, unknown>[] = [];
  const details: Record<string, unknown> = {};
  const seenPdfs = new Set<string>();

  const stream = fs.createReadStream(AGGREGATE_PATH).pipe(zlib.createGunzip());
  const lines = readline.createInterface({ input: stream, crlfDelay: Infinity });

  for await (const line of lines) {
    if (!line.trim()) continue;
    const doc = JSON.parse(line) as AggregateDoc;

    const members = doc.metadata?._member_cba_ids ?? [];
    let cba = doc.metadata?.filename ? byFilename.get(doc.metadata.filename) : undefined;
    if (!cba) {
      for (const id of members) {
        const hit = byMemberId.get(id);
        if (hit) {
          cba = hit;
          break;
        }
      }
    }
    if (!cba) continue;

    seenPdfs.add(`${cba.source}/${cba.filename}`);
    const detailKey = `${doc.run}/${doc.document_id}`;
    details[detailKey] = {
      run: doc.run,
      documentId: doc.document_id,
      document: doc.document,
      metadata: doc.metadata,
      quality: doc.quality,
      concept_records: doc.concept_records,
      concept_fields: doc.concept_fields,
      dimension_coverage: doc.dimension_coverage,
    };

    // Group both arrays by concept_id — a unit is everything recorded for one
    // concept, whether that is records, fields, or both.
    const counts = new Map<string, { records: number; fields: number; label: string | null }>();
    const bump = (id: string, kind: "records" | "fields", label?: string | null) => {
      if (!id) return;
      const entry = counts.get(id) ?? { records: 0, fields: 0, label: null };
      entry[kind] += 1;
      if (!entry.label && label) entry.label = label;
      counts.set(id, entry);
    };
    for (const r of doc.concept_records ?? []) bump(r.concept_id, "records", r.concept_label);
    for (const f of doc.concept_fields ?? []) bump(f.concept_id, "fields");

    for (const [conceptId, c] of Array.from(counts).sort((a, b) => a[0].localeCompare(b[0]))) {
      const known = dict.get(conceptId);
      units.push({
        source: cba.source,
        filename: cba.filename,
        run: doc.run,
        documentId: doc.document_id,
        conceptId,
        category: known?.category ?? "Uncategorised",
        label: known?.label ?? c.label ?? conceptId,
        nRecords: c.records,
        nFields: c.fields,
        offDictionary: !known,
      });
    }
  }

  fs.writeFileSync(path.join(LIB_DIR, "review-units.json"), JSON.stringify(units));
  if (!fs.existsSync(DATA_DIR)) fs.mkdirSync(DATA_DIR, { recursive: true });
  const detailPath = path.join(DATA_DIR, "review-extractions.json");
  fs.writeFileSync(detailPath, JSON.stringify(details));

  const mb = (fs.statSync(detailPath).size / 1e6).toFixed(1);
  console.log(
    `✓ review-units.json  — ${units.length} units · ${seenPdfs.size}/${cbas.length} PDFs linked · ` +
      `${Object.keys(details).length} extraction documents`
  );
  console.log(`✓ data/review-extractions.json — ${mb} MB (server-side only)`);

  const unlinked = cbas.filter((c) => !seenPdfs.has(`${c.source}/${c.filename}`));
  if (unlinked.length) {
    console.log(
      `  ! ${unlinked.length} PDF(s) had no extraction: ` +
        unlinked
          .slice(0, 5)
          .map((c) => `${c.source}/${c.filename}`)
          .join(", ")
    );
  }
}

// tsx transpiles this file to CJS, so no top-level await.
buildReviewData().catch((err) => {
  console.error("✗ review data generation failed:", err);
  process.exit(1);
});
