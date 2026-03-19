import {
  createHmac,
  randomBytes,
  randomUUID,
  scrypt as scryptCallback,
  timingSafeEqual,
} from "node:crypto";

import type { Request, RequestHandler, Response } from "express";

import { query } from "./db";

const SESSION_COOKIE_NAME = "todo_app_session";
const DEFAULT_SESSION_DURATION_MS = 7 * 24 * 60 * 60 * 1000;
const PASSWORD_HASH_KEY_LENGTH = 64;
const EMAIL_MAX_LENGTH = 320;
const PASSWORD_MIN_LENGTH = 8;
const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

type UserRow = {
  id: string;
  email: string;
  password_hash: string;
  created_at: Date | string;
};

type SessionRow = {
  session_id: string;
  session_user_id: string;
  session_created_at: Date | string;
  session_expires_at: Date | string;
  user_id: string;
  user_email: string;
  user_created_at: Date | string;
};

type SessionTokenPayload = {
  sub: string;
  sid: string;
  iat: number;
  exp: number;
};

export type AuthUser = {
  id: string;
  email: string;
  createdAt: string;
};

export type AuthSession = {
  id: string;
  userId: string;
  createdAt: string;
  expiresAt: string;
  token: string;
};

export type AuthenticatedRequestContext = {
  user: AuthUser;
  session: AuthSession;
};

export type AuthResult = AuthenticatedRequestContext;

declare module "express-serve-static-core" {
  interface Request {
    auth?: AuthenticatedRequestContext;
  }
}

export class AuthValidationError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "AuthValidationError";
  }
}

export class AuthConflictError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "AuthConflictError";
  }
}

export class AuthUnauthorizedError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "AuthUnauthorizedError";
  }
}

type Credentials = {
  email: string;
  password: string;
};

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function getRequiredJwtSecret(): string {
  const value = process.env.JWT_SECRET?.trim();

  if (!value) {
    throw new Error("Missing required environment variable: JWT_SECRET");
  }

  return value;
}

function normalizeEmail(value: unknown): string {
  if (typeof value !== "string") {
    throw new AuthValidationError("email must be a string.");
  }

  const normalizedValue = value.trim().toLowerCase();

  if (!normalizedValue) {
    throw new AuthValidationError("email is required.");
  }

  if (normalizedValue.length > EMAIL_MAX_LENGTH) {
    throw new AuthValidationError(
      `email must be ${EMAIL_MAX_LENGTH} characters or fewer.`,
    );
  }

  if (!EMAIL_PATTERN.test(normalizedValue)) {
    throw new AuthValidationError("email must be a valid email address.");
  }

  return normalizedValue;
}

function normalizePassword(value: unknown): string {
  if (typeof value !== "string") {
    throw new AuthValidationError("password must be a string.");
  }

  if (value.trim().length < PASSWORD_MIN_LENGTH) {
    throw new AuthValidationError(
      `password must be at least ${PASSWORD_MIN_LENGTH} characters long.`,
    );
  }

  return value;
}

function normalizeCredentials(payload: unknown): Credentials {
  if (!isRecord(payload)) {
    throw new AuthValidationError(
      "Authentication payload must be a JSON object.",
    );
  }

  return {
    email: normalizeEmail(payload.email),
    password: normalizePassword(payload.password),
  };
}

function toIsoString(value: Date | string): string {
  return value instanceof Date
    ? value.toISOString()
    : new Date(value).toISOString();
}

function base64UrlEncode(value: string): string {
  return Buffer.from(value).toString("base64url");
}

function base64UrlDecode(value: string): string {
  return Buffer.from(value, "base64url").toString("utf8");
}

function signToken(data: string): string {
  return createHmac("sha256", getRequiredJwtSecret())
    .update(data)
    .digest("base64url");
}

function createSessionToken(payload: SessionTokenPayload): string {
  const encodedHeader = base64UrlEncode(
    JSON.stringify({
      alg: "HS256",
      typ: "JWT",
    }),
  );
  const encodedPayload = base64UrlEncode(JSON.stringify(payload));
  const signature = signToken(`${encodedHeader}.${encodedPayload}`);

  return `${encodedHeader}.${encodedPayload}.${signature}`;
}

