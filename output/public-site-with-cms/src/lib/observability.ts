const LOG_LEVELS = {
  debug: 10,
  info: 20,
  warn: 30,
  error: 40,
} as const;

const DEFAULT_LOG_LEVEL = process.env.NODE_ENV === "development" ? "debug" : "info";

type LoggerBindings = Record<string, unknown>;
type GlobalObservabilityState = {
  processHandlersRegistered: boolean;
};

export const REQUEST_ID_HEADER = "x-request-id";

export type LogLevel = keyof typeof LOG_LEVELS;
export type StructuredLogger = {
  debug: (event: string, details?: LoggerBindings) => void;
  info: (event: string, details?: LoggerBindings) => void;
  warn: (event: string, details?: LoggerBindings) => void;
  error: (event: string, details?: LoggerBindings) => void;
};

type CreateLoggerOptions = {
  bindings?: LoggerBindings;
  scope?: string;
  service: string;
};

type CaptureErrorOptions = {
  details?: LoggerBindings;
  error: unknown;
  event: string;
  scope?: string;
  service: string;
};

type ObservedRouteOptions<TContext> = {
  handler: (request: Request, context: TContext) => Response | Promise<Response>;
  rethrowErrors?: boolean;
  route: string;
  service: string;
};

type ProcessErrorHandlerOptions = {
  exitOnUncaughtException?: boolean;
  scope?: string;
  service: string;
};

const parseLogLevel = (value: string | undefined): LogLevel | null => {
  if (!value) {
    return null;
  }

  const normalizedValue = value.toLowerCase();

  return normalizedValue in LOG_LEVELS ? (normalizedValue as LogLevel) : null;
};

const getGlobalObservabilityState = (): GlobalObservabilityState => {
  const globalScope = globalThis as typeof globalThis & {
    __publicSiteWithCmsObservability?: GlobalObservabilityState;
  };

  if (!globalScope.__publicSiteWithCmsObservability) {
    globalScope.__publicSiteWithCmsObservability = {
      processHandlersRegistered: false,
    };
  }

  return globalScope.__publicSiteWithCmsObservability;
};

const getCurrentLogLevel = (): LogLevel =>
  parseLogLevel(process.env.LOG_LEVEL) ?? DEFAULT_LOG_LEVEL;

const safeJsonStringify = (value: unknown): string => {
  const seen = new WeakSet<object>();

  return JSON.stringify(value, (_key, currentValue: unknown) => {
    if (currentValue instanceof Error) {
      return serializeError(currentValue);
    }

    if (typeof currentValue === "bigint") {
      return currentValue.toString();
    }

    if (typeof currentValue === "object" && currentValue !== null) {
      if (seen.has(currentValue)) {
        return "[Circular]";
      }

      seen.add(currentValue);
    }

    return currentValue;
  });
};

const shouldLog = (level: LogLevel): boolean =>
  LOG_LEVELS[level] >= LOG_LEVELS[getCurrentLogLevel()];

const writeLog = (
  level: LogLevel,
  event: string,
  context: LoggerBindings,
): void => {
  if (!shouldLog(level)) {
    return;
  }

  const payload = {
    timestamp: new Date().toISOString(),
    level,
    event,
    environment: process.env.NODE_ENV ?? "development",
    ...context,
  };

  const method =
    level === "debug"
      ? "debug"
      : level === "info"
        ? "info"
        : level === "warn"
          ? "warn"
          : "error";

  console[method](safeJsonStringify(payload));
};

const getRequestPath = (request: Request): string => {
  try {
    return new URL(request.url).pathname;
  } catch {
    return request.url;
  }
};

const getLogLevelForStatus = (status: number): "error" | "info" | "warn" => {
  if (status >= 500) {
    return "error";
  }

  if (status >= 400) {
    return "warn";
  }

  return "info";
};

