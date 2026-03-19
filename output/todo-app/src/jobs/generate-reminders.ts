import "dotenv/config";

import { pathToFileURL } from "node:url";

import { closeDatabasePool } from "../lib/db";
import { createLogger, registerProcessErrorHandlers } from "../lib/logger";
import { generateReminders } from "../lib/reminders";

const reminderJobLogger = createLogger({
  component: "job",
  job: "generate-reminders",
  service: "todo-app-worker",
});

export async function runGenerateRemindersJob(): Promise<void> {
  const startedAt = Date.now();

  reminderJobLogger.debug("Reminder job started", {
    event: "job.started",
    startedAt: new Date(startedAt).toISOString(),
  });

  const result = await generateReminders();

  reminderJobLogger.info("Reminder job completed", {
    durationMs: Date.now() - startedAt,
    event: "job.completed",
    outcome: {
      candidateCount: result.candidateCount,
      dueSoonTodoCount: result.dueSoonTodoCount,
      existingCount: result.existingCount,
      filteredCount: result.filteredCount,
      generatedCount: result.generatedCount,
      referenceDate: result.referenceDate,
      timingDays: result.timingDays,
    },
  });
}

async function main(): Promise<void> {
  try {
    await runGenerateRemindersJob();
  } finally {
    await closeDatabasePool();
  }
}

function isDirectRun(): boolean {
  const entrypoint = process.argv[1];

  return Boolean(entrypoint) && import.meta.url === pathToFileURL(entrypoint).href;
}

if (isDirectRun()) {
  registerProcessErrorHandlers(
    "todo-app-worker-generate-reminders",
    reminderJobLogger.child({
      component: "process",
    }),
  );

  void main().catch((error) => {
    reminderJobLogger.error("Failed to generate reminders", {
      error,
      event: "job.failed",
    });
    process.exitCode = 1;
  });
}
