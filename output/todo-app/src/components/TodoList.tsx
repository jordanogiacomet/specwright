"use client";

import Link from "next/link";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { useEffect, useState } from "react";

import {
  workItemStatusLabels,
  type WorkItemStatus,
} from "@/lib/status-machine";

import { AddTodoForm, type AddTodoFormValues } from "./AddTodoForm";
import { type AssigneeOption } from "./AssigneeSelect";
import {
  type TodoAssignmentFilter,
  TodoFilters,
  type TodoSortOption,
  type TodoStatusFilter,
} from "./TodoFilters";
import { TodoItem, type TodoRecord } from "./TodoItem";

const apiBaseUrl =
  process.env.NEXT_PUBLIC_API_BASE_URL?.replace(/\/$/, "") ||
  "http://localhost:3001";

type TodoListResponse = {
  items: TodoRecord[];
};

type UserListResponse = {
  items: AssigneeOption[];
};

type StatusState = {
  tone: "neutral" | "success" | "error";
  message: string;
};

type TodoViewState = {
  assignment: TodoAssignmentFilter;
  filter: TodoStatusFilter;
  sort: TodoSortOption;
};

type SearchParamsReader = Pick<URLSearchParams, "get">;

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

async function request<T>(
  path: string,
  init: RequestInit,
): Promise<{ ok: boolean; status: number; body: T | null }> {
  const response = await fetch(`${apiBaseUrl}${path}`, {
    ...init,
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
      ...(init.headers ?? {}),
    },
  });

  return {
    ok: response.ok,
    status: response.status,
    body: (await parseResponse(response)) as T | null,
  };
}

function getTodoViewState(searchParams: SearchParamsReader): TodoViewState {
  const assignment = searchParams.get("assignment");
  const completed = searchParams.get("completed");
  const sort = searchParams.get("sort");
  const order = searchParams.get("order");

  return {
    assignment:
      assignment === "assigned"
        ? "assigned"
        : assignment === "unassigned"
          ? "unassigned"
          : "owned",
    filter:
      completed === "true"
        ? "completed"
        : completed === "false"
          ? "pending"
          : "all",
    sort:
      sort === "priority"
        ? "priority"
        : sort === "createdAt" && order === "asc"
          ? "oldest"
          : "newest",
  };
}

function buildTodoSearchParams(viewState: TodoViewState): URLSearchParams {
  const params = new URLSearchParams();

  if (viewState.assignment !== "owned") {
    params.set("assignment", viewState.assignment);
  }

  if (viewState.filter === "completed") {
    params.set("completed", "true");
  } else if (viewState.filter === "pending") {
    params.set("completed", "false");
  }

  if (viewState.sort === "oldest") {
    params.set("sort", "createdAt");
    params.set("order", "asc");
  } else if (viewState.sort === "priority") {
    params.set("sort", "priority");
    params.set("order", "desc");
  }

  return params;
}

function buildTodosRequestPath(viewState: TodoViewState): string {
  const queryString = buildTodoSearchParams(viewState).toString();

  return queryString ? `/api/todos?${queryString}` : "/api/todos";
}

function getLoadedStatusMessage(
  assignment: TodoAssignmentFilter,
  filter: TodoStatusFilter,
  count: number,
): string {
  if (count > 0) {
    return "Todo list loaded.";
  }

  if (assignment === "assigned") {
    return "No assignments match the current filters.";
  }

  if (assignment === "unassigned") {
    return "No unassigned todos match the current filters.";
  }

  if (filter === "pending") {
    return "You do not have any pending todos.";
  }

  if (filter === "completed") {
    return "You do not have any completed todos.";
  }

  return "You do not have any todos yet.";
}

