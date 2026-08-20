/**
 * A block-level tokenizer for OCR'd page markdown.
 *
 * Not a markdown parser. Its one job is to produce something renderable while
 * preserving a single invariant, which is what makes a highlighted span
 * traceable back to the source file:
 *
 *     Every leaf's text is a contiguous slice of the source:
 *       src.slice(leaf.start, leaf.end) === leaf.text
 *
 * Rendering emits one element per leaf carrying `leaf.start`, so resolving a DOM
 * selection to a source offset is arithmetic rather than estimation.
 *
 * Inline emphasis is deliberately NOT parsed. Dropping `*`/`_` from the
 * displayed text would break the invariant for no real gain — the OCR output
 * barely uses inline markup.
 *
 * Pure module: no DOM, no React.
 */

export interface Leaf {
  start: number;
  end: number;
  text: string;
}

export type Block =
  /** `## ARTICLE 24` — the leaf covers only the text after the hashes. */
  | { kind: "heading"; level: number; leaf: Leaf }
  /** A run of non-blank lines. `indent` marks an OCR'd list item (`1.`, `A.`). */
  | { kind: "para"; leaf: Leaf; indent: boolean }
  /** A GFM pipe table; one leaf per cell, alignment row dropped. */
  | { kind: "table"; rows: Leaf[][] }
  /** A bare integer on its own — the printed page folio, not the file's page N. */
  | { kind: "folio"; leaf: Leaf }
  /**
   * A `--- Page N ---` separator from full.txt. Rendered as a page-break marker
   * rather than as text, and given no selectable leaf: it is scaffolding the
   * concatenation added, not contract language, so it must never end up inside a
   * highlighted span's displayed text.
   */
  | { kind: "pagebreak"; page: number; leaf: Leaf };

