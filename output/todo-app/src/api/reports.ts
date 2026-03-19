import {
  Router,
  type ErrorRequestHandler,
  type Request,
  type RequestHandler,
  type Response,
} from "express";

import { requireAuth } from "../lib/auth";
import { query } from "../lib/db";
import { createLogger } from "../lib/logger";
import {
  workItemStatusLabels,
  workItemStatuses,
  type WorkItemStatus,
} from "../lib/status-machine";

const reportsLogger = createLogger({
  component: "reports-router",
  service: "todo-app-api",
});

const DEFAULT_REPORT_RANGE_DAYS = 30;
const DATE_ONLY_PATTERN = /^\d{4}-\d{2}-\d{2}$/;

type StatusCountRow = {
  status: WorkItemStatus;
  count: number;
};

type SummaryRow = {
  total: number;
  completed: number;
  overdue: number;
  high_priority: number;
};

type ReportFilters = {
  from: string;
  to: string;
};

export class ReportValidationError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "ReportValidationError";
  }
}

function asyncHandler(
  handler: (request: Request, response: Response) => Promise<void>,
): RequestHandler {
  return (request, response, next) => {
    void handler(request, response).catch(next);
  };
}

function getSingleQueryValue(value: unknown, fieldName: string): string | undefined {
  if (value === undefined) {
    return undefined;
  }

  if (Array.isArray(value)) {
    throw new ReportValidationError(`${fieldName} must be provided only once.`);
  }

  if (typeof value !== "string") {
    throw new ReportValidationError(`${fieldName} must be a string.`);
  }

  return value;
}

function formatDateOnlyUtc(value: Date): string {
  return value.toISOString().slice(0, 10);
}

function parseDateOnly(value: string, fieldName: string): Date {
  if (!DATE_ONLY_PATTERN.test(value)) {
    throw new ReportValidationError(
      `${fieldName} must use the YYYY-MM-DD format.`,
    );
  }

  const parsedValue = new Date(`${value}T00:00:00.000Z`);

  if (
    Number.isNaN(parsedValue.getTime()) ||
    formatDateOnlyUtc(parsedValue) !== value
  ) {
    throw new ReportValidationError(`${fieldName} must be a valid date.`);
  }

  return parsedValue;
}

function addUtcDays(value: Date, days: number): Date {
  const nextValue = new Date(value);
  nextValue.setUTCDate(nextValue.getUTCDate() + days);
  return nextValue;
}

function getDefaultReportRange(): ReportFilters {
  const today = new Date();
  const endDate = new Date(
    Date.UTC(today.getUTCFullYear(), today.getUTCMonth(), today.getUTCDate()),
  );
  const startDate = addUtcDays(endDate, -(DEFAULT_REPORT_RANGE_DAYS - 1));

  return {
    from: formatDateOnlyUtc(startDate),
    to: formatDateOnlyUtc(endDate),
  };
}

function parseReportFilters(request: Request): ReportFilters {
  const fromValue = getSingleQueryValue(request.query.from, "from");
  const toValue = getSingleQueryValue(request.query.to, "to");

  if (!fromValue && !toValue) {
    return getDefaultReportRange();
  }

  const today = getDefaultReportRange().to;
  const resolvedTo = toValue ?? today;
  const resolvedToDate = parseDateOnly(resolvedTo, "to");
  const resolvedFrom =
    fromValue ??
    formatDateOnlyUtc(addUtcDays(resolvedToDate, -(DEFAULT_REPORT_RANGE_DAYS - 1)));

  parseDateOnly(resolvedFrom, "from");

  if (resolvedFrom > resolvedTo) {
    throw new ReportValidationError("from must be on or before to.");
  }

  return {
    from: resolvedFrom,
    to: resolvedTo,
  };
}

function getCompletionRate(total: number, completed: number): number {
  if (total === 0) {
    return 0;
  }

  return Number(((completed / total) * 100).toFixed(1));
}

const getStatusDistributionHandler = asyncHandler(async (request, response) => {
  const filters = parseReportFilters(request);
  const values = [request.auth!.user.id, filters.from, filters.to];

  const [summaryResult, statusResult] = await Promise.all([
    query<SummaryRow>(
      `
        WITH filtered_todos AS (
          SELECT status, priority, due_date
          FROM todos
          WHERE user_id = $1
            AND created_at >= $2::date
            AND created_at < ($3::date + INTERVAL '1 day')
        )
        SELECT
          COUNT(*)::int AS total,
          COUNT(*) FILTER (WHERE status = 'completed')::int AS completed,
          COUNT(*) FILTER (
            WHERE due_date IS NOT NULL
              AND due_date < CURRENT_DATE
              AND status <> 'completed'
          )::int AS overdue,
          COUNT(*) FILTER (WHERE priority = 'high')::int AS high_priority
        FROM filtered_todos
      `,
      values,
    ),
    query<StatusCountRow>(
      `
        WITH filtered_todos AS (
          SELECT status
          FROM todos
          WHERE user_id = $1
            AND created_at >= $2::date
            AND created_at < ($3::date + INTERVAL '1 day')
        )
        SELECT status, COUNT(*)::int AS count
        FROM filtered_todos
        GROUP BY status
      `,
      values,
    ),
  ]);

  const summary = summaryResult.rows[0] ?? {
    total: 0,
    completed: 0,
    overdue: 0,
    high_priority: 0,
  };
  const statusCountMap = new Map(
    statusResult.rows.map((row) => [row.status, row.count]),
  );

  response.status(200).json({
    reportType: "status_distribution",
    generatedAt: new Date().toISOString(),
    filters: {
      from: filters.from,
      to: filters.to,
      dateField: "createdAt",
    },
    summary: {
      total: summary.total,
      completed: summary.completed,
      overdue: summary.overdue,
      highPriority: summary.high_priority,
      completionRate: getCompletionRate(summary.total, summary.completed),
    },
    breakdown: workItemStatuses.map((status) => {
      const count = statusCountMap.get(status) ?? 0;

      return {
        status,
        label: workItemStatusLabels[status],
        count,
        share:
          summary.total === 0
            ? 0
            : Number(((count / summary.total) * 100).toFixed(1)),
      };
    }),
  });
});

const reportsErrorHandler: ErrorRequestHandler = (error, _request, response) => {
  if (error instanceof ReportValidationError) {
    response.status(400).json({
      error: error.name,
      message: error.message,
    });
    return;
  }

  reportsLogger.error("Unexpected reports API error", {
    error,
  });
  response.status(500).json({
    error: "InternalServerError",
    message: "Unexpected error while generating the report.",
  });
};

const reportsRouter = Router();

reportsRouter.use(requireAuth);
reportsRouter.get("/status-distribution", getStatusDistributionHandler);
reportsRouter.use(reportsErrorHandler);

export { reportsRouter };