function verifySessionToken(token: string): SessionTokenPayload | null {
  const [encodedHeader, encodedPayload, signature] = token.split(".");

  if (!encodedHeader || !encodedPayload || !signature) {
    return null;
  }

  const expectedSignature = signToken(`${encodedHeader}.${encodedPayload}`);
  const providedSignature = Buffer.from(signature);
  const computedSignature = Buffer.from(expectedSignature);

  if (
    providedSignature.length !== computedSignature.length ||
    !timingSafeEqual(providedSignature, computedSignature)
  ) {
    return null;
  }

  try {
    const header = JSON.parse(base64UrlDecode(encodedHeader)) as {
      alg?: string;
      typ?: string;
    };

    if (header.alg !== "HS256" || header.typ !== "JWT") {
      return null;
    }

    const payload = JSON.parse(
      base64UrlDecode(encodedPayload),
    ) as Partial<SessionTokenPayload>;

    if (
      typeof payload.sub !== "string" ||
      typeof payload.sid !== "string" ||
      typeof payload.iat !== "number" ||
      typeof payload.exp !== "number"
    ) {
      return null;
    }

    if (payload.exp <= Math.floor(Date.now() / 1000)) {
      return null;
    }

    return payload as SessionTokenPayload;
  } catch {
    return null;
  }
}

function getSessionDurationMs(): number {
  const configuredValue = process.env.AUTH_SESSION_DURATION_MS?.trim();

  if (!configuredValue) {
    return DEFAULT_SESSION_DURATION_MS;
  }

  const parsedValue = Number.parseInt(configuredValue, 10);

  if (!Number.isInteger(parsedValue) || parsedValue < 1) {
    throw new Error("AUTH_SESSION_DURATION_MS must be a positive integer.");
  }

  return parsedValue;
}

async function scrypt(password: string, salt: string): Promise<Buffer> {
  return new Promise<Buffer>((resolve, reject) => {
    scryptCallback(
      password,
      salt,
      PASSWORD_HASH_KEY_LENGTH,
      (error, derivedKey) => {
        if (error) {
          reject(error);
          return;
        }

        resolve(derivedKey);
      },
    );
  });
}

async function hashPassword(password: string): Promise<string> {
  const salt = randomBytes(16).toString("hex");
  const derivedKey = await scrypt(password, salt);

  return `scrypt:${salt}:${derivedKey.toString("hex")}`;
}

async function verifyPassword(
  password: string,
  passwordHash: string,
): Promise<boolean> {
  const [algorithm, salt, storedHash] = passwordHash.split(":");

  if (algorithm !== "scrypt" || !salt || !storedHash) {
    return false;
  }

  const derivedKey = await scrypt(password, salt);
  const storedBuffer = Buffer.from(storedHash, "hex");

  if (storedBuffer.length !== derivedKey.length) {
    return false;
  }

  return timingSafeEqual(derivedKey, storedBuffer);
}

function mapUserRow(
  row: Pick<UserRow, "id" | "email" | "created_at">,
): AuthUser {
  return {
    id: row.id,
    email: row.email,
    createdAt: toIsoString(row.created_at),
  };
}

function mapSessionRow(
  row: SessionRow,
  token: string,
): AuthenticatedRequestContext {
  return {
    user: {
      id: row.user_id,
      email: row.user_email,
      createdAt: toIsoString(row.user_created_at),
    },
    session: {
      id: row.session_id,
      userId: row.session_user_id,
      createdAt: toIsoString(row.session_created_at),
      expiresAt: toIsoString(row.session_expires_at),
      token,
    },
  };
}

function getCookieValue(request: Request, key: string): string | null {
  const cookieHeader = request.header("cookie");

  if (!cookieHeader) {
    return null;
  }

  for (const cookieEntry of cookieHeader.split(";")) {
    const [cookieName, ...cookieValueParts] = cookieEntry.trim().split("=");

    if (cookieName === key) {
      return decodeURIComponent(cookieValueParts.join("="));
    }
  }

  return null;
}

function getBearerToken(request: Request): string | null {
  const authorizationHeader = request.header("authorization");

  if (!authorizationHeader) {
    return null;
  }

  const [scheme, token] = authorizationHeader.split(" ");

  if (scheme !== "Bearer" || !token) {
    return null;
  }

  return token.trim();
}

function getRequestToken(request: Request): string | null {
  return (
    getBearerToken(request) ?? getCookieValue(request, SESSION_COOKIE_NAME)
  );
}

function setSessionCookie(response: Response, session: AuthSession): void {
  response.cookie(SESSION_COOKIE_NAME, session.token, {
    expires: new Date(session.expiresAt),
    httpOnly: true,
    sameSite: "lax",
    secure: process.env.NODE_ENV === "production",
    path: "/",
  });
}

export function clearSessionCookie(response: Response): void {
  response.clearCookie(SESSION_COOKIE_NAME, {
    httpOnly: true,
    sameSite: "lax",
    secure: process.env.NODE_ENV === "production",
    path: "/",
  });
}