const HEADING = /^(#{1,6})[ \t]+/;
const PAGE_SEP = /^--- Page (\d+) ---[ \t]*$/;
const ALIGN_CELL = /^:?-{2,}:?$/;
// Ordered/lettered markers the OCR leaves as literal text at the start of a line.
const LIST_MARKER = /^(\(?[a-zA-Z0-9]{1,4}[.)]|[-*•])[ \t]/;
const FOLIO = /^\d{1,4}$/;

function isSpace(ch: string): boolean {
  return ch === " " || ch === "\t" || ch === "\r" || ch === "\n";
}

/** Trims a source range without disturbing its absolute offsets. */
function leafFrom(src: string, start: number, end: number): Leaf {
  let s = start;
  let e = end;
  while (s < e && isSpace(src[s])) s++;
  while (e > s && isSpace(src[e - 1])) e--;
  return { start: s, end: e, text: src.slice(s, e) };
}

/**
 * Splits one `|`-delimited line into cell leaves. Escaped pipes are not handled;
 * the OCR does not produce them.
 */
function parseTableRow(src: string, lineStart: number, lineEnd: number): Leaf[] | null {
  const pipes: number[] = [];
  for (let i = lineStart; i < lineEnd; i++) if (src[i] === "|") pipes.push(i);
  if (pipes.length < 2) return null;

  const cells: Leaf[] = [];
  for (let k = 0; k < pipes.length - 1; k++) {
    cells.push(leafFrom(src, pipes[k] + 1, pipes[k + 1]));
  }
  return cells;
}

interface Line {
  start: number;
  end: number; // exclusive, newline not included
  text: string;
}

function splitLines(src: string): Line[] {
  const lines: Line[] = [];
  let start = 0;
  while (start <= src.length) {
    let end = src.indexOf("\n", start);
    if (end === -1) end = src.length;
    lines.push({ start, end, text: src.slice(start, end) });
    if (end === src.length) break;
    start = end + 1;
  }
  return lines;
}

/** Emits the blocks for one chunk of consecutive non-blank lines. */
function classifyChunk(src: string, lines: Line[], out: Block[]): void {
  if (lines.length === 0) return;

  // A heading owns its line only; anything after it in the same chunk is body
  // text (the OCR usually blank-line-separates them, but not always).
  const h = HEADING.exec(lines[0].text);
  if (h) {
    const first = lines[0];
    out.push({
      kind: "heading",
      level: h[1].length,
      leaf: leafFrom(src, first.start + h[0].length, first.end),
    });
    classifyChunk(src, lines.slice(1), out);
    return;
  }

  if (lines.every((l) => l.text.trimStart().startsWith("|"))) {
    const rows: Leaf[][] = [];
    for (const l of lines) {
      const cells = parseTableRow(src, l.start, l.end);
      if (!cells) continue;
      // Drop the alignment row. The row above it is kept as a normal body row:
      // the OCR emits a separator after row 1 even when row 1 is plain data
      // (county lists, wage tables), so treating it as a header would bold data.
      if (cells.length > 0 && cells.every((c) => ALIGN_CELL.test(c.text))) continue;
      rows.push(cells);
    }
    if (rows.length > 0) {
      out.push({ kind: "table", rows });
      return;
    }
  }

  const sep = lines.length === 1 ? PAGE_SEP.exec(lines[0].text.trim()) : null;
  if (sep) {
    out.push({
      kind: "pagebreak",
      page: Number(sep[1]),
      leaf: leafFrom(src, lines[0].start, lines[0].end),
    });
    return;
  }

  if (lines.length === 1 && FOLIO.test(lines[0].text.trim())) {
    out.push({ kind: "folio", leaf: leafFrom(src, lines[0].start, lines[0].end) });
    return;
  }

  out.push({
    kind: "para",
    leaf: leafFrom(src, lines[0].start, lines[lines.length - 1].end),
    indent: LIST_MARKER.test(lines[0].text.trimStart()),
  });
}

export function parseBlocks(src: string): Block[] {
  const out: Block[] = [];
  let chunk: Line[] = [];

  for (const line of splitLines(src)) {
    if (line.text.trim() === "") {
      classifyChunk(src, chunk, out);
      chunk = [];
    } else {
      chunk.push(line);
    }
  }
  classifyChunk(src, chunk, out);

  return out.filter((b) => (b.kind === "table" ? true : b.leaf.end > b.leaf.start));
}

// ── Invariant check ───────────────────────────────────────────────────────────

export function leavesOf(blocks: Block[]): Leaf[] {
  const leaves: Leaf[] = [];
  for (const b of blocks) {
    if (b.kind === "table") for (const row of b.rows) leaves.push(...row);
    else leaves.push(b.leaf);
  }
  return leaves;
}

/** Page numbers whose separator falls inside these blocks, in order. */
export function pageBreaksOf(blocks: Block[]): number[] {
  const pages: number[] = [];
  for (const b of blocks) if (b.kind === "pagebreak") pages.push(b.page);
  return pages;
}

/**
 * Throws if any leaf is not a true slice of the source. A violation would
 * silently shift every span recorded in that block, so this runs in dev.
 */
export function assertLeafInvariant(src: string, blocks: Block[]): void {
  for (const leaf of leavesOf(blocks)) {
    if (src.slice(leaf.start, leaf.end) !== leaf.text) {
      throw new Error(
        `md-blocks: leaf [${leaf.start},${leaf.end}) is not a source slice — ` +
          `expected ${JSON.stringify(src.slice(leaf.start, leaf.end))}, ` +
          `got ${JSON.stringify(leaf.text)}`
      );
    }
  }
}

// ── Highlight runs ────────────────────────────────────────────────────────────

export interface Run {
  start: number;
  end: number;
  text: string;
  /** Index into the committed-span list, or null for unhighlighted text. */
  spanIndex: number | null;
}

/**
 * Splits a leaf at committed-span boundaries so highlighting and offset-tracking
 * share one mechanism: each run is still a pure source slice and still carries
 * its own start offset.
 *
 * Overlapping spans resolve to the lowest-indexed span covering the run.
 */
export function splitLeaf(
  leaf: Leaf,
  spans: readonly { start: number; end: number }[]
): Run[] {
  const cuts = new Set<number>([leaf.start, leaf.end]);
  let anyOverlap = false;

  for (const s of spans) {
    if (s.end <= leaf.start || s.start >= leaf.end) continue;
    anyOverlap = true;
    if (s.start > leaf.start) cuts.add(s.start);
    if (s.end < leaf.end) cuts.add(s.end);
  }

  if (!anyOverlap) {
    return [{ start: leaf.start, end: leaf.end, text: leaf.text, spanIndex: null }];
  }

  const bounds = Array.from(cuts).sort((a, b) => a - b);
  const runs: Run[] = [];

  for (let i = 0; i < bounds.length - 1; i++) {
    const a = bounds[i];
    const b = bounds[i + 1];
    if (b <= a) continue;
    const spanIndex = spans.findIndex((s) => s.start <= a && s.end >= b);
    runs.push({
      start: a,
      end: b,
      text: leaf.text.slice(a - leaf.start, b - leaf.start),
      spanIndex: spanIndex === -1 ? null : spanIndex,
    });
  }

  return runs;
}
