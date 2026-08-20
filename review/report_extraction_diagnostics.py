#!/usr/bin/env python3
"""Build an HTML diagnostics report on extraction consistency across runs.

Reads the provisions aggregate and emits a single self-contained HTML file with
inline SVG figures. No external assets, no JavaScript, no plotting library —
stdlib only, deterministic apart from the timestamp.

    python scripts/report_extraction_diagnostics.py
    python scripts/report_extraction_diagnostics.py --out /tmp/report.html

The report's subject is *unintended* variation: each run is a separate batch of
agentic extractions given the same instructions, so differences between runs in
vocabulary, key names, and yield are properties of the pipeline rather than of
the contracts. Figures are chosen to separate that from real content signal.
"""

from __future__ import annotations

import argparse
import gzip
import json
import html
import math
import os
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

# ── Palette ───────────────────────────────────────────────────────────────────
# Validated with the dataviz validator: 3 slots pass all-pairs in both modes;
# 6 slots pass adjacent (stacked bars) in both modes. Light-mode aqua/yellow/
# magenta sit under 3:1 on the light surface, so every figure ships visible
# labels and a table view — that is the required relief, not an optional extra.
SERIES_LIGHT = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300"]
SERIES_DARK = ["#3987e5", "#d95926", "#199e70", "#c98500", "#d55181", "#008300"]
# Sequential blue, light→dark (magnitude encoding only).
SEQ_LIGHT = ["#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95"]
SEQ_DARK = ["#184f95", "#1c5cab", "#256abf", "#3987e5", "#5598e7", "#86b6ef"]

TIERS = ["core", "controlled", "drift"]
TIER_LABEL = {
    "core": "Core tier",
    "controlled": "Other controlled",
    "drift": "Off-dictionary drift",
}

PROVENANCE_ORDER = [
    "cba_contained",
    "externalized_recoverable",
    "externalized_offpage",
    "source_gap",
    "not_applicable",
    "absent",
]

RUN_ORDER = [
    "run200_2026-06",
    "run_next50_2026-06",
    "run_next100_2026-06",
    "run_next150_2026-06",
    "run_next498_2026-06",
    "run_cornell_dol_2026-06",
    "run_cornell_dol2_2026-06",
    "run_cornell_dol3_2026-06",
    "run_cornell_dol4_2026-06",
    "run_dol_textlayer_2026-07",
    "run_retailed500_2026-07",
    "run_retailed_tail79_2026-07",
]

SHORT_AREAS = {"Security", "Recognition", "Disputes", "Ancillary"}
LONG_AREAS = {"Job Security", "Union Recognition", "Dispute Resolution", "Ancillary benefits"}

RETAILED_PART = re.compile(r"_\d+\.pdf$")


# ── Collection ────────────────────────────────────────────────────────────────


def load_tiers(schema_path: Path):
    """concept_id → tier, from the UI provision schema when it is available.

    Falls back to the aggregate's own `concept_reporting_class` if the schema is
    missing, so the script still runs standalone; the fallback is coarser (39
    concepts are flagged required_core against the schema's 15 core-tier).
    """
    if not schema_path.is_file():
        return None, "concept_reporting_class == 'required_core' (schema file not found)"
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    tiers = {}
    for cid, meta in schema.items():
        tier = (meta.get("meta") or {}).get("priority_tier")
        tiers[cid] = "core" if tier == "core" else "controlled"
    return tiers, f"{schema_path.name} priority_tier"


def collect(agg_path: Path, tiers):
    """One streaming pass over the aggregate, gathering every figure's inputs."""
    s = {
        "n_docs": 0,
        "runs": Counter(),
        "concept_records": Counter(),  # concept_id → n records
        "field_names": defaultdict(set),  # concept_id → distinct field_name
        "cf_keys": defaultdict(Counter),  # run → key → n rows
        "cr_keys": defaultdict(Counter),
        "cf_rows": Counter(),
        "cr_rows": Counter(),
        "dc_rows": Counter(),
        "measurement_status": defaultdict(set),
        "support_status": defaultdict(set),
        "field_unit": defaultdict(set),
        "provenance": defaultdict(Counter),
        "category_conv": defaultdict(Counter),  # run → short/long
        "yield_records": defaultdict(list),
        "yield_fields": defaultdict(list),
        "offdict_docs": Counter(),
        "core_missing_docs": Counter(),
        "by_file": defaultdict(list),
        "required_core": set(),
    }

    with gzip.open(agg_path, "rt", encoding="utf-8") as fh:
        for line in fh:
            if not line.strip():
                continue
            d = json.loads(line)
            run = d["run"]
            s["n_docs"] += 1
            s["runs"][run] += 1

            meta = d.get("metadata") or {}
            filename = meta.get("filename")
            if not filename:
                members = meta.get("_member_cba_ids") or []
                if members:
                    filename = re.sub(r"^Cornell_RetailEd_", "", RETAILED_PART.sub("", members[0]))

            doc_concepts = set()
            for r in d["concept_records"]:
                s["cr_rows"][run] += 1
                s["cr_keys"][run].update(r.keys())
                cid = r.get("concept_id")
                s["concept_records"][cid] += 1
                doc_concepts.add(cid)
                if r.get("measurement_status") is not None:
                    s["measurement_status"][run].add(str(r["measurement_status"]))
                if r.get("concept_reporting_class") == "required_core":
                    s["required_core"].add(cid)

            for f in d["concept_fields"]:
                s["cf_rows"][run] += 1
                s["cf_keys"][run].update(f.keys())
                cid = f.get("concept_id")
                doc_concepts.add(cid)
                s["field_names"][cid].add(f.get("field_name"))
                if f.get("support_status") is not None:
                    s["support_status"][run].add(str(f["support_status"]))
                if f.get("field_unit") is not None:
                    s["field_unit"][run].add(str(f["field_unit"]))

            for row in d["dimension_coverage"]:
                s["dc_rows"][run] += 1
                s["provenance"][run][row.get("provenance")] += 1
                cat = row.get("category_as_recorded")
                if cat in SHORT_AREAS:
                    s["category_conv"][run]["short"] += 1
                elif cat in LONG_AREAS:
                    s["category_conv"][run]["long"] += 1

            s["yield_records"][run].append(len(d["concept_records"]))
            s["yield_fields"][run].append(len(d["concept_fields"]))
            if tiers is not None and any(c not in tiers for c in doc_concepts if c):
                s["offdict_docs"][run] += 1
            if filename:
                s["by_file"][filename].append(
                    (run, d["document_id"], len(d["concept_records"]), len(d["concept_fields"]))
                )
    return s


