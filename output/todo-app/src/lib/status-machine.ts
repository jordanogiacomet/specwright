export const workItemStatuses = [
  "pending",
  "in_progress",
  "completed",
] as const;

export type WorkItemStatus = (typeof workItemStatuses)[number];

export const workItemStatusLabels: Record<WorkItemStatus, string> = {
  pending: "Pending",
  in_progress: "In progress",
  completed: "Completed",
};

export const workItemStatusTransitions: Record<
  WorkItemStatus,
  readonly WorkItemStatus[]
> = {
  pending: ["in_progress", "completed"],
  in_progress: ["pending", "completed"],
  completed: ["in_progress"],
};

export function isWorkItemStatus(value: unknown): value is WorkItemStatus {
  return (
    typeof value === "string" &&
    workItemStatuses.includes(value as WorkItemStatus)
  );
}

export function getAllowedWorkItemStatusTransitions(
  status: WorkItemStatus,
): readonly WorkItemStatus[] {
  return workItemStatusTransitions[status];
}

export function canTransitionWorkItemStatus(
  currentStatus: WorkItemStatus,
  nextStatus: WorkItemStatus,
): boolean {
  return (
    currentStatus === nextStatus ||
    workItemStatusTransitions[currentStatus].includes(nextStatus)
  );
}

export function getCompletedStateForWorkItemStatus(
  status: WorkItemStatus,
): boolean {
  return status === "completed";
}

export function getWorkItemStatusFromCompletionFlag(
  completed: boolean,
  currentStatus: WorkItemStatus,
): WorkItemStatus {
  if (completed) {
    return "completed";
  }

  return currentStatus === "completed" ? "in_progress" : "pending";
}
