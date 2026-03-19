import { randomUUID } from "node:crypto";

import { query } from "./db";

const NOTIFICATION_TITLE_MAX_LENGTH = 160;
const NOTIFICATION_BODY_MAX_LENGTH = 500;
const NOTIFICATION_EVENT_KEY_MAX_LENGTH = 120;
const NOTIFICATION_TYPE_MAX_LENGTH = 64;
const DEFAULT_NOTIFICATION_LIMIT = 25;
const MAX_NOTIFICATION_LIMIT = 100;

const notificationPriorities = ["low", "normal", "high", "critical"] as const;

const priorityRank: Record<NotificationPriority, number> = {
  low: 0,
  normal: 1,
  high: 2,
  critical: 3,
};

type NotificationRow = {
  id: string;
  user_id: string;
  event_key: string;
  type: string;
  priority: NotificationPriority;
  title: string;
  body: string;
  metadata: unknown;
  is_read: boolean;
  read_at: Date | string | null;
  created_at: Date | string;
};

type NotificationPreferenceRow = {
  user_id: string;
  notifications_enabled: boolean;
  minimum_priority: NotificationPriority;
  updated_at: Date | string;
};

type NotificationCountRow = {
  count: string;
};

export type NotificationPriority = (typeof notificationPriorities)[number];

export type NotificationRecord = {
  id: string;
  userId: string;
  eventKey: string;
  type: string;
  priority: NotificationPriority;
  title: string;
  body: string;
  metadata: Record<string, unknown>;
  isRead: boolean;
  readAt: string | null;
  createdAt: string;
};

export type NotificationPreferences = {
  userId: string;
  notificationsEnabled: boolean;
  minimumPriority: NotificationPriority;
  updatedAt: string;
};

export type NotificationInbox = {
  items: NotificationRecord[];
  unreadCount: number;
  preferences: NotificationPreferences;
};

export type CreateNotificationInput = {
  eventKey: string;
  type: string;
  priority?: NotificationPriority;
  title: string;
  body: string;
  metadata?: Record<string, unknown>;
};

export type UpdateNotificationReadStateInput = {
  isRead: boolean;
};

export type UpdateNotificationPreferencesInput = {
  notificationsEnabled?: boolean;
  minimumPriority?: NotificationPriority;
};

export class NotificationValidationError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "NotificationValidationError";
  }
}

export class NotificationNotFoundError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "NotificationNotFoundError";
  }
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function toIsoString(value: Date | string): string {
  return value instanceof Date
    ? value.toISOString()
    : new Date(value).toISOString();
}

function normalizeTrimmedString(
  value: unknown,
  fieldName: string,
  maxLength: number,
): string {
  if (typeof value !== "string") {
    throw new NotificationValidationError(`${fieldName} must be a string.`);
  }

  const normalizedValue = value.trim();

  if (!normalizedValue) {
    throw new NotificationValidationError(`${fieldName} is required.`);
  }

  if (normalizedValue.length > maxLength) {
    throw new NotificationValidationError(
      `${fieldName} must be ${maxLength} characters or fewer.`,
    );
  }

  return normalizedValue;
}

function normalizePriority(
  value: unknown,
  fieldName = "minimumPriority",
): NotificationPriority {
  if (typeof value !== "string") {
    throw new NotificationValidationError(`${fieldName} must be a string.`);
  }

  if (!notificationPriorities.includes(value as NotificationPriority)) {
    throw new NotificationValidationError(
      `${fieldName} must be one of: ${notificationPriorities.join(", ")}.`,
    );
  }

  return value as NotificationPriority;
}

function normalizeMetadata(value: unknown): Record<string, unknown> {
  if (value === undefined) {
    return {};
  }

  if (!isRecord(value)) {
    throw new NotificationValidationError("metadata must be a JSON object.");
  }

  return value;
}

function normalizeCreateNotificationInput(
  payload: unknown,
): Required<CreateNotificationInput> {
  if (!isRecord(payload)) {
    throw new NotificationValidationError(
      "Notification payload must be a JSON object.",
    );
  }

  return {
    eventKey: normalizeTrimmedString(
      payload.eventKey,
      "eventKey",
      NOTIFICATION_EVENT_KEY_MAX_LENGTH,
    ),
    type: normalizeTrimmedString(
      payload.type,
      "type",
      NOTIFICATION_TYPE_MAX_LENGTH,
    ),
    priority:
      payload.priority === undefined
        ? "normal"
        : normalizePriority(payload.priority, "priority"),
    title: normalizeTrimmedString(
      payload.title,
      "title",
      NOTIFICATION_TITLE_MAX_LENGTH,
    ),
    body: normalizeTrimmedString(
      payload.body,
      "body",
      NOTIFICATION_BODY_MAX_LENGTH,
    ),
    metadata: normalizeMetadata(payload.metadata),
  };
}

