import { serializeDueDate } from "./deadlines";
import { query } from "./db";
import {
  createNotification,
  type NotificationPriority,
} from "./notifications";

const DATE_ONLY_PATTERN = /^(\d{4})-(\d{2})-(\d{2})$/;
const DEFAULT_REMINDER_TIMING_DAYS = [1, 0] as const;
const MILLISECONDS_PER_DAY = 24 * 60 * 60 * 1000;
const REMINDER_NOTIFICATION_TYPE = "reminder";
const REMINDER_TIMING_ENV_VAR = "REMINDER_TIMING_DAYS";

type ReminderTodoRow = {
  id: string;
  user_id: string;
  owner_email: string;
  assignee_id: string | null;
  assignee_email: string | null;
  title: string;
  due_date: Date | string;
};

type NotificationLookupRow = {
  id: string;
};

type ReminderTodo = {
  id: string;
  userId: string;
  ownerEmail: string;
  assigneeId: string | null;
  assigneeEmail: string | null;
  title: string;
  dueDate: string;
};

export type ReminderGenerationOptions = {
  referenceDate?: Date;
  timingDays?: readonly number[] | string;
};

export type ReminderDeliveryRecord = {
  notificationId: string;
  recipientUserId: string;
  todoId: string;
  eventKey: string;
  dueDate: string;
  daysUntilDue: number;
};

export type ReminderGenerationResult = {
  referenceDate: string;
  timingDays: number[];
  dueSoonTodoCount: number;
  candidateCount: number;
  generatedCount: number;
  existingCount: number;
  filteredCount: number;
  reminders: ReminderDeliveryRecord[];
};

export class ReminderConfigurationError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "ReminderConfigurationError";
  }
}

function formatDateParts(year: number, month: number, day: number): string {
  return `${year}-${`${month}`.padStart(2, "0")}-${`${day}`.padStart(2, "0")}`;
}

function formatUtcDateOnly(value: Date): string {
  return formatDateParts(
    value.getUTCFullYear(),
    value.getUTCMonth() + 1,
    value.getUTCDate(),
  );
}

function parseDateOnly(value: string): Date {
  const match = DATE_ONLY_PATTERN.exec(value);

  if (!match) {
    throw new ReminderConfigurationError(
      `Expected a YYYY-MM-DD date value, received "${value}".`,
    );
  }

  const year = Number.parseInt(match[1], 10);
  const month = Number.parseInt(match[2], 10);
  const day = Number.parseInt(match[3], 10);
  const parsedDate = new Date(Date.UTC(year, month - 1, day));

  if (formatUtcDateOnly(parsedDate) !== value) {
    throw new ReminderConfigurationError(`Invalid date value "${value}".`);
  }

  return parsedDate;
}

function addDaysToDateOnly(value: string, days: number): string {
  const nextDate = parseDateOnly(value);
  nextDate.setUTCDate(nextDate.getUTCDate() + days);
  return formatUtcDateOnly(nextDate);
}

function getDaysUntilDue(dueDate: string, referenceDate: string): number {
  const differenceInMilliseconds =
    parseDateOnly(dueDate).getTime() - parseDateOnly(referenceDate).getTime();

  return Math.round(differenceInMilliseconds / MILLISECONDS_PER_DAY);
}

function normalizeReminderTimingDay(value: unknown): number {
  const parsedValue =
    typeof value === "number"
      ? value
      : Number.parseInt(`${value}`.trim(), 10);

  if (!Number.isInteger(parsedValue) || parsedValue < 0) {
    throw new ReminderConfigurationError(
      "Reminder timing values must be non-negative integers.",
    );
  }

  return parsedValue;
}

export function normalizeReminderTimingDays(
  value:
    | readonly number[]
    | string
    | undefined = process.env[REMINDER_TIMING_ENV_VAR],
): number[] {
  if (value === undefined) {
    return [...DEFAULT_REMINDER_TIMING_DAYS];
  }

  let rawValues: Array<number | string>;

  if (typeof value === "string") {
    rawValues = value
      .split(",")
      .map((entry: string) => entry.trim())
      .filter((entry: string) => Boolean(entry));
  } else {
    rawValues = [...value];
  }

  if (rawValues.length === 0) {
    throw new ReminderConfigurationError(
      `${REMINDER_TIMING_ENV_VAR} must include at least one timing value.`,
    );
  }

  const normalizedValues = rawValues.map((entry) =>
    normalizeReminderTimingDay(entry),
  );

  return [...new Set(normalizedValues)].sort((left, right) => right - left);
}

export function getConfiguredReminderTimingDays(): number[] {
  return normalizeReminderTimingDays();
}

function buildReminderEventKey(
  todoId: string,
  dueDate: string,
  daysUntilDue: number,
): string {
  return `todo.reminder.${todoId}.${dueDate}.${daysUntilDue}d`;
}

