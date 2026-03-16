import { getPayload, type Payload } from "payload";

import {
  PUBLISHED_STATUS,
  SCHEDULED_PUBLISH_CONTEXT_FLAG,
  SCHEDULED_STATUS,
} from "../lib/content-status.ts";
import {
  resolveSchedulerIntervalMs,
  startScheduler,
  type SchedulerController,
} from "../lib/scheduler.ts";
import {
  captureError,
  createLogger,
  registerProcessErrorHandlers,
} from "../lib/observability.ts";
import config from "../payload.config.ts";
import type { Article } from "../payload-types.ts";

const SCHEDULED_PUBLISHER_NAME = "publish-scheduled";
const SCHEDULED_PUBLISH_INTERVAL_ENV = "SCHEDULED_PUBLISH_INTERVAL_MS";
const SCHEDULED_PUBLISH_RUN_ENV = "RUN_SCHEDULED_PUBLISH_WORKER";
const DEFAULT_SCHEDULED_PUBLISH_INTERVAL_MS = 60_000;
const DEFAULT_BATCH_SIZE = 100;
const logger = createLogger({
  bindings: {
    job: SCHEDULED_PUBLISHER_NAME,
  },
  scope: "jobs",
  service: SCHEDULED_PUBLISHER_NAME,
});

type PublishScheduledSummary = {
  checked: number;
  failed: number;
  published: number;
};

const getBatchSize = (): number => {
  const parsedValue = Number.parseInt(
    process.env.SCHEDULED_PUBLISH_BATCH_SIZE ?? "",
    10,
  );

  if (Number.isFinite(parsedValue) && parsedValue > 0) {
    return parsedValue;
  }

  return DEFAULT_BATCH_SIZE;
};

const findDueArticles = async ({
  now,
  payload,
}: {
  now: Date;
  payload: Payload;
}): Promise<Article[]> => {
  const { docs } = await payload.find({
    collection: "articles",
    depth: 0,
    limit: getBatchSize(),
    overrideAccess: true,
    pagination: false,
    sort: "publishAt",
    where: {
      and: [
        {
          status: {
            equals: SCHEDULED_STATUS,
          },
        },
        {
          publishAt: {
            less_than_equal: now.toISOString(),
          },
        },
      ],
    },
  });

  return docs as Article[];
};

export const publishScheduledArticles = async ({
  now = new Date(),
  payload,
}: {
  now?: Date;
  payload: Payload;
}): Promise<PublishScheduledSummary> => {
  const dueArticles = await findDueArticles({
    now,
    payload,
  });

  let failed = 0;
  let published = 0;

  for (const article of dueArticles) {
    try {
      await payload.update({
        collection: "articles",
        id: article.id,
        data: {
          publishedAt: article.publishAt ?? now.toISOString(),
          status: PUBLISHED_STATUS,
        },
        overrideAccess: true,
        context: {
          [SCHEDULED_PUBLISH_CONTEXT_FLAG]: true,
        },
      });

      published += 1;
    } catch (error) {
      failed += 1;

      captureError({
        details: {
          articleId: article.id,
          publishAt: article.publishAt ?? null,
        },
        error,
        event: "publish-failed",
        scope: "jobs",
        service: SCHEDULED_PUBLISHER_NAME,
      });
    }
  }

  return {
    checked: dueArticles.length,
    failed,
    published,
  };
};

export const runScheduledPublishJob = async (
  payload: Payload,
): Promise<PublishScheduledSummary> => {
  const now = new Date();

  logger.info("run-started", {
    batchSize: getBatchSize(),
    startedAt: now.toISOString(),
  });

  const summary = await publishScheduledArticles({
    now,
    payload,
  });

  logger.info("run-completed", {
    checked: summary.checked,
    failed: summary.failed,
    finishedAt: new Date().toISOString(),
    published: summary.published,
  });

  return summary;
};

export const startScheduledPublishWorker = (
  payload: Payload,
): SchedulerController =>
  startScheduler({
    intervalMs: resolveSchedulerIntervalMs(
      process.env[SCHEDULED_PUBLISH_INTERVAL_ENV],
      DEFAULT_SCHEDULED_PUBLISH_INTERVAL_MS,
    ),
    logger: createLogger({
      bindings: {
        job: SCHEDULED_PUBLISHER_NAME,
      },
      scope: "scheduler",
      service: SCHEDULED_PUBLISHER_NAME,
    }),
    name: SCHEDULED_PUBLISHER_NAME,
    task: async () => {
      await runScheduledPublishJob(payload);
    },
  });

const registerShutdownHandlers = (controller: SchedulerController): void => {
  const stopWorker = (signal: NodeJS.Signals): void => {
    logger.info("worker-stopping", {
      signal,
    });

    controller.stop();
    process.exit(0);
  };

  process.once("SIGINT", () => {
    stopWorker("SIGINT");
  });

  process.once("SIGTERM", () => {
    stopWorker("SIGTERM");
  });
};

async function main(): Promise<void> {
  registerProcessErrorHandlers({
    scope: "jobs",
    service: SCHEDULED_PUBLISHER_NAME,
  });

  const payload = await getPayload({
    config,
  });
  const controller = startScheduledPublishWorker(payload);

  registerShutdownHandlers(controller);

  logger.info("worker-started", {
    intervalMs: controller.intervalMs,
  });
}

if (process.env[SCHEDULED_PUBLISH_RUN_ENV] === "true") {
  void main().catch((error) => {
    captureError({
      error,
      event: "worker-startup-failed",
      scope: "jobs",
      service: SCHEDULED_PUBLISHER_NAME,
    });

    process.exit(1);
  });
}
