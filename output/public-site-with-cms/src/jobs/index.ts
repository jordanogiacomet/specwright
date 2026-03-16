import {
  closeDatabasePool,
  verifyDatabaseConnection,
} from "../lib/db.ts";
import {
  captureError,
  createLogger,
  registerProcessErrorHandlers,
} from "../lib/observability.ts";
import {
  resolveSchedulerIntervalMs,
  startScheduler,
  type SchedulerController,
} from "../lib/scheduler.ts";

const JOB_WORKER_NAME = "job-worker";
const JOB_WORKER_INTERVAL_ENV = "JOB_WORKER_INTERVAL_MS";
const DEFAULT_JOB_WORKER_INTERVAL_MS = 60_000;
const logger = createLogger({
  bindings: {
    worker: JOB_WORKER_NAME,
  },
  scope: "jobs",
  service: JOB_WORKER_NAME,
});

const runWorkerHeartbeat = async (): Promise<void> => {
  const connectionStatus = await verifyDatabaseConnection();

  logger.info("heartbeat", {
    currentDatabase: connectionStatus.currentDatabase,
    currentSchema: connectionStatus.currentSchema,
    serverTime: connectionStatus.serverTime.toISOString(),
  });
};

export const startJobWorker = (): SchedulerController =>
  startScheduler({
    intervalMs: resolveSchedulerIntervalMs(
      process.env[JOB_WORKER_INTERVAL_ENV],
      DEFAULT_JOB_WORKER_INTERVAL_MS,
    ),
    logger: createLogger({
      bindings: {
        worker: JOB_WORKER_NAME,
      },
      scope: "scheduler",
      service: JOB_WORKER_NAME,
    }),
    name: JOB_WORKER_NAME,
    task: runWorkerHeartbeat,
  });

const registerShutdownHandlers = (controller: SchedulerController): void => {
  const stopWorker = async (signal: NodeJS.Signals): Promise<void> => {
    logger.info("worker-stopping", {
      signal,
    });

    controller.stop();

    try {
      await closeDatabasePool();

      logger.info("database-disconnected");
      process.exit(0);
    } catch (error) {
      captureError({
        error,
        event: "worker-shutdown-failed",
        scope: "jobs",
        service: JOB_WORKER_NAME,
      });

      process.exit(1);
    }
  };

  process.once("SIGINT", () => {
    void stopWorker("SIGINT");
  });

  process.once("SIGTERM", () => {
    void stopWorker("SIGTERM");
  });
};

async function main(): Promise<void> {
  registerProcessErrorHandlers({
    scope: "jobs",
    service: JOB_WORKER_NAME,
  });

  const connectionStatus = await verifyDatabaseConnection();

  logger.info("database-connected", {
    currentDatabase: connectionStatus.currentDatabase,
    currentSchema: connectionStatus.currentSchema,
    serverTime: connectionStatus.serverTime.toISOString(),
  });

  const controller = startJobWorker();

  registerShutdownHandlers(controller);

  logger.info("worker-started", {
    intervalMs: controller.intervalMs,
  });
}

void main().catch((error) => {
  captureError({
    error,
    event: "worker-startup-failed",
    scope: "jobs",
    service: JOB_WORKER_NAME,
  });

  void closeDatabasePool().finally(() => {
    process.exit(1);
  });
});
