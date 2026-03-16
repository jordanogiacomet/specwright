import "server-only";

import { CONTENT_STATUSES, type ContentStatus } from "./content-status.ts";
import { getDatabasePool } from "./db.ts";
import { EDITORIAL_ROLES, type UserRole } from "./permissions.ts";

const DEFAULT_LOOKBACK_DAYS = 27;
const DATE_INPUT_PATTERN = /^\d{4}-\d{2}-\d{2}$/;

const REPORT_STATUS_LABELS: Record<ContentStatus, string> = {
  archived: "Archived",
  draft: "Draft",
  in_review: "In review",
  published: "Published",
  scheduled: "Scheduled",
};

const TEAM_LABELS: Record<ReportTeam, string> = {
  admin: "Admins",
  editor: "Editors",
  reviewer: "Reviewers",
};

export type ReportTeam = (typeof EDITORIAL_ROLES)[number];

export type ReportSearchParams = {
  endDate?: string | string[];
  startDate?: string | string[];
  team?: string | string[];
};

export type ReportFilters = {
  endAtExclusive: Date;
  endDate: string;
  startAt: Date;
  startDate: string;
  team: ReportTeam | "all";
};

export type WorkflowProgressReport = {
  generatedAt: Date;
  statusDistribution: Array<{
    count: number;
    label: string;
    share: number;
    status: ContentStatus;
  }>;
  summary: {
    contributors: number;
    inReviewArticles: number;
    publishedArticles: number;
    scheduledArticles: number;
    totalArticles: number;
  };
  weeklySummary: Array<{
    inReviewArticles: number;
    itemsTouched: number;
    publishedArticles: number;
    scheduledArticles: number;
    weekEnd: string;
    weekStart: string;
  }>;
};

type SummaryRow = {
  contributors: number;
  in_review_articles: number;
  published_articles: number;
  scheduled_articles: number;
  total_articles: number;
};

type StatusDistributionRow = {
  status: ContentStatus;
  total: number;
};

type WeeklySummaryRow = {
  in_review_articles: number;
  items_touched: number;
  published_articles: number;
  scheduled_articles: number;
  week_end: string;
  week_start: string;
};

export const REPORT_TEAM_OPTIONS = EDITORIAL_ROLES.map((role) => ({
  label: TEAM_LABELS[role],
  value: role,
})) as ReadonlyArray<{
  label: string;
  value: ReportTeam;
}>;

const getSearchParamValue = (value: string | string[] | undefined): string => {
  if (typeof value === "string") {
    return value.trim();
  }

  if (Array.isArray(value)) {
    return typeof value[0] === "string" ? value[0].trim() : "";
  }

  return "";
};

const addUtcDays = (date: Date, days: number): Date =>
  new Date(
    Date.UTC(
      date.getUTCFullYear(),
      date.getUTCMonth(),
      date.getUTCDate() + days,
    ),
  );

const formatDateInput = (date: Date): string => date.toISOString().slice(0, 10);

const getTodayUtc = (): Date => {
  const now = new Date();

  return new Date(
    Date.UTC(now.getUTCFullYear(), now.getUTCMonth(), now.getUTCDate()),
  );
};

const parseDateInput = (value: string): Date | null => {
  if (!DATE_INPUT_PATTERN.test(value)) {
    return null;
  }

  const [yearValue, monthValue, dayValue] = value.split("-");
  const year = Number.parseInt(yearValue, 10);
  const month = Number.parseInt(monthValue, 10);
  const day = Number.parseInt(dayValue, 10);

  if (
    !Number.isInteger(year) ||
    !Number.isInteger(month) ||
    !Number.isInteger(day)
  ) {
    return null;
  }

  const parsedDate = new Date(Date.UTC(year, month - 1, day));

  if (
    parsedDate.getUTCFullYear() !== year ||
    parsedDate.getUTCMonth() !== month - 1 ||
    parsedDate.getUTCDate() !== day
  ) {
    return null;
  }

  return parsedDate;
};

const parseReportTeam = (value: string): ReportTeam | "all" => {
  if ((EDITORIAL_ROLES as readonly string[]).includes(value)) {
    return value as UserRole as ReportTeam;
  }

  return "all";
};

export const getReportTeamLabel = (team: ReportTeam | "all"): string =>
  team === "all" ? "All editorial teams" : TEAM_LABELS[team];

