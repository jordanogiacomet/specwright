import Link from "next/link";
import { redirect } from "next/navigation";

import AdminShell from "@/components/AdminShell";
import { getCurrentUser } from "@/lib/auth";
import {
  REPORT_TEAM_OPTIONS,
  getReportTeamLabel,
  getWorkflowProgressReport,
  normalizeReportFilters,
  type ReportSearchParams,
} from "@/lib/reports";

export const dynamic = "force-dynamic";
export const runtime = "nodejs";

type ReportsPageProps = {
  searchParams: Promise<ReportSearchParams>;
};

const dateFormatter = new Intl.DateTimeFormat("en-US", {
  dateStyle: "medium",
});
const dateTimeFormatter = new Intl.DateTimeFormat("en-US", {
  dateStyle: "medium",
  timeStyle: "short",
});
const numberFormatter = new Intl.NumberFormat("en-US");

const formatDisplayDate = (value: string): string =>
  dateFormatter.format(new Date(`${value}T00:00:00.000Z`));

export default async function ReportsPage({ searchParams }: ReportsPageProps) {
  const [currentUser, resolvedSearchParams] = await Promise.all([
    getCurrentUser(),
    searchParams,
  ]);

  if (!currentUser) {
    redirect("/login");
  }

  const filters = normalizeReportFilters(resolvedSearchParams);
  const report = await getWorkflowProgressReport(filters);

  const summaryCards = [
    {
      label: "Articles touched",
      value: report.summary.totalArticles,
    },
    {
      label: "Published",
      value: report.summary.publishedArticles,
    },
    {
      label: "Scheduled",
      value: report.summary.scheduledArticles,
    },
    {
      label: "Contributors",
      value: report.summary.contributors,
    },
  ];

  return (
    <AdminShell currentUser={currentUser}>
      <div className="space-y-6">
        <section className="rounded-[2rem] border border-slate-200 bg-white p-8 shadow-sm shadow-slate-200/60">
          <div className="flex flex-col gap-6 xl:flex-row xl:items-end xl:justify-between">
            <div className="max-w-3xl space-y-3">
              <p className="text-sm font-medium uppercase tracking-[0.2em] text-slate-500">
                Reports
              </p>
              <h1 className="text-3xl font-semibold tracking-tight text-slate-950">
                Workflow progress report
              </h1>
              <p className="text-base leading-7 text-slate-600">
                Database-backed visibility into article workflow activity,
                filtered by update window and editorial team.
              </p>
            </div>

            <div className="rounded-[1.5rem] bg-slate-100 px-5 py-4">
              <p className="text-xs font-medium uppercase tracking-[0.18em] text-slate-500">
                Generated
              </p>
              <p className="mt-2 text-sm font-medium text-slate-950">
                {dateTimeFormatter.format(report.generatedAt)}
              </p>
            </div>
          </div>

          <div className="mt-6 flex flex-wrap gap-3 text-sm text-slate-600">
            <span className="rounded-full bg-slate-100 px-4 py-2">
              Range: {formatDisplayDate(filters.startDate)} to{" "}
              {formatDisplayDate(filters.endDate)}
            </span>
            <span className="rounded-full bg-slate-100 px-4 py-2">
              Team: {getReportTeamLabel(filters.team)}
            </span>
          </div>
        </section>

        <section className="rounded-[2rem] border border-slate-200 bg-white p-8 shadow-sm shadow-slate-200/60">
          <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
            <div>
              <p className="text-sm font-medium uppercase tracking-[0.2em] text-slate-500">
                Filters
              </p>
              <h2 className="mt-2 text-2xl font-semibold tracking-tight text-slate-950">
                Refine the report window
              </h2>
            </div>

            <Link
              href="/reports"
              className="text-sm font-medium text-slate-500 transition hover:text-slate-950"
            >
              Reset filters
            </Link>
          </div>

          <form className="mt-6 grid gap-4 md:grid-cols-2 xl:grid-cols-[minmax(0,1fr)_minmax(0,1fr)_minmax(0,1fr)_auto]">
            <label className="space-y-2">
              <span className="text-sm font-medium text-slate-700">Start date</span>
              <input
                type="date"
                name="startDate"
                defaultValue={filters.startDate}
                className="w-full rounded-[1rem] border border-slate-300 bg-slate-50 px-4 py-3 text-sm text-slate-950 outline-none transition focus:border-slate-950 focus:bg-white"
              />
            </label>

            <label className="space-y-2">
              <span className="text-sm font-medium text-slate-700">End date</span>
              <input
                type="date"
                name="endDate"
                defaultValue={filters.endDate}
                className="w-full rounded-[1rem] border border-slate-300 bg-slate-50 px-4 py-3 text-sm text-slate-950 outline-none transition focus:border-slate-950 focus:bg-white"
              />
            </label>

            <label className="space-y-2">
              <span className="text-sm font-medium text-slate-700">
                Team (author role)
              </span>
              <select
                name="team"
                defaultValue={filters.team}
                className="w-full rounded-[1rem] border border-slate-300 bg-slate-50 px-4 py-3 text-sm text-slate-950 outline-none transition focus:border-slate-950 focus:bg-white"
              >
                <option value="all">All editorial teams</option>
                {REPORT_TEAM_OPTIONS.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </label>

            <button
              type="submit"
              className="inline-flex items-center justify-center rounded-full bg-slate-950 px-5 py-3 text-sm font-medium text-white transition hover:bg-slate-800"
            >
              Apply filters
            </button>
          </form>

          <p className="mt-4 text-sm leading-6 text-slate-500">
            The report uses article <code>updated_at</code> activity from the
            database. Team filters are based on the author&apos;s user role.
          </p>
        </section>

        <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          {summaryCards.map((card) => (
            <article
              key={card.label}
              className="rounded-[1.75rem] border border-slate-200 bg-white px-6 py-5 shadow-sm shadow-slate-200/60"
            >
              <p className="text-xs font-medium uppercase tracking-[0.18em] text-slate-500">
                {card.label}
              </p>
              <p className="mt-3 text-3xl font-semibold tracking-tight text-slate-950">
                {numberFormatter.format(card.value)}
              </p>
            </article>
          ))}
        </section>

        <div className="grid gap-6 xl:grid-cols-[minmax(0,1.15fr)_minmax(0,1fr)]">
          <section className="rounded-[2rem] border border-slate-200 bg-white p-8 shadow-sm shadow-slate-200/60">
            <div className="flex items-center justify-between gap-4">
              <div>
                <p className="text-sm font-medium uppercase tracking-[0.2em] text-slate-500">
                  Report type
                </p>
                <h2 className="mt-2 text-2xl font-semibold tracking-tight text-slate-950">
                  Status distribution
                </h2>
              </div>
              <p className="text-sm text-slate-500">
                {numberFormatter.format(report.summary.totalArticles)} matched
              </p>
            </div>

            <div className="mt-6 space-y-4">
              {report.statusDistribution.map((item) => (
                <article
                  key={item.status}
                  className="rounded-[1.5rem] border border-slate-200 bg-slate-50 p-5"
                >
                  <div className="flex items-center justify-between gap-4">
                    <div>
                      <h3 className="text-lg font-semibold tracking-tight text-slate-950">
                        {item.label}
                      </h3>
                      <p className="mt-1 text-sm text-slate-500">
                        {Math.round(item.share * 100)}% of filtered activity
                      </p>
                    </div>
                    <p className="text-2xl font-semibold tracking-tight text-slate-950">
                      {numberFormatter.format(item.count)}
                    </p>
                  </div>

                  <div className="mt-4 h-3 overflow-hidden rounded-full bg-slate-200">
                    <div
                      className="h-full rounded-full bg-slate-950 transition-[width]"
                      style={{ width: `${item.share * 100}%` }}
                    />
                  </div>
                </article>
              ))}
            </div>
          </section>

          <section className="rounded-[2rem] border border-slate-200 bg-white p-8 shadow-sm shadow-slate-200/60">
            <div className="flex items-center justify-between gap-4">
              <div>
                <p className="text-sm font-medium uppercase tracking-[0.2em] text-slate-500">
                  Report type
                </p>
                <h2 className="mt-2 text-2xl font-semibold tracking-tight text-slate-950">
                  Weekly summary
                </h2>
              </div>
              <p className="text-sm text-slate-500">Grouped by week</p>
            </div>

            {report.weeklySummary.length === 0 ? (
              <div className="mt-6 rounded-[1.5rem] border border-dashed border-slate-300 bg-slate-50 p-6">
                <p className="text-base font-medium text-slate-950">
                  No workflow activity in this window.
                </p>
                <p className="mt-2 text-sm leading-6 text-slate-500">
                  Expand the date range or clear the team filter to inspect a
                  broader slice of operational data.
                </p>
              </div>
            ) : (
              <div className="mt-6 overflow-hidden rounded-[1.5rem] border border-slate-200">
                <table className="min-w-full divide-y divide-slate-200 text-left text-sm">
                  <thead className="bg-slate-50 text-slate-500">
                    <tr>
                      <th className="px-4 py-3 font-medium">Week</th>
                      <th className="px-4 py-3 font-medium">Touched</th>
                      <th className="px-4 py-3 font-medium">Published</th>
                      <th className="px-4 py-3 font-medium">In review</th>
                      <th className="px-4 py-3 font-medium">Scheduled</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-200 bg-white text-slate-700">
                    {report.weeklySummary.map((week) => (
                      <tr key={week.weekStart}>
                        <td className="px-4 py-4 font-medium text-slate-950">
                          {formatDisplayDate(week.weekStart)} to{" "}
                          {formatDisplayDate(week.weekEnd)}
                        </td>
                        <td className="px-4 py-4">
                          {numberFormatter.format(week.itemsTouched)}
                        </td>
                        <td className="px-4 py-4">
                          {numberFormatter.format(week.publishedArticles)}
                        </td>
                        <td className="px-4 py-4">
                          {numberFormatter.format(week.inReviewArticles)}
                        </td>
                        <td className="px-4 py-4">
                          {numberFormatter.format(week.scheduledArticles)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </section>
        </div>
      </div>
    </AdminShell>
  );
}
