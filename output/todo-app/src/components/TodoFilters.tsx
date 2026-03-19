"use client";

export const todoStatusFilters = ["all", "pending", "completed"] as const;
export const todoAssignmentFilters = [
  "owned",
  "assigned",
  "unassigned",
] as const;
export const todoSortOptions = ["newest", "oldest", "priority"] as const;

export type TodoStatusFilter = (typeof todoStatusFilters)[number];
export type TodoAssignmentFilter = (typeof todoAssignmentFilters)[number];
export type TodoSortOption = (typeof todoSortOptions)[number];

type TodoFiltersProps = {
  assignment: TodoAssignmentFilter;
  filter: TodoStatusFilter;
  sort: TodoSortOption;
  disabled?: boolean;
  onAssignmentChange: (assignment: TodoAssignmentFilter) => void;
  onFilterChange: (filter: TodoStatusFilter) => void;
  onSortChange: (sort: TodoSortOption) => void;
};

const assignmentLabels: Record<TodoAssignmentFilter, string> = {
  owned: "Owned by me",
  assigned: "Assigned to me",
  unassigned: "Unassigned only",
};

const filterLabels: Record<TodoStatusFilter, string> = {
  all: "All",
  pending: "Pending",
  completed: "Completed",
};

const sortLabels: Record<TodoSortOption, string> = {
  newest: "Newest first",
  oldest: "Oldest first",
  priority: "Priority (high to low)",
};

export function TodoFilters({
  assignment,
  filter,
  sort,
  disabled = false,
  onAssignmentChange,
  onFilterChange,
  onSortChange,
}: TodoFiltersProps) {
  return (
    <div className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
      <div className="flex flex-col gap-5">
        <div className="space-y-3">
          <div>
            <p className="text-sm font-semibold uppercase tracking-[0.24em] text-slate-500">
              Filters
            </p>
            <h2 className="mt-2 text-2xl font-semibold tracking-tight text-slate-950">
              Shape the current view
            </h2>
          </div>

          <div className="flex flex-wrap gap-2">
            {todoStatusFilters.map((statusFilter) => {
              const isActive = statusFilter === filter;

              return (
                <button
                  key={statusFilter}
                  className={`rounded-full border px-4 py-2 text-sm font-semibold transition disabled:cursor-not-allowed disabled:opacity-60 ${
                    isActive
                      ? "border-sky-600 bg-sky-600 text-white"
                      : "border-slate-300 bg-white text-slate-700 hover:border-slate-400 hover:text-slate-950"
                  }`}
                  type="button"
                  onClick={() => onFilterChange(statusFilter)}
                  aria-pressed={isActive}
                  disabled={disabled}
                >
                  {filterLabels[statusFilter]}
                </button>
              );
            })}
          </div>
        </div>

        <div className="grid gap-4 md:grid-cols-2">
          <label className="block space-y-2">
            <span className="text-sm font-medium text-slate-700">
              Assignment view
            </span>
            <select
              className="w-full rounded-xl border border-slate-300 bg-white px-4 py-3 text-sm outline-none transition focus:border-sky-500 disabled:cursor-not-allowed disabled:bg-slate-100"
              value={assignment}
              onChange={(event) =>
                onAssignmentChange(event.target.value as TodoAssignmentFilter)
              }
              disabled={disabled}
            >
              {todoAssignmentFilters.map((assignmentFilter) => (
                <option key={assignmentFilter} value={assignmentFilter}>
                  {assignmentLabels[assignmentFilter]}
                </option>
              ))}
            </select>
          </label>

          <label className="block space-y-2">
            <span className="text-sm font-medium text-slate-700">Sort by</span>
            <select
              className="w-full rounded-xl border border-slate-300 bg-white px-4 py-3 text-sm outline-none transition focus:border-sky-500 disabled:cursor-not-allowed disabled:bg-slate-100"
              value={sort}
              onChange={(event) =>
                onSortChange(event.target.value as TodoSortOption)
              }
              disabled={disabled}
            >
              {todoSortOptions.map((sortOption) => (
                <option key={sortOption} value={sortOption}>
                  {sortLabels[sortOption]}
                </option>
              ))}
            </select>
          </label>
        </div>
      </div>
    </div>
  );
}
