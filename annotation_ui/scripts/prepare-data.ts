/**
 * DORMANT — kept for the recipe, not part of the current workflow.
 *
 * The app no longer reads anything this script generates. The span-annotation
 * flow reads stg_01_ocr/ and results/tier_1_concepts.md directly at request time
 * (see lib/ocr.ts), so there is no build step to run before `npm run dev`.
 *
 * What it still knows how to build, if the inputs ever come back:
 *   lib/cba-manifest.json      — { source, filename } for every PDF in data/cbas/
 *   lib/provisions.json        — the provision dictionary, from CSV
 *   lib/provision-schemas.json — format + flags per concept_id, via Python
 *
 * All three files are still committed under lib/ but are imported by nothing.
 * Their input trees (data/cbas, data/cba_meta, structures/) were removed from the
 * repo, so every stage below now skips with a notice rather than crashing.
 *
 * The review-data stage that used to live here was removed along with the
 * extraction-review tab.
 *
 * Usage:  npx tsx scripts/prepare-data.ts
 */

import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";
import { execSync } from "child_process";
import Papa from "papaparse";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const REPO_ROOT = path.resolve(__dirname, "../..");
const CBAS_DIR = path.join(REPO_ROOT, "data", "cbas");
const DICT_PATH = path.join(REPO_ROOT, "data", "cba_meta", "cba_provision_dictionary.csv");
const LIB_DIR = path.join(__dirname, "..", "lib");

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
