"use client";

import { useState, useEffect, useCallback } from "react";
import type { SessionData, ProvisionAnnotation, SubmitPayload } from "@/lib/types";
import provisionSchemas from "@/lib/provision-schemas.json";
import { ProvisionForm, emptyAnnotation } from "./components/ProvisionForm";

const SCHEMAS = provisionSchemas as Record<string, { format: "binary" | "quantitative" | "complex"; flags: string[] }>;

function generateSessionId(): string {
  return Date.now().toString(36) + Math.random().toString(36).slice(2, 7);
}

export default function Page() {
  const [session, setSession] = useState<SessionData | null>(null);
  const [sessionId, setSessionId] = useState<string>("");
  const [annotations, setAnnotations] = useState<ProvisionAnnotation[]>([]);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [status, setStatus] = useState<{ type: "success" | "error"; msg: string } | null>(null);
  const [pdfLoaded, setPdfLoaded] = useState(false);
  const [totalSubmitted, setTotalSubmitted] = useState(0);

  const loadSession = useCallback(async () => {
    setLoading(true);
    setPdfLoaded(false);
    setStatus(null);
    try {
      const res = await fetch("/api/session");
      const data: SessionData = await res.json();
      setSession(data);
      setSessionId(generateSessionId());
      setAnnotations(
        data.provisions.map((p) => {
          const schema = SCHEMAS[p.conceptId] ?? { format: "binary" as const, flags: [] };
          return emptyAnnotation(p.conceptId, p.category, schema);
        })
      );
    } catch {
      setStatus({ type: "error", msg: "Failed to load session." });
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { loadSession(); }, [loadSession]);

  async function handleSubmit() {
    if (!session) return;
    setSubmitting(true);
    setStatus(null);
    const payload: SubmitPayload = { sessionId, cba: session.cba, provisions: annotations };
    try {
      const res = await fetch("/api/submit", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      if (!res.ok) throw new Error("Submit failed");
      setTotalSubmitted((n) => n + 1);
      setStatus({ type: "success", msg: "Saved! Loading next CBA…" });
      setTimeout(loadSession, 900);
    } catch {
      setStatus({ type: "error", msg: "Failed to save. Please try again." });
    } finally {
      setSubmitting(false);
    }
  }

  const pdfSrc = session ? `/api/pdf/${session.cba.source}/${session.cba.filename}` : null;

  return (
    <div className="app">
      <header className="header">
        <h1>CBA Annotation Tool</h1>
        {session && (
          <span className="cba-id">
            {session.cba.source} / {session.cba.filename}
          </span>
        )}
        {totalSubmitted > 0 && (
          <span className="cba-id" style={{ color: "#86efac" }}>
            {totalSubmitted} submitted
          </span>
        )}
      </header>

      <div className="main">
        {/* PDF panel */}
        <div className="pdf-panel">
          {loading && <div className="pdf-loading">Loading CBA…</div>}
          {!loading && pdfSrc && (
            <iframe
              key={pdfSrc}
              src={pdfSrc}
              title="CBA PDF"
              onLoad={() => setPdfLoaded(true)}
              style={{ opacity: pdfLoaded ? 1 : 0, transition: "opacity 0.2s" }}
            />
          )}
        </div>

        {/* Annotation panel */}
        <div className="annotation-panel">
          <div className="annotation-scroll">
            {loading && (
              <p style={{ color: "#94a3b8", fontSize: "0.85rem", padding: "0.5rem" }}>
                Loading provisions…
              </p>
            )}
            {!loading && session &&
              session.provisions.map((p, i) => {
                const schema = SCHEMAS[p.conceptId] ?? { format: "binary" as const, flags: [] };
                return (
                  <ProvisionForm
                    key={p.conceptId}
                    index={i}
                    conceptId={p.conceptId}
                    category={p.category}
                    label={p.label}
                    schema={schema}
                    annotation={annotations[i] ?? emptyAnnotation(p.conceptId, p.category, schema)}
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
              onClick={loadSession}
              disabled={loading || submitting}
            >
              Skip CBA
            </button>

            {status && (
              <span className={`status-msg status-${status.type}`}>{status.msg}</span>
            )}

            <button
              className="btn btn-primary"
              onClick={handleSubmit}
              disabled={loading || submitting || !session}
            >
              {submitting ? "Saving…" : "Submit & Next"}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
