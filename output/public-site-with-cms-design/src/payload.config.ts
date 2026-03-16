import { postgresAdapter } from "@payloadcms/db-postgres";
import { buildConfig } from "payload";

import { Articles } from "./collections/Articles.ts";
import { Media } from "./collections/Media.ts";
import { Users } from "./collections/Users.ts";
import {
  databaseMigrationDir,
  getDatabasePoolConfig,
  verifyDatabaseConnection,
} from "./lib/db.ts";
import { localizationConfig } from "./lib/i18n.ts";

const defaultPayloadSecret =
  "change-me-before-production-this-secret-is-only-for-local-builds";

function getServerURL(): string {
  return (
    process.env.NEXT_PUBLIC_APP_URL ??
    `http://localhost:${process.env.PORT ?? "3000"}`
  );
}

export default buildConfig({
  admin: {
    user: Users.slug,
  },
  collections: [Users, Media, Articles],
  db: postgresAdapter({
    migrationDir: databaseMigrationDir,
    pool: getDatabasePoolConfig(),
  }),
  localization: localizationConfig,
  endpoints: [
    {
      handler: async () => {
        try {
          const database = await verifyDatabaseConnection();

          return Response.json(
            {
              checkedAt: database.checkedAt,
              database: database.database,
              schema: database.schema,
              service: "payload",
              status: "ok",
            },
            { status: 200 },
          );
        } catch (error) {
          const message =
            error instanceof Error ? error.message : "Database health check failed.";

          return Response.json(
            {
              service: "payload",
              status: "error",
              message,
            },
            { status: 503 },
          );
        }
      },
      method: "get",
      path: "/health",
    },
  ],
  secret: process.env.PAYLOAD_SECRET ?? defaultPayloadSecret,
  serverURL: getServerURL(),
});
