import { closeDatabasePool, verifyDatabaseConnection } from "../lib/db.ts";
import {
  captureError,
  createLogger,
  registerProcessErrorHandlers,
} from "../lib/observability.ts";

const logger = createLogger({
  scope: "scripts",
  service: "db-verify",
});

async function main(): Promise<void> {
  registerProcessErrorHandlers({
    exitOnUncaughtException: false,
    scope: "scripts",
    service: "db-verify",
  });

  try {
    const status = await verifyDatabaseConnection();

    logger.info("database-connection-verified", {
      currentDatabase: status.currentDatabase,
      currentSchema: status.currentSchema,
      serverTime: status.serverTime.toISOString(),
    });
  } catch (error) {
    captureError({
      error,
      event: "database-connection-failed",
      scope: "scripts",
      service: "db-verify",
    });
    process.exitCode = 1;
  } finally {
    await closeDatabasePool();
  }
}

void main();
