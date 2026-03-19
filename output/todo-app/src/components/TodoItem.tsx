"use client";

import { useEffect, useState, type FormEvent } from "react";

import { formatDueDateForDisplay, isOverdueDueDate } from "@/lib/deadlines";
import {
  getAllowedWorkItemStatusTransitions,
  workItemStatusLabels,
  workItemStatuses,
  type WorkItemStatus,
} from "@/lib/status-machine";

import type { TodoPriority } from "./AddTodoForm";
import { AssigneeSelect, type AssigneeOption } from "./AssigneeSelect";

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

type TodoItemProps = {
  assigneeOptions: AssigneeOption[];
  todo: TodoRecord;
  isTransitioningStatus: boolean;
  isDeleting: boolean;
  isSavingAssignee: boolean;
  isSavingDueDate: boolean;
  onTransitionStatus: (
    todo: TodoRecord,
    nextStatus: WorkItemStatus,
  ) => Promise<void>;
  onDelete: (todo: TodoRecord) => Promise<void>;
  onSaveAssignee: (
    todo: TodoRecord,
    assigneeId: string | null,
  ) => Promise<void>;
  onSaveDueDate: (todo: TodoRecord, dueDate: string | null) => Promise<void>;
};

const priorityStyles: Record<TodoPriority, string> = {
  low: "border-emerald-200 bg-emerald-50 text-emerald-700",
  medium: "border-amber-200 bg-amber-50 text-amber-700",
  high: "border-rose-200 bg-rose-50 text-rose-700",
};

const workItemStatusStyles: Record<WorkItemStatus, string> = {
  pending: "border-slate-300 bg-slate-100 text-slate-700",
  in_progress: "border-sky-200 bg-sky-50 text-sky-700",
  completed: "border-emerald-200 bg-emerald-50 text-emerald-700",
};

const workItemStatusActionLabels: Record<
  WorkItemStatus,
  Partial<Record<WorkItemStatus, string>>
> = {
  pending: {
    in_progress: "Start work",
    completed: "Mark complete",
  },
  in_progress: {
    pending: "Move to pending",
    completed: "Mark complete",
  },
  completed: {
    in_progress: "Reopen task",
  },
};

function formatDate(value: string): string {
  return new Date(value).toLocaleDateString();
}

function formatTimestamp(value: string): string {
  return new Date(value).toLocaleString();
}