const withRequestId = (response: Response, requestId: string): Response => {
  const headers = new Headers(response.headers);

  headers.set(REQUEST_ID_HEADER, requestId);

  return new Response(response.body, {
    headers,
    status: response.status,
    statusText: response.statusText,
  });
};

export const getConfiguredLogLevel = (): LogLevel => getCurrentLogLevel();

export const createLogger = ({
  bindings = {},
  scope,
  service,
}: CreateLoggerOptions): StructuredLogger => {
  const baseContext: LoggerBindings = {
    service,
    ...bindings,
  };

  if (scope) {
    baseContext.scope = scope;
  }

  return {
    debug: (event, details = {}) => {
      writeLog("debug", event, {
        ...baseContext,
        ...details,
      });
    },
    info: (event, details = {}) => {
      writeLog("info", event, {
        ...baseContext,
        ...details,
      });
    },
    warn: (event, details = {}) => {
      writeLog("warn", event, {
        ...baseContext,
        ...details,
      });
    },
    error: (event, details = {}) => {
      writeLog("error", event, {
        ...baseContext,
        ...details,
      });
    },
  };
};

export const serializeError = (error: unknown): Record<string, unknown> => {
  if (error instanceof Error) {
    return {
      cause: error.cause ? serializeError(error.cause) : undefined,
      message: error.message,
      name: error.name,
      stack: error.stack,
    };
  }

  return {
    message: String(error),
  };
};

export const captureError = ({
  details = {},
  error,
  event,
  scope,
  service,
}: CaptureErrorOptions): string => {
  const errorId = crypto.randomUUID();

  createLogger({
    scope,
    service,
  }).error(event, {
    ...details,
    error: serializeError(error),
    errorId,
  });

  return errorId;
};

export const withObservedRoute = <TContext = unknown>({
  handler,
  rethrowErrors = false,
  route,
  service,
}: ObservedRouteOptions<TContext>) => {
  const logger = createLogger({
    scope: "http",
    service,
  });

  return async (request: Request, context: TContext): Promise<Response> => {
    const startedAt = Date.now();
    const requestId =
      request.headers.get(REQUEST_ID_HEADER) ?? crypto.randomUUID();
    const path = getRequestPath(request);

    try {
      const response = await handler(request, context);
      const durationMs = Date.now() - startedAt;
      const level = getLogLevelForStatus(response.status);

      logger[level]("request-completed", {
        durationMs,
        method: request.method,
        path,
        requestId,
        route,
        status: response.status,
      });

      return withRequestId(response, requestId);
    } catch (error) {
      const errorId = captureError({
        details: {
          durationMs: Date.now() - startedAt,
          method: request.method,
          path,
          requestId,
          route,
        },
        error,
        event: "request-failed",
        scope: "http",
        service,
      });

      if (rethrowErrors) {
        throw error;
      }

      return Response.json(
        {
          error: "Internal Server Error",
          errorId,
          requestId,
        },
        {
          headers: {
            "Cache-Control": "no-store",
            [REQUEST_ID_HEADER]: requestId,
          },
          status: 500,
        },
      );
    }
  };
};

export const registerProcessErrorHandlers = ({
  exitOnUncaughtException = true,
  scope,
  service,
}: ProcessErrorHandlerOptions): void => {
  const state = getGlobalObservabilityState();

  if (state.processHandlersRegistered) {
    return;
  }

  state.processHandlersRegistered = true;

  process.on("unhandledRejection", (reason) => {
    captureError({
      error: reason,
      event: "unhandled-rejection",
      scope,
      service,
    });
  });

  process.on("uncaughtException", (error) => {
    const errorId = captureError({
      error,
      event: "uncaught-exception",
      scope,
      service,
    });

    if (!exitOnUncaughtException) {
      return;
    }

    createLogger({
      scope,
      service,
    }).error("process-exiting", {
      errorId,
      reason: "uncaught-exception",
    });

    setImmediate(() => {
      process.exit(1);
    });
  });
};
