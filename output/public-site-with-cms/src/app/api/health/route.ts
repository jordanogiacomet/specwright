import { NextResponse } from "next/server";

import { getDatabaseConnectionString } from "@/lib/db";
import { getConfiguredLogLevel, withObservedRoute } from "@/lib/observability";

export const dynamic = "force-dynamic";
export const runtime = "nodejs";

const handleGet = async () => {
  const databaseURL = getDatabaseConnectionString({ optional: true });

  return NextResponse.json({
    adminURL: "/admin",
    apiURL: "/api",
    checks: {
      databaseConfigured: Boolean(databaseURL),
    },
    monitoring: {
      logFormat: "json",
      logLevel: getConfiguredLogLevel(),
      requestErrorTracking: true,
      requestIdHeader: "x-request-id",
      requestLogging: true,
    },
    service: "backend",
    status: "ok",
    timestamp: new Date().toISOString(),
    uptimeSeconds: Math.round(process.uptime()),
  }, {
    headers: {
      "Cache-Control": "no-store",
    },
  });
};

export const GET = withObservedRoute({
  handler: handleGet,
  route: "/api/health",
  service: "api",
});
