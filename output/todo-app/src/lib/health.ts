import { verifyDatabaseConnection } from "./db";

export type HealthPayload = {
  status: "ok" | "degraded";
  service: string;
  timestamp: string;
  database: {
    status: "up" | "down";
  };
};

export type ServiceHealth = {
  databaseError?: unknown;
  payload: HealthPayload;
};

export async function getServiceHealth(service: string): Promise<ServiceHealth> {
  const timestamp = new Date().toISOString();

  try {
    await verifyDatabaseConnection();

    return {
      payload: {
        status: "ok",
        service,
        timestamp,
        database: {
          status: "up",
        },
      },
    };
  } catch (error) {
    return {
      databaseError: error,
      payload: {
        status: "degraded",
        service,
        timestamp,
        database: {
          status: "down",
        },
      },
    };
  }
}

export function getHealthStatusCode(payload: HealthPayload): number {
  return payload.status === "ok" ? 200 : 503;
}
