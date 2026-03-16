import { createLogger, type StructuredLogger } from "./observability.ts";

const DEFAULT_SCHEDULER_INTERVAL_MS = 60_000;

type SchedulerTask = () => Promise<void> | void;
type SchedulerLogLevel = "error" | "info" | "warn";
type SchedulerLogger = Pick<StructuredLogger, SchedulerLogLevel>;

export type SchedulerController = {
  intervalMs: number;
  runNow: () => Promise<void>;
  stop: () => void;
};

type StartSchedulerOptions = {
  intervalMs: number;
  logger?: SchedulerLogger;
  name: string;
  runOnStart?: boolean;
  task: SchedulerTask;
};

const getErrorMessage = (error: unknown): string =>
  error instanceof Error ? error.message : String(error);

const logSchedulerEvent = (
  logger: SchedulerLogger,
  level: SchedulerLogLevel,
  schedulerName: string,
  event: string,
  details: Record<string, unknown> = {},
): void => {
  logger[level](event, {
    ...details,
    scheduler: schedulerName,
  });
};

export const resolveSchedulerIntervalMs = (
  value: string | undefined,
  fallback = DEFAULT_SCHEDULER_INTERVAL_MS,
): number => {
  const parsedValue = Number.parseInt(value ?? "", 10);

  if (Number.isFinite(parsedValue) && parsedValue > 0) {
    return parsedValue;
  }

  return fallback;
};

export const startScheduler = ({
  intervalMs,
  logger,
  name,
  runOnStart = true,
  task,
}: StartSchedulerOptions): SchedulerController => {
  const activeLogger =
    logger ??
    createLogger({
      scope: "scheduler",
      service: name,
    });
  let activeRun: Promise<void> | null = null;
  let stopped = false;
  let timeout: NodeJS.Timeout | undefined;

  const scheduleNextRun = (): void => {
    if (stopped) {
      return;
    }

    timeout = setTimeout(() => {
      void runNow();
    }, intervalMs);
  };

  const runNow = async (): Promise<void> => {
    if (stopped) {
      return;
    }

    if (activeRun) {
      return activeRun;
    }

    const startedAt = Date.now();

    logSchedulerEvent(activeLogger, "info", name, "run-started", {
      intervalMs,
    });

    activeRun = (async () => {
      try {
        await task();

        logSchedulerEvent(activeLogger, "info", name, "run-completed", {
          durationMs: Date.now() - startedAt,
        });
      } catch (error) {
        logSchedulerEvent(activeLogger, "error", name, "run-failed", {
          durationMs: Date.now() - startedAt,
          error: getErrorMessage(error),
        });
      } finally {
        activeRun = null;
        scheduleNextRun();
      }
    })();

    return activeRun;
  };

  logSchedulerEvent(activeLogger, "info", name, "started", {
    intervalMs,
  });

  if (runOnStart) {
    void runNow();
  } else {
    scheduleNextRun();
  }

  return {
    intervalMs,
    runNow,
    stop: () => {
      stopped = true;

      if (timeout) {
        clearTimeout(timeout);
        timeout = undefined;
      }

      logSchedulerEvent(activeLogger, "info", name, "stopped");
    },
  };
};
