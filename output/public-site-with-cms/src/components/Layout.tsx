import Link from "next/link";

import LocaleSwitcher from "@/components/LocaleSwitcher";
import { getLocalizedPathname, type SupportedLocaleCode } from "@/lib/i18n";

type LayoutProps = {
  children: React.ReactNode;
  locale: SupportedLocaleCode;
};

export default function Layout({ children, locale }: LayoutProps) {
  return (
    <div className="min-h-screen bg-white text-slate-950">
      <header className="border-b border-slate-200">
        <div className="mx-auto flex max-w-5xl items-center justify-between px-6 py-4">
          <Link
            href={getLocalizedPathname("/", locale)}
            className="text-lg font-semibold tracking-tight"
          >
            Public site with cms
          </Link>
          <LocaleSwitcher locale={locale} />
        </div>
      </header>

      <main className="mx-auto max-w-5xl px-6 py-12">{children}</main>
    </div>
  );
}