def tier_of(cid, tiers, required_core):
    if tiers is None:
        return "core" if cid in required_core else "drift"
    return tiers.get(cid, "drift")


# ── SVG primitives ────────────────────────────────────────────────────────────

BAR_R = 4  # rounded data-end radius
GAP = 2  # surface gap between adjacent/stacked marks


def esc(t):
    return html.escape(str(t), quote=True)


def bar_path(x, y, w, h, r=BAR_R):
    """Horizontal bar: square at the baseline, rounded at the data end."""
    r = max(0, min(r, w, h / 2))
    if r <= 0 or w <= 0:
        return f'M{x:.1f},{y:.1f} h{max(w,0):.1f} v{h:.1f} h{-max(w,0):.1f} Z'
    return (
        f"M{x:.1f},{y:.1f} h{w - r:.1f} a{r},{r} 0 0 1 {r},{r} "
        f"v{h - 2 * r:.1f} a{r},{r} 0 0 1 {-r},{r} h{-(w - r):.1f} Z"
    )


def svg_open(w, h, label):
    return (
        f'<svg viewBox="0 0 {w} {h}" width="100%" height="{h}" role="img" '
        f'aria-label="{esc(label)}" preserveAspectRatio="xMinYMin meet" '
        f'style="max-width:{w}px">'
    )


def axis_ticks(vmax, n=4):
    """Nice round ticks from 0 to >= vmax."""
    if vmax <= 0:
        return [0], 1
    raw = vmax / n
    mag = 10 ** math.floor(math.log10(raw))
    step = next((m * mag for m in (1, 2, 2.5, 5, 10) if m * mag >= raw), 10 * mag)
    top = math.ceil(vmax / step) * step
    return [i * step for i in range(int(top / step) + 1)], top


CHAR_W = 5.8  # approx advance width of the 11px row-label face


def gutter(labels, minimum=210):
    """Label gutter wide enough for the longest label, so nothing collides."""
    longest = max((len(str(x)) for x in labels), default=0)
    return max(minimum, int(longest * CHAR_W) + 22)


def grouped_hbar(rows, series, colors, label, fmt=lambda v: f"{v:,.0f}", row_h=None):
    """rows: [(label, [v1, v2, ...])]. One group per row, one bar per series."""
    lab_w, pad_r, top, bot = gutter([r[0] for r in rows]), 60, 30, 30
    nser = len(series)
    bar_h = 11 if nser > 1 else 15
    row_h = row_h or (nser * (bar_h + GAP) + 12)
    h = top + len(rows) * row_h + bot
    plot_w = 620
    w = lab_w + plot_w + pad_r
    vmax = max((max(v) for _, v in rows), default=0)
    ticks, top_v = axis_ticks(vmax)
    sx = (lambda v: plot_w * v / top_v) if top_v else (lambda v: 0)

    out = [svg_open(w, h, label)]
    for t in ticks:  # recessive grid
        x = lab_w + sx(t)
        out.append(f'<line x1="{x:.1f}" y1="{top-6}" x2="{x:.1f}" y2="{h-bot}" class="grid"/>')
        out.append(f'<text x="{x:.1f}" y="{top-12}" class="tick mid">{fmt(t)}</text>')
    for i, (name, vals) in enumerate(rows):
        y0 = top + i * row_h + 6
        out.append(
            f'<text x="{lab_w-10}" y="{y0 + nser*(bar_h+GAP)/2 + 1}" class="rowlab end">{esc(name)}</text>'
        )
        for j, v in enumerate(vals):
            y = y0 + j * (bar_h + GAP)
            bw = sx(v)
            out.append(
                f'<path d="{bar_path(lab_w, y, bw, bar_h)}" fill="{colors[j]}">'
                f"<title>{esc(name)} — {esc(series[j])}: {fmt(v)}</title></path>"
            )
            out.append(
                f'<text x="{lab_w + bw + 6:.1f}" y="{y + bar_h - 2}" class="val">{fmt(v)}</text>'
            )
    out.append(f'<line x1="{lab_w}" y1="{top-6}" x2="{lab_w}" y2="{h-bot}" class="axis"/>')
    out.append("</svg>")
    return "".join(out)


