import { Suspense } from "react";
import Link from "next/link";

import { TodoList } from "@/components/TodoList";

function TodoListFallback() {
  return (
    <section className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
      <div className="rounded-2xl border border-dashed border-slate-200 bg-slate-50 px-5 py-12 text-center text-sm text-slate-600">
        Loading todos...
      </div>
    </section>
  );
}

export default function TodosPage() {
  return (
    <main className="min-h-screen bg-[radial-gradient(circle_at_top,_#dbeafe,_#f8fafc_36%,_#e2e8f0_100%)] px-6 py-16 text-slate-950">
      <div className="mx-auto flex max-w-5xl flex-col gap-6">
        <section className="rounded-3xl border border-slate-200 bg-white/90 p-8 shadow-[0_24px_60px_rgba(15,23,42,0.08)] backdrop-blur">
          <div className="flex flex-col gap-5 md:flex-row md:items-start md:justify-between">
            <div className="space-y-3">
              <p className="text-sm font-semibold uppercase tracking-[0.24em] text-sky-700">
                Todos
              </p>
              <div className="space-y-2">
                <h1 className="text-4xl font-semibold tracking-tight text-slate-950">
                  Manage your current work in one place.
                </h1>
                <p className="max-w-2xl text-base leading-7 text-slate-600">
                  This page loads the logged-in user&apos;s todo list from the
                  Node API and supports add, status transitions, due-date
                  updates, delete, filter, and sorting actions.
                </p>
              </div>
            </div>

            <Link
              href="/login"
              className="inline-flex items-center justify-center rounded-full border border-slate-300 bg-white px-4 py-2 text-sm font-medium text-slate-700 transition hover:border-slate-400 hover:text-slate-950"
            >
              Open login
            </Link>
          </div>
        </section>

        <Suspense fallback={<TodoListFallback />}>
          <TodoList />
        </Suspense>
      </div>
    </main>
  );
}
