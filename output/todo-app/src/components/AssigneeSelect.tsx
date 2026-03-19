"use client";

export type AssigneeOption = {
  id: string;
  email: string;
};

type AssigneeSelectProps = {
  id?: string;
  value: string | null;
  users: AssigneeOption[];
  disabled?: boolean;
  emptyLabel?: string;
  onChange: (assigneeId: string | null) => void;
};

export function AssigneeSelect({
  id,
  value,
  users,
  disabled = false,
  emptyLabel = "Unassigned",
  onChange,
}: AssigneeSelectProps) {
  return (
    <select
      id={id}
      className="w-full rounded-xl border border-slate-300 bg-white px-4 py-3 text-sm outline-none transition focus:border-sky-500 disabled:cursor-not-allowed disabled:bg-slate-100"
      value={value ?? ""}
      onChange={(event) => onChange(event.target.value || null)}
      disabled={disabled}
    >
      <option value="">{emptyLabel}</option>
      {users.map((user) => (
        <option key={user.id} value={user.id}>
          {user.email}
        </option>
      ))}
    </select>
  );
}