function normalizeReadStateInput(
  payload: unknown,
): UpdateNotificationReadStateInput {
  if (!isRecord(payload)) {
    throw new NotificationValidationError(
      "Notification read state payload must be a JSON object.",
    );
  }

  if (typeof payload.isRead !== "boolean") {
    throw new NotificationValidationError("isRead must be a boolean.");
  }

  return {
    isRead: payload.isRead,
  };
}

function normalizePreferencesUpdateInput(
  payload: unknown,
): UpdateNotificationPreferencesInput {
  if (!isRecord(payload)) {
    throw new NotificationValidationError(
      "Notification preferences payload must be a JSON object.",
    );
  }

  const nextPreferences: UpdateNotificationPreferencesInput = {};

  if ("notificationsEnabled" in payload) {
    if (typeof payload.notificationsEnabled !== "boolean") {
      throw new NotificationValidationError(
        "notificationsEnabled must be a boolean.",
      );
    }

    nextPreferences.notificationsEnabled = payload.notificationsEnabled;
  }

  if ("minimumPriority" in payload) {
    nextPreferences.minimumPriority = normalizePriority(
      payload.minimumPriority,
      "minimumPriority",
    );
  }

  return nextPreferences;
}

function normalizeMetadataOutput(value: unknown): Record<string, unknown> {
  return isRecord(value) ? value : {};
}

function mapNotificationRow(row: NotificationRow): NotificationRecord {
  return {
    id: row.id,
    userId: row.user_id,
    eventKey: row.event_key,
    type: row.type,
    priority: row.priority,
    title: row.title,
    body: row.body,
    metadata: normalizeMetadataOutput(row.metadata),
    isRead: row.is_read,
    readAt: row.read_at ? toIsoString(row.read_at) : null,
    createdAt: toIsoString(row.created_at),
  };
}

function mapNotificationPreferenceRow(
  row: NotificationPreferenceRow,
): NotificationPreferences {
  return {
    userId: row.user_id,
    notificationsEnabled: row.notifications_enabled,
    minimumPriority: row.minimum_priority,
    updatedAt: toIsoString(row.updated_at),
  };
}

function normalizeNotificationLimit(limit?: number): number {
  if (limit === undefined) {
    return DEFAULT_NOTIFICATION_LIMIT;
  }

  if (!Number.isInteger(limit) || limit < 1 || limit > MAX_NOTIFICATION_LIMIT) {
    throw new NotificationValidationError(
      `limit must be an integer between 1 and ${MAX_NOTIFICATION_LIMIT}.`,
    );
  }

  return limit;
}

async function ensureNotificationPreferences(
  userId: string,
): Promise<NotificationPreferences> {
  await query(
    `
      INSERT INTO notification_preferences (user_id)
      VALUES ($1)
      ON CONFLICT (user_id) DO NOTHING
    `,
    [userId],
  );

  const result = await query<NotificationPreferenceRow>(
    `
      SELECT user_id, notifications_enabled, minimum_priority, updated_at
      FROM notification_preferences
      WHERE user_id = $1
      LIMIT 1
    `,
    [userId],
  );

  const preferences = result.rows[0];

  if (!preferences) {
    throw new NotificationNotFoundError(
      "Notification preferences were not found.",
    );
  }

  return mapNotificationPreferenceRow(preferences);
}

function shouldDeliverNotification(
  preferences: NotificationPreferences,
  priority: NotificationPriority,
): boolean {
  if (!preferences.notificationsEnabled) {
    return false;
  }

  return priorityRank[priority] >= priorityRank[preferences.minimumPriority];
}

export async function getNotificationPreferences(
  userId: string,
): Promise<NotificationPreferences> {
  return ensureNotificationPreferences(userId);
}

