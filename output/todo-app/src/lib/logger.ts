type LogLevel = "debug" | "info" | "warn" | "error";

type SerializableLogValue =
  | string
  | number
  | boolean
  | null
  | SerializableLogValue[]
  | {
      [key: string]: SerializableLogValue;
    };

type LogContext = Record<string, unknown>;

type ProcessErrorEvent = "process.unhandled_rejection" | "process.uncaught_exception";

const LOG_LEVEL_VALUES: Record<LogLevel, number> = {
  debug: 10,
  info: 20,
  warn: 30,
  error: 40,
};

const DEFAULT_LOG_LEVEL: LogLevel = "info";

const registeredProcessHandlers = new Set<string>();

function isPlainObject(
  value: unknown,
): value is Record<string, unknown> {
  return (
    typeof value === "object" &&
    value !== null &&
    Object.getPrototypeOf(value) === Object.prototype
  );
}

function getConfiguredLogLevel(): LogLevel {
  const value = process.env.LOG_LEVEL?.trim().toLowerCase();

  if (
    value === "debug" ||
    value === "info" ||
    value === "warn" ||
    value === "error"
  ) {
    return value;
  }

  return DEFAULT_LOG_LEVEL;
}

function serializeError(error: unknown): SerializableLogValue {
  if (error instanceof Error) {
    return {
      message: error.message,
      name: error.name,
      stack: error.stack ?? null,
    };
  }

  return {
    message: "Non-Error value thrown or rejected.",
    name: "NonError",
    value: serializeValue(error),
  };
}

function serializeValue(value: unknown): SerializableLogValue {
  if (
    value === null ||
    typeof value === "string" ||
    typeof value === "boolean"
  ) {
    return value;
  }

  if (typeof value === "number") {
    return Number.isFinite(value) ? value : String(value);
  }

  if (typeof value === "bigint") {
    return value.toString();
  }

  if (value instanceof Date) {
    return value.toISOString();
  }

  if (value instanceof Error) {
    return serializeError(value);
  }

  if (Array.isArray(value)) {
    return value.map((item) => serializeValue(item));
  }

  if (isPlainObject(value)) {
    const serializedEntries = Object.entries(value).flatMap(([key, entry]) => {
      if (entry === undefined) {
        return [];
      }

      return [[key, serializeValue(entry)]];
    });

    return Object.fromEntries(serializedEntries);
  }

  if (value === undefined) {
    return null;
  }

  return String(value);
}

function serializeContext(context: LogContext): Record<string, SerializableLogValue> {
  return Object.fromEntries(
    Object.entries(context).flatMap(([key, value]) => {
      if (value === undefined) {
        return [];
      }

      return [[key, serializeValue(value)]];
    }),
  );
}

function shouldLog(level: LogLevel): boolean {
  return LOG_LEVEL_VALUES[level] >= LOG_LEVEL_VALUES[getConfiguredLogLevel()];
}

function getConsoleMethod(level: LogLevel): keyof Pick<
  Console,
  "debug" | "info" | "warn" | "error"
> {
  return level;
}

function writeLog(
  level: LogLevel,
  bindings: LogContext,
  message: string,
  context: LogContext = {},
): void {
  if (!shouldLog(level)) {
    return;
  }

  const entry = {
    timestamp: new Date().toISOString(),
    level,
    message,
    ...serializeContext(bindings),
    ...serializeContext(context),
  };

  console[getConsoleMethod(level)](JSON.stringify(entry));
}

export interface Logger {
  child(bindings: LogContext): Logger;
  debug(message: string, context?: LogContext): void;
  info(message: string, context?: LogContext): void;
  warn(message: string, context?: LogContext): void;
  error(message: string, context?: LogContext): void;
}

export function createLogger(bindings: LogContext = {}): Logger {
  return {
    child(childBindings) {
      return createLogger({
        ...bindings,
        ...childBindings,
      });
    },

    debug(message, context) {
      writeLog("debug", bindings, message, context);
    },

    info(message, context) {
      writeLog("info", bindings, message, context);
    },

    warn(message, context) {
      writeLog("warn", bindings, message, context);
    },

    error(message, context) {
      writeLog("error", bindings, message, context);
    },
  };
}

function logProcessError(
  logger: Logger,
  event: ProcessErrorEvent,
  error: unknown,
): void {
  logger.error("Unhandled process error", {
    error,
    event,
  });
}

export function registerProcessErrorHandlers(
  registrationKey: string,
  logger: Logger,
): void {
  if (registeredProcessHandlers.has(registrationKey)) {
    return;
  }

  registeredProcessHandlers.add(registrationKey);

  process.on("unhandledRejection", (reason) => {
    logProcessError(logger, "process.unhandled_rejection", reason);
  });

  process.on("uncaughtExceptionMonitor", (error) => {
    logProcessError(logger, "process.uncaught_exception", error);
  });
}
