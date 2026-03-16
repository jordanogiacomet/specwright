"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import {
  getLocalePathname,
  supportedLocales,
  type AppLocale,
} from "@/lib/i18n";

type Props = {
  locale: AppLocale;
};

export default function LocaleSwitcher({ locale }: Props) {
  const pathname = usePathname();

  return (
    <div className="locale-switcher">
      {supportedLocales.map(({ code, label }) => {
        const href = getLocalePathname(code, pathname);

        return (
          <Link
            aria-current={code === locale ? "page" : undefined}
            className={`locale-link${code === locale ? " locale-link-current" : ""}`}
            href={href}
            key={code}
          >
            {label}
          </Link>
        );
      })}
    </div>
  );
}