function buildReminderTitle(daysUntilDue: number): string {
  if (daysUntilDue === 0) {
    return "Work item due today";
  }

  return `Work item due in ${daysUntilDue} day${daysUntilDue === 1 ? "" : "s"}`;
}

function buildReminderBody(todo: ReminderTodo, daysUntilDue: number): string {
  if (daysUntilDue === 0) {
    return `"${todo.title}" is due today (${todo.dueDate}).`;
  }

  return `"${todo.title}" is due on ${todo.dueDate}.`;
}

function getReminderPriority(daysUntilDue: number): NotificationPriority {
  return daysUntilDue === 0 ? "high" : "normal";
}

function mapReminderTodoRow(row: ReminderTodoRow): ReminderTodo {
  return {
    id: row.id,
    userId: row.user_id,
    ownerEmail: row.owner_email,
    assigneeId: row.assignee_id,
    assigneeEmail: row.assignee_email,
    title: row.title,
    dueDate: serializeDueDate(row.due_date),
  };
}

function getReminderRecipientUserIds(todo: ReminderTodo): string[] {
  return [
    ...new Set(
      [todo.userId, todo.assigneeId].filter(
        (value): value is string => Boolean(value),
      ),
    ),
  ];
}

async function listDueSoonTodos(
  referenceDate: string,
  timingDays: readonly number[],
): Promise<ReminderTodo[]> {
  const maxLeadTime = Math.max(...timingDays);
  const latestDueDate = addDaysToDateOnly(referenceDate, maxLeadTime);
  const result = await query<ReminderTodoRow>(
    `
      SELECT
        todos.id,
        todos.user_id,
        owners.email AS owner_email,
        todos.assignee_id,
        assignees.email AS assignee_email,
        todos.title,
        todos.due_date
      FROM todos
      INNER JOIN users AS owners
        ON owners.id = todos.user_id
      LEFT JOIN users AS assignees
        ON assignees.id = todos.assignee_id
      WHERE todos.completed = FALSE
        AND todos.due_date IS NOT NULL
        AND todos.due_date BETWEEN $1::date AND $2::date
      ORDER BY todos.due_date ASC, todos.created_at ASC, todos.id ASC
    `,
    [referenceDate, latestDueDate],
  );

  return result.rows.map(mapReminderTodoRow);
}

async function notificationExists(
  userId: string,
  eventKey: string,
): Promise<boolean> {
  const result = await query<NotificationLookupRow>(
    `
      SELECT id
      FROM notifications
      WHERE user_id = $1
        AND event_key = $2
      LIMIT 1
    `,
    [userId, eventKey],
  );

  return Boolean(result.rows[0]);
}

export async function generateReminders(
  options: ReminderGenerationOptions = {},
): Promise<ReminderGenerationResult> {
  const referenceDate = formatUtcDateOnly(options.referenceDate ?? new Date());
  const timingDays = normalizeReminderTimingDays(options.timingDays);
  const reminderOffsets = new Set(timingDays);
  const dueSoonTodos = await listDueSoonTodos(referenceDate, timingDays);
  const reminders: ReminderDeliveryRecord[] = [];

  let candidateCount = 0;
  let existingCount = 0;
  let filteredCount = 0;

  for (const todo of dueSoonTodos) {
    const daysUntilDue = getDaysUntilDue(todo.dueDate, referenceDate);

    if (!reminderOffsets.has(daysUntilDue)) {
      continue;
    }

    for (const recipientUserId of getReminderRecipientUserIds(todo)) {
      const eventKey = buildReminderEventKey(
        todo.id,
        todo.dueDate,
        daysUntilDue,
      );

      candidateCount += 1;

      if (await notificationExists(recipientUserId, eventKey)) {
        existingCount += 1;
        continue;
      }

      const notification = await createNotification(recipientUserId, {
        eventKey,
        type: REMINDER_NOTIFICATION_TYPE,
        priority: getReminderPriority(daysUntilDue),
        title: buildReminderTitle(daysUntilDue),
        body: buildReminderBody(todo, daysUntilDue),
        metadata: {
          todoId: todo.id,
          dueDate: todo.dueDate,
          daysUntilDue,
          ownerEmail: todo.ownerEmail,
          assigneeEmail: todo.assigneeEmail,
        },
      });

      if (!notification) {
        filteredCount += 1;
        continue;
      }

      reminders.push({
        notificationId: notification.id,
        recipientUserId,
        todoId: todo.id,
        eventKey,
        dueDate: todo.dueDate,
        daysUntilDue,
      });
    }
  }

  return {
    referenceDate,
    timingDays,
    dueSoonTodoCount: dueSoonTodos.length,
    candidateCount,
    generatedCount: reminders.length,
    existingCount,
    filteredCount,
    reminders,
  };
}
