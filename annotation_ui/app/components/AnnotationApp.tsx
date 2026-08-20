"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import type {
  AnnotationUnit,
  Band,
  Relevance,
  Span,
  SpanDraft,
  SpanSubmitPayload,
} from "@/lib/types";
import { BANDS, DEFAULT_BAND, isBand, RELEVANCE_OPTIONS, unitKey } from "@/lib/types";
import { AppShell } from "./AppShell";
import { ChunkText, type Selection } from "./ChunkText";

const TITLE = "CBA Provision Span Annotation";

const LS_ANNOTATOR = "cba-spans:annotator";
const LS_BAND = "cba-spans:band";
const LS_DRAFT = "cba-spans:draft";

type AppState = "no-annotator" | "loading" | "annotating" | "exhausted";

function generateSessionId(): string {
  return Date.now().toString(36) + Math.random().toString(36).slice(2, 7);
}

function areaClass(area: string): string {
  return `area-${area.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-+|-+$/g, "")}`;
}

/** Collapses whitespace so a multi-line quote fits on one or two lines. */
function preview(text: string, max = 220): string {
  const flat = text.replace(/\s+/g, " ").trim();
  return flat.length > max ? flat.slice(0, max - 1) + "…" : flat;
}

export default function AnnotationApp() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const pathname = usePathname();
  const docFilter = searchParams.get("doc") ?? "";
  const conceptFilter = searchParams.get("concept") ?? "";

  const [appState, setAppState] = useState<AppState>("loading");
  const [annotator, setAnnotator] = useState("");
  const [nameInput, setNameInput] = useState("");
  const [band, setBand] = useState<Band>(DEFAULT_BAND);

  const [unit, setUnit] = useState<AnnotationUnit | null>(null);
  const [sessionId, setSessionId] = useState("");
  const [relevance, setRelevance] = useState<Relevance | null>(null);
  const [spans, setSpans] = useState<Span[]>([]);
  const [pending, setPending] = useState<Selection | null>(null);
  const [pendingNote, setPendingNote] = useState("");
  const [activeSpanIndex, setActiveSpanIndex] = useState<number | null>(null);

  const [completedKeys, setCompletedKeys] = useState<Set<string>>(new Set());
  // Session-local: units skipped this session, so they aren't re-served at once.
  const [skippedKeys, setSkippedKeys] = useState<Set<string>>(new Set());
  const [bandDone, setBandDone] = useState<Record<string, number>>({});
  const [bandPool, setBandPool] = useState<Record<string, number>>({});

  const [submitting, setSubmitting] = useState(false);
  const [status, setStatus] = useState<{ type: "success" | "error"; msg: string } | null>(null);

  const draftTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  // ── Draft helpers ──────────────────────────────────────────────────────────

  function saveDraft(sid: string, u: AnnotationUnit, r: Relevance | null, s: Span[]) {
    const draft: SpanDraft = {
      sessionId: sid,
      unit: u,
      relevance: r,
      spans: s,
      savedAt: new Date().toISOString(),
    };
    try {
      localStorage.setItem(LS_DRAFT, JSON.stringify(draft));
    } catch {
      // A quota failure must not break annotating; the draft is a convenience.
    }
  }

  function clearDraft() {
    localStorage.removeItem(LS_DRAFT);
  }

  function resetUnitState() {
    setPending(null);
    setPendingNote("");
    setActiveSpanIndex(null);
    setRelevance(null);
  }

  // ── Load a unit ────────────────────────────────────────────────────────────

  const loadUnit = useCallback(
    async (who: string, forBand: Band, exclude: string[]) => {
      setStatus(null);
      resetUnitState();
      try {
        const res = await fetch("/api/session", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            annotator: who,
            band: forBand,
            exclude,
            doc: docFilter || undefined,
            concept: conceptFilter || undefined,
          }),
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data?.error ?? "Session request failed");

        if (data.exhausted) {
          setUnit(null);
          setAppState("exhausted");
          return;
        }

        const next = data as AnnotationUnit;
        if (data.bandCounts) setBandPool(data.bandCounts);
        const sid = generateSessionId();
        setUnit(next);
        setSessionId(sid);
        setSpans([]);
        setAppState("annotating");
        saveDraft(sid, next, null, []);
      } catch (err) {
        setStatus({
          type: "error",
          msg: err instanceof Error ? err.message : "Failed to load a chunk.",
        });
        setAppState("annotating");
      }
    },
    [docFilter, conceptFilter]
  );

  const refreshProgress = useCallback(async (who: string) => {
    try {
      const res = await fetch(`/api/progress?annotator=${encodeURIComponent(who)}`);
      if (!res.ok) return [] as string[];
      const json = await res.json();
      setBandDone(json.done ?? {});
      if (json.pool) setBandPool(json.pool);
      return (json.completed ?? []) as string[];
    } catch {
      return [] as string[]; // non-fatal: proceed with an empty completed list
    }
  }, []);

  // ── Start: annotator, then progress, then draft or a new unit ──────────────

  const start = useCallback(
    async (who: string, forBand: Band) => {
      setAnnotator(who);
      setBand(forBand);
      localStorage.setItem(LS_ANNOTATOR, who);
      localStorage.setItem(LS_BAND, forBand);
      setAppState("loading");

      const completed = await refreshProgress(who);
      const completedSet = new Set(completed);
      setCompletedKeys(completedSet);

      const raw = localStorage.getItem(LS_DRAFT);
      if (raw) {
        try {
          const draft: SpanDraft = JSON.parse(raw);
          const key = unitKey(draft.unit.chunk, draft.unit.concept.conceptId);
          // A draft from a different band, document or concept must not be restored
          // while a filter is pinned: the header would advertise one thing while the
          // panel showed another, and the row would be attributed to the wrong stratum.
          const matches =
            draft.unit.band === forBand &&
            (!docFilter || draft.unit.chunk.documentId === docFilter) &&
            (!conceptFilter || draft.unit.concept.conceptId === conceptFilter);
          if (!completedSet.has(key) && matches) {
            setUnit(draft.unit);
            setSessionId(draft.sessionId);
            setSpans(draft.spans ?? []);
            resetUnitState();
            setRelevance(draft.relevance ?? null);
            setAppState("annotating");
            return;
          }
          clearDraft();
        } catch {
          clearDraft();
        }
      }

      await loadUnit(who, forBand, completed);
    },
    [loadUnit, refreshProgress, docFilter, conceptFilter]
  );

  useEffect(() => {
    const urlBand = searchParams.get("band");
    const storedBand = typeof window !== "undefined" ? localStorage.getItem(LS_BAND) : null;
    const initialBand: Band = isBand(urlBand)
      ? urlBand
      : isBand(storedBand)
        ? storedBand
        : DEFAULT_BAND;

    const fromUrl = searchParams.get("annotator");
    const stored = typeof window !== "undefined" ? localStorage.getItem(LS_ANNOTATOR) : null;
    const who = (fromUrl ?? stored ?? "").trim();
    if (!who) {
      setBand(initialBand);
      setAppState("no-annotator");
      return;
    }
    start(who, initialBand);
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  // ── Auto-save draft (debounced 500 ms) ─────────────────────────────────────

  useEffect(() => {
    if (appState !== "annotating" || !unit) return;
    if (draftTimer.current) clearTimeout(draftTimer.current);
    draftTimer.current = setTimeout(() => saveDraft(sessionId, unit, relevance, spans), 500);
    return () => {
      if (draftTimer.current) clearTimeout(draftTimer.current);
    };
  }, [spans, relevance, unit, sessionId, appState]);

  // ── Band switching ─────────────────────────────────────────────────────────

  function switchBand(next: Band) {
    if (next === band || !annotator) return;
    localStorage.setItem(LS_BAND, next);
    // Keep the URL authoritative: it wins over localStorage on mount, so without
    // this a reload would drop back to the band the link was opened with, and the
    // rows that followed would carry the wrong stratum.
    const params = new URLSearchParams(searchParams.toString());
    params.set("band", next);
    router.replace(`${pathname}?${params.toString()}`, { scroll: false });
    clearDraft();
    setBand(next);
    setUnit(null);
    setSpans([]);
    setAppState("loading");
    loadUnit(annotator, next, Array.from(completedKeys).concat(Array.from(skippedKeys)));
  }

  // ── Spans ──────────────────────────────────────────────────────────────────

  function commitPending() {
    if (!pending) return;
    const dupe = spans.some((s) => s.start === pending.start && s.end === pending.end);
    if (dupe) {
      setStatus({ type: "error", msg: "That passage is already recorded." });
      setPending(null);
      setPendingNote("");
      return;
    }
    const next = [...spans, { ...pending, note: pendingNote.trim(), page: null }].sort(
      (a, b) => a.start - b.start
    );
    setSpans(next);
    setPending(null);
    setPendingNote("");
    setStatus(null);
    // Highlighting evidence implies the passage is relevant; don't make the
    // annotator state the obvious twice, but leave it overridable.
    if (relevance === null) setRelevance("yes");
    window.getSelection()?.removeAllRanges();
  }

  function removeSpan(i: number) {
    setSpans((prev) => prev.filter((_, j) => j !== i));
    setActiveSpanIndex(null);
  }

  function updateNote(i: number, note: string) {
    setSpans((prev) => prev.map((s, j) => (j === i ? { ...s, note } : s)));
  }

  function chooseRelevance(next: Relevance) {
    setRelevance(next);
    setStatus(null);
  }

  // ── Submit / skip ──────────────────────────────────────────────────────────

  async function submit() {
    if (!unit || !annotator || !relevance) return;
    if (relevance === "no" && spans.length > 0) {
      setStatus({
        type: "error",
        msg: 'Remove the spans, or change the verdict — a "no" cannot carry evidence.',
      });
      return;
    }

    const payload: SpanSubmitPayload = {
      sessionId,
      annotator,
      chunk: unit.chunk,
      conceptId: unit.concept.conceptId,
      band: unit.band,
      relevance,
      spans,
    };

    setSubmitting(true);
    setStatus(null);
    try {
      const res = await fetch("/api/submit", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const data = await res.json();
      if (!res.ok || !data.ok) throw new Error(data?.error ?? "Submit failed");

      const key = unitKey(unit.chunk, unit.concept.conceptId);
      const nextCompleted = new Set(completedKeys);
      nextCompleted.add(key);
      setCompletedKeys(nextCompleted);
      setBandDone((prev) => ({ ...prev, [unit.band]: (prev[unit.band] ?? 0) + 1 }));
      clearDraft();

      setStatus({ type: "success", msg: "Saved. Loading next…" });
      const exclude = Array.from(nextCompleted).concat(Array.from(skippedKeys));
      setTimeout(() => loadUnit(annotator, band, exclude), 700);
    } catch (err) {
      setStatus({
        type: "error",
        msg: err instanceof Error ? err.message : "Failed to save. Please try again.",
      });
    } finally {
      setSubmitting(false);
    }
  }

  function skip() {
    if (!unit || !annotator) return;
    const nextSkipped = new Set(skippedKeys);
    nextSkipped.add(unitKey(unit.chunk, unit.concept.conceptId));
    setSkippedKeys(nextSkipped);
    clearDraft();
    loadUnit(annotator, band, Array.from(completedKeys).concat(Array.from(nextSkipped)));
  }

  // ── Band selector ──────────────────────────────────────────────────────────

  const bandSelector = (
    <div className="band-bar">
      <span className="band-bar-label">Similarity percentile within document</span>
      <div className="band-buttons">
        {BANDS.map((b) => {
          const done = bandDone[b.id] ?? 0;
          const pool = bandPool[b.id];
          return (
            <button
              key={b.id}
              className={`band-btn${b.id === band ? " band-btn-active" : ""}`}
              onClick={() => switchBand(b.id)}
              disabled={submitting}
              title={`${b.lo}–${b.hi}th percentile${pool ? ` · ${pool.toLocaleString()} units` : ""}`}
            >
              <span className="band-btn-label">{b.label}</span>
              <span className="band-btn-count">
                {done}
                {pool ? ` / ${pool.toLocaleString()}` : ""}
              </span>
            </button>
          );
        })}
      </div>
    </div>
  );

  // ── Gate / overlay states ──────────────────────────────────────────────────

  if (appState === "no-annotator") {
    return (
      <AppShell title={TITLE}>
        <div className="overlay-screen">
          <div className="overlay-card">
            <h2>Who is annotating?</h2>
            <p>
              Enter a name or initials. It labels every judgement you submit and lets the tool
              skip passages you have already seen.
            </p>
            <form
              className="name-form"
              onSubmit={(e) => {
                e.preventDefault();
                const who = nameInput.trim();
                if (who) start(who, band);
              }}
            >
              <input
                className="name-input"
                value={nameInput}
                onChange={(e) => setNameInput(e.target.value)}
                placeholder="e.g. mb"
                autoFocus
              />
              <button className="btn btn-primary" type="submit" disabled={!nameInput.trim()}>
                Start
              </button>
            </form>
          </div>
        </div>
      </AppShell>
    );
  }

  if (appState === "loading") {
    return (
      <AppShell title={TITLE}>
        <div className="overlay-screen">
          <div className="overlay-card">
            <div className="spinner" />
            <p>Loading…</p>
          </div>
        </div>
      </AppShell>
    );
  }

  if (appState === "exhausted") {
    const label = BANDS.find((b) => b.id === band)?.label ?? band;
    return (
      <AppShell title={TITLE} right={<span className="cba-id">{annotator}</span>}>
        {bandSelector}
        <div className="overlay-screen">
          <div className="overlay-card">
            <h2>Nothing left in this band</h2>
            <p>
              You have covered every passage in the <strong>{label}</strong> band
              {docFilter || conceptFilter ? " matching the current filter" : ""}. Pick another
              band above, or widen the filter.
            </p>
            <p className="hint-text">{completedKeys.size} judgements submitted in total.</p>
          </div>
        </div>
      </AppShell>
    );
  }

  // ── Annotating ─────────────────────────────────────────────────────────────

  const c = unit?.concept;
  const canSubmit = !!relevance && !(relevance === "no" && spans.length > 0);

  return (
    <AppShell
      title={TITLE}
      right={
        <>
          {unit && (
            <span className="cba-id">
              {unit.chunk.source} / {unit.chunk.documentId} · chunk {unit.chunkIndex} of{" "}
              {unit.chunkCount}
              {unit.pageStart !== null && (
                <>
                  {" "}
                  · p{unit.pageStart}
                  {unit.pageEnd !== null && unit.pageEnd !== unit.pageStart
                    ? `–${unit.pageEnd}`
                    : ""}
                </>
              )}
            </span>
          )}
          {(docFilter || conceptFilter) && (
            <span className="filter-chip">
              filtered: {[docFilter, conceptFilter].filter(Boolean).join(" + ")}
            </span>
          )}
          <span className="cba-id done-count">{completedKeys.size} done</span>
          <span className="cba-id">{annotator}</span>
        </>
      }
    >
      {bandSelector}
      <div className="main">
        <div className="text-panel">
          {!unit && <div className="text-loading">Loading passage…</div>}
          {unit && (
            <ChunkText
              key={unitKey(unit.chunk, unit.concept.conceptId)}
              text={unit.text}
              offset={unit.charStart}
              spans={spans}
              activeSpanIndex={activeSpanIndex}
              onSelect={(sel) => {
                if (sel) setPendingNote("");
                setPending(sel);
              }}
              onSpanClick={(i) => setActiveSpanIndex(i)}
            />
          )}
        </div>

        <div className="annotation-panel">
          <div className="annotation-scroll">
            {c && (
              <div className="concept-card">
                <div className="concept-head">
                  <span className={`area-badge ${areaClass(c.area)}`}>{c.area}</span>
                  <span className="concept-id">{c.conceptId}</span>
                </div>
                <p className="concept-label">{c.label}</p>
                {c.description && <p className="concept-desc">{c.description}</p>}
              </div>
            )}

            <div className="relevance-block">
              <div className="relevance-question">Does this passage address the concept?</div>
              <div className="relevance-options">
                {RELEVANCE_OPTIONS.map((opt) => (
                  <button
                    key={opt.id}
                    className={`relevance-btn${relevance === opt.id ? " relevance-btn-active" : ""}`}
                    onClick={() => chooseRelevance(opt.id)}
                    title={opt.hint}
                  >
                    {opt.label}
                  </button>
                ))}
              </div>
            </div>

            <p className="hint-text">
              Highlight the passages that are evidence for the concept, then add them. A passage
              can be relevant with no clean span to mark — submit it as such.
            </p>

            {pending && (
              <div className="span-pending">
                <div className="span-pending-head">
                  Selected
                  <span className="span-offsets">
                    [{pending.start}–{pending.end}]
                  </span>
                </div>
                <blockquote className="span-quote">{preview(pending.text, 400)}</blockquote>
                <input
                  className="span-note-input"
                  value={pendingNote}
                  onChange={(e) => setPendingNote(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter") {
                      e.preventDefault();
                      commitPending();
                    }
                  }}
                  placeholder="Note (optional)"
                  autoFocus
                />
                <div className="span-pending-actions">
                  <button
                    className="btn btn-skip btn-sm"
                    onClick={() => {
                      setPending(null);
                      setPendingNote("");
                      window.getSelection()?.removeAllRanges();
                    }}
                  >
                    Discard
                  </button>
                  <button className="btn btn-primary btn-sm" onClick={commitPending}>
                    Add span
                  </button>
                </div>
              </div>
            )}

            <div className="span-list">
              <div className="span-list-head">
                {spans.length === 0
                  ? "No spans added yet"
                  : `${spans.length} span${spans.length === 1 ? "" : "s"}`}
              </div>
              {spans.map((s, i) => (
                <div
                  key={`${s.start}-${s.end}`}
                  className={`span-item${i === activeSpanIndex ? " span-item-active" : ""}`}
                  onMouseEnter={() => setActiveSpanIndex(i)}
                  onMouseLeave={() => setActiveSpanIndex(null)}
                >
                  <div className="span-item-head">
                    <span className="span-num">{i + 1}</span>
                    <span className="span-offsets">
                      [{s.start}–{s.end}]
                    </span>
                    <button
                      className="span-remove"
                      onClick={() => removeSpan(i)}
                      title="Remove this span"
                      aria-label={`Remove span ${i + 1}`}
                    >
                      ✕
                    </button>
                  </div>
                  <blockquote className="span-quote" title={s.text}>
                    {preview(s.text)}
                  </blockquote>
                  <input
                    className="span-note-input"
                    value={s.note}
                    onChange={(e) => updateNote(i, e.target.value)}
                    placeholder="Note (optional)"
                  />
                </div>
              ))}
            </div>
          </div>

          <div className="footer">
            {status && <span className={`status-msg status-${status.type}`}>{status.msg}</span>}
            {!relevance && (
              <span className="footer-hint">Choose a verdict above to submit.</span>
            )}
            <div className="footer-actions">
              <button className="btn btn-skip" onClick={skip} disabled={submitting || !unit}>
                Skip
              </button>
              <button
                className="btn btn-primary"
                onClick={submit}
                disabled={submitting || !unit || !canSubmit}
              >
                {submitting
                  ? "Saving…"
                  : `Submit${spans.length ? ` ${spans.length}` : ""}`}
              </button>
            </div>
          </div>
        </div>
      </div>
    </AppShell>
  );
}