export async function registerUser(payload: unknown): Promise<AuthUser> {
  const credentials = normalizeCredentials(payload);
  const passwordHash = await hashPassword(credentials.password);

  try {
    const result = await query<UserRow>(
      `
        INSERT INTO users (id, email, password_hash)
        VALUES ($1, $2, $3)
        RETURNING id, email, password_hash, created_at
      `,
      [randomUUID(), credentials.email, passwordHash],
    );

    return mapUserRow(result.rows[0]);
  } catch (error) {
    const code = (error as { code?: string }).code;

    if (code === "23505") {
      throw new AuthConflictError("An account with that email already exists.");
    }

    throw error;
  }
}

export async function authenticateUser(payload: unknown): Promise<AuthUser> {
  const credentials = normalizeCredentials(payload);
  const result = await query<UserRow>(
    `
      SELECT id, email, password_hash, created_at
      FROM users
      WHERE email = $1
      LIMIT 1
    `,
    [credentials.email],
  );
  const user = result.rows[0];

  if (
    !user ||
    !(await verifyPassword(credentials.password, user.password_hash))
  ) {
    throw new AuthUnauthorizedError("Invalid email or password.");
  }

  return mapUserRow(user);
}

export async function listUsers(): Promise<AuthUser[]> {
  const result = await query<Pick<UserRow, "id" | "email" | "created_at">>(
    `
      SELECT id, email, created_at
      FROM users
      ORDER BY email ASC, id ASC
    `,
  );

  return result.rows.map(mapUserRow);
}

export async function createUserSession(user: AuthUser): Promise<AuthResult> {
  const sessionId = randomUUID();
  const createdAt = new Date();
  const expiresAt = new Date(createdAt.getTime() + getSessionDurationMs());

  await query(
    `
      INSERT INTO auth_sessions (id, user_id, expires_at)
      VALUES ($1, $2, $3)
    `,
    [sessionId, user.id, expiresAt.toISOString()],
  );

  const token = createSessionToken({
    sub: user.id,
    sid: sessionId,
    iat: Math.floor(createdAt.getTime() / 1000),
    exp: Math.floor(expiresAt.getTime() / 1000),
  });

  return {
    user,
    session: {
      id: sessionId,
      userId: user.id,
      createdAt: createdAt.toISOString(),
      expiresAt: expiresAt.toISOString(),
      token,
    },
  };
}

export function applySessionToResponse(
  response: Response,
  authResult: AuthResult,
): AuthResult {
  setSessionCookie(response, authResult.session);
  return authResult;
}

async function getStoredSession(
  sessionId: string,
  token: string,
): Promise<AuthenticatedRequestContext | null> {
  const result = await query<SessionRow>(
    `
      SELECT
        auth_sessions.id AS session_id,
        auth_sessions.user_id AS session_user_id,
        auth_sessions.created_at AS session_created_at,
        auth_sessions.expires_at AS session_expires_at,
        users.id AS user_id,
        users.email AS user_email,
        users.created_at AS user_created_at
      FROM auth_sessions
      INNER JOIN users ON users.id = auth_sessions.user_id
      WHERE auth_sessions.id = $1
        AND auth_sessions.expires_at > CURRENT_TIMESTAMP
      LIMIT 1
    `,
    [sessionId],
  );
  const session = result.rows[0];

  if (!session) {
    return null;
  }

  return mapSessionRow(session, token);
}

export async function getAuthFromRequest(
  request: Request,
): Promise<AuthenticatedRequestContext | null> {
  const token = getRequestToken(request);

  if (!token) {
    return null;
  }

  const payload = verifySessionToken(token);

  if (!payload) {
    return null;
  }

  const authContext = await getStoredSession(payload.sid, token);

  if (!authContext || authContext.user.id !== payload.sub) {
    return null;
  }

  return authContext;
}

export async function invalidateSession(sessionId: string): Promise<void> {
  await query(
    `
      DELETE FROM auth_sessions
      WHERE id = $1
    `,
    [sessionId],
  );
}

export async function logoutRequest(
  request: Request,
  response: Response,
): Promise<void> {
  const token = getRequestToken(request);

  if (token) {
    const payload = verifySessionToken(token);

    if (payload) {
      await invalidateSession(payload.sid);
    }
  }

  clearSessionCookie(response);
}

export const requireAuth: RequestHandler = (request, response, next) => {
  void getAuthFromRequest(request)
    .then((authContext) => {
      if (!authContext) {
        response.status(401).json({
          error: "AuthUnauthorizedError",
          message: "Authentication is required.",
        });
        return;
      }

      request.auth = authContext;
      next();
    })
    .catch(next);
};
