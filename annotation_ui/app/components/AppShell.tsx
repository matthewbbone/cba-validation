"use client";

/**
 * Shared chrome: the fixed header (title, tab bar, contextual right-hand info)
 * above whatever the active view renders.
 *
 * Overlay states render inside the shell too, so the tab bar stays reachable --
 * a reviewer who has not entered a name must still be able to switch views.
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
