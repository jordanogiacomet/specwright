import "dotenv/config";

import { pathToFileURL } from "node:url";

import { closeDatabasePool, verifyDatabaseConnection } from "../lib/db";
import { createLogger, registerProcessErrorHandlers } from "../lib/logger";
import { generateReminders } from "../lib/reminders";
import { createScheduler, type SchedulerHandle } from "../lib/scheduler";
import {
  PUBLISH_SCHEDULED_JOB_NAME,
  publishScheduledContent,
} from "./publish-scheduled";

const DEFAULT_WORKER_INTERVAL_MS = 60_000;
const DEFAULT_WORKER_MAX_RETRIES = 1;
const REMINDER_JOB_NAME = "generate-reminders";
const WORKER_NAME = "automation-worker";
const WORKER_SERVICE_NAME = "todo-app-worker";

const workerLogger = createLogger({
  service: WORKER_SERVICE_NAME,
  worker: WORKER_NAME,
});
const workerLifecycleLogger = workerLogger.child({
  component: "lifecycle",
});

function parsePositiveInteger(
  configuredValue: string | undefined,
  defaultValue: number,
  envName: string,
): number {
  const parsedValue = Number.parseInt(
    configuredValue ?? `${defaultValue}`,
    10,
  );

  if (Number.isNaN(parsedValue) || parsedValue < 1) {
    throw new Error(`${envName} must be a positive integer.`);
  }

  return parsedValue;
}

function parseNonNegativeInteger(
  configuredValue: string | undefined,
  defaultValue: number,
  envName: string,
): number {
  const parsedValue = Number.parseInt(
    configuredValue ?? `${defaultValue}`,
    10,
  );

  if (Number.isNaN(parsedValue) || parsedValue < 0) {
    throw new Error(`${envName} must be a non-negative integer.`);
  }

  return parsedValue;
}

function getJobIntervalMs(
  configuredValue: string | undefined,
  envName: string,
): number {
  return parsePositiveInteger(
    configuredValue ?? process.env.WORKER_INTERVAL_MS,
    DEFAULT_WORKER_INTERVAL_MS,
    `${envName} or WORKER_INTERVAL_MS`,
  );
}

function getJobMaxRetries(
  configuredValue: string | undefined,
  envName: string,
): number {
  return parseNonNegativeInteger(
    configuredValue ?? process.env.WORKER_MAX_RETRIES,
    DEFAULT_WORKER_MAX_RETRIES,
    `${envName} or WORKER_MAX_RETRIES`,
  );
}

async function runReminderAutomationJob() {
  const result = await generateReminders();

  return {
    candidateCount: result.candidateCount,
    existingCount: result.existingCount,
    filteredCount: result.filteredCount,
    generatedCount: result.generatedCount,
    dueSoonTodoCount: result.dueSoonTodoCount,
    referenceDate: result.referenceDate,
    timingDays: result.timingDays,
  };
}

async function runScheduledPublishingJob() {
  return publishScheduledContent({
    logger: workerLogger.child({
      component: "job",
      job: PUBLISH_SCHEDULED_JOB_NAME,
    }),
  });
}

type WorkerJobConfig = {
  intervalMs: number;
  maxRetries: number;
  name: string;
  task: () => Promise<Record<string, unknown>>;
};

function getWorkerJobs(): WorkerJobConfig[] {
  return [
    {
      intervalMs: getJobIntervalMs(
        process.env.REMINDER_JOB_INTERVAL_MS,
        "REMINDER_JOB_INTERVAL_MS",
      ),
      maxRetries: getJobMaxRetries(
        process.env.REMINDER_JOB_MAX_RETRIES,
        "REMINDER_JOB_MAX_RETRIES",
      ),
      name: REMINDER_JOB_NAME,
      task: runReminderAutomationJob,
    },
    {
      intervalMs: getJobIntervalMs(
        process.env.PUBLISH_JOB_INTERVAL_MS,
        "PUBLISH_JOB_INTERVAL_MS",
      ),
      maxRetries: getJobMaxRetries(
        process.env.PUBLISH_JOB_MAX_RETRIES,
        "PUBLISH_JOB_MAX_RETRIES",
      ),
      name: PUBLISH_SCHEDULED_JOB_NAME,
      task: runScheduledPublishingJob,
    },
  ];
}

function registerShutdownHandlers(schedulers: SchedulerHandle[]): void {
  let isShuttingDown = false;

  const shutdown = async (signal: NodeJS.Signals) => {
    if (isShuttingDown) {
      return;
    }

    isShuttingDown = true;
    workerLifecycleLogger.info("Worker shutdown started", {
      event: "shutdown.started",
      signal,
    });

    try {
      await Promise.all(schedulers.map((scheduler) => scheduler.stop()));
      await closeDatabasePool();
      workerLifecycleLogger.info("Worker shutdown completed", {
        event: "shutdown.completed",
        signal,
      });
    } catch (error) {
      workerLifecycleLogger.error("Worker shutdown failed", {
        error,
        event: "shutdown.failed",
        signal,
      });
      process.exitCode = 1;
    } finally {
      process.exit();
    }
  };

  process.once("SIGINT", () => {
    void shutdown("SIGINT");
  });

  process.once("SIGTERM", () => {
    void shutdown("SIGTERM");
  });
}

export async function startWorker(): Promise<SchedulerHandle[]> {
  const jobs = getWorkerJobs();

  registerProcessErrorHandlers(
    WORKER_SERVICE_NAME,
    workerLogger.child({
      component: "process",
    }),
  );

  await verifyDatabaseConnection();
  workerLifecycleLogger.info("Database connection verified", {
    event: "database.verified",
  });

  const schedulers = jobs.map((job) =>
    createScheduler({
      intervalMs: job.intervalMs,
      logger: workerLogger.child({
        component: "scheduler",
        job: job.name,
      }),
      maxRetries: job.maxRetries,
      name: job.name,
      task: job.task,
    }),
  );

  registerShutdownHandlers(schedulers);

  workerLifecycleLogger.info("Worker started", {
    event: "worker.started",
    jobs: jobs.map((job) => ({
      intervalMs: job.intervalMs,
      maxRetries: job.maxRetries,
      name: job.name,
    })),
  });

  for (const scheduler of schedulers) {
    scheduler.start();
  }

  return schedulers;
}

function isDirectRun(): boolean {
  const entrypoint = process.argv[1];

  return (
    Boolean(entrypoint) && import.meta.url === pathToFileURL(entrypoint).href
  );
}

async function main(): Promise<void> {
  await startWorker();
}

if (isDirectRun()) {
  void main().catch(async (error) => {
    workerLifecycleLogger.error("Worker startup failed", {
      error,
      event: "startup.failed",
      jobs: [REMINDER_JOB_NAME, PUBLISH_SCHEDULED_JOB_NAME],
    });

    try {
      await closeDatabasePool();
    } finally {
      process.exit(1);
    }
  });
}
