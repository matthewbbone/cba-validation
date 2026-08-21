"use client";

import { useState, useEffect, useMemo, useRef, useCallback } from "react";
import type {
  ReviewUnit,
  ReviewIssue,
  ReviewQuality,
  ExtractionDetail,
  ExtractionRecordRow,
  ExtractionFieldRow,
  ReviewDraft,
} from "@/lib/types";
import provisionSchemas from "@/lib/provision-schemas.json";
import type { ProvisionSchema } from "@/lib/types";
import { AppShell } from "./AppShell";

const SCHEMAS = provisionSchemas as Record<string, ProvisionSchema>;
const TITLE = "CBA Extraction Review";

const LS_REVIEWER = "cba-review:reviewer";
const LS_DRAFT = "cba-review:draft";

/**
 * Overall assessment. These are toggles like the issues below, so nothing stops
 * a reviewer setting good and bad together — that is recorded as-is rather than
 * silently resolved.
 */
const QUALITIES: { id: ReviewQuality; label: string; hint: string }[] = [
  { id: "good", label: "Good", hint: "Faithful to the contract" },
  { id: "okay", label: "Okay", hint: "Usable, with reservations" },
  { id: "bad", label: "Bad", hint: "Should not be relied on" },
];

/**
 * Independent toggles, not a scale — any combination is valid, and none set is
 * the ordinary "reviewed, nothing wrong" answer.
 */
const ISSUES: { id: ReviewIssue; label: string; hint: string }[] = [
  { id: "missing", label: "Missing", hint: "The contract says more than the extraction captured" },
  { id: "hallucinating", label: "Hallucinating", hint: "Asserts something the contract does not say" },
  { id: "confusing", label: "Confusing", hint: "Garbled, mislabelled, or attached to the wrong object" },
];

/**
 * The provision dictionary labels categories with the short convention
 * (`Security`), while the aggregate's `dimension_coverage.area` uses the long
 * canonical one (`Job Security`). Map across before comparing the two.
 */
const AREA_ALIASES: Record<string, string> = {
  Security: "Job Security",
  Recognition: "Union Recognition",
  Disputes: "Dispute Resolution",
  Ancillary: "Ancillary benefits",
};

function areaFor(category: string): string {
  return AREA_ALIASES[category] ?? category;
}

function unitKey(u: ReviewUnit): string {
  return `${u.run}/${u.documentId}/${u.conceptId}`;
}

function docKey(u: ReviewUnit): string {
  return `${u.run}/${u.documentId}`;
}

function generateSessionId(): string {
  return Date.now().toString(36) + Math.random().toString(36).slice(2, 7);
}

/**
 * field_value is heterogeneously typed by construction — int, float, str, null,
 * bool, and occasionally list/dict. Render every shape without assuming one.
 */
function renderValue(v: unknown): string {
  if (v === null || v === undefined) return "—";
  if (typeof v === "object") return JSON.stringify(v);
  return String(v);
}

function isCore(conceptId: string): boolean {
  return SCHEMAS[conceptId]?.meta?.priority_tier === "core";
}

// ── Small presentational pieces ──────────────────────────────────────────────

function Row({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="rv-row">
      <span className="rv-row-label">{label}</span>
      <span className="rv-row-value">{children}</span>
    </div>
  );
}

function RecordCard({ row, index }: { row: ExtractionRecordRow; index: number }) {
  const flags = Array.isArray(row.status_flags) ? row.status_flags : [];
  return (
    <div className="rv-card rv-card-record">
      <div className="rv-card-head">
        <span className="rv-kind rv-kind-record">concept_record {index + 1}</span>
        {row.measurement_status && (
          <span className="rv-status">{String(row.measurement_status)}</span>
        )}
      </div>
      {row.concept_label && <Row label="Label">{String(row.concept_label)}</Row>}
      {row.status_reason && (
        <Row label="Reason">
          <span className="rv-prose">{String(row.status_reason)}</span>
        </Row>
      )}
      {flags.length > 0 && (
        <Row label="Flags">
          <span className="rv-flags">
            {flags.map((f) => (
              <span key={f} className="rv-flag">
                {f}
              </span>
            ))}
          </span>
        </Row>
      )}
      <Row label="Evidence">
        <code className="rv-pointer">{row.evidence_pointer ?? "— none recorded —"}</code>
      </Row>
    </div>
  );
}