def stacked_hbar(rows, series, colors, label, pct=True):
    """rows: [(label, [v1..vn])] rendered as 100% stacked with a 2px surface gap."""
    lab_w, pad_r, top, bot = gutter([r[0] for r in rows]), 30, 30, 26
    bar_h, row_h = 18, 26
    plot_w = 620
    w = lab_w + plot_w + pad_r
    h = top + len(rows) * row_h + bot
    out = [svg_open(w, h, label)]
    for i, (name, vals) in enumerate(rows):
        total = sum(vals) or 1
        y = top + i * row_h
        out.append(f'<text x="{lab_w-10}" y="{y+bar_h-4}" class="rowlab end">{esc(name)}</text>')
        x = float(lab_w)
        for j, v in enumerate(vals):
            seg = plot_w * v / total
            if seg <= 0:
                continue
            draw = max(seg - GAP, 0.6)
            share = 100 * v / total
            out.append(
                f'<rect x="{x:.1f}" y="{y}" width="{draw:.1f}" height="{bar_h}" fill="{colors[j]}">'
                f"<title>{esc(name)} — {esc(series[j])}: {v:,} ({share:.1f}%)</title></rect>"
            )
            if seg > 46:  # direct label where it fits — required relief on light
                out.append(
                    f'<text x="{x + draw/2:.1f}" y="{y+bar_h-5}" class="seglab">{share:.0f}%</text>'
                )
            x += seg
    out.append("</svg>")
    return "".join(out)


def heatmap(row_labels, col_labels, values, label, colors):
    """values[r][c] as a percentage 0–100. Sequential single hue, more = darker."""
    lab_w, top, cell_w, cell_h = gutter(row_labels), 118, 34, 20
    w = lab_w + len(col_labels) * cell_w + 40
    h = top + len(row_labels) * cell_h + 20

    def step(p):
        if p <= 0:
            return None
        idx = min(len(colors) - 1, int(p / 100 * len(colors)))
        return colors[idx]

    out = [svg_open(w, h, label)]
    for c, cl in enumerate(col_labels):
        x = lab_w + c * cell_w + cell_w / 2
        out.append(
            f'<text x="{x:.1f}" y="{top-8}" class="tick mid" '
            f'transform="rotate(-55 {x:.1f} {top-8})">{esc(cl)}</text>'
        )
    for r, rl in enumerate(row_labels):
        y = top + r * cell_h
        out.append(f'<text x="{lab_w-10}" y="{y+cell_h-6}" class="rowlab end">{esc(rl)}</text>')
        for c, cl in enumerate(col_labels):
            p = values[r][c]
            fill = step(p)
            x = lab_w + c * cell_w
            body = (
                f'<rect x="{x+1}" y="{y+1}" width="{cell_w-2-GAP}" height="{cell_h-2-GAP}" '
                f'rx="2" fill="{fill or "none"}" class="{"" if fill else "cell-empty"}">'
                f"<title>{esc(rl)} · {esc(cl)}: {p:.0f}% of rows</title></rect>"
            )
            out.append(body)
    out.append("</svg>")
    return "".join(out)


def dumbbell(rows, colors, label, series=("Run A", "Run B")):
    """rows: [(label, a, b)] — one item, two runs. Before→after per item."""
    lab_w, pad_r, top, bot = gutter([r[0] for r in rows], 250), 50, 30, 26
    row_h = 20
    plot_w = 560
    w = lab_w + plot_w + pad_r
    h = top + len(rows) * row_h + bot
    vmax = max((max(a, b) for _, a, b in rows), default=1)
    ticks, top_v = axis_ticks(vmax)
    sx = lambda v: lab_w + plot_w * v / top_v
    out = [svg_open(w, h, label)]
    for t in ticks:
        out.append(f'<line x1="{sx(t):.1f}" y1="{top-6}" x2="{sx(t):.1f}" y2="{h-bot}" class="grid"/>')
        out.append(f'<text x="{sx(t):.1f}" y="{top-12}" class="tick mid">{t:,.0f}</text>')
    for i, (name, a, b) in enumerate(rows):
        y = top + i * row_h + row_h / 2
        out.append(f'<text x="{lab_w-10}" y="{y+3}" class="rowlab end">{esc(name)}</text>')
        out.append(
            f'<line x1="{sx(a):.1f}" y1="{y:.1f}" x2="{sx(b):.1f}" y2="{y:.1f}" class="connector"/>'
        )
        for v, col, nm in ((a, colors[0], series[0]), (b, colors[1], series[1])):
            out.append(f'<circle cx="{sx(v):.1f}" cy="{y:.1f}" r="4.5" fill="{col}" class="dot"/>')
            # Transparent hit target — a 9px dot is too small to land on.
            out.append(
                f'<circle cx="{sx(v):.1f}" cy="{y:.1f}" r="12" fill="transparent">'
                f"<title>{esc(name)} — {esc(nm)}: {v:,}</title></circle>"
            )
        out.append(f'<text x="{lab_w+plot_w+8}" y="{y+3}" class="val">{a:,}→{b:,}</text>')
    out.append("</svg>")
    return "".join(out)


