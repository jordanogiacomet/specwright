import type { PoolConfig } from "pg";
import { Pool } from "pg";

const defaultDatabaseURL =
  "postgresql://postgres:postgres@127.0.0.1:5433/public_site_with_cms_design";
const defaultPoolMax = 10;
const defaultPoolIdleTimeoutMs = 30_000;
const defaultPoolConnectionTimeoutMs = 5_000;

export const databaseMigrationDir = "./src/migrations";

declare global {
  var __databasePool: Pool | undefined;
}

function readPositiveIntegerEnv(name: string, fallback: number): number {
  const rawValue = process.env[name];

  if (!rawValue) {
    return fallback;
  }

  const parsedValue = Number.parseInt(rawValue, 10);

  if (!Number.isInteger(parsedValue) || parsedValue <= 0) {
    throw new Error(`${name} must be a positive integer.`);
  }

  return parsedValue;
}

function readNonNegativeIntegerEnv(name: string, fallback: number): number {
  const rawValue = process.env[name];

  if (!rawValue) {
    return fallback;
  }

  const parsedValue = Number.parseInt(rawValue, 10);

  if (!Number.isInteger(parsedValue) || parsedValue < 0) {
    throw new Error(`${name} must be a non-negative integer.`);
  }

  return parsedValue;
}

export function getDatabaseURL(): string {
  return (
    process.env.DATABASE_URL ??
    process.env.DATABASE_URI ??
    defaultDatabaseURL
  );
}

export function getDatabasePoolConfig(): PoolConfig {
  return {
    allowExitOnIdle: true,
    connectionString: getDatabaseURL(),
    connectionTimeoutMillis: readNonNegativeIntegerEnv(
      "DATABASE_POOL_CONNECTION_TIMEOUT_MS",
      defaultPoolConnectionTimeoutMs,
    ),
    idleTimeoutMillis: readNonNegativeIntegerEnv(
      "DATABASE_POOL_IDLE_TIMEOUT_MS",
      defaultPoolIdleTimeoutMs,
    ),
    max: readPositiveIntegerEnv("DATABASE_POOL_MAX", defaultPoolMax),
  };
}

export function getDatabasePool(): Pool {
  // Reuse a single pool across reloads in local development.
  if (!globalThis.__databasePool) {
    globalThis.__databasePool = new Pool(getDatabasePoolConfig());
  }

  return globalThis.__databasePool;
}

export async function verifyDatabaseConnection() {
  const connectionResult = await getDatabasePool().query<{
    checked_at: string;
    current_database: string;
    current_schema: string;
    server_version: string;
  }>(
    `
      select
        current_database() as current_database,
        current_schema() as current_schema,
        version() as server_version,
        now() at time zone 'utc' as checked_at
    `,
  );

  const [row] = connectionResult.rows;

  if (!row) {
    throw new Error("Database verification query returned no rows.");
  }

  return {
    checkedAt: row.checked_at,
    database: row.current_database,
    schema: row.current_schema,
    serverVersion: row.server_version,
  };
}

export async function closeDatabasePool(): Promise<void> {
  if (!globalThis.__databasePool) {
    return;
  }

  await globalThis.__databasePool.end();
  globalThis.__databasePool = undefined;
}
