"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  getLocalizedPathname,
  localeDefinitions,
  type AppLocale,
} from "@/lib/i18n";

type LocaleSwitcherProps = {
  currentLocale: AppLocale;
};

export function LocaleSwitcher({ currentLocale }: LocaleSwitcherProps) {
  const pathname = usePathname();

  return (
    <nav aria-label="Locale switcher" className="flex items-center gap-2">
      {localeDefinitions.map(({ code, label }) => {
        const isActive = code === currentLocale;

        return (
          <Link
            key={code}
            href={getLocalizedPathname(pathname, code)}
            aria-current={isActive ? "page" : undefined}
            className={`rounded border px-3 py-2 text-sm transition ${
              isActive
                ? "border-slate-950 bg-slate-950 text-white"
                : "border-slate-300 bg-white text-slate-700 hover:border-slate-400 hover:text-slate-950"
            }`}
          >
            {label}
          </Link>
        );
      })}
    </nav>
  );
}
