import {
  Router,
  type ErrorRequestHandler,
  type Request,
  type RequestHandler,
  type Response,
} from "express";

import { requireAuth } from "../lib/auth";
import { createLogger } from "../lib/logger";
import {
  createNotification,
  getNotificationInbox,
  getNotificationPreferences,
  NotificationNotFoundError,
  NotificationValidationError,
  updateNotificationPreferences,
  updateNotificationReadState,
} from "../lib/notifications";

const DEFAULT_NOTIFICATION_LIMIT = 25;
const MAX_NOTIFICATION_LIMIT = 100;

const notificationsLogger = createLogger({
  component: "notifications-router",
  service: "todo-app-api",
});

function asyncHandler(
  handler: (request: Request, response: Response) => Promise<void>,
): RequestHandler {
  return (request, response, next) => {
    void handler(request, response).catch(next);
  };
}

function getNotificationLimit(request: Request): number {
  const limit = request.query.limit;

  if (limit === undefined) {
    return DEFAULT_NOTIFICATION_LIMIT;
  }

  const value = Array.isArray(limit) ? limit[0] : limit;
  const parsedValue = Number.parseInt(`${value}`, 10);

  if (
    !Number.isInteger(parsedValue) ||
    parsedValue < 1 ||
    parsedValue > MAX_NOTIFICATION_LIMIT
  ) {
    throw new NotificationValidationError(
      `limit must be an integer between 1 and ${MAX_NOTIFICATION_LIMIT}.`,
    );
  }

  return parsedValue;
}

const listNotificationsHandler = asyncHandler(async (request, response) => {
  const notificationInbox = await getNotificationInbox(
    request.auth!.user.id,
    getNotificationLimit(request),
  );

  response.status(200).json(notificationInbox);
});

const updatePreferencesHandler = asyncHandler(async (request, response) => {
  const preferences = await updateNotificationPreferences(
    request.auth!.user.id,
    request.body,
  );

  response.status(200).json(preferences);
});

const updateReadStateHandler = asyncHandler(async (request, response) => {
  const notification = await updateNotificationReadState(
    request.auth!.user.id,
    request.params.id,
    request.body,
  );

  response.status(200).json(notification);
});

const triggerNotificationHandler = asyncHandler(async (request, response) => {
  const user = request.auth!.user;
  const notification = await createNotification(user.id, {
    eventKey:
      typeof request.body?.eventKey === "string"
        ? request.body.eventKey
        : "manual.trigger",
    type: typeof request.body?.type === "string" ? request.body.type : "system",
    priority:
      typeof request.body?.priority === "string"
        ? request.body.priority
        : "high",
    title:
      typeof request.body?.title === "string"
        ? request.body.title
        : "Notification triggered",
    body:
      typeof request.body?.body === "string"
        ? request.body.body
        : `A notification was created for ${user.email}.`,
    metadata:
      typeof request.body?.metadata === "object" &&
      request.body.metadata !== null &&
      !Array.isArray(request.body.metadata)
        ? request.body.metadata
        : {
            source: "manual-trigger",
          },
  });

  const preferences = await getNotificationPreferences(user.id);

  response.status(notification ? 201 : 202).json({
    delivered: Boolean(notification),
    message: notification
      ? "Notification created."
      : "Notification skipped because current preferences filtered it out.",
    notification,
    preferences,
  });
});

const notificationsErrorHandler: ErrorRequestHandler = (
  error,
  _request,
  response,
) => {
  if (error instanceof NotificationValidationError) {
    response.status(400).json({
      error: error.name,
      message: error.message,
    });
    return;
  }

  if (error instanceof NotificationNotFoundError) {
    response.status(404).json({
      error: error.name,
      message: error.message,
    });
    return;
  }

  notificationsLogger.error("Unexpected notifications API error", {
    error,
  });
  response.status(500).json({
    error: "InternalServerError",
    message: "Unexpected error while handling notifications request.",
  });
};

const notificationsRouter = Router();

notificationsRouter.use(requireAuth);

notificationsRouter.get("/", listNotificationsHandler);
notificationsRouter.put("/preferences", updatePreferencesHandler);
notificationsRouter.patch("/:id", updateReadStateHandler);
notificationsRouter.post("/trigger", triggerNotificationHandler);

notificationsRouter.use(notificationsErrorHandler);

export { notificationsRouter };