export async function updateNotificationPreferences(
  userId: string,
  payload: unknown,
): Promise<NotificationPreferences> {
  const updates = normalizePreferencesUpdateInput(payload);
  const currentPreferences = await ensureNotificationPreferences(userId);

  const nextPreferences = {
    notificationsEnabled:
      updates.notificationsEnabled ?? currentPreferences.notificationsEnabled,
    minimumPriority:
      updates.minimumPriority ?? currentPreferences.minimumPriority,
  };

  const result = await query<NotificationPreferenceRow>(
    `
      INSERT INTO notification_preferences (
        user_id,
        notifications_enabled,
        minimum_priority
      )
      VALUES ($1, $2, $3)
      ON CONFLICT (user_id) DO UPDATE
      SET
        notifications_enabled = EXCLUDED.notifications_enabled,
        minimum_priority = EXCLUDED.minimum_priority,
        updated_at = CURRENT_TIMESTAMP
      RETURNING user_id, notifications_enabled, minimum_priority, updated_at
    `,
    [
      userId,
      nextPreferences.notificationsEnabled,
      nextPreferences.minimumPriority,
    ],
  );

  return mapNotificationPreferenceRow(result.rows[0]);
}

export async function createNotification(
  userId: string,
  payload: unknown,
): Promise<NotificationRecord | null> {
  const notificationInput = normalizeCreateNotificationInput(payload);
  const preferences = await ensureNotificationPreferences(userId);

  if (!shouldDeliverNotification(preferences, notificationInput.priority)) {
    return null;
  }

  const result = await query<NotificationRow>(
    `
      INSERT INTO notifications (
        id,
        user_id,
        event_key,
        type,
        priority,
        title,
        body,
        metadata
      )
      VALUES ($1, $2, $3, $4, $5, $6, $7, $8::jsonb)
      RETURNING
        id,
        user_id,
        event_key,
        type,
        priority,
        title,
        body,
        metadata,
        is_read,
        read_at,
        created_at
    `,
    [
      randomUUID(),
      userId,
      notificationInput.eventKey,
      notificationInput.type,
      notificationInput.priority,
      notificationInput.title,
      notificationInput.body,
      JSON.stringify(notificationInput.metadata),
    ],
  );

  return mapNotificationRow(result.rows[0]);
}

export async function listNotifications(
  userId: string,
  limit?: number,
): Promise<NotificationRecord[]> {
  const normalizedLimit = normalizeNotificationLimit(limit);
  const result = await query<NotificationRow>(
    `
      SELECT
        id,
        user_id,
        event_key,
        type,
        priority,
        title,
        body,
        metadata,
        is_read,
        read_at,
        created_at
      FROM notifications
      WHERE user_id = $1
      ORDER BY created_at DESC
      LIMIT $2
    `,
    [userId, normalizedLimit],
  );

  return result.rows.map(mapNotificationRow);
}

export async function getUnreadNotificationCount(
  userId: string,
): Promise<number> {
  const result = await query<NotificationCountRow>(
    `
      SELECT COUNT(*)::text AS count
      FROM notifications
      WHERE user_id = $1
        AND is_read = FALSE
    `,
    [userId],
  );

  return Number.parseInt(result.rows[0]?.count ?? "0", 10);
}

export async function updateNotificationReadState(
  userId: string,
  notificationId: string,
  payload: unknown,
): Promise<NotificationRecord> {
  const { isRead } = normalizeReadStateInput(payload);
  const result = await query<NotificationRow>(
    `
      UPDATE notifications
      SET
        is_read = $3,
        read_at = CASE
          WHEN $3 = TRUE THEN CURRENT_TIMESTAMP
          ELSE NULL
        END
      WHERE id = $1
        AND user_id = $2
      RETURNING
        id,
        user_id,
        event_key,
        type,
        priority,
        title,
        body,
        metadata,
        is_read,
        read_at,
        created_at
    `,
    [notificationId, userId, isRead],
  );

  const notification = result.rows[0];

  if (!notification) {
    throw new NotificationNotFoundError("Notification not found.");
  }

  return mapNotificationRow(notification);
}

export async function getNotificationInbox(
  userId: string,
  limit?: number,
): Promise<NotificationInbox> {
  const normalizedLimit = normalizeNotificationLimit(limit);
  const [items, unreadCount, preferences] = await Promise.all([
    listNotifications(userId, normalizedLimit),
    getUnreadNotificationCount(userId),
    ensureNotificationPreferences(userId),
  ]);

  return {
    items,
    unreadCount,
    preferences,
  };
}
