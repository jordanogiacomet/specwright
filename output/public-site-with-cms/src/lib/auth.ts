import "server-only";

import config from "@payload-config";
import { cookies, headers } from "next/headers";
import { redirect } from "next/navigation";
import {
  createPayloadRequest,
  generateExpiredPayloadCookie,
  generatePayloadCookie,
  getPayload,
  logoutOperation,
} from "payload";

import type { User } from "@/payload-types";
import { DEFAULT_USER_ROLE } from "@/lib/permissions";

const LOGIN_PATH = "/login";
const USERS_COLLECTION = "users" as const;

export type AuthenticatedUser = Pick<User, "email" | "id" | "role">;

type AuthFormState = {
  email: string;
  password: string;
};

type CookieSameSite = "lax" | "none" | "strict";

const getSearchParamValue = (value: FormDataEntryValue | null): string =>
  typeof value === "string" ? value.trim() : "";

const normalizeEmail = (email: string): string => email.trim().toLowerCase();

const buildLoginRedirect = (params: Record<string, string>): string => {
  const searchParams = new URLSearchParams();

  for (const [key, value] of Object.entries(params)) {
    if (value) {
      searchParams.set(key, value);
    }
  }

  const queryString = searchParams.toString();

  return queryString ? `${LOGIN_PATH}?${queryString}` : LOGIN_PATH;
};

const getCurrentOrigin = (requestHeaders: Headers): string => {
  const forwardedHost = requestHeaders.get("x-forwarded-host");
  const host = forwardedHost ?? requestHeaders.get("host") ?? "localhost:3000";
  const protocol =
    requestHeaders.get("x-forwarded-proto") ??
    (host.startsWith("localhost") || host.startsWith("127.0.0.1") ? "http" : "https");

  return `${protocol}://${host}`;
};

const getCurrentRequestHeaders = async (): Promise<Headers> => {
  const currentHeaders = await headers();
  const requestHeaders = new Headers();

  for (const [key, value] of currentHeaders.entries()) {
    requestHeaders.set(key, value);
  }

  return requestHeaders;
};

const createSyntheticRequest = async (pathname: string): Promise<Request> => {
  const requestHeaders = await getCurrentRequestHeaders();
  const origin = getCurrentOrigin(requestHeaders);

  return new Request(new URL(pathname, origin), {
    headers: requestHeaders,
    method: "GET",
  });
};

const createServerPayloadRequest = async (pathname: string, request?: Request) =>
  createPayloadRequest({
    canSetHeaders: false,
    config,
    request: request ?? (await createSyntheticRequest(pathname)),
  });

const getUsersCollectionAuth = async () => {
  const payload = await getPayload({
    config,
  });
  const usersCollection = payload.collections[USERS_COLLECTION];

  if (!usersCollection?.config.auth) {
    throw new Error("Users collection auth is not configured.");
  }

  return {
    authConfig: usersCollection.config.auth,
    payload,
    usersCollection,
  };
};

const applyCookie = async (
  cookie: {
    domain?: string;
    expires?: string;
    httpOnly?: boolean;
    maxAge?: number;
    name: string;
    path?: string;
    sameSite?: "Lax" | "None" | "Strict";
    secure?: boolean;
    value: string | undefined;
  },
): Promise<void> => {
  const cookieStore = await cookies();

  cookieStore.set({
    domain: cookie.domain,
    expires: cookie.expires ? new Date(cookie.expires) : undefined,
    httpOnly: cookie.httpOnly,
    maxAge: cookie.maxAge,
    name: cookie.name,
    path: cookie.path,
    sameSite: cookie.sameSite?.toLowerCase() as CookieSameSite | undefined,
    secure: cookie.secure,
    value: cookie.value ?? "",
  });
};

const persistLoginCookie = async (token: string): Promise<void> => {
  const { authConfig, payload } = await getUsersCollectionAuth();

  const cookie = generatePayloadCookie({
    collectionAuthConfig: authConfig,
    cookiePrefix: payload.config.cookiePrefix,
    returnCookieAsObject: true,
    token,
  });

  await applyCookie(cookie);
};

