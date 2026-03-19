"use client";

import Link from "next/link";
import { useEffect, useState, type FormEvent } from "react";

type DateRange = {
  from: string;
  to: string;
};

type ReportSummary = {
  total: number;
  completed: number;
  overdue: number;
  highPriority: number;
  completionRate: number;
};

type ReportBreakdownItem = {
  status: "pending" | "in_progress" | "completed";
  label: string;
  count: number;
  share: number;
};

type StatusDistributionReport = {
  reportType: "status_distribution";
  generatedAt: string;
  filters: DateRange & {
    dateField: "createdAt";
  };
  summary: ReportSummary;
  breakdown: ReportBreakdownItem[];
};

type StatusState = {
  tone: "neutral" | "success" | "error";
  message: string;
};

const apiBaseUrl =
  process.env.NEXT_PUBLIC_API_BASE_URL?.replace(/\/$/, "") ||
  "http://localhost:3001";

const DATE_ONLY_PATTERN = /^\d{4}-\d{2}-\d{2}$/;

const statusAccentStyles: Record<ReportBreakdownItem["status"], string> = {
  pending: "border-amber-200 bg-amber-50 text-amber-900",
  in_progress: "border-sky-200 bg-sky-50 text-sky-900",
  completed: "border-emerald-200 bg-emerald-50 text-emerald-900",
};

const statusBarStyles: Record<ReportBreakdownItem["status"], string> = {
  pending: "bg-amber-500",
  in_progress: "bg-sky-500",
  completed: "bg-emerald-500",
};

function formatDateInput(value: Date): string {
  return value.toISOString().slice(0, 10);
}

function addDays(value: Date, days: number): Date {
  const nextValue = new Date(value);
  nextValue.setDate(nextValue.getDate() + days);
  return nextValue;
}

function getRelativeDateRange(days: number): DateRange {
  const today = new Date();
  return {
    from: formatDateInput(addDays(today, -(days - 1))),
    to: formatDateInput(today),
  };
}

function getDefaultDateRange(): DateRange {
  return getRelativeDateRange(30);
}

async function parseResponse(response: Response) {
  const contentType = response.headers.get("content-type") ?? "";

  if (!contentType.includes("application/json")) {
    return null;
  }

  return (await response.json()) as Record<string, unknown>;
}

function getResponseMessage(body: unknown, fallbackMessage: string): string {
  if (
    typeof body === "object" &&
    body !== null &&
    "message" in body &&
    typeof body.message === "string"
  ) {
    return body.message;
  }

  return fallbackMessage;
}

function buildReportRequestPath(filters: DateRange): string {
  const searchParams = new URLSearchParams({
    from: filters.from,
    to: filters.to,
  });

  return `/api/reports/status-distribution?${searchParams.toString()}`;
}

function isDateRangeValid(filters: DateRange): boolean {
  return (
    DATE_ONLY_PATTERN.test(filters.from) &&
    DATE_ONLY_PATTERN.test(filters.to) &&
    filters.from <= filters.to
  );
}

