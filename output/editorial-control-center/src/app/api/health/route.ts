import { NextResponse } from "next/server";

import { verifyDatabaseConnection } from "../../../lib/db";
import {
  SERVICE_NAME,
  createRequestTimer,
  healthLogger,
} from "../../../lib/logger";

export const dynamic = "force-dynamic";
export const runtime = "nodejs";

export async function GET() {
  const requestTimer = createRequestTimer();
  const requestPath = "/api/health";

  healthLogger.debug("Health check requested", {
    method: "GET",
    path: requestPath,
    visibility: "public",
  });

  try {
    const database = await verifyDatabaseConnection();
    const response = {
      database,
      ok: true,
      service: SERVICE_NAME,
      status: "ok",
      timestamp: new Date().toISOString(),
      uptimeSeconds: Number(process.uptime().toFixed(2)),
    };

    healthLogger.info("Health check completed", {
      databaseOk: true,
      method: "GET",
      path: requestPath,
      responseTimeMs: requestTimer.durationMs(),
      statusCode: 200,
      visibility: "public",
    });

    return NextResponse.json(response);
  } catch (error) {
    healthLogger.warn("Health check degraded", {
      databaseOk: false,
      error,
      method: "GET",
      path: requestPath,
      responseTimeMs: requestTimer.durationMs(),
      statusCode: 503,
      visibility: "public",
    });

    return NextResponse.json(
      {
        database: {
          ok: false,
        },
        ok: false,
        service: SERVICE_NAME,
        status: "degraded",
        timestamp: new Date().toISOString(),
        uptimeSeconds: Number(process.uptime().toFixed(2)),
      },
      { status: 503 },
    );
  }
}
