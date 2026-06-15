"use client";

import { useState, useEffect, useCallback, useRef, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import type {
  SessionData,
  ProvisionAnnotation,
  ProvisionSchema,
  SubmitPayload,
  ProlificContext,
  DraftState,
} from "@/lib/types";
import provisionSchemas from "@/lib/provision-schemas.json";
import { ProvisionForm, emptyAnnotation } from "./components/ProvisionForm";

const SCHEMAS = provisionSchemas as Record<string, ProvisionSchema>;

const LS_PID = "cba-annotation:prolific_pid";
const LS_STUDY = "cba-annotation:study_id";
const LS_SESSION = "cba-annotation:prolific_session_id";
const LS_DRAFT = "cba-annotation:draft";

const ANNOTATION_TARGET = process.env.NEXT_PUBLIC_ANNOTATION_TARGET
  ? parseInt(process.env.NEXT_PUBLIC_ANNOTATION_TARGET, 10)
  : 0;
const COMPLETION_URL = process.env.NEXT_PUBLIC_PROLIFIC_COMPLETION_URL ?? "";

type AppState = "no-pid" | "loading-progress" | "annotating" | "completed";

function generateSessionId(): string {
  return Date.now().toString(36) + Math.random().toString(36).slice(2, 7);
}

// Annotation keys are namespaced by the PDF stem (document_id), matching the
// S3 object path annotations/{pid}/{source}/{document_id}.json.
function cbaKey(source: string, filename: string): string {
  const documentId = filename.replace(/\.[^./]+$/, "");
  return `${source}/${documentId}`;
}

// Require an explicit present/absent decision for every provision, plus a
// summary when the provision is marked present. Returns an error message for
// the first incomplete provision, or null if all are complete.
function validateAnnotations(anns: ProvisionAnnotation[]): string | null {
  for (let i = 0; i < anns.length; i++) {
    const a = anns[i];
    if (a.exists === null) {
      return `Provision ${i + 1}: choose whether it is present (Yes/No).`;
    }
    if (a.exists && !a.summarize.trim()) {
      return `Provision ${i + 1}: add a summary describing the provision.`;
    }
  }
  return null;
}

// ── Inner component (needs useSearchParams, must be inside Suspense) ─────────

function AnnotationApp() {
  const searchParams = useSearchParams();

  const [appState, setAppState] = useState<AppState>("loading-progress");
  const [prolific, setProlific] = useState<ProlificContext | null>(null);
  const [completedKeys, setCompletedKeys] = useState<Set<string>>(new Set());
  // Session-local: CBAs skipped this session, so they aren't immediately re-served.
  const [skippedKeys, setSkippedKeys] = useState<Set<string>>(new Set());
  const [session, setSession] = useState<SessionData | null>(null);
  const [sessionId, setSessionId] = useState<string>("");
  const [annotations, setAnnotations] = useState<ProvisionAnnotation[]>([]);
  const [submitting, setSubmitting] = useState(false);
  const [status, setStatus] = useState<{ type: "success" | "error"; msg: string } | null>(null);
  const [pdfLoaded, setPdfLoaded] = useState(false);

  const draftTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  // ── Draft helpers ────────────────────────────────────────────────────────

  function saveDraft(sid: string, s: SessionData, anns: ProvisionAnnotation[]) {
    const draft: DraftState = {
      sessionId: sid,
      cba: s.cba,
      provisions: s.provisions,
      annotations: anns,
      savedAt: new Date().toISOString(),
    };
    localStorage.setItem(LS_DRAFT, JSON.stringify(draft));
  }

  function clearDraft() {
    localStorage.removeItem(LS_DRAFT);
  }

  // ── Load a new CBA session ───────────────────────────────────────────────

  const loadSession = useCallback(async (excludeKeys: string[], pid: string) => {
    setStatus(null);
    setPdfLoaded(false);
    try {
      const res = await fetch("/api/session", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ pid, exclude: excludeKeys }),
      });
      if (!res.ok) throw new Error("Session request failed");
      const data: SessionData = await res.json();

      if (data.exhausted) {
        setAppState("completed");
        return;
      }

      const newSessionId = generateSessionId();
      const newAnnotations = data.provisions.map((p) => {
        const schema = SCHEMAS[p.conceptId] ?? { format: "binary" as const, flags: [] };
        return emptyAnnotation(p.conceptId, p.category, schema);
      });

      setSession(data);
      setSessionId(newSessionId);
      setAnnotations(newAnnotations);
      setAppState("annotating");
      saveDraft(newSessionId, data, newAnnotations);
    } catch {
      setStatus({ type: "error", msg: "Failed to load session." });
    }
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  // ── Initialise on mount: resolve PID + fetch server progress ────────────

  useEffect(() => {
    const urlPid = searchParams.get("PROLIFIC_PID");
    const urlStudy = searchParams.get("STUDY_ID") ?? "";
    const urlProlificSession = searchParams.get("SESSION_ID") ?? "";

    let ctx: ProlificContext;

    if (urlPid) {
      ctx = { prolific_pid: urlPid, study_id: urlStudy, prolific_session_id: urlProlificSession };
      localStorage.setItem(LS_PID, urlPid);
      localStorage.setItem(LS_STUDY, urlStudy);
      localStorage.setItem(LS_SESSION, urlProlificSession);
    } else {
      const storedPid = localStorage.getItem(LS_PID);
      if (!storedPid) {
        setAppState("no-pid");
        return;
      }
      ctx = {
        prolific_pid: storedPid,
        study_id: localStorage.getItem(LS_STUDY) ?? "",
        prolific_session_id: localStorage.getItem(LS_SESSION) ?? "",
      };
    }

    setProlific(ctx);

    (async () => {
      let serverCompleted: string[] = [];
      try {
        const res = await fetch(`/api/progress?pid=${encodeURIComponent(ctx.prolific_pid)}`);
        if (!res.ok) throw new Error("Progress request failed");
        const json = await res.json();
        serverCompleted = json.completed ?? [];
      } catch {
        // non-fatal: proceed with empty server list
      }

      const completedSet = new Set(serverCompleted);

      if (ANNOTATION_TARGET > 0 && completedSet.size >= ANNOTATION_TARGET) {
        setCompletedKeys(completedSet);
        setAppState("completed");
        return;
      }

      setCompletedKeys(completedSet);

      // Try to restore a draft
      const draftRaw = localStorage.getItem(LS_DRAFT);
      if (draftRaw) {
        try {
          const draft: DraftState = JSON.parse(draftRaw);
          const key = cbaKey(draft.cba.source, draft.cba.filename);
          if (!completedSet.has(key)) {
            setSession({ cba: draft.cba, provisions: draft.provisions });
            setSessionId(draft.sessionId);
            setAnnotations(draft.annotations);
            setAppState("annotating");
            return;
          }
        } catch {
          clearDraft();
        }
      }

      await loadSession(serverCompleted, ctx.prolific_pid);
    })();
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  // ── Auto-save draft (debounced 500 ms) ──────────────────────────────────

  useEffect(() => {
    if (appState !== "annotating" || !session) return;
    if (draftTimer.current) clearTimeout(draftTimer.current);
    draftTimer.current = setTimeout(() => {
      saveDraft(sessionId, session, annotations);
    }, 500);
    return () => {
      if (draftTimer.current) clearTimeout(draftTimer.current);
    };
  }, [annotations, session, sessionId, appState]);

  // ── Completion redirect ──────────────────────────────────────────────────

  useEffect(() => {
    if (appState !== "completed" || !COMPLETION_URL) return;
    const t = setTimeout(() => {
      window.location.href = COMPLETION_URL;
    }, 5000);
    return () => clearTimeout(t);
  }, [appState]);

  // ── Submit ───────────────────────────────────────────────────────────────

  async function handleSubmit() {
    if (!session || !prolific) return;

    const validationError = validateAnnotations(annotations);
    if (validationError) {
      setStatus({ type: "error", msg: validationError });
      return;
    }

    setSubmitting(true);
    setStatus(null);

    const payload: SubmitPayload = { sessionId, cba: session.cba, provisions: annotations, prolific };

    try {
      const res = await fetch("/api/submit", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      if (!res.ok) throw new Error("Submit failed");

      const key = cbaKey(session.cba.source, session.cba.filename);
      const next = new Set(completedKeys);
      next.add(key);
      setCompletedKeys(next);
      clearDraft();

      if (ANNOTATION_TARGET > 0 && next.size >= ANNOTATION_TARGET) {
        setAppState("completed");
        return;
      }

      setStatus({ type: "success", msg: "Saved! Loading next CBA…" });
      const exclude = Array.from(
        new Set(Array.from(next).concat(Array.from(skippedKeys)))
      );
      setTimeout(() => loadSession(exclude, prolific.prolific_pid), 900);
    } catch {
      setStatus({ type: "error", msg: "Failed to save. Please try again." });
    } finally {
      setSubmitting(false);
    }
  }

  // ── Skip ─────────────────────────────────────────────────────────────────

  function handleSkip() {
    if (!session || !prolific) return;
    const key = cbaKey(session.cba.source, session.cba.filename);
    const nextSkipped = new Set(skippedKeys);
    nextSkipped.add(key);
    setSkippedKeys(nextSkipped);
    clearDraft();
    const exclude = Array.from(
      new Set(Array.from(completedKeys).concat(Array.from(nextSkipped)))
    );
    loadSession(exclude, prolific.prolific_pid);
  }

  // ── Overlay states ───────────────────────────────────────────────────────

  if (appState === "no-pid") {
    return (
      <div className="overlay-screen">
        <div className="overlay-card">
          <h2>Welcome</h2>
          <p>
            Please access this tool via your Prolific study link. Your Prolific
            participant ID is required to save your progress.
          </p>
        </div>
      </div>
    );
  }

  if (appState === "loading-progress") {
    return (
      <div className="overlay-screen">
        <div className="overlay-card">
          <div className="spinner" />
          <p>Loading your progress…</p>
        </div>
      </div>
    );
  }

  if (appState === "completed") {
    const target = ANNOTATION_TARGET > 0 ? ANNOTATION_TARGET : completedKeys.size;
    return (
      <div className="overlay-screen">
        <div className="overlay-card">
          <h2>All done!</h2>
          <p>
            You have completed {target} annotation{target !== 1 ? "s" : ""}. Thank you
            for your contribution to this research.
          </p>
          {COMPLETION_URL && (
            <>
              <p className="redirect-note">You will be redirected to Prolific in 5 seconds…</p>
              <a href={COMPLETION_URL} className="btn btn-primary completion-btn">
                Return to Prolific now
              </a>
            </>
          )}
        </div>
      </div>
    );
  }

  // ── Annotating ───────────────────────────────────────────────────────────

  const pdfSrc = session ? `/api/pdf/${session.cba.source}/${session.cba.filename}` : null;
  const completedCount = completedKeys.size;
  const targetLabel =
    ANNOTATION_TARGET > 0 ? `${completedCount} / ${ANNOTATION_TARGET}` : `${completedCount}`;

  return (
    <div className="app">
      <header className="header">
        <h1>CBA Annotation Tool</h1>
        {session && (
          <span className="cba-id">
            {session.cba.source} / {session.cba.filename}
          </span>
        )}
        <span className="cba-id" style={{ color: "#86efac" }}>
          {targetLabel} completed
        </span>
      </header>

      <div className="main">
        <div className="pdf-panel">
          {!pdfSrc && <div className="pdf-loading">Loading CBA…</div>}
          {pdfSrc && (
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
          <div className="annotation-scroll">
            {!session && (
              <p style={{ color: "#94a3b8", fontSize: "0.85rem", padding: "0.5rem" }}>
                Loading provisions…
              </p>
            )}
            {session &&
              session.provisions.map((p, i) => {
                const schema = SCHEMAS[p.conceptId] ?? { format: "binary" as const, flags: [] };
                return (
                  <ProvisionForm
                    key={p.conceptId}
                    index={i}
                    conceptId={p.conceptId}
                    category={p.category}
                    label={schema.description || p.label}
                    schema={schema}
                    annotation={
                      annotations[i] ?? emptyAnnotation(p.conceptId, p.category, schema)
                    }
                    onChange={(updated) =>
                      setAnnotations((prev) => prev.map((a, j) => (j === i ? updated : a)))
                    }
                  />
                );
              })}
          </div>

          <div className="footer">
            <button
              className="btn btn-skip"
              onClick={handleSkip}
              disabled={submitting || !session}
            >
              Skip CBA
            </button>

            {status && (
              <span className={`status-msg status-${status.type}`}>{status.msg}</span>
            )}

            <button
              className="btn btn-primary"
              onClick={handleSubmit}
              disabled={submitting || !session}
            >
              {submitting ? "Saving…" : "Submit & Next"}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

// ── Page wrapper — Suspense required for useSearchParams ─────────────────────

export default function Page() {
  return (
    <Suspense
      fallback={
        <div className="overlay-screen">
          <div className="overlay-card">
            <div className="spinner" />
            <p>Loading…</p>
          </div>
        </div>
      }
    >
      <AnnotationApp />
    </Suspense>
  );
}
