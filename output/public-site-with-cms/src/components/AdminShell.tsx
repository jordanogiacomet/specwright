"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import { DEFAULT_LOCALE, getLocalizedPathname } from "@/lib/i18n";

type AdminShellProps = {
  children: React.ReactNode;
  currentUser: {
    email: string;
    id: number | string;
    role?: string | null;
  };
};

type NavItem = {
  description: string;
  href: string;
  label: string;
};

const editorialNavigation: NavItem[] = [
  {
    description: "Placeholder list and detail views for editorial entries.",
    href: "/content",
    label: "Content",
  },
  {
    description: "Operational reporting for workflow progress and visibility.",
    href: "/reports",
    label: "Reports",
  },
  {
    description: "Reserved surface for media library workflows.",
    href: "/media",
    label: "Media",
  },
  {
    description: "Reserved surface for platform and editorial settings.",
    href: "/settings",
    label: "Settings",
  },
];

const publicSiteHref = getLocalizedPathname("/", DEFAULT_LOCALE);

const isActivePath = (pathname: string, href: string): boolean =>
  pathname === href || pathname.startsWith(`${href}/`);

const formatRoleLabel = (role?: string | null): string => {
  if (!role) {
    return "Authenticated";
  }

  return role
    .split("_")
    .map((segment) => segment.charAt(0).toUpperCase() + segment.slice(1))
    .join(" ");
};

export default function AdminShell({
  children,
  currentUser,
}: AdminShellProps) {
  const pathname = usePathname();

  return (
    <div className="min-h-screen bg-slate-100 text-slate-950">
      <div className="mx-auto flex max-w-7xl flex-col gap-6 px-6 py-8 lg:flex-row">
        <aside className="w-full shrink-0 lg:sticky lg:top-8 lg:w-80 lg:self-start">
          <div className="space-y-6">
            <section className="overflow-hidden rounded-[2rem] bg-slate-950 text-white shadow-xl shadow-slate-950/10">
              <div className="border-b border-white/10 px-6 py-6">
                <p className="text-xs font-medium uppercase tracking-[0.24em] text-slate-300">
                  Editorial shell
                </p>
                <h1 className="mt-3 text-2xl font-semibold tracking-tight">
                  Content platform
                </h1>
                <p className="mt-3 text-sm leading-6 text-slate-300">
                  Shared navigation for editorial operations and delivery
                  surfaces.
                </p>
              </div>

              <dl className="grid gap-4 px-6 py-5 text-sm sm:grid-cols-2 lg:grid-cols-1">
                <div className="space-y-1">
                  <dt className="text-xs font-medium uppercase tracking-[0.2em] text-slate-400">
                    Signed in
                  </dt>
                  <dd className="break-all font-medium text-white">
                    {currentUser.email}
                  </dd>
                </div>
                <div className="space-y-1">
                  <dt className="text-xs font-medium uppercase tracking-[0.2em] text-slate-400">
                    Access
                  </dt>
                  <dd className="font-medium text-white">
                    {formatRoleLabel(currentUser.role)}
                  </dd>
                </div>
              </dl>
            </section>

            <nav
              aria-label="Editorial navigation"
              className="rounded-[2rem] border border-slate-200 bg-white p-3 shadow-sm shadow-slate-200/60"
            >
              <p className="px-3 pt-2 text-xs font-medium uppercase tracking-[0.2em] text-slate-500">
                Editorial navigation
              </p>

              <div className="mt-3 space-y-1">
                {editorialNavigation.map((item) => {
                  const active = isActivePath(pathname, item.href);

                  return (
                    <Link
                      key={item.href}
                      href={item.href}
                      className={`block rounded-[1.5rem] px-4 py-4 transition ${
                        active
                          ? "bg-slate-950 text-white"
                          : "text-slate-700 hover:bg-slate-100 hover:text-slate-950"
                      }`}
                    >
                      <div className="flex items-center justify-between gap-3">
                        <span className="text-base font-semibold tracking-tight">
                          {item.label}
                        </span>
                        <span
                          className={`rounded-full px-2 py-1 text-[11px] font-medium uppercase tracking-[0.18em] ${
                            active
                              ? "bg-white/10 text-slate-200"
                              : "bg-slate-100 text-slate-500"
                          }`}
                        >
                          {active ? "Open" : "Route"}
                        </span>
                      </div>
                      <p
                        className={`mt-2 text-sm leading-6 ${
                          active ? "text-slate-300" : "text-slate-500"
                        }`}
                      >
                        {item.description}
                      </p>
                    </Link>
                  );
                })}
              </div>
            </nav>

            <section className="rounded-[2rem] border border-slate-200 bg-white p-6 shadow-sm shadow-slate-200/60">
              <p className="text-xs font-medium uppercase tracking-[0.2em] text-slate-500">
                Delivery surface
              </p>
              <h2 className="mt-3 text-lg font-semibold tracking-tight text-slate-950">
                Public route group
              </h2>
              <p className="mt-2 text-sm leading-6 text-slate-600">
                The public site remains on its own route group and layout. Use
                this shortcut to jump to the delivery surface without changing
                its implementation in this story.
              </p>

              <Link
                href={publicSiteHref}
                className="mt-5 inline-flex items-center justify-center rounded-full bg-slate-950 px-4 py-2 text-sm font-medium text-white transition hover:bg-slate-800"
              >
                Open public site
              </Link>
            </section>
          </div>
        </aside>

        <main className="min-w-0 flex-1">{children}</main>
      </div>
    </div>
  );
}
