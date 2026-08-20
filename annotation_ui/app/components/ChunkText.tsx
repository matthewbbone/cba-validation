"use client";

import { useCallback, useMemo, useRef } from "react";
import {
  assertLeafInvariant,
  parseBlocks,
  splitLeaf,
  type Block,
  type Leaf,
} from "@/lib/md-blocks";
import type { Span } from "@/lib/types";

export interface Selection {
  start: number;
  end: number;
  text: string;
}

/**
 * Renders one chunk as block-level markdown while keeping every displayed
 * character addressable in source coordinates -- offsets here are into the
 * document's full.txt, the same coordinate system the pipeline chunked in.
 *
 * The invariant that makes this work: each element carrying `data-s` holds
 * exactly one text node, and that text is a contiguous slice of full.txt
 * starting at `data-s`. Highlighting splits a leaf into several such elements,
 * so it preserves the invariant rather than complicating it.
 *
 * `text` is the chunk, which the tokenizer necessarily indexes from 0, while
 * spans are recorded in full.txt coordinates. The leaves are shifted by `offset`
 * immediately after parsing, so everything below this line — data-s attributes,
 * splitLeaf, the resolved selection — is in absolute coordinates and there is
 * only one place where the two systems meet.
 */
export function ChunkText({
  text,
  offset,
  spans,
  activeSpanIndex,
  onSelect,
  onSpanClick,
}: {
  text: string;
  /** Where `text` begins in full.txt — the chunk's char_start. */
  offset: number;
  spans: Span[];
  activeSpanIndex: number | null;
  onSelect: (selection: Selection | null) => void;
  onSpanClick: (index: number) => void;
}) {
  const rootRef = useRef<HTMLDivElement | null>(null);

  const blocks = useMemo(() => {
    const parsed = parseBlocks(text);
    // Assert while still in the tokenizer's own 0-based coordinates, then shift.
    if (process.env.NODE_ENV !== "production") assertLeafInvariant(text, parsed);
    return shiftBlocks(parsed, offset);
  }, [text, offset]);

  const handleMouseUp = useCallback(() => {
    const root = rootRef.current;
    const sel = window.getSelection();
    if (!root || !sel || sel.rangeCount === 0 || sel.isCollapsed) {
      onSelect(null);
      return;
    }

    const range = sel.getRangeAt(0);
    if (!root.contains(range.commonAncestorContainer)) return; // selection outside the panel

    let start = Infinity;
    let end = -Infinity;

    for (const el of Array.from(root.querySelectorAll<HTMLElement>("[data-s]"))) {
      const node = el.firstChild;
      if (!node || node.nodeType !== Node.TEXT_NODE) continue;

      const clipped = clipToRange(range, node as Text);
      if (!clipped) continue;

      const base = Number(el.dataset.s);
      start = Math.min(start, base + clipped[0]);
      end = Math.max(end, base + clipped[1]);
    }

    if (!Number.isFinite(start) || !Number.isFinite(end) || end <= start) {
      onSelect(null);
      return;
    }

    // Trim the outer edges, but keep everything in between: a selection crossing
    // a block boundary records the real source range, blank line and pipes
    // included, so `text.slice(start, end)` still round-trips exactly.
    let a = Math.max(offset, start);
    let b = Math.min(offset + text.length, end);
    while (a < b && /\s/.test(text[a - offset])) a++;
    while (b > a && /\s/.test(text[b - 1 - offset])) b--;

    if (b <= a) {
      onSelect(null);
      return;
    }

    onSelect({ start: a, end: b, text: text.slice(a - offset, b - offset) });
  }, [text, offset, onSelect]);

  const renderLeaf = (leaf: Leaf) => {
    if (leaf.end <= leaf.start) return null;
    return splitLeaf(leaf, spans).map((run) => {
      if (run.spanIndex === null) {
        return (
          <span key={run.start} data-s={run.start}>
            {run.text}
          </span>
        );
      }
      const isActive = run.spanIndex === activeSpanIndex;
      return (
        <mark
          key={run.start}
          data-s={run.start}
          className={`span-hl${isActive ? " span-hl-active" : ""}`}
          title={spans[run.spanIndex]?.note || `Span ${run.spanIndex + 1}`}
          onClick={() => onSpanClick(run.spanIndex as number)}
        >
          {run.text}
        </mark>
      );
    });
  };

  return (
    <div className="ocr-page" ref={rootRef} onMouseUp={handleMouseUp}>
      {blocks.map((block, i) => renderBlock(block, i, renderLeaf))}
    </div>
  );
}

/** Re-bases every leaf from chunk-local to full.txt coordinates. */
function shiftBlocks(blocks: Block[], offset: number): Block[] {
  if (offset === 0) return blocks;
  const shift = (leaf: Leaf): Leaf => ({
    start: leaf.start + offset,
    end: leaf.end + offset,
    text: leaf.text,
  });
  return blocks.map((b) =>
    b.kind === "table"
      ? { ...b, rows: b.rows.map((row) => row.map(shift)) }
      : { ...b, leaf: shift(b.leaf) }
  );
}

function renderBlock(
  block: Block,
  i: number,
  renderLeaf: (leaf: Leaf) => React.ReactNode
): React.ReactNode {
  switch (block.kind) {
    case "heading": {
      const Tag = (block.level <= 2 ? "h3" : "h4") as "h3" | "h4";
      return <Tag key={i}>{renderLeaf(block.leaf)}</Tag>;
    }
    case "para":
      return (
        <p key={i} className={block.indent ? "ocr-indent" : undefined}>
          {renderLeaf(block.leaf)}
        </p>
      );
    case "pagebreak":
      // Scaffolding the concatenation added, not contract language: shown as a
      // rule so the annotator can see where the printed page turned, but given
      // no data-s so it can never be selected into a span.
      return (
        <div key={i} className="ocr-pagebreak" aria-label={`page ${block.page}`}>
          <span>page {block.page}</span>
        </div>
      );
    case "folio":
      return (
        <div key={i} className="ocr-folio" title="Printed page number">
          {renderLeaf(block.leaf)}
        </div>
      );
    case "table":
      return (
        <div key={i} className="ocr-table-wrap">
          <table className="ocr-table">
            <tbody>
              {block.rows.map((row, r) => (
                <tr key={r}>
                  {row.map((cell, c) => (
                    <td key={c}>{renderLeaf(cell)}</td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      );
  }
}

/**
 * Intersects a selection range with one text node, in the node's own
 * coordinates. Returns null when they do not overlap.
 *
 * `comparePoint` tells us where each end of the node sits relative to the range;
 * a boundary that falls outside the node is only usable when the range's own
 * container *is* this node, which is what distinguishes a real partial overlap
 * from a range that merely touches the node's edge.
 */
function clipToRange(range: Range, node: Text): [number, number] | null {
  const len = node.data.length;
  if (len === 0) return null;

  let startCmp: number;
  let endCmp: number;
  try {
    startCmp = range.comparePoint(node, 0);
    endCmp = range.comparePoint(node, len);
  } catch {
    return null; // node is not comparable with this range
  }

  if (startCmp > 0 || endCmp < 0) return null; // wholly after / before the range

  const a = startCmp < 0 ? (range.startContainer === node ? range.startOffset : len) : 0;
  const b = endCmp > 0 ? (range.endContainer === node ? range.endOffset : 0) : len;

  return b > a ? [a, b] : null;
}
