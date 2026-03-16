import { login, logout } from "@payloadcms/next/auth";
import { headers as getHeaders } from "next/headers";
import { getPayload } from "payload";

import config from "@payload-config";
import { getUserRole, type UserRole } from "./permissions";

const authCollection = "users";
const configPromise = Promise.resolve(config);

type AuthCredentials = {
  email: string;
  password: string;
};

type PayloadErrorShape = {
  data?: {
    errors?: Array<{
      message?: unknown;
    }>;
  };
  message?: unknown;
};

export type SessionUser = {
  collection: string;
  email?: string;
  id: number | string;
  role: UserRole;
};

function normalizeEmail(email: string): string {
  return email.trim().toLowerCase();
}

async function getPayloadClient() {
  return getPayload({
    config: configPromise,
    cron: true,
  });
}

export function getAuthErrorMessage(error: unknown): string {
  const payloadError = error as PayloadErrorShape;
  const firstError = payloadError.data?.errors?.[0];

  if (typeof firstError?.message === "string" && firstError.message.trim()) {
    return firstError.message;
  }

  if (typeof payloadError.message === "string" && payloadError.message.trim()) {
    return payloadError.message;
  }

  return "Authentication failed.";
}

export async function registerUser({ email, password }: AuthCredentials) {
  const payload = await getPayloadClient();

  return payload.create({
    collection: authCollection,
    data: {
      email: normalizeEmail(email),
      password,
    },
    depth: 0,
    overrideAccess: false,
  });
}

export async function loginUser({ email, password }: AuthCredentials) {
  return login({
    collection: authCollection,
    config: configPromise,
    email: normalizeEmail(email),
    password,
  });
}

export async function logoutUser() {
  return logout({
    config: configPromise,
  });
}

export async function getSessionUser(
  requestHeaders?: Request["headers"],
): Promise<SessionUser | null> {
  const payload = await getPayloadClient();
  const headers = requestHeaders ?? (await getHeaders());
  const { user } = await payload.auth({ headers });

  if (!user || typeof user.id === "undefined") {
    return null;
  }

  const sessionUser = user as {
    collection?: unknown;
    email?: unknown;
    id: number | string;
    role?: unknown;
  };

  if (typeof sessionUser.collection !== "string") {
    return null;
  }

  return {
    collection: sessionUser.collection,
    email: typeof sessionUser.email === "string" ? sessionUser.email : undefined,
    id: sessionUser.id,
    role: getUserRole(sessionUser),
  };
}
