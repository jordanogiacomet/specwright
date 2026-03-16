import {
  resolveAppLocale,
  type AppLocale,
  supportedLocales,
} from "@/lib/i18n";

type LocaleHomePageProps = {
  params: Promise<{
    locale: string;
  }>;
};

const homePageCopy = {
  en: {
    description:
      "This placeholder confirms the public site renders through a locale-prefixed route.",
    kicker: "ST-004 - locale routing",
    secondary:
      "Use the header switcher to move between English and Portuguese without leaving the current page.",
    title: "Frontend application shell",
  },
  pt: {
    description:
      "Este placeholder confirma que o site publico renderiza por uma rota com prefixo de locale.",
    kicker: "ST-004 - roteamento de locale",
    secondary:
      "Use o seletor no cabecalho para alternar entre ingles e portugues sem sair da pagina atual.",
    title: "Shell da aplicacao frontend",
  },
} satisfies Record<
  AppLocale,
  {
    description: string;
    kicker: string;
    secondary: string;
    title: string;
  }
>;

const localeLabels = Object.fromEntries(
  supportedLocales.map(({ code, label }) => [code, label]),
) as Record<AppLocale, string>;

export default async function LocaleHomePage({
  params,
}: LocaleHomePageProps) {
  const { locale: localeParam } = await params;
  const locale = resolveAppLocale(localeParam);
  const copy = homePageCopy[locale];

  return (
    <section className="home-placeholder">
      <p className="home-kicker">{copy.kicker}</p>
      <h1>{copy.title}</h1>
      <p>{copy.description}</p>
      <p>{copy.secondary}</p>
      <p>
        {locale === "en" ? "Current locale" : "Locale atual"}:{" "}
        {localeLabels[locale]}
      </p>
    </section>
  );
}
