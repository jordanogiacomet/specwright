import { postgresAdapter } from "@payloadcms/db-postgres";
import { buildConfig } from "payload";
import path from "path";
import sharp from "sharp";
import { fileURLToPath } from "url";

import { Articles } from "./collections/Articles.ts";
import { Categories } from "./collections/Categories.ts";
import { Media } from "./collections/Media.ts";
import { Users } from "./collections/Users.ts";
import { createDatabasePoolConfig } from "./lib/db.ts";
import { payloadLocalizationConfig } from "./lib/i18n.ts";
import { migrations } from "./migrations/index.ts";

const filename = fileURLToPath(import.meta.url);
const dirname = path.dirname(filename);

export default buildConfig({
  secret: process.env.PAYLOAD_SECRET || "development-only-payload-secret",
  sharp,
  admin: {
    user: "users",
  },
  routes: {
    admin: "/admin",
    api: "/api",
  },
  typescript: {
    outputFile: path.resolve(dirname, "payload-types.ts"),
  },
  localization: payloadLocalizationConfig,
  collections: [Users, Media, Categories, Articles],
  db: postgresAdapter({
    migrationDir: path.resolve(dirname, "migrations"),
    pool: createDatabasePoolConfig({ allowMissingConnectionString: true }),
    prodMigrations: migrations,
    push: false,
  }),
});
