import { randomUUID } from "node:crypto";

import { query, toIsoTimestamp, type DatabaseDateValue } from "../lib/db";
import { normalizeDueDateInput, serializeDueDate } from "../lib/deadlines";
import {
  canTransitionWorkItemStatus,
  getCompletedStateForWorkItemStatus,
  getWorkItemStatusFromCompletionFlag,
  isWorkItemStatus,
  type WorkItemStatus,
} from "../lib/status-machine";

export const todoPriorities = ["low", "medium", "high"] as const;
export const todoSortFields = ["createdAt", "priority"] as const;
export const todoSortOrders = ["asc", "desc"] as const;
export const todoAssignmentFilters = [
  "owned",
  "assigned",
  "unassigned",
] as const;

type TodoRow = {
  id: string;
  user_id: string;
  owner_email: string;
  assignee_id: string | null;
  assignee_email: string | null;
  title: string;
  description: string | null;
  completed: boolean;
  status: WorkItemStatus;
  last_status_transition_from: WorkItemStatus | null;
  last_status_transition_at: DatabaseDateValue | null;
  due_date: DatabaseDateValue | null;
  priority: TodoPriority;
  created_at: DatabaseDateValue;
  updated_at: DatabaseDateValue;
};

export type TodoPriority = (typeof todoPriorities)[number];
export type TodoSortField = (typeof todoSortFields)[number];
export type TodoSortOrder = (typeof todoSortOrders)[number];
export type TodoAssignmentFilter = (typeof todoAssignmentFilters)[number];

export type TodoRecord = {
  id: string;
  userId: string;
  ownerEmail: string;
  assigneeId: string | null;
  assigneeEmail: string | null;
  isOwner: boolean;
  isAssignedToCurrentUser: boolean;
  title: string;
  description: string | null;
  completed: boolean;
  status: WorkItemStatus;
  lastStatusTransitionFrom: WorkItemStatus | null;
  lastStatusTransitionAt: string | null;
  dueDate: string | null;
  priority: TodoPriority;
  createdAt: string;
  updatedAt: string;
};

export type CreateTodoInput = {
  title: string;
  description?: string | null;
  assigneeId?: string | null;
  completed?: boolean;
  status?: WorkItemStatus;
  dueDate?: string | Date | null;
  priority?: TodoPriority;
};

export type UpdateTodoInput = {
  title?: string;
  description?: string | null;
  assigneeId?: string | null;
  completed?: boolean;
  status?: WorkItemStatus;
  dueDate?: string | Date | null;
  priority?: TodoPriority;
};

export type ListTodosOptions = {
  assignment?: TodoAssignmentFilter;
  completed?: boolean;
  overdue?: boolean;
  sort?: TodoSortField;
  order?: TodoSortOrder;
};

type NormalizedCreateTodoInput = {
  title: string;
  description: string | null;
  assigneeId: string | null;
  status: WorkItemStatus;
  dueDate: string | null;
  priority: TodoPriority;
};

export class TodoValidationError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "TodoValidationError";
  }
}

export class TodoNotFoundError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "TodoNotFoundError";
  }
}

