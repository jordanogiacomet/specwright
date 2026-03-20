import { Pool, type PoolConfig } from "pg";

const DATABASE_URI_ENV_VAR = "DATABASE_URI";
const DEFAULT_CONNECTION_TIMEOUT_MS = 5_000;
const DEFAULT_IDLE_TIMEOUT_MS = 30_000;
const DEFAULT_MAX_CONNECTIONS = 10;

export type DatabaseConnectionStatus = {
  currentDatabase: string;
  ok: true;
};

export type VerifyDatabaseConnectionOptions = {
  closePool?: boolean;
  pool?: Pool;
};

export function getDatabaseConnectionString(): string {
  const connectionString = process.env[DATABASE_URI_ENV_VAR]?.trim();

  if (!connectionString) {
    throw new Error(`${DATABASE_URI_ENV_VAR} env var is required`);
  }

  return connectionString;
}

export function getDatabasePoolConfig(): PoolConfig {
  return {
    connectionString: getDatabaseConnectionString(),
    connectionTimeoutMillis: DEFAULT_CONNECTION_TIMEOUT_MS,
    idleTimeoutMillis: DEFAULT_IDLE_TIMEOUT_MS,
    max: DEFAULT_MAX_CONNECTIONS,
  };
}

export const databasePoolConfig = getDatabasePoolConfig();

export function createDatabasePool(
  config: PoolConfig = databasePoolConfig,
): Pool {
  return new Pool(config);
}

export async function verifyDatabaseConnection(
  options: VerifyDatabaseConnectionOptions = {},
): Promise<DatabaseConnectionStatus> {
  const pool = options.pool ?? createDatabasePool();
  const shouldClosePool = options.closePool ?? !options.pool;

  try {
    const result = await pool.query<{ currentDatabase: string }>(
      'select current_database() as "currentDatabase"',
    );
    const currentDatabase = result.rows[0]?.currentDatabase;

    if (!currentDatabase) {
      throw new Error("Database connection check returned no database name");
    }

    return {
      currentDatabase,
      ok: true,
    };
  } finally {
    if (shouldClosePool) {
      await pool.end();
    }
  }
}
