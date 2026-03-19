import type { ReactNode } from "react";
import { notFound } from "next/navigation";
import { Layout } from "@/components/Layout";
import { LocaleSwitcher } from "@/components/LocaleSwitcher";
import { isLocaleCode, supportedLocales, type AppLocale } from "@/lib/i18n";

const layoutCopy = {
  en: {
    eyebrow: "Todo App",
    title: "Application Shell",
  },
  pt: {
    eyebrow: "Aplicativo de Tarefas",
    title: "Estrutura do Aplicativo",
  },
} satisfies Record<AppLocale, { eyebrow: string; title: string }>;

type LocaleLayoutProps = {
  children: ReactNode;
  params: Promise<{
    locale: string;
  }>;
};

export function generateStaticParams() {
  return supportedLocales.map((locale) => ({ locale }));
}

export default async function LocaleLayout({
  children,
  params,
}: LocaleLayoutProps) {
  const { locale } = await params;

  if (!isLocaleCode(locale)) {
    notFound();
  }

  const copy = layoutCopy[locale];

  return (
    <div lang={locale}>
      <Layout
        headerEyebrow={copy.eyebrow}
        headerTitle={copy.title}
        headerActions={<LocaleSwitcher currentLocale={locale} />}
      >
        {children}
      </Layout>
    </div>
  );
}
