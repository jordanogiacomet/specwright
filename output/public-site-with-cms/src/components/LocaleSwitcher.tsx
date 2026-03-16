"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import {
  getLocalizedPathname,
  SUPPORTED_LOCALES,
  type SupportedLocaleCode,
} from "@/lib/i18n";

type LocaleSwitcherProps = {
  locale: SupportedLocaleCode;
};

export default function LocaleSwitcher({ locale }: LocaleSwitcherProps) {
  const pathname = usePathname() ?? "/";

  return (
    <nav aria-label="Locale switcher" className="flex items-center gap-2 text-sm">
      {SUPPORTED_LOCALES.map(({ code, label }) => {
        const isActive = code === locale;

        return (
          <Link
            key={code}
            href={getLocalizedPathname(pathname, code)}
            hrefLang={code}
            aria-current={isActive ? "page" : undefined}
            className={[
              "rounded-full border px-3 py-1 transition-colors",
              isActive
                ? "border-slate-900 bg-slate-900 text-white"
                : "border-slate-300 text-slate-600 hover:border-slate-400 hover:text-slate-950",
            ].join(" ")}
          >
            <span className="sr-only">{label}</span>
            {code.toUpperCase()}
          </Link>
        );
      })}
    </nav>
  );
}
