import {
  Router,
  type ErrorRequestHandler,
  type Request,
  type RequestHandler,
  type Response,
} from "express";

import {
  applySessionToResponse,
  authenticateUser,
  AuthConflictError,
  AuthUnauthorizedError,
  AuthValidationError,
  getAuthFromRequest,
  logoutRequest,
  listUsers,
  registerUser,
  requireAuth,
  createUserSession,
} from "../lib/auth";
import { createLogger } from "../lib/logger";

const authLogger = createLogger({
  component: "auth-router",
  service: "todo-app-api",
});

function asyncHandler(
  handler: (request: Request, response: Response) => Promise<void>,
): RequestHandler {
  return (request, response, next) => {
    void handler(request, response).catch(next);
  };
}

const registerHandler = asyncHandler(async (request, response) => {
  const user = await registerUser(request.body);
  const authResult = applySessionToResponse(
    response,
    await createUserSession(user),
  );

  response.status(201).json(authResult);
});

const loginHandler = asyncHandler(async (request, response) => {
  const user = await authenticateUser(request.body);
  const authResult = applySessionToResponse(
    response,
    await createUserSession(user),
  );

  response.status(200).json(authResult);
});

const logoutHandler = asyncHandler(async (request, response) => {
  await logoutRequest(request, response);
  response.status(200).json({
    success: true,
  });
});

const usersHandler = asyncHandler(async (_request, response) => {
  const users = await listUsers();

  response.status(200).json({
    items: users,
  });
});

const sessionHandler: RequestHandler = asyncHandler(
  async (request, response) => {
    const authContext = request.auth ?? (await getAuthFromRequest(request));

    if (!authContext) {
      throw new AuthUnauthorizedError("Authentication is required.");
    }

    response.status(200).json({
      authenticated: true,
      user: authContext.user,
      session: authContext.session,
    });
  },
);

const authErrorHandler: ErrorRequestHandler = (
  error,
  _request,
  response,
  next,
) => {
  void next;

  if (error instanceof AuthValidationError) {
    response.status(400).json({
      error: error.name,
      message: error.message,
    });
    return;
  }

  if (error instanceof AuthConflictError) {
    response.status(409).json({
      error: error.name,
      message: error.message,
    });
    return;
  }

  if (error instanceof AuthUnauthorizedError) {
    response.status(401).json({
      error: error.name,
      message: error.message,
    });
    return;
  }

  authLogger.error("Unexpected auth API error", {
    error,
  });
  response.status(500).json({
    error: "InternalServerError",
    message: "Unexpected error while handling authentication request.",
  });
};

const authRouter = Router();

authRouter.post("/register", registerHandler);
authRouter.post("/login", loginHandler);
authRouter.post("/logout", logoutHandler);
authRouter.get("/users", requireAuth, usersHandler);
authRouter.get("/session", requireAuth, sessionHandler);

authRouter.use(authErrorHandler);

export { authRouter };