function getEmptyState(viewState: TodoViewState): {
  heading: string;
  message: string;
} {
  if (viewState.assignment === "assigned") {
    return {
      heading:
        viewState.filter === "completed"
          ? "No completed assignments"
          : viewState.filter === "pending"
            ? "No pending assignments"
            : "No assignments",
      message:
        "Nothing assigned to your account matches this view. Switch back to owned work or adjust the status filter.",
    };
  }

  if (viewState.assignment === "unassigned") {
    return {
      heading:
        viewState.filter === "completed"
          ? "No completed unassigned todos"
          : viewState.filter === "pending"
            ? "No pending unassigned todos"
            : "No unassigned todos",
      message:
        "Every item in your owned list currently has an assignee, or the current status filter is too narrow.",
    };
  }

  if (viewState.filter === "pending") {
    return {
      heading: "No pending todos",
      message:
        "You have cleared the current queue. Change the filter to review completed work or add a new task from the form on the left.",
    };
  }

  if (viewState.filter === "completed") {
    return {
      heading: "No completed todos",
      message:
        "Nothing has been marked complete in this view yet. Switch back to all items or pending work to continue.",
    };
  }

  return {
    heading: "No todos yet",
    message:
      "Add a task with a title to create your first todo. Optional details like priority, description, and due date can be added from the form on the left.",
  };
}

function getTodoCountLabel(viewState: TodoViewState, count: number): string {
  if (viewState.assignment === "assigned") {
    if (viewState.filter === "pending") {
      return count === 1
        ? "1 pending assignment"
        : `${count} pending assignments`;
    }

    if (viewState.filter === "completed") {
      return count === 1
        ? "1 completed assignment"
        : `${count} completed assignments`;
    }

    return count === 1 ? "1 assignment" : `${count} assignments`;
  }

  if (viewState.assignment === "unassigned") {
    if (viewState.filter === "pending") {
      return count === 1 ? "1 unassigned todo" : `${count} unassigned todos`;
    }

    if (viewState.filter === "completed") {
      return count === 1
        ? "1 completed unassigned todo"
        : `${count} completed unassigned todos`;
    }

    return count === 1 ? "1 unassigned todo" : `${count} unassigned todos`;
  }

  if (viewState.filter === "pending") {
    return count === 1 ? "1 pending todo" : `${count} pending todos`;
  }

  if (viewState.filter === "completed") {
    return count === 1 ? "1 completed todo" : `${count} completed todos`;
  }

  return count === 1 ? "1 todo" : `${count} todos`;
}

