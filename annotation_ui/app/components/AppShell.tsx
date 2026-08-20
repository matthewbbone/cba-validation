"use client";

/**
 * Shared chrome for both tabs: the fixed header (title, tab bar, contextual
 * right-hand info) above whatever the active view renders.
 *
 * Overlay states render inside this shell too, so the tab bar stays reachable —
 * an internal reviewer with no Prolific ID must still be able to reach Review.
 */
export function AppShell({
  title,
  tabs,
  right,
  children,
}: {
  title: string;
  tabs?: React.ReactNode;
  right?: React.ReactNode;
  children: React.ReactNode;
}) {
  return (
    <div className="app">
      <header className="header">
        <h1>{title}</h1>
        {tabs}
        <div className="header-right">{right}</div>
      </header>
      {children}
    </div>
  );
}
