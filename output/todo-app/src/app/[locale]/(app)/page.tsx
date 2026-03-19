import { notFound } from "next/navigation";
import { NotificationCenter } from "@/components/NotificationCenter";
import { isLocaleCode, type AppLocale } from "@/lib/i18n";

const pageCopy = {
  en: {
    eyebrow: "Home",
    title: "Todo application",
    description:
      "Use this page to validate the in-app notification workflow for authenticated users.",
  },
  pt: {
    eyebrow: "Inicio",
    title: "Aplicativo de tarefas",
    description:
      "Use esta pagina para validar o fluxo de notificacoes no aplicativo para usuarios autenticados.",
  },
} satisfies Record<
  AppLocale,
  { eyebrow: string; title: string; description: string }
>;

type AppHomePageProps = {
  params: Promise<{
    locale: string;
  }>;
};

export default async function AppHomePage({ params }: AppHomePageProps) {
  const { locale } = await params;

  if (!isLocaleCode(locale)) {
    notFound();
  }

  const copy = pageCopy[locale];

  return (
    <div className="space-y-8">
      <section className="space-y-3">
        <p className="text-sm font-medium uppercase tracking-[0.2em] text-slate-500">
          {copy.eyebrow}
        </p>
        <div className="space-y-2">
          <h2 className="text-3xl font-semibold tracking-tight">
            {copy.title}
          </h2>
          <p className="max-w-2xl text-sm text-slate-600">{copy.description}</p>
        </div>
      </section>

      <NotificationCenter locale={locale} />
    </div>
  );
}