export function TodoItem({
  assigneeOptions,
  todo,
  isTransitioningStatus,
  isDeleting,
  isSavingAssignee,
  isSavingDueDate,
  onTransitionStatus,
  onDelete,
  onSaveAssignee,
  onSaveDueDate,
}: TodoItemProps) {
  const [assigneeIdDraft, setAssigneeIdDraft] = useState(todo.assigneeId ?? "");
  const [dueDateDraft, setDueDateDraft] = useState(todo.dueDate ?? "");
  const isOverdue = isOverdueDueDate(todo.dueDate, {
    completed: todo.completed,
  });
  const isBusy =
    isTransitioningStatus || isDeleting || isSavingAssignee || isSavingDueDate;
  const hasAssigneeChanges = assigneeIdDraft !== (todo.assigneeId ?? "");
  const hasDueDateChanges = dueDateDraft !== (todo.dueDate ?? "");
  const assigneeActionLabel = isSavingAssignee
    ? "Saving..."
    : assigneeIdDraft
      ? "Save assignee"
      : todo.assigneeId
        ? "Clear assignment"
        : "Save assignee";
  const dueDateActionLabel = isSavingDueDate
    ? "Saving..."
    : dueDateDraft
      ? "Save due date"
      : todo.dueDate
        ? "Clear due date"
        : "Save due date";
  const currentStatusIndex = workItemStatuses.indexOf(todo.status);
  const allowedTransitions = getAllowedWorkItemStatusTransitions(todo.status);

  useEffect(() => {
    setAssigneeIdDraft(todo.assigneeId ?? "");
  }, [todo.assigneeId]);

  useEffect(() => {
    setDueDateDraft(todo.dueDate ?? "");
  }, [todo.dueDate]);

  async function handleAssigneeSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    if (!hasAssigneeChanges) {
      return;
    }

    await onSaveAssignee(todo, assigneeIdDraft || null);
  }

  async function handleDueDateSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    if (!hasDueDateChanges) {
      return;
    }

    await onSaveDueDate(todo, dueDateDraft || null);
  }

  return (
    <article
      className={`rounded-3xl border p-5 transition ${
        todo.completed
          ? "border-slate-200 bg-slate-50/90"
          : "border-slate-200 bg-white shadow-sm"
      }`}
    >
      <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
        <div className="space-y-3">
          <div className="flex flex-wrap items-center gap-2">
            <span
              className={`rounded-full border px-3 py-1 text-xs font-semibold uppercase tracking-[0.18em] ${
                priorityStyles[todo.priority]
              }`}
            >
              {todo.priority}
            </span>
            <span
              className={`rounded-full border px-3 py-1 text-xs font-semibold uppercase tracking-[0.18em] ${
                workItemStatusStyles[todo.status]
              }`}
            >
              {workItemStatusLabels[todo.status]}
            </span>
            <span className="text-xs uppercase tracking-[0.18em] text-slate-500">
              Created {formatDate(todo.createdAt)}
            </span>
            {todo.dueDate ? (
              <span className="text-xs uppercase tracking-[0.18em] text-slate-500">
                Due {formatDueDateForDisplay(todo.dueDate)}
              </span>
            ) : null}
            {isOverdue ? (
              <span className="rounded-full border border-rose-200 bg-rose-50 px-3 py-1 text-xs font-semibold uppercase tracking-[0.16em] text-rose-700">
                Overdue
              </span>
            ) : null}
            <span
              className={`rounded-full border px-3 py-1 text-xs font-semibold uppercase tracking-[0.16em] ${
                todo.assigneeEmail
                  ? "border-violet-200 bg-violet-50 text-violet-700"
                  : "border-slate-200 bg-white text-slate-500"
              }`}
            >
              {todo.assigneeEmail
                ? todo.isAssignedToCurrentUser
                  ? "Assigned to you"
                  : `Assigned to ${todo.assigneeEmail}`
                : "Unassigned"}
            </span>
            <span className="text-xs uppercase tracking-[0.18em] text-slate-500">
              Owner {todo.ownerEmail}
            </span>
          </div>

          <div className="space-y-2">
            <h3
              className={`text-xl font-semibold tracking-tight ${
                todo.completed
                  ? "text-slate-500 line-through"
                  : "text-slate-950"
              }`}
            >
              {todo.title}
            </h3>
            {todo.description ? (
              <p
                className={`max-w-2xl text-sm leading-6 ${
                  todo.completed ? "text-slate-500" : "text-slate-600"
                }`}
              >
                {todo.description}
              </p>
            ) : null}

            <div className="grid gap-2 sm:grid-cols-3">
              {workItemStatuses.map((statusStep, index) => {
                const isCurrent = statusStep === todo.status;
                const isReached = index <= currentStatusIndex;

                return (
                  <div
                    key={statusStep}
                    className={`rounded-2xl border px-3 py-2 text-xs font-semibold uppercase tracking-[0.16em] transition ${
                      isCurrent
                        ? "border-slate-900 bg-slate-900 text-white"
                        : isReached
                          ? "border-slate-300 bg-slate-100 text-slate-700"
                          : "border-slate-200 bg-white text-slate-400"
                    }`}
                  >
                    {workItemStatusLabels[statusStep]}
                  </div>
                );
              })}
            </div>

            <p className="text-xs leading-5 text-slate-500">
              {todo.lastStatusTransitionAt && todo.lastStatusTransitionFrom
                ? `Last moved from ${workItemStatusLabels[todo.lastStatusTransitionFrom]} on ${formatTimestamp(todo.lastStatusTransitionAt)}.`
                : "Status changes are logged after the first transition."}
            </p>
          </div>
        </div>

        {todo.isOwner ? (
          <div className="flex flex-wrap gap-3">
            {allowedTransitions.map((nextStatus) => (
              <button
                key={nextStatus}
                className={`rounded-full px-4 py-2 text-sm font-semibold transition disabled:cursor-not-allowed disabled:opacity-60 ${
                  nextStatus === "completed"
                    ? "bg-emerald-500 text-slate-950 hover:bg-emerald-400"
                    : nextStatus === "in_progress"
                      ? "bg-sky-600 text-white hover:bg-sky-700"
                      : "border border-slate-300 bg-white text-slate-700 hover:border-slate-400 hover:text-slate-950"
                }`}
                type="button"
                onClick={() => void onTransitionStatus(todo, nextStatus)}
                disabled={isBusy}
              >
                {isTransitioningStatus
                  ? "Updating..."
                  : workItemStatusActionLabels[todo.status][nextStatus]}
              </button>
            ))}

            <button
              className="rounded-full border border-rose-200 bg-white px-4 py-2 text-sm font-semibold text-rose-700 transition hover:border-rose-300 hover:bg-rose-50 disabled:cursor-not-allowed disabled:opacity-60"
              type="button"
              onClick={() => {
                if (!window.confirm(`Delete "${todo.title}"?`)) {
                  return;
                }

                void onDelete(todo);
              }}
              disabled={isBusy}
            >
              {isDeleting ? "Deleting..." : "Delete"}
            </button>
          </div>
        ) : null}
      </div>

      {!todo.isOwner ? (
        <div className="mt-4 rounded-2xl border border-amber-200 bg-amber-50/80 p-4 text-sm text-amber-900">
          This item is visible because it is assigned to you. Only the owner can
          change its status, deadline, or assignee in the current access model.
        </div>
      ) : null}

      {todo.isOwner ? (
        <form
          className="mt-4 rounded-2xl border border-slate-200 bg-slate-50/80 p-4"
          onSubmit={(event) => void handleAssigneeSubmit(event)}
        >
          <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
            <div className="space-y-2">
              <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">
                Assignment
              </p>
              <div className="flex flex-wrap items-center gap-2">
                <span
                  className={`rounded-full border px-3 py-1 text-xs font-semibold uppercase tracking-[0.16em] ${
                    todo.assigneeEmail
                      ? "border-violet-200 bg-violet-50 text-violet-700"
                      : "border-slate-200 bg-white text-slate-500"
                  }`}
                >
                  {todo.assigneeEmail
                    ? `Assigned to ${todo.assigneeEmail}`
                    : "Unassigned"}
                </span>
              </div>
              <p className="text-sm text-slate-600">
                Assign this item to an individual owner or clear the field to
                keep it unassigned.
              </p>
            </div>

            <div className="flex w-full flex-col gap-3 sm:w-auto sm:flex-row sm:items-center">
              <label className="sr-only" htmlFor={`todo-assignee-${todo.id}`}>
                Assignee
              </label>
              <div className="w-full sm:w-[280px]">
                <AssigneeSelect
                  id={`todo-assignee-${todo.id}`}
                  value={assigneeIdDraft || null}
                  users={assigneeOptions}
                  disabled={isBusy}
                  onChange={(assigneeId) =>
                    setAssigneeIdDraft(assigneeId ?? "")
                  }
                />
              </div>
              <button
                className="inline-flex items-center justify-center rounded-xl bg-sky-600 px-4 py-3 text-sm font-semibold text-white transition hover:bg-sky-700 disabled:cursor-not-allowed disabled:bg-slate-400"
                type="submit"
                disabled={isBusy || !hasAssigneeChanges}
              >
                {assigneeActionLabel}
              </button>
            </div>
          </div>
        </form>
      ) : null}

      {todo.isOwner ? (
        <form
          className="mt-4 rounded-2xl border border-slate-200 bg-slate-50/80 p-4"
          onSubmit={(event) => void handleDueDateSubmit(event)}
        >
          <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
            <div className="space-y-2">
              <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">
                Deadline
              </p>
              <div className="flex flex-wrap items-center gap-2">
                <span
                  className={`rounded-full border px-3 py-1 text-xs font-semibold uppercase tracking-[0.16em] ${
                    isOverdue
                      ? "border-rose-200 bg-rose-50 text-rose-700"
                      : todo.dueDate
                        ? "border-sky-200 bg-sky-50 text-sky-700"
                        : "border-slate-200 bg-white text-slate-500"
                  }`}
                >
                  {todo.dueDate
                    ? `Due ${formatDueDateForDisplay(todo.dueDate)}`
                    : "No due date"}
                </span>
              </div>
              <p className="text-sm text-slate-600">
                {isOverdue
                  ? "This todo is past its due date."
                  : todo.dueDate
                    ? "Adjust the due date here if the schedule changes."
                    : "Set a due date to track time-sensitive work."}
              </p>
            </div>

            <div className="flex w-full flex-col gap-3 sm:w-auto sm:flex-row sm:items-center">
              <label className="sr-only" htmlFor={`todo-due-date-${todo.id}`}>
                Due date
              </label>
              <input
                id={`todo-due-date-${todo.id}`}
                className="w-full rounded-xl border border-slate-300 bg-white px-4 py-3 text-sm outline-none transition focus:border-sky-500 sm:w-[190px]"
                type="date"
                value={dueDateDraft}
                onChange={(event) => setDueDateDraft(event.target.value)}
                disabled={isBusy}
              />
              <button
                className="inline-flex items-center justify-center rounded-xl bg-sky-600 px-4 py-3 text-sm font-semibold text-white transition hover:bg-sky-700 disabled:cursor-not-allowed disabled:bg-slate-400"
                type="submit"
                disabled={isBusy || !hasDueDateChanges}
              >
                {dueDateActionLabel}
              </button>
            </div>
          </div>
        </form>
      ) : null}
    </article>
  );
}