const expireLoginCookie = async (): Promise<void> => {
  const { authConfig, payload } = await getUsersCollectionAuth();

  const cookie = generateExpiredPayloadCookie({
    collectionAuthConfig: authConfig,
    cookiePrefix: payload.config.cookiePrefix,
    returnCookieAsObject: true,
  });

  await applyCookie(cookie);
};

const readAuthFormState = (formData: FormData): AuthFormState => ({
  email: normalizeEmail(getSearchParamValue(formData.get("email"))),
  password: getSearchParamValue(formData.get("password")),
});

const resolveAuthenticatedUser = async (
  request: Awaited<ReturnType<typeof createServerPayloadRequest>>,
): Promise<AuthenticatedUser | null> => {
  if (!request.user || request.user.collection !== USERS_COLLECTION) {
    return null;
  }

  const user = await request.payload.findByID({
    collection: USERS_COLLECTION,
    depth: 0,
    id: request.user.id,
    overrideAccess: false,
    req: request,
  });

  return {
    email: user.email,
    id: user.id,
    role: user.role,
  };
};

export async function getCurrentUser(): Promise<AuthenticatedUser | null> {
  const request = await createServerPayloadRequest("/api/protected");

  return resolveAuthenticatedUser(request);
}

export async function getCurrentUserFromRequest(
  request: Request,
): Promise<AuthenticatedUser | null> {
  const payloadRequest = await createServerPayloadRequest("/api/protected", request);

  return resolveAuthenticatedUser(payloadRequest);
}

export async function registerUser({
  email,
  password,
}: AuthFormState): Promise<AuthenticatedUser> {
  const { payload } = await getUsersCollectionAuth();
  const createRequest = await createServerPayloadRequest("/api/users");

  const user = await payload.create({
    collection: USERS_COLLECTION,
    data: {
      email,
      password,
      role: DEFAULT_USER_ROLE,
    },
    draft: false,
    overrideAccess: false,
    req: createRequest,
  });

  const loginRequest = await createServerPayloadRequest("/api/users/login");
  const result = await payload.login({
    collection: USERS_COLLECTION,
    data: {
      email,
      password,
    },
    req: loginRequest,
  });

  if (!result.token) {
    throw new Error("Login did not return a session token.");
  }

  await persistLoginCookie(result.token);

  return {
    email: user.email,
    id: user.id,
    role: user.role,
  };
}

export async function loginUser({ email, password }: AuthFormState): Promise<void> {
  const { payload } = await getUsersCollectionAuth();
  const request = await createServerPayloadRequest("/api/users/login");
  const result = await payload.login({
    collection: USERS_COLLECTION,
    data: {
      email,
      password,
    },
    req: request,
  });

  if (!result.token) {
    throw new Error("Login did not return a session token.");
  }

  await persistLoginCookie(result.token);
}

export async function logoutUser(): Promise<void> {
  const { usersCollection } = await getUsersCollectionAuth();
  const request = await createServerPayloadRequest("/api/users/logout");

  if (request.user?.collection === USERS_COLLECTION) {
    await logoutOperation({
      collection: usersCollection,
      req: request,
    });
  }

  await expireLoginCookie();
}

export async function loginAction(formData: FormData): Promise<void> {
  "use server";

  const { email, password } = readAuthFormState(formData);

  if (!email || !password) {
    redirect(buildLoginRedirect({ error: "missing-fields" }));
  }

  try {
    await loginUser({
      email,
      password,
    });
  } catch {
    redirect(buildLoginRedirect({ error: "login-failed" }));
  }

  redirect(buildLoginRedirect({ status: "logged-in" }));
}

export async function registerAction(formData: FormData): Promise<void> {
  "use server";

  const { email, password } = readAuthFormState(formData);

  if (!email || !password) {
    redirect(buildLoginRedirect({ error: "missing-fields" }));
  }

  try {
    await registerUser({
      email,
      password,
    });
  } catch {
    redirect(buildLoginRedirect({ error: "register-failed" }));
  }

  redirect(buildLoginRedirect({ status: "registered" }));
}

export async function logoutAction(): Promise<void> {
  "use server";

  await logoutUser();

  redirect(buildLoginRedirect({ status: "logged-out" }));
}
