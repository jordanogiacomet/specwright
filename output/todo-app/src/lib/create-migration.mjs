import { spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";
import { dirname, resolve } from "node:path";

const migrationName = process.argv
  .slice(2)
  .join("-")
  .replace(/[ _]+/g, "-") || "migration";

const currentFilePath = fileURLToPath(import.meta.url);
const projectRoot = resolve(dirname(currentFilePath), "../..");

const result = spawnSync(
  process.execPath,
  [
    "./node_modules/node-pg-migrate/bin/node-pg-migrate.js",
    "create",
    "--migrations-dir",
    "src/models/migrations",
    "--migration-file-language",
    "js",
    migrationName,
  ],
  {
    cwd: projectRoot,
    stdio: "inherit",
  },
);

process.exit(result.status ?? 1);
