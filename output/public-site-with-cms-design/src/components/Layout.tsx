import Link from "next/link";
import type { ReactNode } from "react";

import LocaleSwitcher from "@/components/LocaleSwitcher";
import {
  defaultLocale,
  getLocalePathname,
  type AppLocale,
} from "@/lib/i18n";

type Props = {
  children: ReactNode;
  locale?: AppLocale;
};

const shellCopy = {
  en: {
    navLabel: "Locale switcher",
    siteEyebrow: "Public site with CMS design",
    siteTitle: "Frontend application",
  },
  pt: {
    navLabel: "Seletor de locale",
    siteEyebrow: "Site publico com CMS",
    siteTitle: "Aplicacao frontend",
  },
} satisfies Record<
  AppLocale,
  {
    navLabel: string;
    siteEyebrow: string;
    siteTitle: string;
  }
>;

export default function Layout({
  children,
  locale = defaultLocale,
}: Props) {
  const copy = shellCopy[locale];

  return (
    <div className="site-shell">
      <header className="site-header">
        <div>
          <p className="site-eyebrow">{copy.siteEyebrow}</p>
          <Link className="site-title" href={getLocalePathname(locale)}>
            {copy.siteTitle}
          </Link>
        </div>
        <nav aria-label={copy.navLabel} className="site-nav">
          <LocaleSwitcher locale={locale} />
        </nav>
      </header>

      <main className="site-main">{children}</main>
    </div>
  );
}