# ── HTML assembly ─────────────────────────────────────────────────────────────


def scale_legend(colors, lo="0%", hi="100% of rows"):
    """Sequential ramp key — darkness is magnitude, so the reader needs the direction."""
    swatches = "".join(f'<i style="background:{c}"></i>' for c in colors)
    return (f'<div class="legend"><span class="lg">{esc(lo)}</span>'
            f'<span class="ramp">{swatches}</span>'
            f'<span class="lg">{esc(hi)}</span>'
            f'<span class="lg">· blank = key absent from that run</span></div>')


def legend(series, colors):
    items = "".join(
        f'<span class="lg"><i style="background:{c}"></i>{esc(s)}</span>'
        for s, c in zip(series, colors)
    )
    return f'<div class="legend">{items}</div>'


def table(headers, rows):
    head = "".join(f"<th>{esc(h)}</th>" for h in headers)
    body = "".join(
        "<tr>" + "".join(f"<td>{esc(c)}</td>" for c in r) + "</tr>" for r in rows
    )
    return (
        "<details><summary>Table view</summary>"
        f"<div class='tw'><table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table></div>"
        "</details>"
    )


def figure(num, title, blurb, svg_light, svg_dark, legend_html="", table_html=""):
    return f"""
<figure class="fig">
  <figcaption><span class="fignum">Figure {num}</span> {esc(title)}</figcaption>
  <p class="blurb">{blurb}</p>
  {legend_html}
  <div class="plot light-only">{svg_light}</div>
  <div class="plot dark-only">{svg_dark}</div>
  {table_html}
</figure>"""


def kpi(value, label, note=""):
    return (
        f'<div class="kpi"><div class="kpi-v">{esc(value)}</div>'
        f'<div class="kpi-l">{esc(label)}</div>'
        f'<div class="kpi-n">{esc(note)}</div></div>'
    )


CSS = """
:root{color-scheme:light;--surface:#fcfcfb;--plane:#f9f9f7;--ink:#0b0b0b;--ink2:#52514e;
--muted:#898781;--grid:#e1e0d9;--axis:#c3c2b7;--border:rgba(11,11,11,.10);--warn:#b45309}
@media (prefers-color-scheme:dark){:root:not([data-theme=light]){color-scheme:dark;
--surface:#1a1a19;--plane:#0d0d0d;--ink:#fff;--ink2:#c3c2b7;--muted:#898781;
--grid:#2c2c2a;--axis:#383835;--border:rgba(255,255,255,.10);--warn:#fab219}}
:root[data-theme=dark]{color-scheme:dark;--surface:#1a1a19;--plane:#0d0d0d;--ink:#fff;
--ink2:#c3c2b7;--muted:#898781;--grid:#2c2c2a;--axis:#383835;--border:rgba(255,255,255,.10);--warn:#fab219}
*{box-sizing:border-box}
body{margin:0;background:var(--plane);color:var(--ink);
font-family:system-ui,-apple-system,"Segoe UI",sans-serif;line-height:1.5;font-size:15px}
.wrap{max-width:1000px;margin:0 auto;padding:2.5rem 1.25rem 4rem}
h1{font-size:1.6rem;margin:0 0 .35rem}
h2{font-size:1.05rem;margin:2.5rem 0 .5rem;padding-top:1.25rem;border-top:1px solid var(--border)}
.sub{color:var(--ink2);margin:0 0 1.5rem}
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:.6rem;margin:1.5rem 0}
.kpi{background:var(--surface);border:1px solid var(--border);border-radius:10px;padding:.8rem .9rem}
.kpi-v{font-size:1.55rem;font-weight:650;letter-spacing:-.02em}
.kpi-l{font-size:.75rem;color:var(--ink2);margin-top:.1rem}
.kpi-n{font-size:.68rem;color:var(--muted);margin-top:.15rem}
.fig{margin:0 0 2rem;background:var(--surface);border:1px solid var(--border);
border-radius:12px;padding:1.1rem 1.2rem 1rem}
figcaption{font-weight:600;font-size:.95rem;margin-bottom:.3rem}
.fignum{color:var(--muted);font-weight:600;font-size:.72rem;text-transform:uppercase;
letter-spacing:.06em;margin-right:.5rem}
.blurb{color:var(--ink2);font-size:.84rem;margin:0 0 .8rem}
.blurb code,.tw code{font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:.92em}
.plot{overflow-x:auto;margin:.2rem 0}
.legend{display:flex;flex-wrap:wrap;gap:.85rem;margin:.1rem 0 .7rem}
.lg{display:inline-flex;align-items:center;gap:.35rem;font-size:.76rem;color:var(--ink2)}
.lg i{width:11px;height:11px;border-radius:3px;display:inline-block}
.ramp{display:inline-flex;gap:1px}
.ramp i{width:20px;height:11px;border-radius:2px;display:inline-block}
text{font-family:system-ui,-apple-system,sans-serif}
.tick{font-size:10px;fill:var(--muted);font-variant-numeric:tabular-nums}
.mid{text-anchor:middle}.end{text-anchor:end}
.rowlab{font-size:11px;fill:var(--ink2)}
.val{font-size:10px;fill:var(--muted);font-variant-numeric:tabular-nums}
.seglab{font-size:9.5px;fill:#fff;text-anchor:middle;font-weight:600}
.grid{stroke:var(--grid);stroke-width:1}
.axis{stroke:var(--axis);stroke-width:1}
.connector{stroke:var(--axis);stroke-width:2}
.dot{stroke:var(--surface);stroke-width:2}
.cell-empty{fill:var(--grid);opacity:.4}
details{margin-top:.6rem}
summary{cursor:pointer;font-size:.78rem;color:var(--ink2)}
.tw{overflow-x:auto;margin-top:.5rem}
table{border-collapse:collapse;font-size:.76rem;width:100%}
th,td{text-align:left;padding:.28rem .55rem;border-bottom:1px solid var(--border);
white-space:nowrap;font-variant-numeric:tabular-nums}
th{color:var(--ink2);font-weight:600}
.note{background:var(--surface);border:1px solid var(--border);border-left:3px solid var(--warn);
border-radius:8px;padding:.7rem .9rem;font-size:.82rem;color:var(--ink2);margin:1rem 0}
footer{color:var(--muted);font-size:.75rem;margin-top:2.5rem;padding-top:1rem;
border-top:1px solid var(--border)}
.dark-only{display:none}
@media (prefers-color-scheme:dark){:root:not([data-theme=light]) .light-only{display:none}
:root:not([data-theme=light]) .dark-only{display:block}}
:root[data-theme=dark] .light-only{display:none}
:root[data-theme=dark] .dark-only{display:block}
"""