function formatGeneratedAt(value: string): string {
  return new Intl.DateTimeFormat(undefined, {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}

function formatPercent(value: number): string {
  return `${value.toFixed(1).replace(/\.0$/, "")}%`;
}

function getStatusClasses(tone: StatusState["tone"]): string {
  if (tone === "error") {
    return "border-rose-200 bg-rose-50 text-rose-700";
  }

  if (tone === "success") {
    return "border-emerald-200 bg-emerald-50 text-emerald-700";
  }

  return "border-slate-200 bg-slate-50 text-slate-600";
}

export default function ReportsPage() {
  const [draftFilters, setDraftFilters] = useState<DateRange>(() =>
    getDefaultDateRange(),
  );
  const [appliedFilters, setAppliedFilters] = useState<DateRange>(() =>
    getDefaultDateRange(),
  );
  const [report, setReport] = useState<StatusDistributionReport | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isAuthenticated, setIsAuthenticated] = useState<boolean | null>(null);
  const [status, setStatus] = useState<StatusState>({
    tone: "neutral",
    message: "Loading the current status distribution report.",
  });

  useEffect(() => {
    let cancelled = false;

    async function loadReport() {
      setIsLoading(true);

      try {
        const response = await fetch(
          `${apiBaseUrl}${buildReportRequestPath(appliedFilters)}`,
          {
            credentials: "include",
          },
        );
        const body = await parseResponse(response);

        if (cancelled) {
          return;
        }

        if (response.status === 401) {
          setIsAuthenticated(false);
          setReport(null);
          setStatus({
            tone: "neutral",
            message: "Sign in to view reports for your account.",
          });
          return;
        }

        if (!response.ok || !body) {
          setIsAuthenticated(true);
          setStatus({
            tone: "error",
            message: getResponseMessage(
              body,
              "Unable to load the status distribution report.",
            ),
          });
          return;
        }

        const nextReport = body as unknown as StatusDistributionReport;
        setIsAuthenticated(true);
        setReport(nextReport);
        setStatus({
          tone: "success",
          message:
            nextReport.summary.total > 0
              ? "Report loaded from the database."
              : "No todos were created in the selected date range.",
        });
      } catch {
        if (cancelled) {
          return;
        }

        setStatus({
          tone: "error",
          message: "Unable to reach the reports API.",
        });
      } finally {
        if (!cancelled) {
          setIsLoading(false);
        }
      }
    }

    void loadReport();

    return () => {
      cancelled = true;
    };
  }, [appliedFilters]);

  function handleFilterSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    if (!isDateRangeValid(draftFilters)) {
      setStatus({
        tone: "error",
        message: "Use a valid YYYY-MM-DD range where the start date is not after the end date.",
      });
      return;
    }

    setAppliedFilters({
      from: draftFilters.from,
      to: draftFilters.to,
    });
  }

  function applyPreset(days: number) {
    const nextFilters = getRelativeDateRange(days);
    setDraftFilters(nextFilters);
    setAppliedFilters(nextFilters);
  }

  function resetFilters() {
    const nextFilters = getDefaultDateRange();
    setDraftFilters(nextFilters);
    setAppliedFilters(nextFilters);
  }

  return (
    <main className="min-h-screen bg-[radial-gradient(circle_at_top,_#fef3c7,_#fff7ed_24%,_#f8fafc_60%,_#e2e8f0_100%)] px-6 py-16 text-slate-950">
      <div className="mx-auto flex max-w-6xl flex-col gap-6">
        <section className="rounded-3xl border border-slate-200 bg-white/90 p-8 shadow-[0_24px_60px_rgba(15,23,42,0.08)] backdrop-blur">
          <div className="flex flex-col gap-5 lg:flex-row lg:items-end lg:justify-between">
            <div className="space-y-3">
              <p className="text-sm font-semibold uppercase tracking-[0.24em] text-amber-700">
                Reports
              </p>
              <div className="space-y-2">
                <h1 className="text-4xl font-semibold tracking-tight text-slate-950">
                  Status distribution for work created in a selected date range.
                </h1>
                <p className="max-w-3xl text-base leading-7 text-slate-600">
                  This report reads todo data from Postgres and summarizes the
                  current state of work for the signed-in user. Filter by
                  created date to review operational load, completion rate, and
                  overdue items.
                </p>
              </div>
            </div>

            <div className="flex flex-wrap gap-3">
              <Link
                href="/todos"
                className="inline-flex items-center justify-center rounded-full border border-slate-300 bg-white px-4 py-2 text-sm font-medium text-slate-700 transition hover:border-slate-400 hover:text-slate-950"
              >
                Open todos
              </Link>
              <Link
                href="/login"
                className="inline-flex items-center justify-center rounded-full border border-slate-300 bg-white px-4 py-2 text-sm font-medium text-slate-700 transition hover:border-slate-400 hover:text-slate-950"
              >
                Open login
              </Link>
            </div>
          </div>
        </section>

        <section className="grid gap-6 lg:grid-cols-[minmax(0,22rem)_minmax(0,1fr)]">
          <aside className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
            <div className="space-y-2">
              <h2 className="text-xl font-semibold text-slate-950">Filters</h2>
              <p className="text-sm leading-6 text-slate-600">
                Report type: <span className="font-medium">Status distribution</span>
              </p>
            </div>

            <form className="mt-6 space-y-5" onSubmit={handleFilterSubmit}>
              <label className="block space-y-2">
                <span className="text-sm font-medium text-slate-700">
                  From date
                </span>
                <input
                  type="date"
                  value={draftFilters.from}
                  onChange={(event) =>
                    setDraftFilters((current) => ({
                      ...current,
                      from: event.target.value,
                    }))
                  }
                  className="w-full rounded-2xl border border-slate-300 bg-white px-4 py-3 text-sm text-slate-900 outline-none transition focus:border-amber-500 focus:ring-2 focus:ring-amber-100"
                />
              </label>

              <label className="block space-y-2">
                <span className="text-sm font-medium text-slate-700">To date</span>
                <input
                  type="date"
                  value={draftFilters.to}
                  onChange={(event) =>
                    setDraftFilters((current) => ({
                      ...current,
                      to: event.target.value,
                    }))
                  }
                  className="w-full rounded-2xl border border-slate-300 bg-white px-4 py-3 text-sm text-slate-900 outline-none transition focus:border-amber-500 focus:ring-2 focus:ring-amber-100"
                />
              </label>

              <div className="flex flex-wrap gap-2">
                <button
                  type="button"
                  onClick={() => applyPreset(7)}
                  className="rounded-full border border-slate-300 px-3 py-2 text-sm font-medium text-slate-700 transition hover:border-slate-400 hover:text-slate-950"
                >
                  Last 7 days
                </button>
                <button
                  type="button"
                  onClick={() => applyPreset(30)}
                  className="rounded-full border border-slate-300 px-3 py-2 text-sm font-medium text-slate-700 transition hover:border-slate-400 hover:text-slate-950"
                >
                  Last 30 days
                </button>
                <button
                  type="button"
                  onClick={() => applyPreset(90)}
                  className="rounded-full border border-slate-300 px-3 py-2 text-sm font-medium text-slate-700 transition hover:border-slate-400 hover:text-slate-950"
                >
                  Last 90 days
                </button>
              </div>

              <div className="flex flex-wrap gap-3">
                <button
                  type="submit"
                  className="inline-flex items-center justify-center rounded-full bg-slate-950 px-4 py-2 text-sm font-medium text-white transition hover:bg-slate-800"
                >
                  Apply filters
                </button>
                <button
                  type="button"
                  onClick={resetFilters}
                  className="inline-flex items-center justify-center rounded-full border border-slate-300 px-4 py-2 text-sm font-medium text-slate-700 transition hover:border-slate-400 hover:text-slate-950"
                >
                  Reset
                </button>
              </div>
            </form>

            <div className={`mt-6 rounded-2xl border px-4 py-3 text-sm ${getStatusClasses(status.tone)}`}>
              {status.message}
            </div>
          </aside>

          <section className="space-y-6">
            {isAuthenticated === false ? (
              <div className="rounded-3xl border border-dashed border-slate-300 bg-white px-6 py-12 text-center shadow-sm">
                <h2 className="text-xl font-semibold text-slate-950">
                  Authentication required
                </h2>
                <p className="mt-3 text-sm leading-6 text-slate-600">
                  Sign in first to load report data for your account.
                </p>
              </div>
            ) : (
              <>
                <section className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
                  <div className="flex flex-col gap-3 md:flex-row md:items-end md:justify-between">
                    <div className="space-y-2">
                      <h2 className="text-2xl font-semibold text-slate-950">
                        Status distribution
                      </h2>
                      <p className="text-sm leading-6 text-slate-600">
                        Created between {appliedFilters.from} and {appliedFilters.to}
                      </p>
                    </div>
                    {report ? (
                      <p className="text-sm text-slate-500">
                        Generated {formatGeneratedAt(report.generatedAt)}
                      </p>
                    ) : null}
                  </div>

                  <div className="mt-6 grid gap-4 md:grid-cols-2 xl:grid-cols-4">
                    {[
                      {
                        label: "Total todos",
                        value: report?.summary.total ?? 0,
                      },
                      {
                        label: "Completed",
                        value: report?.summary.completed ?? 0,
                      },
                      {
                        label: "Overdue",
                        value: report?.summary.overdue ?? 0,
                      },
                      {
                        label: "Completion rate",
                        value: formatPercent(report?.summary.completionRate ?? 0),
                      },
                    ].map((item) => (
                      <div
                        key={item.label}
                        className="rounded-2xl border border-slate-200 bg-slate-50 px-5 py-4"
                      >
                        <p className="text-sm text-slate-500">{item.label}</p>
                        <p className="mt-2 text-3xl font-semibold tracking-tight text-slate-950">
                          {item.value}
                        </p>
                      </div>
                    ))}
                  </div>
                </section>

                <section className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
                  <div className="flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
                    <div>
                      <h2 className="text-xl font-semibold text-slate-950">
                        Breakdown by status
                      </h2>
                      <p className="text-sm leading-6 text-slate-600">
                        Share of all todos created during the selected reporting
                        window.
                      </p>
                    </div>
                    {report ? (
                      <p className="text-sm text-slate-500">
                        High priority in range: {report.summary.highPriority}
                      </p>
                    ) : null}
                  </div>

                  {isLoading && !report ? (
                    <div className="mt-6 rounded-2xl border border-dashed border-slate-200 bg-slate-50 px-5 py-12 text-center text-sm text-slate-600">
                      Loading report data...
                    </div>
                  ) : (
                    <div className="mt-6 space-y-4">
                      {(report?.breakdown ?? []).map((item) => {
                        const barWidth =
                          item.count === 0 ? 0 : Math.max(item.share, 8);

                        return (
                          <div
                            key={item.status}
                            className={`rounded-2xl border px-5 py-4 ${statusAccentStyles[item.status]}`}
                          >
                            <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
                              <div>
                                <h3 className="text-lg font-semibold">
                                  {item.label}
                                </h3>
                                <p className="text-sm opacity-80">
                                  {item.count} item{item.count === 1 ? "" : "s"}
                                </p>
                              </div>
                              <p className="text-sm font-medium">
                                {formatPercent(item.share)} of selected work
                              </p>
                            </div>

                            <div className="mt-4 h-3 overflow-hidden rounded-full bg-white/70">
                              <div
                                className={`h-full rounded-full transition-[width] duration-300 ${statusBarStyles[item.status]}`}
                                style={{ width: `${barWidth}%` }}
                              />
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  )}
                </section>
              </>
            )}
          </section>
        </section>
      </div>
    </main>
  );
}