export function TodoList() {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const viewState = getTodoViewState(searchParams);
  const todosRequestPath = buildTodosRequestPath(viewState);
  const [assigneeOptions, setAssigneeOptions] = useState<AssigneeOption[]>([]);
  const [todos, setTodos] = useState<TodoRecord[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isAuthenticated, setIsAuthenticated] = useState<boolean | null>(null);
  const [activeAction, setActiveAction] = useState<string | null>(null);
  const [status, setStatus] = useState<StatusState>({
    tone: "neutral",
    message: "Review your current tasks and keep the list up to date.",
  });

  function setUnauthenticatedState(message: string) {
    setIsAuthenticated(false);
    setTodos([]);
    setAssigneeOptions([]);
    setStatus({
      tone: "neutral",
      message,
    });
  }

  async function loadTodos(options?: {
    preserveStatus?: boolean;
    successStatus?: StatusState;
  }) {
    setIsLoading(true);

    try {
      const response = await request<TodoListResponse>(todosRequestPath, {
        method: "GET",
      });

      if (response.status === 401) {
        setUnauthenticatedState(
          "Sign in to load the todo list for your account.",
        );
        return;
      }

      if (!response.ok || !response.body) {
        setStatus({
          tone: "error",
          message: getResponseMessage(response.body, "Unable to load todos."),
        });
        return;
      }

      setIsAuthenticated(true);
      setTodos(response.body.items);

      if (options?.successStatus) {
        setStatus(options.successStatus);
      } else if (!options?.preserveStatus) {
        setStatus({
          tone: "neutral",
          message: getLoadedStatusMessage(
            viewState.assignment,
            viewState.filter,
            response.body.items.length,
          ),
        });
      }
    } catch {
      setStatus({
        tone: "error",
        message: "Unable to reach the todo API.",
      });
    } finally {
      setIsLoading(false);
      setActiveAction(null);
    }
  }

  useEffect(() => {
    let isCancelled = false;
    const shouldLoadAssignees = assigneeOptions.length === 0;

    setIsLoading(true);

    void Promise.all([
      request<TodoListResponse>(todosRequestPath, {
        method: "GET",
      }),
      shouldLoadAssignees
        ? request<UserListResponse>("/api/auth/users", {
            method: "GET",
          })
        : Promise.resolve(null),
    ])
      .then(([response, usersResponse]) => {
        if (isCancelled) {
          return;
        }

        if (response.status === 401 || usersResponse?.status === 401) {
          setUnauthenticatedState(
            "Sign in to load the todo list for your account.",
          );
          return;
        }

        if (!response.ok || !response.body) {
          setStatus({
            tone: "error",
            message: getResponseMessage(response.body, "Unable to load todos."),
          });
          return;
        }

        setIsAuthenticated(true);
        setTodos(response.body.items);

        if (usersResponse?.ok && usersResponse.body) {
          setAssigneeOptions(usersResponse.body.items);
        }

        setStatus({
          tone: "neutral",
          message: getLoadedStatusMessage(
            viewState.assignment,
            viewState.filter,
            response.body.items.length,
          ),
        });
      })
      .catch(() => {
        if (isCancelled) {
          return;
        }

        setStatus({
          tone: "error",
          message: "Unable to reach the todo API.",
        });
      })
      .finally(() => {
        if (isCancelled) {
          return;
        }

        setIsLoading(false);
        setActiveAction(null);
      });

    return () => {
      isCancelled = true;
    };
  }, [
    assigneeOptions.length,
    todosRequestPath,
    viewState.assignment,
    viewState.filter,
  ]);

  function updateViewState(nextViewState: TodoViewState) {
    const nextSearchParams = buildTodoSearchParams(nextViewState);
    const nextQueryString = nextSearchParams.toString();
    const nextUrl = nextQueryString
      ? `${pathname}?${nextQueryString}`
      : pathname;

    router.replace(nextUrl, { scroll: false });
  }

  async function handleAddTodo(values: AddTodoFormValues): Promise<boolean> {
    setActiveAction("create");

    try {
      const response = await request<TodoRecord>("/api/todos", {
        method: "POST",
        body: JSON.stringify(values),
      });

      if (response.status === 401) {
        setUnauthenticatedState("Sign in to add todos for your account.");
        return false;
      }

      if (!response.ok || !response.body) {
        setStatus({
          tone: "error",
          message: getResponseMessage(response.body, "Unable to add todo."),
        });
        return false;
      }

      setIsAuthenticated(true);
      await loadTodos({
        successStatus: {
          tone: "success",
          message: "Todo added.",
        },
      });

      return true;
    } catch {
      setStatus({
        tone: "error",
        message: "Unable to reach the todo API.",
      });
      return false;
    } finally {
      setActiveAction(null);
    }
  }

  async function handleTransitionTodoStatus(
    todo: TodoRecord,
    nextStatus: WorkItemStatus,
  ) {
    setActiveAction(`status:${todo.id}`);

    try {
      const response = await request<TodoRecord>(`/api/todos/${todo.id}`, {
        method: "PATCH",
        body: JSON.stringify({
          status: nextStatus,
        }),
      });

      if (response.status === 401) {
        setUnauthenticatedState("Sign in to update todos for your account.");
        return;
      }

      if (!response.ok || !response.body) {
        setStatus({
          tone: "error",
          message: getResponseMessage(response.body, "Unable to update todo."),
        });
        return;
      }

      await loadTodos({
        successStatus: {
          tone: "success",
          message: `Todo moved to ${workItemStatusLabels[response.body.status]}.`,
        },
      });
    } catch {
      setStatus({
        tone: "error",
        message: "Unable to reach the todo API.",
      });
    } finally {
      setActiveAction(null);
    }
  }

  async function handleSaveDueDate(todo: TodoRecord, dueDate: string | null) {
    setActiveAction(`dueDate:${todo.id}`);

    try {
      const response = await request<TodoRecord>(`/api/todos/${todo.id}`, {
        method: "PATCH",
        body: JSON.stringify({
          dueDate,
        }),
      });

      if (response.status === 401) {
        setUnauthenticatedState("Sign in to update todos for your account.");
        return;
      }

      if (!response.ok || !response.body) {
        setStatus({
          tone: "error",
          message: getResponseMessage(
            response.body,
            "Unable to update the due date.",
          ),
        });
        return;
      }

      await loadTodos({
        successStatus: {
          tone: "success",
          message: response.body.dueDate
            ? "Todo due date updated."
            : "Todo due date cleared.",
        },
      });
    } catch {
      setStatus({
        tone: "error",
        message: "Unable to reach the todo API.",
      });
    } finally {
      setActiveAction(null);
    }
  }

  async function handleSaveAssignee(
    todo: TodoRecord,
    assigneeId: string | null,
  ) {
    setActiveAction(`assignee:${todo.id}`);

    try {
      const response = await request<TodoRecord>(`/api/todos/${todo.id}`, {
        method: "PATCH",
        body: JSON.stringify({
          assigneeId,
        }),
      });

      if (response.status === 401) {
        setUnauthenticatedState("Sign in to update todos for your account.");
        return;
      }

      if (!response.ok || !response.body) {
        setStatus({
          tone: "error",
          message: getResponseMessage(
            response.body,
            "Unable to update the assignee.",
          ),
        });
        return;
      }

      await loadTodos({
        successStatus: {
          tone: "success",
          message: response.body.assigneeEmail
            ? `Todo assigned to ${response.body.assigneeEmail}.`
            : "Todo unassigned.",
        },
      });
    } catch {
      setStatus({
        tone: "error",
        message: "Unable to reach the todo API.",
      });
    } finally {
      setActiveAction(null);
    }
  }

  async function handleDeleteTodo(todo: TodoRecord) {
    setActiveAction(`delete:${todo.id}`);

    try {
      const response = await request<Record<string, never>>(
        `/api/todos/${todo.id}`,
        {
          method: "DELETE",
        },
      );

      if (response.status === 401) {
        setUnauthenticatedState("Sign in to delete todos for your account.");
        return;
      }

      if (!response.ok) {
        setStatus({
          tone: "error",
          message: getResponseMessage(response.body, "Unable to delete todo."),
        });
        return;
      }

      await loadTodos({
        successStatus: {
          tone: "success",
          message: "Todo deleted.",
        },
      });
    } catch {
      setStatus({
        tone: "error",
        message: "Unable to reach the todo API.",
      });
    } finally {
      setActiveAction(null);
    }
  }

  const statusStyles =
    status.tone === "error"
      ? "border-rose-200 bg-rose-50 text-rose-700"
      : status.tone === "success"
        ? "border-emerald-200 bg-emerald-50 text-emerald-700"
        : "border-slate-200 bg-white text-slate-600";

  if (isLoading) {
    return (
      <section className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
        <div className="rounded-2xl border border-dashed border-slate-200 bg-slate-50 px-5 py-12 text-center text-sm text-slate-600">
          Loading todos...
        </div>
      </section>
    );
  }

  if (isAuthenticated === false) {
    return (
      <section className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
        <div className="space-y-4 rounded-3xl border border-amber-200 bg-amber-50 p-6 text-slate-900">
          <div className="space-y-2">
            <p className="text-sm font-semibold uppercase tracking-[0.24em] text-amber-700">
              Authentication required
            </p>
            <h2 className="text-2xl font-semibold tracking-tight">
              Sign in to manage your todos.
            </h2>
            <p className="max-w-2xl text-sm leading-6 text-slate-700">
              The todo API is protected per user. Open the login page, create a
              session, then return here.
            </p>
          </div>

          <div
            className={`rounded-2xl border px-4 py-3 text-sm ${statusStyles}`}
          >
            {status.message}
          </div>

          <Link
            href="/login"
            className="inline-flex items-center justify-center rounded-full bg-slate-950 px-4 py-2 text-sm font-semibold text-white transition hover:bg-slate-800"
          >
            Open login
          </Link>
        </div>
      </section>
    );
  }

  return (
    <section className="grid gap-6 lg:grid-cols-[380px_minmax(0,1fr)]">
      <div className="space-y-4">
        <TodoFilters
          assignment={viewState.assignment}
          filter={viewState.filter}
          sort={viewState.sort}
          disabled={isLoading || activeAction !== null}
          onAssignmentChange={(assignment) => {
            if (assignment === viewState.assignment) {
              return;
            }

            updateViewState({
              ...viewState,
              assignment,
            });
          }}
          onFilterChange={(filter) => {
            if (filter === viewState.filter) {
              return;
            }

            updateViewState({
              ...viewState,
              filter,
            });
          }}
          onSortChange={(sort) => {
            if (sort === viewState.sort) {
              return;
            }

            updateViewState({
              ...viewState,
              sort,
            });
          }}
        />

        <AddTodoForm
          assigneeOptions={assigneeOptions}
          isSubmitting={activeAction === "create"}
          onSubmit={handleAddTodo}
        />

        <div className={`rounded-2xl border px-4 py-3 text-sm ${statusStyles}`}>
          {status.message}
        </div>
      </div>

      <div className="space-y-4">
        <div className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
          <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <p className="text-sm font-semibold uppercase tracking-[0.24em] text-slate-500">
                Current list
              </p>
              <h2 className="mt-2 text-2xl font-semibold tracking-tight text-slate-950">
                {getTodoCountLabel(viewState, todos.length)}
              </h2>
            </div>

            <button
              className="inline-flex items-center justify-center rounded-full border border-slate-300 bg-white px-4 py-2 text-sm font-medium text-slate-700 transition hover:border-slate-400 hover:text-slate-950 disabled:cursor-not-allowed disabled:opacity-60"
              type="button"
              onClick={() => {
                setActiveAction("refresh");
                void loadTodos({ preserveStatus: true });
              }}
              disabled={activeAction !== null}
            >
              {activeAction === "refresh" ? "Refreshing..." : "Refresh"}
            </button>
          </div>
        </div>

        {todos.length === 0 ? (
          <div className="rounded-3xl border border-dashed border-slate-300 bg-white/80 px-6 py-14 text-center shadow-sm">
            <h3 className="text-2xl font-semibold tracking-tight text-slate-950">
              {getEmptyState(viewState).heading}
            </h3>
            <p className="mx-auto mt-3 max-w-xl text-sm leading-6 text-slate-600">
              {getEmptyState(viewState).message}
            </p>
          </div>
        ) : (
          <div className="space-y-4">
            {todos.map((todo) => (
              <TodoItem
                key={todo.id}
                assigneeOptions={assigneeOptions}
                todo={todo}
                isTransitioningStatus={activeAction === `status:${todo.id}`}
                isDeleting={activeAction === `delete:${todo.id}`}
                isSavingAssignee={activeAction === `assignee:${todo.id}`}
                isSavingDueDate={activeAction === `dueDate:${todo.id}`}
                onTransitionStatus={handleTransitionTodoStatus}
                onDelete={handleDeleteTodo}
                onSaveAssignee={handleSaveAssignee}
                onSaveDueDate={handleSaveDueDate}
              />
            ))}
          </div>
        )}
      </div>
    </section>
  );
}