function FieldCard({ row, index }: { row: ExtractionFieldRow; index: number }) {
  const unit = row.field_unit ? ` ${row.field_unit}` : "";
  return (
    <div className="rv-card rv-card-field">
      <div className="rv-card-head">
        <span className="rv-kind rv-kind-field">concept_field {index + 1}</span>
        {row.support_status && <span className="rv-status">{String(row.support_status)}</span>}
      </div>
      <Row label="Field">
        <code>{row.field_name ?? "—"}</code>
      </Row>
      <Row label="Value">
        <strong className="rv-value">
          {renderValue(row.field_value)}
          {unit}
        </strong>
        {row.value_type && <span className="rv-type">{String(row.value_type)}</span>}
      </Row>
      {row.note && (
        <Row label="Note">
          <span className="rv-prose">{String(row.note)}</span>
        </Row>
      )}
      <Row label="Evidence">
        <code className="rv-pointer">{row.evidence_pointer ?? "— none recorded —"}</code>
      </Row>
    </div>
  );
}

// ── Main view ────────────────────────────────────────────────────────────────

export default function ReviewApp({ tabs }: { tabs?: React.ReactNode }) {
  const [reviewer, setReviewer] = useState<string>("");
  const [reviewerInput, setReviewerInput] = useState<string>("");
  const [ready, setReady] = useState(false);
  // Bumped once per completed load of (units + completed), so the auto-selection
  // below can tell "this reviewer's progress has arrived" from "still the previous
  // reviewer's". Both setStates happen in the same batch as this one.
  const [loadSeq, setLoadSeq] = useState(0);

  const [units, setUnits] = useState<ReviewUnit[]>([]);
  const [completed, setCompleted] = useState<Set<string>>(new Set());
  const [loadError, setLoadError] = useState<string | null>(null);

  const [activeDoc, setActiveDoc] = useState<string | null>(null);
  const [activeUnit, setActiveUnit] = useState<string | null>(null);
  const [detail, setDetail] = useState<ExtractionDetail | null>(null);
  const [detailError, setDetailError] = useState<string | null>(null);

  const [quality, setQuality] = useState<ReviewQuality[]>([]);
  const [issues, setIssues] = useState<ReviewIssue[]>([]);
  const [comment, setComment] = useState("");
  const [coreOnly, setCoreOnly] = useState(false);
  const [showDims, setShowDims] = useState(false);
  const [saving, setSaving] = useState(false);
  const [status, setStatus] = useState<{ type: "success" | "error"; msg: string } | null>(null);
  const [pdfLoaded, setPdfLoaded] = useState(false);

  const sessionId = useRef(generateSessionId());
  const draftTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  // ── Load reviewer + unit index ─────────────────────────────────────────────

  const loadUnits = useCallback(async (who: string) => {
    try {
      const res = await fetch(`/api/review/units?reviewer=${encodeURIComponent(who)}`);
      if (!res.ok) throw new Error("units request failed");
      const json = await res.json();
      setUnits(json.units ?? []);
      setCompleted(new Set<string>(json.completed ?? []));
      setLoadError(null);
      setLoadSeq((n) => n + 1);
    } catch {
      setLoadError("Could not load review units. Has `npm run prepare-data` been run?");
    }
  }, []);

  useEffect(() => {
    const stored = localStorage.getItem(LS_REVIEWER) ?? "";
    setReviewer(stored);
    setReviewerInput(stored);
    loadUnits(stored).finally(() => setReady(true));
  }, [loadUnits]);

  // ── Derived groupings ──────────────────────────────────────────────────────

  const visibleUnits = useMemo(
    () => (coreOnly ? units.filter((u) => isCore(u.conceptId)) : units),
    [units, coreOnly]
  );

  /** One entry per extraction document (a PDF can appear under two runs). */
  const documents = useMemo(() => {
    const map = new Map<
      string,
      { key: string; unit: ReviewUnit; total: number; done: number }
    >();
    for (const u of visibleUnits) {
      const k = docKey(u);
      const entry = map.get(k) ?? { key: k, unit: u, total: 0, done: 0 };
      entry.total += 1;
      if (completed.has(unitKey(u))) entry.done += 1;
      map.set(k, entry);
    }
    return Array.from(map.values()).sort((a, b) =>
      `${a.unit.source}/${a.unit.filename}`.localeCompare(`${b.unit.source}/${b.unit.filename}`)
    );
  }, [visibleUnits, completed]);

  const docUnits = useMemo(
    () => visibleUnits.filter((u) => docKey(u) === activeDoc),
    [visibleUnits, activeDoc]
  );

  const unit = useMemo(
    () => docUnits.find((u) => unitKey(u) === activeUnit) ?? null,
    [docUnits, activeUnit]
  );

  // Default to the first document once units arrive.
  useEffect(() => {
    if (!activeDoc && documents.length > 0) setActiveDoc(documents[0].key);
  }, [documents, activeDoc]);

  // Keep the selected concept valid for the selected document, preferring one that
  // has not been reviewed yet so switching document lands on outstanding work.
  useEffect(() => {
    if (docUnits.length === 0) return;
    if (!docUnits.some((u) => unitKey(u) === activeUnit)) {
      const firstUnreviewed = docUnits.find((u) => !completed.has(unitKey(u)));
      setActiveUnit(unitKey(firstUnreviewed ?? docUnits[0]));
    }
  }, [docUnits, activeUnit, completed]);

  // Land on outstanding work once a reviewer's progress has actually loaded.
  //
  // The effect above only fires when the current selection is *invalid*, and the
  // very first pick happens while `completed` is still empty -- so a reviewer
  // resuming used to open on a concept they had already done, shown ticked in the
  // sidebar. Keying on loadSeq means this runs exactly once per load, after both
  // units and completed are applied, and never overrides a later manual click.
  const autoSelectedSeq = useRef(-1);
  useEffect(() => {
    if (loadSeq === 0 || docUnits.length === 0) return;
    if (autoSelectedSeq.current === loadSeq) return;
    autoSelectedSeq.current = loadSeq;
    const firstUnreviewed = docUnits.find((u) => !completed.has(unitKey(u)));
    if (firstUnreviewed) setActiveUnit(unitKey(firstUnreviewed));
  }, [loadSeq, docUnits, completed]);

  // ── Fetch extraction detail when the document changes ──────────────────────

  useEffect(() => {
    if (!activeDoc) return;
    const [run, ...rest] = activeDoc.split("/");
    const documentId = rest.join("/");
    let cancelled = false;
    setDetail(null);
    setDetailError(null);
    (async () => {
      try {
        const res = await fetch(
          `/api/review/extraction?run=${encodeURIComponent(run)}` +
            `&documentId=${encodeURIComponent(documentId)}`
        );
        if (!res.ok) throw new Error((await res.json())?.error ?? "not found");
        const json: ExtractionDetail = await res.json();
        if (!cancelled) setDetail(json);
      } catch (err) {
        if (!cancelled) setDetailError(String(err instanceof Error ? err.message : err));
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [activeDoc]);

  // ── Draft: restore on unit change, autosave while editing ──────────────────

  useEffect(() => {
    if (!activeUnit) return;
    setStatus(null);
    try {
      const raw = localStorage.getItem(LS_DRAFT);
      const draft: ReviewDraft | null = raw ? JSON.parse(raw) : null;
      if (draft && draft.unitKey === activeUnit) {
        setQuality(Array.isArray(draft.quality) ? draft.quality : []);
        setIssues(Array.isArray(draft.issues) ? draft.issues : []);
        setComment(draft.comment);
        return;
      }
    } catch {
      // fall through to a clean slate
    }
    setQuality([]);
    setIssues([]);
    setComment("");
  }, [activeUnit]);

  useEffect(() => {
    if (!activeUnit) return;
    if (draftTimer.current) clearTimeout(draftTimer.current);
    draftTimer.current = setTimeout(() => {
      const draft: ReviewDraft = {
        unitKey: activeUnit,
        quality,
        issues,
        comment,
        savedAt: new Date().toISOString(),
      };
      localStorage.setItem(LS_DRAFT, JSON.stringify(draft));
    }, 500);
    return () => {
      if (draftTimer.current) clearTimeout(draftTimer.current);
    };
  }, [quality, issues, comment, activeUnit]);

  /** Toggle membership of `id` in a flag set. */
  function toggle<T>(setter: React.Dispatch<React.SetStateAction<T[]>>, id: T) {
    setter((prev) => (prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]));
  }

  // ── Navigation ─────────────────────────────────────────────────────────────

  function goToUnit(u: ReviewUnit) {
    const dk = docKey(u);
    if (dk !== activeDoc) setActiveDoc(dk);
    setActiveUnit(unitKey(u));
  }

  function step(delta: number) {
    const i = docUnits.findIndex((u) => unitKey(u) === activeUnit);
    const next = docUnits[i + delta];
    if (next) setActiveUnit(unitKey(next));
  }

  function randomUnreviewed() {
    const pool = visibleUnits.filter((u) => !completed.has(unitKey(u)));
    if (pool.length === 0) {
      setStatus({ type: "success", msg: "Every unit in scope has been reviewed." });
      return;
    }
    goToUnit(pool[Math.floor(Math.random() * pool.length)]);
  }

  // ── Save ───────────────────────────────────────────────────────────────────

  async function save() {
    // No issues selected is a valid submission: reviewed, nothing wrong.
    if (!unit || !reviewer) return;
    setSaving(true);
    setStatus(null);
    try {
      const res = await fetch("/api/review/submit", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          sessionId: sessionId.current,
          reviewer,
          unit,
          quality,
          issues,
          comment,
        }),
      });
      if (!res.ok) throw new Error((await res.json())?.error ?? "save failed");

      const key = unitKey(unit);
      setCompleted((prev) => new Set(prev).add(key));
      localStorage.removeItem(LS_DRAFT);
      setStatus({ type: "success", msg: "Saved." });

      // Advance to the next unreviewed concept in this document, if any.
      const i = docUnits.findIndex((u) => unitKey(u) === key);
      const nextInDoc = docUnits.slice(i + 1).find((u) => !completed.has(unitKey(u)));
      if (nextInDoc) setActiveUnit(unitKey(nextInDoc));
    } catch (err) {
      setStatus({
        type: "error",
        msg: err instanceof Error ? err.message : "Failed to save review.",
      });
    } finally {
      setSaving(false);
    }
  }

  // ── Reviewer gate ──────────────────────────────────────────────────────────

  if (!ready) {
    return (
      <AppShell title={TITLE} tabs={tabs}>
        <div className="overlay-screen">
          <div className="overlay-card">
            <div className="spinner" />
            <p>Loading review units…</p>
          </div>
        </div>
      </AppShell>
    );
  }

  if (!reviewer) {
    return (
      <AppShell title={TITLE} tabs={tabs}>
        <div className="overlay-screen">
          <div className="overlay-card">
            <h2>Who is reviewing?</h2>
            <p>
              Enter your name or initials. It is stored in this browser and attached to
              every judgement you record.
            </p>
            <div className="rv-reviewer-entry">
              <input
                className="rv-input"
                value={reviewerInput}
                placeholder="e.g. mb"
                onChange={(e) => setReviewerInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter" && reviewerInput.trim()) {
                    const who = reviewerInput.trim();
                    localStorage.setItem(LS_REVIEWER, who);
                    setReviewer(who);
                    loadUnits(who);
                  }
                }}
              />
              <button
                className="btn btn-primary"
                disabled={!reviewerInput.trim()}
                onClick={() => {
                  const who = reviewerInput.trim();
                  localStorage.setItem(LS_REVIEWER, who);
                  setReviewer(who);
                  loadUnits(who);
                }}
              >
                Start reviewing
              </button>
            </div>
          </div>
        </div>
      </AppShell>
    );
  }

  if (loadError || units.length === 0) {
    return (
      <AppShell title={TITLE} tabs={tabs}>
        <div className="overlay-screen">
          <div className="overlay-card">
            <h2>No review units</h2>
            <p>
              {loadError ??
                "The review index is empty. Build scripts/cba_provisions_aggregate.jsonl.gz, then run `npm run prepare-data`."}
            </p>
          </div>
        </div>
      </AppShell>
    );
  }

  // ── Review view ────────────────────────────────────────────────────────────

  const records = (detail?.concept_records ?? []).filter(
    (r) => unit && r.concept_id === unit.conceptId
  );
  const fields = (detail?.concept_fields ?? []).filter(
    (f) => unit && f.concept_id === unit.conceptId
  );
  const areaDims = (detail?.dimension_coverage ?? []).filter(
    (d) => unit && d.area === areaFor(unit.category)
  );

  const pdfSrc = unit ? `/api/pdf/${unit.source}/${unit.filename}` : null;
  const doneCount = visibleUnits.filter((u) => completed.has(unitKey(u))).length;
  const activeIndex = docUnits.findIndex((u) => unitKey(u) === activeUnit);

  return (
    <AppShell
      title={TITLE}
      tabs={tabs}
      right={
        <>
          <span className="cba-id">{reviewer}</span>
          <span className="cba-id" style={{ color: "#86efac" }}>
            {doneCount} / {visibleUnits.length} reviewed
          </span>
        </>
      }
    >
      <div className="main">
        <div className="pdf-panel">
          {!pdfSrc && <div className="pdf-loading">Select a document…</div>}
          {pdfSrc && (
            // Keyed on the document, not the unit, so stepping between concepts
            // in the same contract does not reload the PDF.
            <iframe
              key={pdfSrc}
              src={pdfSrc}
              title="CBA PDF"
              onLoad={() => setPdfLoaded(true)}
              style={{ opacity: pdfLoaded ? 1 : 0, transition: "opacity 0.2s" }}
            />
          )}
        </div>

        <div className="annotation-panel">
          <div className="rv-toolbar">
            <select
              className="rv-select"
              value={activeDoc ?? ""}
              onChange={(e) => {
                setActiveDoc(e.target.value);
                setPdfLoaded(false);
              }}
            >
              {documents.map((d) => (
                <option key={d.key} value={d.key}>
                  {d.unit.source}/{d.unit.filename} — {d.done}/{d.total}
                  {documents.some(
                    (o) => o.key !== d.key && o.unit.filename === d.unit.filename
                  )
                    ? ` · ${d.unit.run}`
                    : ""}
                </option>
              ))}
            </select>
            <label className="rv-check">
              <input
                type="checkbox"
                checked={coreOnly}
                onChange={(e) => setCoreOnly(e.target.checked)}
              />
              Core tier only
            </label>
            <button className="btn btn-skip" onClick={randomUnreviewed}>
              Random unreviewed
            </button>
          </div>

          <div className="rv-concept-strip">
            {docUnits.map((u) => {
              const k = unitKey(u);
              const done = completed.has(k);
              return (
                <button
                  key={k}
                  className={
                    "rv-chip" +
                    (k === activeUnit ? " rv-chip-active" : "") +
                    (done ? " rv-chip-done" : "")
                  }
                  onClick={() => setActiveUnit(k)}
                  title={`${u.conceptId} · ${u.nRecords} record(s), ${u.nFields} field(s)`}
                >
                  {u.conceptId.replace(/^C_/, "")}
                </button>
              );
            })}
          </div>

          <div className="annotation-scroll">
            {detailError && <p className="rv-empty">Could not load extraction: {detailError}</p>}
            {!detail && !detailError && <p className="rv-empty">Loading extraction…</p>}

            {detail && unit && (
              <>
                <div className="rv-unit-head">
                  <div className="rv-unit-title">
                    <code className="rv-concept-id">{unit.conceptId}</code>
                    <span className={`category-badge category-${unit.category.split(" ")[0]}`}>
                      {unit.category}
                    </span>
                    {unit.offDictionary && (
                      <span className="rv-offdict" title="Not in the provision dictionary">
                        off-dictionary
                      </span>
                    )}
                  </div>
                  <p className="rv-unit-label">{unit.label}</p>
                  <p className="rv-unit-meta">
                    {records.length} record{records.length !== 1 ? "s" : ""} ·{" "}
                    {fields.length} field{fields.length !== 1 ? "s" : ""} · run{" "}
                    <code>{unit.run}</code> · doc <code>{unit.documentId}</code>
                  </p>
                </div>

                {records.length === 0 && fields.length === 0 && (
                  <p className="rv-empty">Nothing recorded for this concept.</p>
                )}

                {records.map((r, i) => (
                  <RecordCard key={`r${i}`} row={r} index={i} />
                ))}
                {fields.map((f, i) => (
                  <FieldCard key={`f${i}`} row={f} index={i} />
                ))}

                {areaDims.length > 0 && (
                  <div className="rv-dims">
                    <button className="rv-dims-toggle" onClick={() => setShowDims((s) => !s)}>
                      {showDims ? "▾" : "▸"} {areaFor(unit.category)} dimension coverage (
                      {areaDims.length}) — area-level context, not this concept
                    </button>
                    {showDims &&
                      areaDims.map((d, i) => (
                        <div key={i} className="rv-dim-row">
                          <code>{d.dimension_id}</code>
                          <span className="rv-status">{d.provenance ?? "—"}</span>
                        </div>
                      ))}
                  </div>
                )}

                <p className="rv-pointer-note">
                  Evidence pointers cite the OCR text, which is not shipped with this repo.
                  Verify against the PDF on the left.
                </p>
              </>
            )}
          </div>

          <div className="rv-footer">
            <div className="rv-toggle-group">
              <span className="rv-toggle-label">Overall</span>
              <div className="rv-issues">
                {QUALITIES.map((v) => {
                  const on = quality.includes(v.id);
                  return (
                    <button
                      key={v.id}
                      type="button"
                      aria-pressed={on}
                      className={`btn btn-issue btn-${v.id}${on ? " rv-issue-on" : ""}`}
                      onClick={() => toggle(setQuality, v.id)}
                      disabled={!unit}
                      title={v.hint}
                    >
                      <span className="rv-issue-mark">{on ? "✓" : ""}</span>
                      {v.label}
                    </button>
                  );
                })}
              </div>
            </div>

            <div className="rv-toggle-group">
              <span className="rv-toggle-label">Issues</span>
              <div className="rv-issues">
                {ISSUES.map((v) => {
                  const on = issues.includes(v.id);
                  return (
                    <button
                      key={v.id}
                      type="button"
                      aria-pressed={on}
                      className={`btn btn-issue btn-${v.id}${on ? " rv-issue-on" : ""}`}
                      onClick={() => toggle(setIssues, v.id)}
                      disabled={!unit}
                      title={v.hint}
                    >
                      <span className="rv-issue-mark">{on ? "✓" : ""}</span>
                      {v.label}
                    </button>
                  );
                })}
              </div>
            </div>

            <p className="rv-issue-hint">
              {quality.length === 0 && issues.length === 0
                ? "Nothing flagged — submitting records this extraction as reviewed and clean."
                : [
                    quality.length ? `Overall: ${quality.join(", ")}` : null,
                    issues.length ? `Issues: ${issues.join(", ")}` : null,
                  ]
                    .filter(Boolean)
                    .join(" · ")}
              {quality.includes("good") && quality.includes("bad") && (
                <span className="rv-contradiction"> — good and bad are both set.</span>
              )}
            </p>
            <textarea
              className="provision-textarea rv-comment"
              value={comment}
              placeholder="Detail (optional)…"
              onChange={(e) => setComment(e.target.value)}
              disabled={!unit}
            />
            <div className="rv-actions">
              <button
                className="btn btn-skip"
                onClick={() => step(-1)}
                disabled={activeIndex <= 0}
              >
                ← Prev
              </button>
              {status && <span className={`status-msg status-${status.type}`}>{status.msg}</span>}
              <button
                className="btn btn-skip"
                onClick={() => step(1)}
                disabled={activeIndex < 0 || activeIndex >= docUnits.length - 1}
              >
                Next →
              </button>
              <button className="btn btn-primary" onClick={save} disabled={saving || !unit}>
                {saving ? "Submitting…" : "Submit"}
              </button>
            </div>
          </div>
        </div>
      </div>
    </AppShell>
  );
}
