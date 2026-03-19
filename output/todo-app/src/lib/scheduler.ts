import { createLogger, type Logger } from "./logger";

export interface ScheduledTaskContext {
  attempt: number;
  maxAttempts: number;
  runNumber: number;
}

export type ScheduledTaskResult = unknown;

export type ScheduledTask = (
  context: ScheduledTaskContext,
) => ScheduledTaskResult | Promise<ScheduledTaskResult>;

export type SchedulerLogger = Pick<Logger, "debug" | "error" | "info" | "warn">;

export interface SchedulerOptions {
  intervalMs: number;
  logger?: SchedulerLogger;
  maxRetries?: number;
  name: string;
  runOnStart?: boolean;
  task: ScheduledTask;
}

export interface SchedulerHandle {
  isRunning(): boolean;
  start(): void;
  stop(): Promise<void>;
}

function validateInterval(intervalMs: number): void {
  if (!Number.isInteger(intervalMs) || intervalMs < 1) {
    throw new Error("Scheduler interval must be a positive integer.");
  }
}

function validateMaxRetries(maxRetries: number): void {
  if (!Number.isInteger(maxRetries) || maxRetries < 0) {
    throw new Error("Scheduler max retries must be a non-negative integer.");
  }
}

function writeSchedulerLog(
  logger: SchedulerLogger,
  level: "debug" | "error" | "info" | "warn",
  payload: Record<string, unknown>,
): void {
  logger[level]("Scheduler run event", payload);
}

export function createScheduler({
  intervalMs,
  logger = createLogger({
    component: "scheduler",
  }),
  maxRetries = 0,
  name,
  runOnStart = true,
  task,
}: SchedulerOptions): SchedulerHandle {
  validateInterval(intervalMs);
  validateMaxRetries(maxRetries);

  let active = false;
  let pendingRun: Promise<void> | undefined;
  let timeoutId: NodeJS.Timeout | undefined;
  let runNumber = 0;

  const clearScheduledRun = () => {
    if (!timeoutId) {
      return;
    }

    clearTimeout(timeoutId);
    timeoutId = undefined;
  };

  const scheduleNextRun = () => {
    if (!active) {
      return;
    }

    timeoutId = setTimeout(() => {
      timeoutId = undefined;
      pendingRun = executeRun();
    }, intervalMs);
  };

  const executeRun = async () => {
    const currentRunNumber = runNumber + 1;
    const maxAttempts = maxRetries + 1;

    runNumber = currentRunNumber;

    try {
      for (let attempt = 1; attempt <= maxAttempts; attempt += 1) {
        const startedAt = Date.now();
        const startedAtIso = new Date(startedAt).toISOString();

        writeSchedulerLog(logger, "debug", {
          attempt,
          event: "run.started",
          maxAttempts,
          scheduler: name,
          runNumber: currentRunNumber,
          startedAt: startedAtIso,
        });

        try {
          const outcome = await task({
            attempt,
            maxAttempts,
            runNumber: currentRunNumber,
          });

          writeSchedulerLog(logger, "info", {
            attempt,
            durationMs: Date.now() - startedAt,
            event: "run.completed",
            maxAttempts,
            outcome,
            scheduler: name,
            startedAt: startedAtIso,
            status: "succeeded",
            runNumber: currentRunNumber,
          });
          return;
        } catch (error) {
          const isFinalAttempt = attempt === maxAttempts;

          writeSchedulerLog(logger, isFinalAttempt ? "error" : "warn", {
            attempt,
            durationMs: Date.now() - startedAt,
            error,
            event: isFinalAttempt ? "run.failed" : "run.retrying",
            maxAttempts,
            scheduler: name,
            startedAt: startedAtIso,
            status: isFinalAttempt ? "failed" : "retrying",
            runNumber: currentRunNumber,
          });
        }
      }
    } finally {
      pendingRun = undefined;
      scheduleNextRun();
    }
  };

  return {
    isRunning() {
      return active;
    },

    start() {
      if (active) {
        return;
      }

      active = true;

      if (runOnStart) {
        pendingRun = executeRun();
        return;
      }

      scheduleNextRun();
    },

    async stop() {
      if (!active) {
        return;
      }

      active = false;
      clearScheduledRun();

      await pendingRun;
    },
  };
}
