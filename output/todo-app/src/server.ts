import "dotenv/config";

import { createServer as createHttpServer, type Server } from "node:http";

import cors from "cors";
import express, {
  type ErrorRequestHandler,
  type RequestHandler,
} from "express";
import helmet from "helmet";

import { authRouter } from "./api/auth";
import { contentRouter } from "./api/content";
import { healthRouter } from "./api/health";
import { notificationsRouter } from "./api/notifications";
import { reportsRouter } from "./api/reports";
import { todosRouter } from "./api/todos";
import { closeDatabasePool, verifyDatabaseConnection } from "./lib/db";
import { createLogger, registerProcessErrorHandlers } from "./lib/logger";

const DEFAULT_API_PORT = 3001;
const API_SERVICE_NAME = "todo-app-api";

const apiLogger = createLogger({
  service: API_SERVICE_NAME,
});
const lifecycleLogger = apiLogger.child({
  component: "lifecycle",
});
const requestLogger = apiLogger.child({
  component: "http",
});

function getDurationInMilliseconds(startedAt: bigint): number {
  return Math.round((Number(process.hrtime.bigint() - startedAt) / 1_000_000) * 100) / 100;
}

function getRequestLogLevel(statusCode: number): "info" | "warn" | "error" {
  if (statusCode >= 500) {
    return "error";
  }

  if (statusCode >= 400) {
    return "warn";
  }

  return "info";
}

function getApiPort(): number {
  const portValue =
    process.env.API_PORT ?? process.env.PORT ?? `${DEFAULT_API_PORT}`;
  const port = Number.parseInt(portValue, 10);

  if (Number.isNaN(port) || port < 1) {
    throw new Error("API_PORT must be a positive integer.");
  }

  return port;
}

function getAllowedOrigins(): string[] {
  const originValues = [
    process.env.NEXT_PUBLIC_APP_URL?.trim(),
    process.env.API_BASE_URL?.trim(),
  ].filter((value): value is string => Boolean(value));

  return [...new Set(originValues)];
}

const requestLoggingMiddleware: RequestHandler = (request, response, next) => {
  const startedAt = process.hrtime.bigint();
  const path = request.originalUrl || request.url;

  requestLogger.debug("Request started", {
    event: "request.started",
    method: request.method,
    path,
  });

  response.on("finish", () => {
    const logLevel = getRequestLogLevel(response.statusCode);
    const logContext = {
      durationMs: getDurationInMilliseconds(startedAt),
      event: "request.completed",
      method: request.method,
      path,
      statusCode: response.statusCode,
    };

    requestLogger[logLevel]("Request completed", logContext);
  });

  next();
};

const unhandledRequestErrorHandler: ErrorRequestHandler = (
  error,
  request,
  response,
  next,
) => {
  requestLogger.error("Unhandled API request error", {
    error,
    event: "request.unhandled_error",
    method: request.method,
    path: request.originalUrl || request.url,
  });

  if (response.headersSent) {
    next(error);
    return;
  }

  response.status(500).json({
    error: "InternalServerError",
    message: "Unexpected error while handling API request.",
  });
};

export function createServer() {
  const app = express();
  const allowedOrigins = getAllowedOrigins();

  app.disable("x-powered-by");
  app.use(helmet());
  app.use(requestLoggingMiddleware);
  app.use(
    cors({
      credentials: true,
      origin(origin, callback) {
        if (
          !origin ||
          allowedOrigins.length === 0 ||
          allowedOrigins.includes(origin)
        ) {
          callback(null, true);
          return;
        }

        callback(new Error("Origin not allowed by CORS."));
      },
    }),
  );
  app.use(express.json());

  app.use("/api", healthRouter);
  app.use("/api/auth", authRouter);
  app.use("/api/content", contentRouter);
  app.use("/api/notifications", notificationsRouter);
  app.use("/api/reports", reportsRouter);
  app.use("/api/todos", todosRouter);
  app.use(unhandledRequestErrorHandler);

  return app;
}

async function listen(server: Server, port: number): Promise<void> {
  await new Promise<void>((resolve, reject) => {
    server.once("listening", resolve);
    server.once("error", reject);
    server.listen(port);
  });
}

async function closeServer(server: Server): Promise<void> {
  await new Promise<void>((resolve, reject) => {
    server.close((error) => {
      if (error) {
        reject(error);
        return;
      }

      resolve();
    });
  });
}

export async function startServer(): Promise<Server> {
  const port = getApiPort();
  const app = createServer();
  const server = createHttpServer(app);

  registerProcessErrorHandlers(
    API_SERVICE_NAME,
    apiLogger.child({
      component: "process",
    }),
  );

  try {
    await verifyDatabaseConnection();
    lifecycleLogger.info("Database connection verified", {
      event: "database.verified",
    });
  } catch (error) {
    lifecycleLogger.warn("Database connection unavailable during startup", {
      error,
      event: "database.unavailable",
    });
  }

  await listen(server, port);

  lifecycleLogger.info("API server listening", {
    event: "server.started",
    port,
  });

  let isShuttingDown = false;

  const shutdown = async (signal: NodeJS.Signals) => {
    if (isShuttingDown) {
      return;
    }

    isShuttingDown = true;
    lifecycleLogger.info("API server shutdown started", {
      event: "server.shutdown.started",
      signal,
    });

    try {
      await closeServer(server);
      await closeDatabasePool();
      lifecycleLogger.info("API server shutdown completed", {
        event: "server.shutdown.completed",
        signal,
      });
    } catch (error) {
      lifecycleLogger.error("Failed to shut down API server cleanly", {
        error,
        event: "server.shutdown.failed",
        signal,
      });
      process.exitCode = 1;
    } finally {
      process.exit();
    }
  };

  process.once("SIGINT", () => {
    void shutdown("SIGINT");
  });

  process.once("SIGTERM", () => {
    void shutdown("SIGTERM");
  });

  return server;
}

void startServer().catch(async (error) => {
  lifecycleLogger.error("Failed to start API server", {
    error,
    event: "server.start.failed",
  });

  try {
    await closeDatabasePool();
  } finally {
    process.exit(1);
  }
});
