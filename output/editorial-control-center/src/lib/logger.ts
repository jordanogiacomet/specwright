import type { Config } from "payload";

const LOG_LEVEL_PRIORITY = {
  debug: 10,
  info: 20,
  warn: 30,
  error: 40,
} as const;

export type LogLevel = keyof typeof LOG_LEVEL_PRIORITY;
export type LogContext = Record<string, unknown>;

export const SERVICE_NAME = "editorial-control-center";

const runtimeEnvironment = process.env.NODE_ENV?.trim() || "development";
const minimumLogLevel: LogLevel =
  runtimeEnvironment === "development" ? "debug" : "info";

function shouldWrite(level: LogLevel): boolean {
  return LOG_LEVEL_PRIORITY[level] >= LOG_LEVEL_PRIORITY[minimumLogLevel];
}

function serializeError(error: unknown): Record<string, unknown> {
  if (error instanceof Error) {
    return {
      cause: error.cause ? serializeError(error.cause) : undefined,
      message: error.message,
      name: error.name,
      stack: error.stack,
    };
  }

  if (typeof error === "string") {
    return { message: error };
  }

  return { value: error };
}

function normalizeContext(context: LogContext = {}): LogContext {
  const normalizedContext: LogContext = {};

  for (const [key, value] of Object.entries(context)) {
    if (value === undefined) {
      continue;
    }

    normalizedContext[key] = key === "error" ? serializeError(value) : value;
  }

  return normalizedContext;
}

function stringifyLogEntry(entry: LogContext): string {
  const seen = new WeakSet<object>();

  return JSON.stringify(entry, (_key, value) => {
    if (value instanceof Error) {
      return serializeError(value);
    }

    if (typeof value === "bigint") {
      return value.toString();
    }

    if (value instanceof Date) {
      return value.toISOString();
    }

    if (value instanceof Map) {
      return Object.fromEntries(value);
    }

    if (value instanceof Set) {
      return [...value];
    }

    if (value && typeof value === "object") {
      if (seen.has(value)) {
        return "[Circular]";
      }

      seen.add(value);
    }

    return value;
  });
}

function writeLog(
  level: LogLevel,
  message: string,
  bindings: LogContext,
  context: LogContext = {},
): void {
  if (!shouldWrite(level)) {
    return;
  }

  const entry = {
    ...bindings,
    ...normalizeContext(context),
    environment: runtimeEnvironment,
    level,
    message,
    service: SERVICE_NAME,
    timestamp: new Date().toISOString(),
  };

  const stream =
    level === "warn" || level === "error" ? process.stderr : process.stdout;

  stream.write(`${stringifyLogEntry(entry)}\n`);
}

export function createLogger(bindings: LogContext = {}) {
  return {
    child(childBindings: LogContext = {}) {
      return createLogger({ ...bindings, ...childBindings });
    },
    debug(message: string, context?: LogContext) {
      writeLog("debug", message, bindings, context);
    },
    error(message: string, context?: LogContext) {
      writeLog("error", message, bindings, context);
    },
    info(message: string, context?: LogContext) {
      writeLog("info", message, bindings, context);
    },
    warn(message: string, context?: LogContext) {
      writeLog("warn", message, bindings, context);
    },
  };
}

export const logger = createLogger();
export const requestLogger = logger.child({ category: "request" });
export const healthLogger = logger.child({ category: "health" });

export const payloadLoggerConfig: NonNullable<Config["logger"]> = {
  options: {
    base: {
      environment: runtimeEnvironment,
      service: SERVICE_NAME,
    },
    formatters: {
      level: (label) => ({ level: label }),
    },
    level: minimumLogLevel,
    messageKey: "message",
    timestamp: () => `,"timestamp":"${new Date().toISOString()}"`,
  },
};

export function createRequestTimer() {
  const startedAt = performance.now();

  return {
    durationMs() {
      return Number((performance.now() - startedAt).toFixed(2));
    },
  };
}

export function registerUnhandledErrorHandlers(): void {
  if (typeof process === "undefined") {
    return;
  }

  const globalState = globalThis as typeof globalThis & {
    __editorialControlCenterUnhandledErrorHandlersRegistered?: boolean;
  };

  if (globalState.__editorialControlCenterUnhandledErrorHandlersRegistered) {
    return;
  }

  globalState.__editorialControlCenterUnhandledErrorHandlersRegistered = true;

  process.on("uncaughtExceptionMonitor", (error, origin) => {
    logger.error("Unhandled exception", {
      category: "process",
      error,
      origin,
    });
  });

  process.on("unhandledRejection", (reason) => {
    logger.error("Unhandled promise rejection", {
      category: "process",
      error: reason,
    });
  });
}
