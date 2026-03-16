import { Pool } from "pg";

const DEFAULT_DB_POOL_MAX = 10;
const DEFAULT_DB_IDLE_TIMEOUT_MS = 30_000;
const DEFAULT_DB_CONNECTION_TIMEOUT_MS = 10_000;
const DEFAULT_POSTGRES_HOST = "localhost";
const DEFAULT_POSTGRES_PORT = "5433";
const DEFAULT_POSTGRES_DB = "public_site_with_cms";
const DEFAULT_POSTGRES_USER = "postgres";
const DEFAULT_POSTGRES_PASSWORD = "postgres";

let pool: Pool | undefined;

type DatabasePoolConfig = {
  allowExitOnIdle: boolean;
  connectionString?: string;
  connectionTimeoutMillis: number;
  idleTimeoutMillis: number;
  max: number;
};

const parsePositiveInt = (
  value: string | undefined,
  fallback: number,
): number => {
  const parsedValue = Number.parseInt(value ?? "", 10);

  if (Number.isFinite(parsedValue) && parsedValue > 0) {
    return parsedValue;
  }

  return fallback;
};

// Match the local docker-compose bootstrap values when DATABASE_URL is not provided.
const buildDefaultConnectionString = (): string => {
  const host = process.env.POSTGRES_HOST ?? DEFAULT_POSTGRES_HOST;
  const port = process.env.POSTGRES_PORT ?? DEFAULT_POSTGRES_PORT;
  const database = process.env.POSTGRES_DB ?? DEFAULT_POSTGRES_DB;
  const user = process.env.POSTGRES_USER ?? DEFAULT_POSTGRES_USER;
  const password = process.env.POSTGRES_PASSWORD ?? DEFAULT_POSTGRES_PASSWORD;

  return `postgresql://${encodeURIComponent(user)}:${encodeURIComponent(password)}@${host}:${port}/${database}`;
};

export function getDatabaseConnectionString({
  optional = false,
}: { optional?: boolean } = {}): string {
  const connectionString =
    process.env.DATABASE_URL ??
    process.env.DATABASE_URI ??
    buildDefaultConnectionString();

  if (!connectionString && !optional) {
    throw new Error(
      "DATABASE_URL is not set. Copy .env.example to .env.local and provide a Postgres connection string.",
    );
  }

  return connectionString;
}

export function createDatabasePoolConfig({
  allowMissingConnectionString = false,
}: {
  allowMissingConnectionString?: boolean;
} = {}): DatabasePoolConfig {
  const connectionString = getDatabaseConnectionString({
    optional: allowMissingConnectionString,
  });

  return {
    allowExitOnIdle: true,
    connectionString: connectionString || undefined,
    connectionTimeoutMillis: parsePositiveInt(
      process.env.DB_CONNECTION_TIMEOUT_MS,
      DEFAULT_DB_CONNECTION_TIMEOUT_MS,
    ),
    idleTimeoutMillis: parsePositiveInt(
      process.env.DB_IDLE_TIMEOUT_MS,
      DEFAULT_DB_IDLE_TIMEOUT_MS,
    ),
    max: parsePositiveInt(process.env.DB_POOL_MAX, DEFAULT_DB_POOL_MAX),
  };
}

export function getDatabasePool(): Pool {
  if (!pool) {
    pool = new Pool(createDatabasePoolConfig());
  }

  return pool;
}

export type DatabaseConnectionStatus = {
  currentDatabase: string;
  currentSchema: string;
  serverTime: Date;
};

export async function verifyDatabaseConnection(): Promise<DatabaseConnectionStatus> {
  const result = await getDatabasePool().query<{
    current_database: string;
    current_schema: string;
    server_time: Date;
  }>(`
    select
      current_database() as current_database,
      current_schema() as current_schema,
      now() as server_time
  `);

  const row = result.rows[0];

  if (!row) {
    throw new Error("Database responded without a verification row.");
  }

  return {
    currentDatabase: row.current_database,
    currentSchema: row.current_schema,
    serverTime: row.server_time,
  };
}

export async function closeDatabasePool(): Promise<void> {
  if (!pool) {
    return;
  }

  const activePool = pool;
  pool = undefined;

  await activePool.end();
}
