import type { ReactNode } from "react";

type LayoutProps = {
  children: ReactNode;
};

export function Layout({ children }: LayoutProps) {
  return (
    <div className="min-h-screen bg-slate-100 text-slate-950">
      <div className="mx-auto flex min-h-screen w-full max-w-6xl flex-col">
        <header className="border-b border-slate-200 bg-white">
          <div className="flex flex-col gap-4 px-6 py-5 sm:flex-row sm:items-center sm:justify-between">
            <div className="space-y-1">
              <p className="text-xs font-semibold uppercase tracking-[0.24em] text-slate-500">
                Editorial Control Center
              </p>
              <p className="text-sm text-slate-600">
                Next.js application shell for internal and public routes.
              </p>
            </div>
            <nav aria-label="Primary navigation">
              <span className="inline-flex rounded-full border border-dashed border-slate-300 px-4 py-2 text-sm text-slate-500">
                Navigation placeholder
              </span>
            </nav>
          </div>
        </header>
        <main className="flex-1 px-6 py-10">{children}</main>
      </div>
    </div>
  );
}
