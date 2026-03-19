import { query } from "../lib/db";
import { createLogger, type Logger } from "../lib/logger";

export const PUBLISH_SCHEDULED_JOB_NAME = "publish-scheduled";

type PublishScheduledLogger = Pick<Logger, "error" | "warn">;

type DueArticleRow = {
  id: string;
  slug: string;
  publish_at: Date | string;
};

export type PublishScheduledResult = {
  checkedCount: number;
  failedCount: number;
  publishedCount: number;
  referenceDate: string;
};

function toIsoString(value: Date | string): string {
  if (value instanceof Date) {
    return value.toISOString();
  }

  return new Date(value).toISOString();
}

export async function publishScheduledContent({
  logger = createLogger({
    component: "job",
    job: PUBLISH_SCHEDULED_JOB_NAME,
  }),
  referenceDate = new Date(),
}: {
  logger?: PublishScheduledLogger;
  referenceDate?: Date;
} = {}): Promise<PublishScheduledResult> {
  const referenceTimestamp = referenceDate.toISOString();
  const dueArticles = await query<DueArticleRow>(
    `
      SELECT id, slug, publish_at
      FROM articles
      WHERE publication_status = 'draft'
        AND publish_at IS NOT NULL
        AND publish_at <= $1
      ORDER BY publish_at ASC
    `,
    [referenceTimestamp],
  );

  let publishedCount = 0;
  let failedCount = 0;

  for (const article of dueArticles.rows) {
    try {
      const result = await query(
        `
          UPDATE articles
          SET
            publication_status = 'published',
            published_at = COALESCE(published_at, CURRENT_TIMESTAMP),
            updated_at = CURRENT_TIMESTAMP
          WHERE id = $1
            AND publication_status = 'draft'
            AND publish_at IS NOT NULL
            AND publish_at <= $2
        `,
        [article.id, referenceTimestamp],
      );

      if ((result.rowCount ?? 0) === 1) {
        publishedCount += 1;
        continue;
      }

      failedCount += 1;
      logger.warn("Scheduled publish skipped", {
        articleId: article.id,
        event: "publish.skipped",
        publishAt: toIsoString(article.publish_at),
        reason: "Article was no longer eligible for publishing.",
        slug: article.slug,
      });
    } catch (error) {
      failedCount += 1;
      logger.error("Scheduled publish failed", {
        articleId: article.id,
        error,
        event: "publish.failed",
        publishAt: toIsoString(article.publish_at),
        slug: article.slug,
      });
    }
  }

  return {
    checkedCount: dueArticles.rowCount ?? dueArticles.rows.length,
    failedCount,
    publishedCount,
    referenceDate: referenceTimestamp,
  };
}