export const normalizeReportFilters = (
  searchParams: ReportSearchParams,
): ReportFilters => {
  const today = getTodayUtc();
  const defaultStartDate = addUtcDays(today, -DEFAULT_LOOKBACK_DAYS);

  const requestedStartDate = parseDateInput(
    getSearchParamValue(searchParams.startDate),
  );
  const requestedEndDate = parseDateInput(
    getSearchParamValue(searchParams.endDate),
  );

  let startAt = requestedStartDate ?? defaultStartDate;
  let endAt = requestedEndDate ?? today;

  if (startAt.getTime() > endAt.getTime()) {
    [startAt, endAt] = [endAt, startAt];
  }

  return {
    endAtExclusive: addUtcDays(endAt, 1),
    endDate: formatDateInput(endAt),
    startAt,
    startDate: formatDateInput(startAt),
    team: parseReportTeam(getSearchParamValue(searchParams.team)),
  };
};

export async function getWorkflowProgressReport(
  filters: ReportFilters,
): Promise<WorkflowProgressReport> {
  const pool = getDatabasePool();
  const teamFilter = filters.team === "all" ? null : filters.team;
  const queryParams = [
    filters.startAt.toISOString(),
    filters.endAtExclusive.toISOString(),
    teamFilter,
  ];

  const [summaryResult, statusResult, weeklyResult] = await Promise.all([
    pool.query<SummaryRow>(
      `
        select
          count(*)::int as total_articles,
          count(*) filter (where a.status = 'published')::int as published_articles,
          count(*) filter (where a.status = 'scheduled')::int as scheduled_articles,
          count(*) filter (where a.status = 'in_review')::int as in_review_articles,
          count(distinct a.author_id)::int as contributors
        from articles a
        left join users u on u.id = a.author_id
        where a.updated_at >= $1
          and a.updated_at < $2
          and ($3::text is null or u.role::text = $3)
      `,
      queryParams,
    ),
    pool.query<StatusDistributionRow>(
      `
        select
          a.status::text as status,
          count(*)::int as total
        from articles a
        left join users u on u.id = a.author_id
        where a.updated_at >= $1
          and a.updated_at < $2
          and ($3::text is null or u.role::text = $3)
        group by a.status
      `,
      queryParams,
    ),
    pool.query<WeeklySummaryRow>(
      `
        select
          to_char(date_trunc('week', a.updated_at at time zone 'utc'), 'YYYY-MM-DD') as week_start,
          to_char(
            date_trunc('week', a.updated_at at time zone 'utc') + interval '6 days',
            'YYYY-MM-DD'
          ) as week_end,
          count(*)::int as items_touched,
          count(*) filter (where a.status = 'published')::int as published_articles,
          count(*) filter (where a.status = 'scheduled')::int as scheduled_articles,
          count(*) filter (where a.status = 'in_review')::int as in_review_articles
        from articles a
        left join users u on u.id = a.author_id
        where a.updated_at >= $1
          and a.updated_at < $2
          and ($3::text is null or u.role::text = $3)
        group by 1, 2
        order by 1 desc
      `,
      queryParams,
    ),
  ]);

  const summaryRow = summaryResult.rows[0] ?? {
    contributors: 0,
    in_review_articles: 0,
    published_articles: 0,
    scheduled_articles: 0,
    total_articles: 0,
  };
  const totalArticles = summaryRow.total_articles;
  const statusCounts = new Map(
    statusResult.rows.map((row) => [row.status, row.total] as const),
  );

  return {
    generatedAt: new Date(),
    statusDistribution: CONTENT_STATUSES.map((status) => {
      const count = statusCounts.get(status) ?? 0;

      return {
        count,
        label: REPORT_STATUS_LABELS[status],
        share: totalArticles > 0 ? count / totalArticles : 0,
        status,
      };
    }),
    summary: {
      contributors: summaryRow.contributors,
      inReviewArticles: summaryRow.in_review_articles,
      publishedArticles: summaryRow.published_articles,
      scheduledArticles: summaryRow.scheduled_articles,
      totalArticles,
    },
    weeklySummary: weeklyResult.rows.map((row) => ({
      inReviewArticles: row.in_review_articles,
      itemsTouched: row.items_touched,
      publishedArticles: row.published_articles,
      scheduledArticles: row.scheduled_articles,
      weekEnd: row.week_end,
      weekStart: row.week_start,
    })),
  };
}
