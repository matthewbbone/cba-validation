"use client";

import { Suspense } from "react";
import { useSearchParams, useRouter, usePathname } from "next/navigation";
import AnnotationApp from "./components/AnnotationApp";
import ReviewApp from "./components/ReviewApp";

type Tab = "annotate" | "review";

const TABS: { id: Tab; label: string }[] = [
  { id: "annotate", label: "Annotate" },
  { id: "review", label: "Review extractions" },
];

function TabBar({ active }: { active: Tab }) {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  return (
    <nav className="tab-bar">
      {TABS.map((t) => (
        <button
          key={t.id}
          className={`tab${t.id === active ? " tab-active" : ""}`}
          onClick={() => {
            // Preserve the rest of the query (band, doc, concept, annotator) so
            // switching tabs and coming back does not silently reset the stratum.
            const params = new URLSearchParams(searchParams.toString());
            params.set("tab", t.id);
            router.replace(`${pathname}?${params.toString()}`, { scroll: false });
          }}
        >
          {t.label}
        </button>
      ))}
    </nav>
  );
}

// Annotate stays the default: a link with no `tab` param lands on the annotation
// flow, which is what the working links point at.
function TabRouter() {
  const searchParams = useSearchParams();
  const active: Tab = searchParams.get("tab") === "review" ? "review" : "annotate";
  const tabs = <TabBar active={active} />;

  return active === "review" ? <ReviewApp tabs={tabs} /> : <AnnotationApp tabs={tabs} />;
}

export default function Page() {
  return (
    // Both views read the query string via useSearchParams.
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
      <TabRouter />
    </Suspense>
  );
}
