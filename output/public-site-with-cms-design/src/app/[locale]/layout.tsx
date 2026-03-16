import type { ReactNode } from "react";
import { notFound } from "next/navigation";

import Layout from "@/components/Layout";
import { isAppLocale, localeCodes } from "@/lib/i18n";

type LocaleLayoutProps = {
  children: ReactNode;
  params: Promise<{
    locale: string;
  }>;
};

export const dynamicParams = false;

export function generateStaticParams() {
  return localeCodes.map((locale) => ({ locale }));
}

export default async function LocaleLayout({
  children,
  params,
}: LocaleLayoutProps) {
  const { locale } = await params;

  if (!isAppLocale(locale)) {
    notFound();
  }

  return <Layout locale={locale}>{children}</Layout>;
}
