import Link from "next/link";

import {
  getCurrentUser,
  loginAction,
  logoutAction,
  registerAction,
} from "@/lib/auth";

type LoginPageProps = {
  searchParams: Promise<{
    error?: string | string[];
    status?: string | string[];
  }>;
};

const statusMessages: Record<string, string> = {
  "logged-in": "Login successful. Your session is active.",
  "logged-out": "You have been logged out and the session cookie was cleared.",
  registered: "Registration successful. A valid session has been created for this account.",
};

const errorMessages: Record<string, string> = {
  "login-failed": "Login failed. Check the email and password and try again.",
  "missing-fields": "Email and password are required for both forms.",
  "register-failed": "Registration failed. The account may already exist or the password may be invalid.",
};

const getSearchParamValue = (value?: string | string[]): string | null => {
  if (Array.isArray(value)) {
    return value[0] ?? null;
  }

  return value ?? null;
};

const renderFlashMessage = (searchParams: Awaited<LoginPageProps["searchParams"]>) => {
  const error = getSearchParamValue(searchParams.error);

  if (error && errorMessages[error]) {
    return (
      <div className="rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800">
        {errorMessages[error]}
      </div>
    );
  }

  const status = getSearchParamValue(searchParams.status);

  if (status && statusMessages[status]) {
    return (
      <div className="rounded-2xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-800">
        {statusMessages[status]}
      </div>
    );
  }

  return null;
};

export default async function LoginPage({ searchParams }: LoginPageProps) {
  const [resolvedSearchParams, currentUser] = await Promise.all([searchParams, getCurrentUser()]);

  return (
    <main className="min-h-screen bg-slate-50 px-6 py-16 text-slate-950">
      <div className="mx-auto max-w-5xl space-y-8">
        <div className="space-y-4">
          <Link href="/" className="text-sm font-medium text-slate-500 transition hover:text-slate-900">
            Back to site
          </Link>
          <div className="space-y-3">
            <p className="text-sm font-medium uppercase tracking-[0.2em] text-slate-500">
              Authentication
            </p>
            <h1 className="text-4xl font-semibold tracking-tight text-slate-950">
              Email and password access
            </h1>
            <p className="max-w-2xl text-base text-slate-600">
              Register a user, start a session, and verify the protected API route at
              <span className="mx-1 rounded bg-slate-200 px-2 py-1 font-mono text-sm text-slate-800">
                /api/protected
              </span>
              returns 401 until you authenticate.
            </p>
          </div>
        </div>

        {renderFlashMessage(resolvedSearchParams)}

        {currentUser ? (
          <section className="rounded-3xl border border-slate-200 bg-white p-8 shadow-sm">
            <div className="space-y-3">
              <p className="text-sm font-medium uppercase tracking-[0.2em] text-slate-500">
                Active session
              </p>
              <h2 className="text-2xl font-semibold tracking-tight text-slate-950">
                Signed in as {currentUser.email}
              </h2>
              <p className="text-sm text-slate-600">User ID: {currentUser.id}</p>
              <p className="max-w-2xl text-sm text-slate-600">
                This session is backed by Payload auth. Open the protected route or log out to
                confirm the session is invalidated.
              </p>
            </div>

            <div className="mt-6 flex flex-col gap-4 sm:flex-row">
              <Link
                href="/api/protected"
                className="inline-flex items-center justify-center rounded-full bg-slate-950 px-5 py-3 text-sm font-medium text-white transition hover:bg-slate-800"
              >
                Open protected route
              </Link>
              <form action={logoutAction}>
                <button
                  type="submit"
                  className="inline-flex items-center justify-center rounded-full border border-slate-300 px-5 py-3 text-sm font-medium text-slate-700 transition hover:border-slate-400 hover:text-slate-950"
                >
                  Log out
                </button>
              </form>
            </div>
          </section>
        ) : (
          <div className="grid gap-6 lg:grid-cols-2">
            <section className="rounded-3xl border border-slate-200 bg-white p-8 shadow-sm">
              <div className="space-y-3">
                <p className="text-sm font-medium uppercase tracking-[0.2em] text-slate-500">
                  Login
                </p>
                <h2 className="text-2xl font-semibold tracking-tight text-slate-950">
                  Start an authenticated session
                </h2>
                <p className="text-sm text-slate-600">
                  Successful login sets the Payload auth cookie used by protected routes.
                </p>
              </div>

              <form action={loginAction} className="mt-6 space-y-4">
                <label className="block space-y-2 text-sm font-medium text-slate-700">
                  <span>Email</span>
                  <input
                    autoComplete="email"
                    className="w-full rounded-2xl border border-slate-300 px-4 py-3 text-base text-slate-950 outline-none transition focus:border-slate-950"
                    name="email"
                    required
                    type="email"
                  />
                </label>
                <label className="block space-y-2 text-sm font-medium text-slate-700">
                  <span>Password</span>
                  <input
                    autoComplete="current-password"
                    className="w-full rounded-2xl border border-slate-300 px-4 py-3 text-base text-slate-950 outline-none transition focus:border-slate-950"
                    name="password"
                    required
                    type="password"
                  />
                </label>
                <button
                  className="inline-flex items-center justify-center rounded-full bg-slate-950 px-5 py-3 text-sm font-medium text-white transition hover:bg-slate-800"
                  type="submit"
                >
                  Log in
                </button>
              </form>
            </section>

            <section className="rounded-3xl border border-slate-200 bg-white p-8 shadow-sm">
              <div className="space-y-3">
                <p className="text-sm font-medium uppercase tracking-[0.2em] text-slate-500">
                  Register
                </p>
                <h2 className="text-2xl font-semibold tracking-tight text-slate-950">
                  Create a new account
                </h2>
                <p className="text-sm text-slate-600">
                  Registration stores a hashed password through Payload local auth and signs the
                  user in immediately.
                </p>
              </div>

              <form action={registerAction} className="mt-6 space-y-4">
                <label className="block space-y-2 text-sm font-medium text-slate-700">
                  <span>Email</span>
                  <input
                    autoComplete="email"
                    className="w-full rounded-2xl border border-slate-300 px-4 py-3 text-base text-slate-950 outline-none transition focus:border-slate-950"
                    name="email"
                    required
                    type="email"
                  />
                </label>
                <label className="block space-y-2 text-sm font-medium text-slate-700">
                  <span>Password</span>
                  <input
                    autoComplete="new-password"
                    className="w-full rounded-2xl border border-slate-300 px-4 py-3 text-base text-slate-950 outline-none transition focus:border-slate-950"
                    name="password"
                    required
                    type="password"
                  />
                </label>
                <button
                  className="inline-flex items-center justify-center rounded-full border border-slate-300 px-5 py-3 text-sm font-medium text-slate-700 transition hover:border-slate-400 hover:text-slate-950"
                  type="submit"
                >
                  Register
                </button>
              </form>
            </section>
          </div>
        )}
      </div>
    </main>
  );
}
