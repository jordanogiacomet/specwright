"use client";

import { useState, type FormEvent } from "react";

import { AssigneeSelect, type AssigneeOption } from "./AssigneeSelect";

export const todoPriorities = ["low", "medium", "high"] as const;

export type TodoPriority = (typeof todoPriorities)[number];

export type AddTodoFormValues = {
  title: string;
  description: string | null;
  assigneeId: string | null;
  dueDate: string | null;
  priority: TodoPriority;
};

type AddTodoFormProps = {
  assigneeOptions: AssigneeOption[];
  isSubmitting: boolean;
  onSubmit: (values: AddTodoFormValues) => Promise<boolean>;
};

type AddTodoFormState = {
  title: string;
  description: string;
  assigneeId: string;
  dueDate: string;
  priority: TodoPriority;
};

const initialFormState: AddTodoFormState = {
  title: "",
  description: "",
  assigneeId: "",
  dueDate: "",
  priority: "medium",
};

export function AddTodoForm({
  assigneeOptions,
  isSubmitting,
  onSubmit,
}: AddTodoFormProps) {
  const [formState, setFormState] = useState(initialFormState);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    const didCreateTodo = await onSubmit({
      title: formState.title.trim(),
      description: formState.description.trim() || null,
      assigneeId: formState.assigneeId || null,
      dueDate: formState.dueDate || null,
      priority: formState.priority,
    });

    if (!didCreateTodo) {
      return;
    }

    setFormState(initialFormState);
  }

  return (
    <form
      className="space-y-4 rounded-3xl border border-slate-200 bg-slate-50 p-5"
      onSubmit={(event) => void handleSubmit(event)}
    >
      <div>
        <h2 className="text-xl font-semibold text-slate-950">Add a todo</h2>
        <p className="mt-1 text-sm text-slate-600">
          Title is required. Description, priority, and due date are optional.
        </p>
      </div>

      <label className="block space-y-2">
        <span className="text-sm font-medium text-slate-700">Title</span>
        <input
          className="w-full rounded-xl border border-slate-300 bg-white px-4 py-3 text-sm outline-none transition focus:border-sky-500"
          type="text"
          value={formState.title}
          onChange={(event) =>
            setFormState((currentState) => ({
              ...currentState,
              title: event.target.value,
            }))
          }
          maxLength={200}
          placeholder="Prepare project update"
          required
        />
      </label>

      <label className="block space-y-2">
        <span className="text-sm font-medium text-slate-700">Description</span>
        <textarea
          className="min-h-28 w-full rounded-xl border border-slate-300 bg-white px-4 py-3 text-sm outline-none transition focus:border-sky-500"
          value={formState.description}
          onChange={(event) =>
            setFormState((currentState) => ({
              ...currentState,
              description: event.target.value,
            }))
          }
          placeholder="Optional details for this task"
        />
      </label>

      <label className="block space-y-2">
        <span className="text-sm font-medium text-slate-700">Assignee</span>
        <AssigneeSelect
          value={formState.assigneeId || null}
          users={assigneeOptions}
          disabled={isSubmitting}
          onChange={(assigneeId) =>
            setFormState((currentState) => ({
              ...currentState,
              assigneeId: assigneeId ?? "",
            }))
          }
        />
        <p className="text-xs text-slate-500">
          Leave this unassigned if the owner should pick it up later.
        </p>
      </label>

      <div className="grid gap-4 md:grid-cols-2">
        <label className="block space-y-2">
          <span className="text-sm font-medium text-slate-700">Due date</span>
          <input
            className="w-full rounded-xl border border-slate-300 bg-white px-4 py-3 text-sm outline-none transition focus:border-sky-500"
            type="date"
            value={formState.dueDate}
            onChange={(event) =>
              setFormState((currentState) => ({
                ...currentState,
                dueDate: event.target.value,
              }))
            }
          />
        </label>

        <label className="block space-y-2">
          <span className="text-sm font-medium text-slate-700">Priority</span>
          <select
            className="w-full rounded-xl border border-slate-300 bg-white px-4 py-3 text-sm outline-none transition focus:border-sky-500"
            value={formState.priority}
            onChange={(event) =>
              setFormState((currentState) => ({
                ...currentState,
                priority: event.target.value as TodoPriority,
              }))
            }
          >
            {todoPriorities.map((priority) => (
              <option key={priority} value={priority}>
                {priority[0].toUpperCase()}
                {priority.slice(1)}
              </option>
            ))}
          </select>
        </label>
      </div>

      <button
        className="inline-flex items-center justify-center rounded-xl bg-sky-600 px-4 py-3 text-sm font-semibold text-white transition hover:bg-sky-700 disabled:cursor-not-allowed disabled:bg-slate-400"
        type="submit"
        disabled={isSubmitting}
      >
        {isSubmitting ? "Adding todo..." : "Add todo"}
      </button>
    </form>
  );
}
