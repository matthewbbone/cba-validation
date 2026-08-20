"use client";

import { Suspense } from "react";
import AnnotationApp from "./components/AnnotationApp";

export default function Page() {
  return (
    // AnnotationApp reads ?annotator / ?doc / ?concept via useSearchParams.
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
