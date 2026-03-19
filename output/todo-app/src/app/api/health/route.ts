import { NextResponse } from "next/server";

import { getHealthStatusCode, getServiceHealth } from "@/lib/health";
import { createLogger } from "@/lib/logger";

const healthRouteLogger = createLogger({
  component: "health-route",
  service: "todo-app-web",
});

export const dynamic = "force-dynamic";
export const runtime = "nodejs";

export async function GET(request: Request) {
  const startedAt = Date.now();
  const { databaseError, payload } = await getServiceHealth("todo-app-web");
  const status = getHealthStatusCode(payload);

  if (databaseError) {
    healthRouteLogger.warn("Health check request completed", {
      durationMs: Date.now() - startedAt,
      error: databaseError,
      event: "request.completed",
      method: "GET",
      path: new URL(request.url).pathname,
      statusCode: status,
    });
  } else {
    healthRouteLogger.info("Health check request completed", {
      durationMs: Date.now() - startedAt,
      event: "request.completed",
      method: "GET",
      path: new URL(request.url).pathname,
      statusCode: status,
    });
  }

  return NextResponse.json(payload, {
    status,
  });
}
