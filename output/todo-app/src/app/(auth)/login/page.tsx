"use client";

import { useEffect, useState, type FormEvent } from "react";

const apiBaseUrl =
  process.env.NEXT_PUBLIC_API_BASE_URL?.replace(/\/$/, "") ||
  "http://localhost:3001";

type AuthUser = {
  id: string;
  email: string;
  createdAt: string;
};

type AuthSession = {
  id: string;
  userId: string;
  createdAt: string;
  expiresAt: string;
  token: string;
};

type AuthPayload = {
  authenticated?: boolean;
  user: AuthUser;
  session: AuthSession;
};

type FormState = {
  email: string;
  password: string;
};

const emptyFormState: FormState = {
  email: "",
  password: "",
};

async function parseResponse(response: Response) {
  const contentType = response.headers.get("content-type") ?? "";

  if (!contentType.includes("application/json")) {
    return null;
  }

  return (await response.json()) as Record<string, unknown>;
}

function getResponseMessage(body: unknown, fallbackMessage: string): string {
  if (
    typeof body === "object" &&
    body !== null &&
    "message" in body &&
    typeof body.message === "string"
  ) {
    return body.message;
  }

  return fallbackMessage;
}

async function request<T>(
  path: string,
  init: RequestInit,
): Promise<{ ok: boolean; status: number; body: T | null }> {
  const response = await fetch(`${apiBaseUrl}${path}`, {
    ...init,
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
      ...(init.headers ?? {}),
    },
  });

  return {
    ok: response.ok,
    status: response.status,
    body: (await parseResponse(response)) as T | null,
  };
}

