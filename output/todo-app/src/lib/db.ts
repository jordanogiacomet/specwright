import {
  Pool,
  type PoolConfig,
  type QueryResult,
  type QueryResultRow,
} from "pg";

const DEFAULT_POOL_MAX = 10;
const DEFAULT_IDLE_TIMEOUT_MS = 30_000;
const DEFAULT_CONNECTION_TIMEOUT_MS = 5_000;

export type DatabaseDateValue = Date | string;

declare global {
  var __todoAppDbPool: Pool | undefined;
}

function getRequiredEnv(name: string): string {
  const value = process.env[name]?.trim();

  if (!value) {
    throw new Error(`Missing required environment variable: ${name}`);
  }

  return value;
}

function getPoolMax(): number {
  const configuredMax = Number.parseInt(
    process.env.DATABASE_POOL_MAX ?? `${DEFAULT_POOL_MAX}`,
    10,
  );

  if (Number.isNaN(configuredMax) || configuredMax < 1) {
    throw new Error("DATABASE_POOL_MAX must be a positive integer.");
  }

  return configuredMax;
}

function getPoolConfig(): PoolConfig {
  return {
    connectionString: getRequiredEnv("DATABASE_URL"),
    max: getPoolMax(),
    idleTimeoutMillis: DEFAULT_IDLE_TIMEOUT_MS,
    connectionTimeoutMillis: DEFAULT_CONNECTION_TIMEOUT_MS,
    allowExitOnIdle: true,
  };
}

export function getDbPool(): Pool {
  if (!globalThis.__todoAppDbPool) {
    globalThis.__todoAppDbPool = new Pool(getPoolConfig());
  }

  return globalThis.__todoAppDbPool;
}

export async function query<T extends QueryResultRow = QueryResultRow>(
  text: string,
  values?: unknown[],
): Promise<QueryResult<T>> {
  return getDbPool().query<T>(text, values);
}

export function toIsoTimestamp(value: DatabaseDateValue): string {
  return value instanceof Date
    ? value.toISOString()
    : new Date(value).toISOString();
}

export async function verifyDatabaseConnection(): Promise<boolean> {
  const client = await getDbPool().connect();

  try {
    await client.query("SELECT 1");
    return true;
  } finally {
    client.release();
  }
}

export async function closeDatabasePool(): Promise<void> {
  if (!globalThis.__todoAppDbPool) {
    return;
  }

  await globalThis.__todoAppDbPool.end();
  globalThis.__todoAppDbPool = undefined;
}