def build(s, tiers, tier_source, agg_path):
    figs = []
    L, D = SERIES_LIGHT, SERIES_DARK
    runs = [r for r in RUN_ORDER if r in s["runs"]] + sorted(set(s["runs"]) - set(RUN_ORDER))
    short = [re.sub(r"^run_", "", re.sub(r"_?2026-\d+$", "", r)) for r in runs]

    concepts = s["concept_records"]
    ctier = {c: tier_of(c, tiers, s["required_core"]) for c in concepts}

    # ── Fig 1: vocabulary by frequency band × tier ────────────────────────────
    bands = [(1, 1, "1 record"), (2, 9, "2–9"), (10, 49, "10–49"),
             (50, 999, "50–999"), (1000, 10**9, "1,000+")]
    rows1 = []
    for lo, hi, lab in bands:
        counts = [sum(1 for c, n in concepts.items() if lo <= n <= hi and ctier[c] == t)
                  for t in TIERS]
        rows1.append((lab, counts))
    figs.append(figure(
        1, "Concept vocabulary by frequency band and tier",
        "Each bar counts <em>distinct concept_ids</em>, not records. The controlled vocabulary "
        "and the drift tail occupy opposite ends: core and other controlled concepts sit almost "
        "entirely above 1,000 records, while off-dictionary ids are overwhelmingly singletons. "
        "A concept seen once in 7,044 documents is a naming accident, not a measurement object.",
        grouped_hbar(rows1, [TIER_LABEL[t] for t in TIERS], L[:3], "Concept vocabulary by band"),
        grouped_hbar(rows1, [TIER_LABEL[t] for t in TIERS], D[:3], "Concept vocabulary by band"),
        legend([TIER_LABEL[t] for t in TIERS], L[:3]),
        table(["Frequency band"] + [TIER_LABEL[t] for t in TIERS],
              [[lab] + [f"{v:,}" for v in vals] for lab, vals in rows1]),
    ))

    # ── Fig 2: top concepts, coloured by tier ────────────────────────────────
    top = concepts.most_common(22)
    rows2 = [(c, [n]) for c, n in top]
    def top_svg(pal):
        cols = [pal[TIERS.index(ctier[c])] for c, _ in top]
        parts, lab_w, plot_w, top_pad, row_h = [], gutter([c for c, _ in top], 250), 560, 30, 17
        h = top_pad + len(top) * row_h + 26
        vmax = max(n for _, n in top)
        ticks, tv = axis_ticks(vmax)
        parts.append(svg_open(lab_w + plot_w + 60, h, "Top concepts by record count"))
        for t in ticks:
            x = lab_w + plot_w * t / tv
            parts.append(f'<line x1="{x:.1f}" y1="{top_pad-6}" x2="{x:.1f}" y2="{h-26}" class="grid"/>')
            parts.append(f'<text x="{x:.1f}" y="{top_pad-12}" class="tick mid">{t:,.0f}</text>')
        for i, (c, n) in enumerate(top):
            y = top_pad + i * row_h
            bw = plot_w * n / tv
            parts.append(f'<text x="{lab_w-10}" y="{y+10}" class="rowlab end">{esc(c)}</text>')
            parts.append(
                f'<path d="{bar_path(lab_w, y, bw, 12)}" fill="{cols[i]}">'
                f"<title>{esc(c)} — {TIER_LABEL[ctier[c]]}: {n:,} records</title></path>"
            )
            parts.append(f'<text x="{lab_w+bw+6:.1f}" y="{y+10}" class="val">{n:,}</text>')
        parts.append(f'<line x1="{lab_w}" y1="{top_pad-6}" x2="{lab_w}" y2="{h-26}" class="axis"/>')
        parts.append("</svg>")
        return "".join(parts)
    figs.append(figure(
        2, "The 22 most-recorded concepts, coloured by tier",
        "Colour is the tier, length is the record count. The head of the distribution is entirely "
        "controlled vocabulary — the drift ids never reach it.",
        top_svg(L), top_svg(D),
        legend([TIER_LABEL[t] for t in TIERS], L[:3]),
        table(["concept_id", "Tier", "Records"],
              [[c, TIER_LABEL[ctier[c]], f"{n:,}"] for c, n in top]),
    ))

    # ── Fig 3: key-space size per run ────────────────────────────────────────
    rows3 = [(sh, [len(s["cf_keys"][r]), len(s["cr_keys"][r])]) for r, sh in zip(runs, short)]
    cf_n = [len(s["cf_keys"][r]) for r in runs]
    cr_n = [len(s["cr_keys"][r]) for r in runs]
    figs.append(figure(
        3, "Distinct keys per run",
        "Every run received the same extraction instructions. <code>concept_fields</code> key "
        f"counts still range from {min(cf_n)} to {max(cf_n)} — an order of magnitude of schema "
        f"invented per batch. <code>concept_records</code> stays tighter but still spans "
        f"{min(cr_n)} to {max(cr_n)}. This is the clearest single measure of unintended "
        "run-to-run variation. Counted on the aggregate's normalised rows, where known aliases "
        "have already been coalesced, so it <em>understates</em> the raw source drift.",
        grouped_hbar(rows3, ["concept_fields keys", "concept_records keys"], [L[0], L[1]], "Keys per run"),
        grouped_hbar(rows3, ["concept_fields keys", "concept_records keys"], [D[0], D[1]], "Keys per run"),
        legend(["concept_fields keys", "concept_records keys"], [L[0], L[1]]),
        table(["Run", "concept_fields keys", "concept_records keys", "Documents"],
              [[r, len(s["cf_keys"][r]), len(s["cr_keys"][r]), f'{s["runs"][r]:,}'] for r in runs]),
    ))

    # ── Fig 4: key presence heatmap ──────────────────────────────────────────
    key_tot = Counter()
    for r in runs:
        key_tot.update(s["cf_keys"][r])
    hot = [k for k, _ in key_tot.most_common(20)]
    vals4 = [[100 * s["cf_keys"][r][k] / max(1, s["cf_rows"][r]) for r in runs] for k in hot]
    figs.append(figure(
        4, "concept_fields key presence — share of each run's rows",
        "Rows are the 20 commonest keys, columns are runs, cell darkness is the share of that "
        "run's field rows carrying the key. A blank cell means the batch never emitted the key at "
        "all. Only the top band is solid across every column; below it, presence is a property of "
        "the batch rather than of the contract — which is why a key's absence cannot be read as a "
        "provision's absence.",
        heatmap(hot, short, vals4, "Key presence by run", SEQ_LIGHT),
        heatmap(hot, short, vals4, "Key presence by run", SEQ_DARK),
        scale_legend(SEQ_LIGHT),
        table(["Key"] + short, [[k] + [f"{v:.0f}%" for v in row] for k, row in zip(hot, vals4)]),
    ))

    # ── Fig 5: field_name cardinality ────────────────────────────────────────
    card = sorted(((c, len(s["field_names"][c])) for c in s["field_names"] if c),
                  key=lambda kv: -kv[1])[:14]
    rows5 = [(c, [n]) for c, n in card]
    figs.append(figure(
        5, "Distinct field_name spellings per concept",
        "<code>field_name</code> is not a controlled vocabulary. Under a single concept it reaches "
        f"{card[0][1]:,} distinct values, because the extractor routinely used the field name "
        "to carry a job classification (<code>journeyman_hourly_rate</code>, "
        "<code>foreman_differential</code>, <code>rate_eff_7_1_79</code>) rather than a stable "
        "slot. Filtering on any one spelling therefore selects almost nothing.",
        grouped_hbar(rows5, ["distinct field_name"], [L[0]], "field_name cardinality"),
        grouped_hbar(rows5, ["distinct field_name"], [D[0]], "field_name cardinality"),
        "",
        table(["concept_id", "Distinct field_name", "Records"],
              [[c, f"{n:,}", f'{concepts[c]:,}'] for c, n in card]),
    ))

    # ── Fig 6: status vocabulary size per run ────────────────────────────────
    rows6 = [(sh, [len(s["support_status"][r]), len(s["measurement_status"][r])])
             for r, sh in zip(runs, short)]
    ss_max = max(len(s["support_status"][r]) for r in runs)
    ms_max = max(len(s["measurement_status"][r]) for r in runs)
    figs.append(figure(
        6, "Distinct status values per run (documented: 2 and 6)",
        "<code>support_status</code> is specified as two values and <code>measurement_status</code> "
        f"as six. Observed counts reach {ss_max} and {ms_max} in a single batch — free-text "
        "variants such as <code>not_supported_external_trust</code> or "
        "<code>not_stated_appendix_missing</code>. Nulls are excluded. The values are informative "
        "individually but are not comparable across runs.",
        grouped_hbar(rows6, ["support_status", "measurement_status"], [L[0], L[1]], "Status vocabulary"),
        grouped_hbar(rows6, ["support_status", "measurement_status"], [D[0], D[1]], "Status vocabulary"),
        legend(["support_status distinct values", "measurement_status distinct values"], [L[0], L[1]]),
        table(["Run", "support_status", "measurement_status", "field_unit"],
              [[r, len(s["support_status"][r]), len(s["measurement_status"][r]),
                f'{len(s["field_unit"][r]):,}'] for r in runs]),
    ))

    # ── Fig 7: provenance mix per run ────────────────────────────────────────
    rows7 = [(sh, [s["provenance"][r][p] for p in PROVENANCE_ORDER]) for r, sh in zip(runs, short)]
    _tot7 = [max(1, sum(v)) for _, v in rows7]
    ab_pct = [100 * v[PROVENANCE_ORDER.index("absent")] / tt for (_, v), tt in zip(rows7, _tot7)]
    sg_pct = [100 * v[PROVENANCE_ORDER.index("source_gap")] / tt for (_, v), tt in zip(rows7, _tot7)]
    figs.append(figure(
        7, "Provenance mix per run",
        "The share of dimension rows in each provenance label. Real sector differences explain "
        f"some of this, but not the spread in <code>absent</code> ({min(ab_pct):.1f}%→"
        f"{max(ab_pct):.1f}%) or <code>source_gap</code> ({min(sg_pct):.1f}%→{max(sg_pct):.1f}%): "
        "a batch that resolves ambiguity toward "
        "<code>absent</code> will look systematically stingier. Always control for run before "
        "comparing presence rates.",
        stacked_hbar(rows7, PROVENANCE_ORDER, L, "Provenance mix"),
        stacked_hbar(rows7, PROVENANCE_ORDER, D, "Provenance mix"),
        legend(PROVENANCE_ORDER, L),
        table(["Run"] + PROVENANCE_ORDER,
              [[r] + [f'{s["provenance"][r][p]:,}' for p in PROVENANCE_ORDER] for r in runs]),
    ))

    # ── Fig 8: category label convention ─────────────────────────────────────
    rows8 = [(sh, [s["category_conv"][r]["short"], s["category_conv"][r]["long"]])
             for r, sh in zip(runs, short)]
    figs.append(figure(
        8, "Area label convention per run — short vs long",
        "The same four areas are written either short (<code>Security</code>) or long "
        "(<code>Job Security</code>). Most runs mix both, sometimes inside one document. Purely "
        "cosmetic drift with no content meaning — the aggregate ignores the recorded label and "
        "derives <code>area</code> from <code>dimension_id</code> — but it is a clean marker of "
        "how loosely the output contract was followed.",
        stacked_hbar(rows8, ["short alias", "long canonical"], [L[0], L[1]], "Label convention"),
        stacked_hbar(rows8, ["short alias", "long canonical"], [D[0], D[1]], "Label convention"),
        legend(["short alias", "long canonical"], [L[0], L[1]]),
        table(["Run", "short", "long", "mixed?"],
              [[r, f'{s["category_conv"][r]["short"]:,}', f'{s["category_conv"][r]["long"]:,}',
                "yes" if s["category_conv"][r]["short"] and s["category_conv"][r]["long"] else "no"]
               for r in runs]),
    ))

    # ── Fig 9: yield per document ────────────────────────────────────────────
    def mean(xs):
        return sum(xs) / len(xs) if xs else 0
    rows9 = [(sh, [mean(s["yield_records"][r]), mean(s["yield_fields"][r])])
             for r, sh in zip(runs, short)]
    figs.append(figure(
        9, "Mean rows emitted per document, by run",
        "How much the extractor wrote per contract. Field yield ranges from "
        f"{min(v[1] for _, v in rows9):.0f} to {max(v[1] for _, v in rows9):.0f} rows per document "
        "across batches given the same instructions. Contract length varies too, so this is "
        "suggestive rather than conclusive — but it moves with batch, not with sector.",
        grouped_hbar(rows9, ["concept_records / doc", "concept_fields / doc"], [L[0], L[1]],
                     "Yield per document", fmt=lambda v: f"{v:.1f}"),
        grouped_hbar(rows9, ["concept_records / doc", "concept_fields / doc"], [D[0], D[1]],
                     "Yield per document", fmt=lambda v: f"{v:.1f}"),
        legend(["concept_records per document", "concept_fields per document"], [L[0], L[1]]),
        table(["Run", "Documents", "records/doc", "fields/doc"],
              [[r, f'{s["runs"][r]:,}', f'{mean(s["yield_records"][r]):.1f}',
                f'{mean(s["yield_fields"][r]):.1f}'] for r in runs]),
    ))

    # ── Fig 10: the same source file extracted by two runs ───────────────────
    dups = []
    for fn, entries in s["by_file"].items():
        byrun = {}
        for run, did, nr, nf in entries:
            byrun.setdefault(run, (did, nr, nf))
        if len(byrun) > 1:
            (ra, (da, nra, nfa)), (rb, (db, nrb, nfb)) = sorted(byrun.items())[:2]
            dups.append((fn, ra, rb, nra, nrb, nfa, nfb))
    dups.sort(key=lambda d: -abs(d[3] - d[4]))
    if dups:
        ra, rb = dups[0][1], dups[0][2]
        rows10 = [(fn.replace(".pdf", ""), a, b) for fn, _, _, a, b, _, _ in dups]
        deltas = [abs(a - b) for _, _, _, a, b, _, _ in dups]
        same = sum(1 for d in deltas if d == 0)
        figs.append(figure(
            10, f"Same source file, two runs — concept_records emitted ({len(dups)} files)",
            f"{len(dups)} source files were extracted by both <code>{esc(ra)}</code> and "
            f"<code>{esc(rb)}</code>. Only {same} produced the same number of concept records; the "
            f"median absolute difference is {sorted(deltas)[len(deltas)//2]} records and the "
            f"largest is {max(deltas)}. <strong>Read with care:</strong> the two runs keyed these "
            "documents differently (one per PDF part, one per document base), so the input text "
            "may not have been identical — this bounds run-to-run agreement rather than isolating "
            "model non-determinism.",
            dumbbell(rows10, [L[0], L[1]], "Records by run", (ra, rb)),
            dumbbell(rows10, [D[0], D[1]], "Records by run", (ra, rb)),
            legend([ra, rb], [L[0], L[1]]),
            table(["Source file", f"{ra} records", f"{rb} records", "Δ records",
                   f"{ra} fields", f"{rb} fields"],
                  [[fn, a, b, b - a, fa, fb] for fn, _, _, a, b, fa, fb in dups]),
        ))

    # ── KPI row ──────────────────────────────────────────────────────────────
    cf_all = set()
    for r in runs:
        cf_all |= set(s["cf_keys"][r])
    once = sum(1 for k in cf_all if sum(1 for r in runs if k in s["cf_keys"][r]) == 1)
    drift = sum(1 for c in concepts if ctier[c] == "drift")
    kpis = "".join([
        kpi(f'{s["n_docs"]:,}', "documents", f"{len(runs)} runs"),
        kpi(f"{len(concepts):,}", "distinct concept_ids", "~58 specified"),
        kpi(f"{drift:,}", "off-dictionary ids", "drift tail"),
        kpi(f"{len(cf_all):,}", "concept_fields keys", "corpus-wide"),
        kpi(f"{once:,}", "keys in one run only", f"{100*once/max(1,len(cf_all)):.0f}% of key space"),
        kpi(f'{max(len(s["support_status"][r]) for r in runs)}', "max support_status values",
            "2 documented"),
    ])

    generated = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>CBA Extraction Diagnostics</title>
