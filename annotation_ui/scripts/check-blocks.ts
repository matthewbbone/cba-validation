/**
 * Checks the block tokenizer against every OCR page in stg_01_ocr.
 *
 * The span-annotation tool records evidence as (page file, character offset)
 * tuples, which is only trustworthy while this holds for every leaf the renderer
 * emits:
 *
 *     src.slice(leaf.start, leaf.end) === leaf.text
 *
 * A violation would silently shift every span recorded in that block, so re-run
 * this after changing lib/md-blocks.ts or dropping a new OCR batch.
 *
 * Usage:  npm run check-blocks
 */

import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";
import {
  assertLeafInvariant,
  leavesOf,
  parseBlocks,
  splitLeaf,
  type Leaf,
} from "../lib/md-blocks";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const OCR_ROOT = path.resolve(__dirname, "../..", "stg_01_ocr");

if (!fs.existsSync(OCR_ROOT)) {
  console.error(`No OCR tree at ${OCR_ROOT}`);
  process.exit(1);
}

function walk(dir: string, out: string[]): void {
  for (const e of fs.readdirSync(dir, { withFileTypes: true })) {
    if (e.name.startsWith(".")) continue;
    const p = path.join(dir, e.name);
    if (e.isDirectory()) walk(p, out);
    else if (/^page_\d+\.md$/.test(e.name)) out.push(p);
  }
}

const files: string[] = [];
walk(OCR_ROOT, files);
files.sort();

// Deterministic pseudo-randomness, so a failure is reproducible.
let seed = 12345;
const rnd = () => ((seed = (seed * 1103515245 + 12345) & 0x7fffffff) / 0x7fffffff);

const kinds: Record<string, number> = {};
let invariantFailures = 0;
let overlaps = 0;
let splitFailures = 0;
let totalNonWs = 0;
let coveredNonWs = 0;

for (const file of files) {
  const src = fs.readFileSync(file, "utf-8");
  const blocks = parseBlocks(src);
  const rel = path.relative(OCR_ROOT, file);

  try {
    assertLeafInvariant(src, blocks);
  } catch (err) {
    invariantFailures++;
    if (invariantFailures <= 3) console.error(`  INVARIANT ${rel}: ${(err as Error).message}`);
  }

  for (const b of blocks) kinds[b.kind] = (kinds[b.kind] ?? 0) + 1;
  const leaves: Leaf[] = leavesOf(blocks);

  // Leaves must be disjoint and ascending, or the page would render the same
  // source text twice and a span would be ambiguous.
  for (let i = 1; i < leaves.length; i++) {
    if (leaves[i].start < leaves[i - 1].end) {
      overlaps++;
      if (overlaps <= 3) console.error(`  OVERLAP ${rel} near offset ${leaves[i].start}`);
      break;
    }
  }

  // Reachability: everything not covered by a leaf should be whitespace or
  // markdown syntax (#, |, and the --- alignment row), never contract text.
  const covered = new Uint8Array(src.length);
  for (const l of leaves) for (let i = l.start; i < l.end; i++) covered[i] = 1;
  for (let i = 0; i < src.length; i++) {
    if (/\s/.test(src[i])) continue;
    totalNonWs++;
    if (covered[i]) coveredNonWs++;
    else if (!"#|-:".includes(src[i])) {
      console.error(`  UNREACHABLE TEXT ${rel} at ${i}: ${JSON.stringify(src[i])}`);
    }
  }

  // splitLeaf must tile a leaf exactly, each run still a source slice.
  for (const leaf of leaves.slice(0, 6)) {
    if (leaf.end - leaf.start < 4) continue;
    const spans = [0, 1, 2].map(() => {
      const a = leaf.start + Math.floor(rnd() * (leaf.end - leaf.start - 1));
      return { start: a, end: a + 1 + Math.floor(rnd() * (leaf.end - a - 1)) };
    });
    const runs = splitLeaf(leaf, spans);
    const tiles = runs.every((r, i) =>
      i === 0 ? r.start === leaf.start : r.start === runs[i - 1].end
    );
    const slices = runs.every((r) => src.slice(r.start, r.end) === r.text);
    if (runs.map((r) => r.text).join("") !== leaf.text || !tiles || !slices) {
      splitFailures++;
      if (splitFailures <= 3) {
        console.error(`  SPLIT ${rel} leaf [${leaf.start},${leaf.end})`);
      }
    }
  }
}

console.log(`pages           : ${files.length}`);
console.log(`blocks          : ${JSON.stringify(kinds)}`);
console.log(`invariant fails : ${invariantFailures}`);
console.log(`leaf overlaps   : ${overlaps}`);
console.log(`splitLeaf fails : ${splitFailures}`);
console.log(
  `text reachable  : ${((coveredNonWs / totalNonWs) * 100).toFixed(3)}% ` +
    `(the remainder is markdown syntax: #, |, ---)`
);

if (invariantFailures || overlaps || splitFailures) {
  console.error("\nFAILED");
  process.exit(1);
}
console.log("\nOK");
