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
  return (
    <nav className="tab-bar">
      {TABS.map((t) => (
        <button
          key={t.id}
          className={`tab${t.id === active ? " tab-active" : ""}`}
          onClick={() => router.replace(`${pathname}?tab=${t.id}`, { scroll: false })}
        >
          {t.label}
        </button>
      ))}
    </nav>
  );
}

// Annotate stays the default so the existing rater flow is unchanged for anyone
// arriving from a Prolific link, which carries no `tab` param.
function TabRouter() {
  const searchParams = useSearchParams();
  const active: Tab = searchParams.get("tab") === "review" ? "review" : "annotate";
  const tabs = <TabBar active={active} />;

  return active === "review" ? <ReviewApp tabs={tabs} /> : <AnnotationApp tabs={tabs} />;
}

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
      <TabRouter />
    </Suspense>
  );
}