export class TodoStatusTransitionError extends TodoValidationError {
  constructor(currentStatus: WorkItemStatus, nextStatus: WorkItemStatus) {
    super(`Invalid status transition from ${currentStatus} to ${nextStatus}.`);
    this.name = "TodoStatusTransitionError";
  }
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function normalizeTitle(value: unknown, fieldName: string): string {
  if (typeof value !== "string") {
    throw new TodoValidationError(`${fieldName} must be a string.`);
  }

  const normalizedValue = value.trim();

  if (!normalizedValue) {
    throw new TodoValidationError(`${fieldName} is required.`);
  }

  return normalizedValue;
}

function normalizeDescription(
  value: unknown,
  fieldName: string,
): string | null {
  if (value === undefined || value === null) {
    return null;
  }

  if (typeof value !== "string") {
    throw new TodoValidationError(`${fieldName} must be a string.`);
  }

  const normalizedValue = value.trim();

  return normalizedValue || null;
}

function normalizeCompleted(value: unknown, fieldName: string): boolean {
  if (typeof value !== "boolean") {
    throw new TodoValidationError(`${fieldName} must be a boolean.`);
  }

  return value;
}

function normalizeStatus(value: unknown, fieldName: string): WorkItemStatus {
  if (!isWorkItemStatus(value)) {
    throw new TodoValidationError(
      `${fieldName} must be one of: pending, in_progress, completed.`,
    );
  }

  return value;
}

function normalizeDueDate(value: unknown, fieldName: string): string | null {
  const normalizedDueDate = normalizeDueDateInput(value);

  if (normalizedDueDate.error) {
    throw new TodoValidationError(`${fieldName} ${normalizedDueDate.error}`);
  }

  return normalizedDueDate.value;
}

function normalizePriority(value: unknown, fieldName: string): TodoPriority {
  if (typeof value !== "string") {
    throw new TodoValidationError(`${fieldName} must be a string.`);
  }

  if (!todoPriorities.includes(value as TodoPriority)) {
    throw new TodoValidationError(
      `${fieldName} must be one of: ${todoPriorities.join(", ")}.`,
    );
  }

  return value as TodoPriority;
}

function normalizeAssigneeId(value: unknown, fieldName: string): string | null {
  if (value === undefined || value === null) {
    return null;
  }

  if (typeof value !== "string") {
    throw new TodoValidationError(`${fieldName} must be a string or null.`);
  }

  const normalizedValue = value.trim();

  return normalizedValue || null;
}

function validateCompletedStatusCompatibility(
  completed: boolean | undefined,
  status: WorkItemStatus | undefined,
): void {
  if (completed === undefined || status === undefined) {
    return;
  }

  if (completed && status !== "completed") {
    throw new TodoValidationError(
      "completed=true requires status to be completed.",
    );
  }

  if (!completed && status === "completed") {
    throw new TodoValidationError(
      "completed=false is not compatible with status=completed.",
    );
  }
}

function normalizeCreateTodoInput(payload: unknown): NormalizedCreateTodoInput {
  if (!isRecord(payload)) {
    throw new TodoValidationError("Todo payload must be a JSON object.");
  }

  const completed =
    payload.completed === undefined
      ? undefined
      : normalizeCompleted(payload.completed, "completed");
  const status =
    payload.status === undefined
      ? undefined
      : normalizeStatus(payload.status, "status");

  validateCompletedStatusCompatibility(completed, status);

  return {
    title: normalizeTitle(payload.title, "title"),
    description: normalizeDescription(payload.description, "description"),
    assigneeId: normalizeAssigneeId(payload.assigneeId, "assigneeId"),
    status: status ?? (completed ? "completed" : "pending"),
    dueDate: normalizeDueDate(payload.dueDate, "dueDate"),
    priority:
      payload.priority === undefined
        ? "medium"
        : normalizePriority(payload.priority, "priority"),
  };
}

function normalizeUpdateTodoInput(payload: unknown): UpdateTodoInput {
  if (!isRecord(payload)) {
    throw new TodoValidationError("Todo payload must be a JSON object.");
  }

  const normalizedPayload: UpdateTodoInput = {};

  if ("title" in payload) {
    normalizedPayload.title = normalizeTitle(payload.title, "title");
  }

  if ("description" in payload) {
    normalizedPayload.description = normalizeDescription(
      payload.description,
      "description",
    );
  }

  if ("assigneeId" in payload) {
    normalizedPayload.assigneeId = normalizeAssigneeId(
      payload.assigneeId,
      "assigneeId",
    );
  }

  if ("completed" in payload) {
    normalizedPayload.completed = normalizeCompleted(
      payload.completed,
      "completed",
    );
  }

  if ("status" in payload) {
    normalizedPayload.status = normalizeStatus(payload.status, "status");
  }

  if ("dueDate" in payload) {
    normalizedPayload.dueDate = normalizeDueDate(payload.dueDate, "dueDate");
  }

  if ("priority" in payload) {
    normalizedPayload.priority = normalizePriority(
      payload.priority,
      "priority",
    );
  }

  validateCompletedStatusCompatibility(
    normalizedPayload.completed,
    normalizedPayload.status,
  );

  if (Object.keys(normalizedPayload).length === 0) {
    throw new TodoValidationError(
      "Todo update payload must include at least one supported field.",
    );
  }

  return normalizedPayload;
}

async function assertUserExists(
  userId: string,
  fieldName: string,
): Promise<void> {
  const result = await query<{ id: string }>(
    `
      SELECT id
      FROM users
      WHERE id = $1
      LIMIT 1
    `,
    [userId],
  );

  if (!result.rows[0]) {
    throw new TodoValidationError(
      `${fieldName} must reference an existing user.`,
    );
  }
}

function mapTodoRow(row: TodoRow, viewerUserId: string): TodoRecord {
  return {
    id: row.id,
    userId: row.user_id,
    ownerEmail: row.owner_email,
    assigneeId: row.assignee_id,
    assigneeEmail: row.assignee_email,
    isOwner: row.user_id === viewerUserId,
    isAssignedToCurrentUser: row.assignee_id === viewerUserId,
    title: row.title,
    description: row.description,
    completed: getCompletedStateForWorkItemStatus(row.status),
    status: row.status,
    lastStatusTransitionFrom: row.last_status_transition_from,
    lastStatusTransitionAt: row.last_status_transition_at
      ? toIsoTimestamp(row.last_status_transition_at)
      : null,
    dueDate: row.due_date ? serializeDueDate(row.due_date) : null,
    priority: row.priority,
    createdAt: toIsoTimestamp(row.created_at),
    updatedAt: toIsoTimestamp(row.updated_at),
  };
}

async function getTodoRowByIdForOwner(
  todoId: string,
  userId: string,
): Promise<TodoRow | null> {
  const result = await query<TodoRow>(
    `
      SELECT
        todos.id,
        todos.user_id,
        owners.email AS owner_email,
        todos.assignee_id,
        assignees.email AS assignee_email,
        todos.title,
        todos.description,
        todos.completed,
        todos.status,
        todos.last_status_transition_from,
        todos.last_status_transition_at,
        todos.due_date,
        todos.priority,
        todos.created_at,
        todos.updated_at
      FROM todos
      INNER JOIN users AS owners
        ON owners.id = todos.user_id
      LEFT JOIN users AS assignees
        ON assignees.id = todos.assignee_id
      WHERE todos.id = $1
        AND todos.user_id = $2
      LIMIT 1
    `,
    [todoId, userId],
  );

  return result.rows[0] ?? null;
}

export async function listTodosForUser(
  userId: string,
  options: ListTodosOptions = {},
): Promise<TodoRecord[]> {
  const values: unknown[] = [userId];
  const whereClauses: string[] = [];
  const assignment = options.assignment ?? "owned";

  if (assignment === "assigned") {
    whereClauses.push("todos.assignee_id = $1");
  } else if (assignment === "unassigned") {
    whereClauses.push("todos.user_id = $1");
    whereClauses.push("todos.assignee_id IS NULL");
  } else {
    whereClauses.push("todos.user_id = $1");
  }

  if (typeof options.completed === "boolean") {
    whereClauses.push(`todos.completed = $${values.length + 1}`);
    values.push(options.completed);
  }

  if (typeof options.overdue === "boolean") {
    if (options.overdue) {
      whereClauses.push("todos.completed = false");
      whereClauses.push("todos.due_date IS NOT NULL");
      whereClauses.push("todos.due_date < CURRENT_DATE");
    } else {
      whereClauses.push(
        "(todos.completed = true OR todos.due_date IS NULL OR todos.due_date >= CURRENT_DATE)",
      );
    }
  }

  const sortField = options.sort ?? "createdAt";
  const sortOrder = options.order ?? "desc";
  const orderDirection = sortOrder.toUpperCase();
  const orderByClause =
    sortField === "priority"
      ? `
          CASE todos.priority
            WHEN 'low' THEN 1
            WHEN 'medium' THEN 2
            WHEN 'high' THEN 3
          END ${orderDirection},
          todos.created_at DESC,
          todos.id DESC
        `
      : `
          todos.created_at ${orderDirection},
          todos.id DESC
        `;

  const result = await query<TodoRow>(
    `
      SELECT
        todos.id,
        todos.user_id,
        owners.email AS owner_email,
        todos.assignee_id,
        assignees.email AS assignee_email,
        todos.title,
        todos.description,
        todos.completed,
        todos.status,
        todos.last_status_transition_from,
        todos.last_status_transition_at,
        todos.due_date,
        todos.priority,
        todos.created_at,
        todos.updated_at
      FROM todos
      INNER JOIN users AS owners
        ON owners.id = todos.user_id
      LEFT JOIN users AS assignees
        ON assignees.id = todos.assignee_id
      WHERE ${whereClauses.join(" AND ")}
      ORDER BY ${orderByClause}
    `,
    values,
  );

  return result.rows.map((row) => mapTodoRow(row, userId));
}

export async function getTodoById(
  todoId: string,
  userId: string,
): Promise<TodoRecord | null> {
  const row = await getTodoRowByIdForOwner(todoId, userId);

  return row ? mapTodoRow(row, userId) : null;
}

export async function createTodo(
  userId: string,
  payload: unknown,
): Promise<TodoRecord> {
  const input = normalizeCreateTodoInput(payload);

  if (input.assigneeId) {
    await assertUserExists(input.assigneeId, "assigneeId");
  }

  const todoId = randomUUID();

  await query(
    `
      INSERT INTO todos (
        id,
        user_id,
        assignee_id,
        title,
        description,
        completed,
        status,
        due_date,
        priority
      )
      VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
    `,
    [
      todoId,
      userId,
      input.assigneeId,
      input.title,
      input.description,
      getCompletedStateForWorkItemStatus(input.status),
      input.status,
      input.dueDate,
      input.priority,
    ],
  );

  const todo = await getTodoRowByIdForOwner(todoId, userId);

  if (!todo) {
    throw new TodoNotFoundError("Todo not found.");
  }

  return mapTodoRow(todo, userId);
}

export async function updateTodo(
  todoId: string,
  userId: string,
  payload: unknown,
): Promise<TodoRecord> {
  const updates = normalizeUpdateTodoInput(payload);
  const existingTodo = await getTodoRowByIdForOwner(todoId, userId);

  if (!existingTodo) {
    throw new TodoNotFoundError("Todo not found.");
  }

  const setClauses: string[] = [];
  const values: unknown[] = [todoId, userId];

  if ("title" in updates) {
    setClauses.push(`title = $${values.length + 1}`);
    values.push(updates.title);
  }

  if ("description" in updates) {
    setClauses.push(`description = $${values.length + 1}`);
    values.push(updates.description);
  }

  if ("assigneeId" in updates) {
    if (updates.assigneeId) {
      await assertUserExists(updates.assigneeId, "assigneeId");
    }

    setClauses.push(`assignee_id = $${values.length + 1}`);
    values.push(updates.assigneeId);
  }

  if ("dueDate" in updates) {
    setClauses.push(`due_date = $${values.length + 1}`);
    values.push(updates.dueDate);
  }

  if ("priority" in updates) {
    setClauses.push(`priority = $${values.length + 1}`);
    values.push(updates.priority);
  }

  let nextStatus: WorkItemStatus | undefined;

  if ("status" in updates) {
    nextStatus = updates.status;
  } else if ("completed" in updates) {
    const completed = updates.completed;

    if (completed === undefined) {
      throw new TodoValidationError("completed must be a boolean.");
    }

    nextStatus = getWorkItemStatusFromCompletionFlag(
      completed,
      existingTodo.status,
    );
  }

  if (nextStatus !== undefined) {
    if (!canTransitionWorkItemStatus(existingTodo.status, nextStatus)) {
      throw new TodoStatusTransitionError(existingTodo.status, nextStatus);
    }

    setClauses.push(`status = $${values.length + 1}`);
    values.push(nextStatus);
    setClauses.push(`completed = $${values.length + 1}`);
    values.push(getCompletedStateForWorkItemStatus(nextStatus));

    if (nextStatus !== existingTodo.status) {
      setClauses.push(`last_status_transition_from = $${values.length + 1}`);
      values.push(existingTodo.status);
      setClauses.push("last_status_transition_at = CURRENT_TIMESTAMP");
    }
  }

  setClauses.push("updated_at = CURRENT_TIMESTAMP");

  const result = await query<{ id: string }>(
    `
      UPDATE todos
      SET ${setClauses.join(", ")}
      WHERE id = $1
        AND user_id = $2
      RETURNING id
    `,
    values,
  );

  if (!result.rows[0]) {
    throw new TodoNotFoundError("Todo not found.");
  }

  const todo = await getTodoRowByIdForOwner(todoId, userId);

  if (!todo) {
    throw new TodoNotFoundError("Todo not found.");
  }

  return mapTodoRow(todo, userId);
}

export async function deleteTodo(
  todoId: string,
  userId: string,
): Promise<void> {
  const result = await query(
    `
      DELETE FROM todos
      WHERE id = $1
        AND user_id = $2
    `,
    [todoId, userId],
  );

  if (result.rowCount === 0) {
    throw new TodoNotFoundError("Todo not found.");
  }
}
