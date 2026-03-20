import { buildConfig } from "payload";
import { postgresAdapter } from "@payloadcms/db-postgres";
import path from "path";
import { fileURLToPath } from "url";

import { Authors } from "./collections/Authors.ts";
import { Homepage } from "./globals/Homepage.ts";
import { Media } from "./collections/Media.ts";
import { Pages } from "./collections/Pages.ts";
import { Posts } from "./collections/Posts.ts";
import { SiteSettings } from "./globals/SiteSettings.ts";
import { databasePoolConfig } from "./lib/db.ts";
import {
  payloadLoggerConfig,
  registerUnhandledErrorHandlers,
} from "./lib/logger.ts";

const filename = fileURLToPath(import.meta.url);
const dirname = path.dirname(filename);

registerUnhandledErrorHandlers();

function getPayloadSecret(): string {
  const secret = process.env.PAYLOAD_SECRET?.trim();

  if (!secret) {
    throw new Error("PAYLOAD_SECRET env var is required");
  }

  return secret;
}

export default buildConfig({
  collections: [Pages, Posts, Authors, Media],
  globals: [SiteSettings, Homepage],
  secret: getPayloadSecret(),
  logger: payloadLoggerConfig,
  typescript: {
    outputFile: path.resolve(dirname, "payload-types.ts"),
  },
  db: postgresAdapter({
    migrationDir: path.resolve(dirname, "lib/migrations"),
    pool: databasePoolConfig,
  }),
});
