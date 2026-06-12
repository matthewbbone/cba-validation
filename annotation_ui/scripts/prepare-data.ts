/**
 * Run once before `npm run dev` or `npm run build`.
 * Generates:
 *   lib/cba-manifest.json       — list of all CBAs { source, filename }
 *   lib/provisions.json         — provision dictionary from CSV
 *   lib/provision-schemas.json  — format + flags per concept_id (from Python structures)
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

// ── Provision dictionary ──────────────────────────────────────────────────────
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

// ── Provision schemas (format + flags per concept_id) ─────────────────────────
const schemaScript = path.join(REPO_ROOT, "structures", "generate_ui_schema.py");
const schemaJson = execSync(`python3 "${schemaScript}"`, { cwd: REPO_ROOT }).toString();
fs.writeFileSync(path.join(LIB_DIR, "provision-schemas.json"), schemaJson);
const schemaCount = Object.keys(JSON.parse(schemaJson)).length;
console.log(`✓ provision-schemas.json — ${schemaCount} provisions`);