<style>{CSS}</style></head><body><div class="wrap">
<h1>Extraction consistency diagnostics</h1>
<p class="sub">Where the CBA provision corpus varies for reasons that come from the extraction
pipeline rather than from the contracts. Each of the {len(runs)} runs is a separate batch of
agentic extractions given the same instructions, so between-run differences in vocabulary, key
names, and yield are unintended variation.</p>
<div class="kpis">{kpis}</div>
<div class="note"><strong>How to read this.</strong> Figures 1–2 describe the concept vocabulary;
3–6 measure schema and vocabulary drift between runs; 7–9 measure differences in what the extractor
recorded; 10 compares two runs on the same source files. Tier is assigned from
{esc(tier_source)}. Every figure has a table view, and marks carry hover tooltips.</div>
<h2>Concept vocabulary</h2>{figs[0]}{figs[1]}
<h2>Schema and vocabulary drift between runs</h2>{figs[2]}{figs[3]}{figs[4]}{figs[5]}
<h2>Differences in what was recorded</h2>{figs[6]}{figs[7]}{figs[8]}
{'<h2>The same document, extracted twice</h2>' + figs[9] if len(figs) > 9 else ''}
<footer>Generated {generated} from {esc(agg_path.name)} ·
scripts/report_extraction_diagnostics.py · {s["n_docs"]:,} documents, {len(runs)} runs</footer>
</div></body></html>"""


def main(argv=None):
    here = Path(__file__).resolve().parent
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--aggregate", default=str(here / "cba_provisions_aggregate.jsonl.gz"))
    p.add_argument("--schema", default=str(
        here.parent / "annotation_ui" / "lib" / "provision-schemas.json"))
    p.add_argument("--out", default=str(here / "extraction_diagnostics.html"))
    args = p.parse_args(argv)

    agg = Path(args.aggregate)
    if not agg.is_file():
        p.error(f"aggregate not found: {agg}\nBuild it with `python scripts/aggregate_provisions.py`.")

    tiers, tier_source = load_tiers(Path(args.schema))
    print(f"tier source: {tier_source}")
    s = collect(agg, tiers)
    print(f"collected {s['n_docs']:,} documents across {len(s['runs'])} runs")

    out = Path(args.out)
    out.write_text(build(s, tiers, tier_source, agg), encoding="utf-8")
    print(f"wrote {out} ({out.stat().st_size/1000:.0f} KB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
