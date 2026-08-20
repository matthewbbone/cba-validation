"use client";

/**
 * Shared chrome: the fixed header (title, contextual right-hand info) above
 * whatever the view renders. Overlay states render inside the shell too, so the
 * header stays visible while waiting or gating.
 */
export function AppShell({
  title,
  right,
  children,
}: {
  title: string;
  right?: React.ReactNode;
  children: React.ReactNode;
}) {
  return (
    <div className="app">
      <header className="header">
        <h1>{title}</h1>
        <div className="header-right">{right}</div>
      </header>
      {children}
    </div>
  );
}
