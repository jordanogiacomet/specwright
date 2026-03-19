import type { ReactNode } from "react";

type LayoutProps = {
  children: ReactNode;
  headerEyebrow?: string;
  headerTitle?: string;
  headerActions?: ReactNode;
};

export function Layout({
  children,
  headerEyebrow = "Todo App",
  headerTitle = "Application Shell",
  headerActions,
}: LayoutProps) {
  return (
    <div className="min-h-screen bg-slate-50 text-slate-950">
      <div className="mx-auto flex min-h-screen w-full max-w-5xl flex-col">
        <header className="border-b border-slate-200 bg-white">
          <div className="flex items-center justify-between px-6 py-4">
            <div>
              <p className="text-xs font-medium uppercase tracking-[0.2em] text-slate-500">
                {headerEyebrow}
              </p>
              <h1 className="text-lg font-semibold">{headerTitle}</h1>
            </div>
            {headerActions ?? (
              <span className="rounded border border-dashed border-slate-300 px-3 py-2 text-sm text-slate-500">
                Navigation placeholder
              </span>
            )}
          </div>
        </header>

        <main className="flex-1 px-6 py-10">{children}</main>
      </div>
    </div>
  );
}