export default function LoginPage() {
  const [loginForm, setLoginForm] = useState<FormState>(emptyFormState);
  const [registerForm, setRegisterForm] = useState<FormState>(emptyFormState);
  const [session, setSession] = useState<AuthPayload | null>(null);
  const [isLoadingSession, setIsLoadingSession] = useState(true);
  const [activeAction, setActiveAction] = useState<
    "login" | "register" | "logout" | "refresh" | null
  >(null);
  const [status, setStatus] = useState<{
    tone: "neutral" | "success" | "error";
    message: string;
  }>({
    tone: "neutral",
    message: "Use the forms below to create an account or start a session.",
  });

  useEffect(() => {
    let isMounted = true;

    setIsLoadingSession(true);

    void request<AuthPayload>("/api/auth/session", {
      method: "GET",
    })
      .then((response) => {
        if (!isMounted) {
          return;
        }

        if (!response.ok || !response.body) {
          if (response.status !== 401) {
            setStatus({
              tone: "error",
              message: getResponseMessage(
                response.body,
                "Unable to load the current session.",
              ),
            });
          }

          setSession(null);
          return;
        }

        setSession(response.body);
        setStatus({
          tone: "success",
          message: "Session is active.",
        });
      })
      .catch(() => {
        if (!isMounted) {
          return;
        }

        setSession(null);
        setStatus({
          tone: "error",
          message: "Unable to reach the authentication API.",
        });
      })
      .finally(() => {
        if (!isMounted) {
          return;
        }

        setIsLoadingSession(false);
        setActiveAction(null);
      });

    return () => {
      isMounted = false;
    };
  }, []);

  async function loadSession() {
    setIsLoadingSession(true);

    try {
      const response = await request<AuthPayload>("/api/auth/session", {
        method: "GET",
      });

      if (!response.ok || !response.body) {
        if (response.status !== 401) {
          setStatus({
            tone: "error",
            message: getResponseMessage(
              response.body,
              "Unable to load the current session.",
            ),
          });
        }

        setSession(null);
        return;
      }

      setSession(response.body);
      setStatus({
        tone: "success",
        message: "Session is active.",
      });
    } catch {
      setSession(null);
      setStatus({
        tone: "error",
        message: "Unable to reach the authentication API.",
      });
    } finally {
      setIsLoadingSession(false);
      setActiveAction(null);
    }
  }

  async function submitForm(
    event: FormEvent<HTMLFormElement>,
    mode: "login" | "register",
  ) {
    event.preventDefault();
    setActiveAction(mode);

    const formState = mode === "login" ? loginForm : registerForm;

    try {
      const response = await request<AuthPayload>(`/api/auth/${mode}`, {
        method: "POST",
        body: JSON.stringify(formState),
      });

      if (!response.ok || !response.body) {
        setStatus({
          tone: "error",
          message: getResponseMessage(response.body, `Unable to ${mode}.`),
        });
        return;
      }

      setSession(response.body);
      setStatus({
        tone: "success",
        message:
          mode === "register"
            ? "Account created and session started."
            : "Logged in successfully.",
      });
      setLoginForm(emptyFormState);
      setRegisterForm(emptyFormState);
    } catch {
      setStatus({
        tone: "error",
        message: "Unable to reach the authentication API.",
      });
    } finally {
      setActiveAction(null);
    }
  }

  async function handleLogout() {
    setActiveAction("logout");

    try {
      await request<{ success: boolean }>("/api/auth/logout", {
        method: "POST",
      });

      setSession(null);
      setStatus({
        tone: "success",
        message: "Logged out successfully.",
      });
    } catch {
      setStatus({
        tone: "error",
        message: "Unable to reach the authentication API.",
      });
    } finally {
      setActiveAction(null);
    }
  }

  const statusStyles =
    status.tone === "error"
      ? "border-rose-200 bg-rose-50 text-rose-700"
      : status.tone === "success"
        ? "border-emerald-200 bg-emerald-50 text-emerald-700"
        : "border-slate-200 bg-white text-slate-600";

  return (
    <main className="min-h-screen bg-[radial-gradient(circle_at_top,_#e0f2fe,_#f8fafc_42%,_#e2e8f0_100%)] px-6 py-16 text-slate-950">
      <div className="mx-auto grid max-w-6xl gap-6 lg:grid-cols-[1.1fr_0.9fr]">
        <section className="rounded-3xl border border-slate-200 bg-white/90 p-8 shadow-[0_24px_60px_rgba(15,23,42,0.08)] backdrop-blur">
          <p className="text-sm font-semibold uppercase tracking-[0.24em] text-sky-700">
            Authentication
          </p>
          <h1 className="mt-4 max-w-xl text-4xl font-semibold tracking-tight text-slate-950">
            Register, log in, inspect the session, and verify the protected
            auth route.
          </h1>
          <p className="mt-4 max-w-2xl text-base leading-7 text-slate-600">
            This page talks to the standalone Node API at{" "}
            <span className="font-medium text-slate-900">{apiBaseUrl}</span>.
            Registration creates the account and starts a session immediately.
          </p>

          <div className={`mt-6 rounded-2xl border px-4 py-3 text-sm ${statusStyles}`}>
            {status.message}
          </div>

          <div className="mt-8 grid gap-6 lg:grid-cols-2">
            <form
              className="space-y-4 rounded-2xl border border-slate-200 bg-slate-50 p-5"
              onSubmit={(event) => void submitForm(event, "register")}
            >
              <div>
                <h2 className="text-xl font-semibold text-slate-950">Register</h2>
                <p className="mt-1 text-sm text-slate-600">
                  Creates a user with a hashed password and starts a session.
                </p>
              </div>

              <label className="block space-y-2">
                <span className="text-sm font-medium text-slate-700">Email</span>
                <input
                  className="w-full rounded-xl border border-slate-300 bg-white px-4 py-3 text-sm outline-none ring-0 transition focus:border-sky-500"
                  type="email"
                  autoComplete="email"
                  value={registerForm.email}
                  onChange={(event) =>
                    setRegisterForm((currentState) => ({
                      ...currentState,
                      email: event.target.value,
                    }))
                  }
                  required
                />
              </label>

              <label className="block space-y-2">
                <span className="text-sm font-medium text-slate-700">Password</span>
                <input
                  className="w-full rounded-xl border border-slate-300 bg-white px-4 py-3 text-sm outline-none ring-0 transition focus:border-sky-500"
                  type="password"
                  autoComplete="new-password"
                  value={registerForm.password}
                  onChange={(event) =>
                    setRegisterForm((currentState) => ({
                      ...currentState,
                      password: event.target.value,
                    }))
                  }
                  minLength={8}
                  required
                />
              </label>

              <button
                className="w-full rounded-xl bg-sky-600 px-4 py-3 text-sm font-semibold text-white transition hover:bg-sky-700 disabled:cursor-not-allowed disabled:bg-slate-400"
                type="submit"
                disabled={activeAction !== null}
              >
                {activeAction === "register" ? "Creating account..." : "Create account"}
              </button>
            </form>

            <form
              className="space-y-4 rounded-2xl border border-slate-200 bg-slate-50 p-5"
              onSubmit={(event) => void submitForm(event, "login")}
            >
              <div>
                <h2 className="text-xl font-semibold text-slate-950">Login</h2>
                <p className="mt-1 text-sm text-slate-600">
                  Starts a new session backed by a signed token and database row.
                </p>
              </div>

              <label className="block space-y-2">
                <span className="text-sm font-medium text-slate-700">Email</span>
                <input
                  className="w-full rounded-xl border border-slate-300 bg-white px-4 py-3 text-sm outline-none ring-0 transition focus:border-amber-500"
                  type="email"
                  autoComplete="email"
                  value={loginForm.email}
                  onChange={(event) =>
                    setLoginForm((currentState) => ({
                      ...currentState,
                      email: event.target.value,
                    }))
                  }
                  required
                />
              </label>

              <label className="block space-y-2">
                <span className="text-sm font-medium text-slate-700">Password</span>
                <input
                  className="w-full rounded-xl border border-slate-300 bg-white px-4 py-3 text-sm outline-none ring-0 transition focus:border-amber-500"
                  type="password"
                  autoComplete="current-password"
                  value={loginForm.password}
                  onChange={(event) =>
                    setLoginForm((currentState) => ({
                      ...currentState,
                      password: event.target.value,
                    }))
                  }
                  minLength={8}
                  required
                />
              </label>

              <button
                className="w-full rounded-xl bg-amber-500 px-4 py-3 text-sm font-semibold text-slate-950 transition hover:bg-amber-400 disabled:cursor-not-allowed disabled:bg-slate-400"
                type="submit"
                disabled={activeAction !== null}
              >
                {activeAction === "login" ? "Logging in..." : "Log in"}
              </button>
            </form>
          </div>
        </section>

        <aside className="rounded-3xl border border-slate-200 bg-slate-950 p-8 text-slate-100 shadow-[0_24px_60px_rgba(15,23,42,0.16)]">
          <div className="flex items-start justify-between gap-4">
            <div>
              <p className="text-sm font-semibold uppercase tracking-[0.24em] text-slate-400">
                Session
              </p>
              <h2 className="mt-4 text-2xl font-semibold tracking-tight">
                Protected route status
              </h2>
            </div>
            <button
              className="rounded-full border border-slate-700 px-4 py-2 text-sm font-medium text-slate-100 transition hover:border-slate-500 disabled:cursor-not-allowed disabled:opacity-60"
              type="button"
              onClick={() => {
                setActiveAction("refresh");
                void loadSession();
              }}
              disabled={activeAction !== null}
            >
              {activeAction === "refresh" ? "Refreshing..." : "Refresh"}
            </button>
          </div>

          <div className="mt-6 rounded-2xl border border-slate-800 bg-slate-900/70 p-5">
            {isLoadingSession ? (
              <p className="text-sm text-slate-300">Checking the current session...</p>
            ) : session ? (
              <div className="space-y-4">
                <div className="rounded-xl border border-emerald-500/30 bg-emerald-500/10 px-4 py-3 text-sm text-emerald-200">
                  Authenticated request accepted by <code>/api/auth/session</code>.
                </div>
                <dl className="space-y-3 text-sm text-slate-300">
                  <div>
                    <dt className="text-slate-500">Email</dt>
                    <dd className="font-medium text-slate-50">{session.user.email}</dd>
                  </div>
                  <div>
                    <dt className="text-slate-500">User ID</dt>
                    <dd className="break-all font-mono text-xs text-slate-50">
                      {session.user.id}
                    </dd>
                  </div>
                  <div>
                    <dt className="text-slate-500">Session ID</dt>
                    <dd className="break-all font-mono text-xs text-slate-50">
                      {session.session.id}
                    </dd>
                  </div>
                  <div>
                    <dt className="text-slate-500">Expires</dt>
                    <dd className="font-medium text-slate-50">
                      {new Date(session.session.expiresAt).toLocaleString()}
                    </dd>
                  </div>
                </dl>

                <button
                  className="w-full rounded-xl bg-white px-4 py-3 text-sm font-semibold text-slate-950 transition hover:bg-slate-200 disabled:cursor-not-allowed disabled:bg-slate-500"
                  type="button"
                  onClick={() => void handleLogout()}
                  disabled={activeAction !== null}
                >
                  {activeAction === "logout" ? "Logging out..." : "Log out"}
                </button>
              </div>
            ) : (
              <div className="space-y-3 text-sm text-slate-300">
                <div className="rounded-xl border border-amber-500/30 bg-amber-500/10 px-4 py-3 text-amber-200">
                  No active session. The protected auth route currently returns
                  401.
                </div>
                <p>
                  Register or log in, then refresh this panel to verify session
                  persistence.
                </p>
              </div>
            )}
          </div>
        </aside>
      </div>
    </main>
  );
}
