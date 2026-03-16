import Link from "next/link";
import { redirect } from "next/navigation";

import Layout from "@/components/Layout";
import {
  getAuthErrorMessage,
  getSessionUser,
  loginUser,
  logoutUser,
  registerUser,
} from "@/lib/auth";

type PageProps = {
  searchParams: Promise<Record<string, string | string[] | undefined>>;
};

const statusMessages = {
  "logged-in": "Session established. Admin-only routes now require the admin role.",
  "logged-out": "Session ended.",
  registered: "Registration complete. Sign in with the new account.",
} as const;

function getSearchParam(
  searchParams: Record<string, string | string[] | undefined>,
  key: string,
): string | null {
  const value = searchParams[key];

  if (typeof value === "string" && value.trim()) {
    return value;
  }

  return null;
}

function getFormValue(formData: FormData, key: string): string {
  const value = formData.get(key);

  return typeof value === "string" ? value : "";
}

function redirectToLogin(params: Record<string, string>) {
  const search = new URLSearchParams(params).toString();
  redirect(search ? `/login?${search}` : "/login");
}

async function registerAction(formData: FormData) {
  "use server";

  const email = getFormValue(formData, "email").trim().toLowerCase();
  const password = getFormValue(formData, "password");

  if (!email || !password) {
    redirectToLogin({
      error: "Email and password are required to register.",
    });
  }

  try {
    await registerUser({ email, password });
  } catch (error) {
    redirectToLogin({
      error: getAuthErrorMessage(error),
    });
  }

  redirectToLogin({
    status: "registered",
  });
}

async function loginAction(formData: FormData) {
  "use server";

  const email = getFormValue(formData, "email").trim().toLowerCase();
  const password = getFormValue(formData, "password");

  if (!email || !password) {
    redirectToLogin({
      error: "Email and password are required to sign in.",
    });
  }

  try {
    await loginUser({ email, password });
  } catch (error) {
    redirectToLogin({
      error: getAuthErrorMessage(error),
    });
  }

  redirectToLogin({
    status: "logged-in",
  });
}

async function logoutAction() {
  "use server";

  await logoutUser();

  redirectToLogin({
    status: "logged-out",
  });
}

export default async function LoginPage({ searchParams }: PageProps) {
  const params = await searchParams;
  const user = await getSessionUser();
  const errorMessage = getSearchParam(params, "error");
  const status = getSearchParam(params, "status");
  const statusMessage =
    status && status in statusMessages
      ? statusMessages[status as keyof typeof statusMessages]
      : null;

  return (
    <Layout>
      <section className="auth-page">
        <div className="auth-header">
          <p className="home-kicker">Authentication</p>
          <h1>{user ? "Session active" : "Access the CMS"}</h1>
          <p className="auth-copy">
            {user
              ? "This story uses Payload's built-in email and password authentication with cookie-backed sessions."
              : "Register a local account or sign in with an existing one to establish a Payload session."}
          </p>
        </div>

        {errorMessage ? (
          <p className="auth-status auth-status-error">{errorMessage}</p>
        ) : null}

        {statusMessage ? (
          <p className="auth-status auth-status-success">{statusMessage}</p>
        ) : null}

        {user ? (
          <section className="auth-card auth-session-card">
            <div className="auth-session">
              <div>
                <h2>Current session</h2>
                <p className="auth-copy">
                  Signed in as{" "}
                  <span className="auth-value">{user.email ?? "unknown user"}</span>
                  {" "}with the <span className="auth-value">{user.role}</span> role.
                </p>
                <p className="auth-copy">
                  Payload admin and the protected API route are restricted to admin
                  users.
                </p>
              </div>

              <div className="auth-links">
                <Link className="auth-link" href="/admin">
                  Open Payload admin
                </Link>
                <a
                  className="auth-link"
                  href="/api/protected"
                  rel="noreferrer"
                  target="_blank"
                >
                  Open admin-only protected route
                </a>
              </div>

              <form action={logoutAction}>
                <button className="auth-button" type="submit">
                  Log out
                </button>
              </form>
            </div>
          </section>
        ) : (
          <div className="auth-grid">
            <section className="auth-card">
              <div>
                <h2>Register</h2>
                <p className="auth-copy">
                  Creates a local user in the Payload `users` collection.
                </p>
              </div>

              <form action={registerAction} className="auth-form">
                <label className="auth-field">
                  <span>Email</span>
                  <input
                    autoComplete="email"
                    name="email"
                    required
                    type="email"
                  />
                </label>

                <label className="auth-field">
                  <span>Password</span>
                  <input
                    autoComplete="new-password"
                    name="password"
                    required
                    type="password"
                  />
                </label>

                <button className="auth-button" type="submit">
                  Create account
                </button>
              </form>
            </section>

            <section className="auth-card">
              <div>
                <h2>Sign in</h2>
                <p className="auth-copy">
                  Starts a session cookie using Payload&apos;s built-in auth flow.
                </p>
              </div>

              <form action={loginAction} className="auth-form">
                <label className="auth-field">
                  <span>Email</span>
                  <input
                    autoComplete="email"
                    name="email"
                    required
                    type="email"
                  />
                </label>

                <label className="auth-field">
                  <span>Password</span>
                  <input
                    autoComplete="current-password"
                    name="password"
                    required
                    type="password"
                  />
                </label>

                <button className="auth-button" type="submit">
                  Log in
                </button>
              </form>
            </section>
          </div>
        )}
      </section>
    </Layout>
  );
}
