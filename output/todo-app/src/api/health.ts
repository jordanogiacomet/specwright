import { Router, type RequestHandler } from "express";

import { getHealthStatusCode, getServiceHealth } from "../lib/health";

const healthHandler: RequestHandler = async (_request, response) => {
  const { payload } = await getServiceHealth("todo-app-api");

  response.status(getHealthStatusCode(payload)).json(payload);
};

const healthRouter = Router();

healthRouter.get("/health", healthHandler);

export { healthHandler, healthRouter };
