import config from "@payload-config";
import { unstable_noStore as noStore } from "next/cache";
import { notFound } from "next/navigation";
import { getPayload } from "payload";

import Layout from "@/components/Layout";
import { PUBLISHED_STATUS } from "@/lib/content-status";
import { isSupportedLocale, type SupportedLocaleCode } from "@/lib/i18n";
import type { Article } from "@/payload-types";

type LocalePageProps = {
  params: Promise<{ locale: string }>;
};

export const dynamic = "force-dynamic";
export const runtime = "nodejs";

const copyByLocale = {
  en: {
    eyebrow: "Public site",
    emptyState: "No published articles are available yet.",
    status: "Viewing the English public content surface.",
    title: "Public site with cms",
    description:
      "Published articles from the CMS appear here. Drafts and review-stage content remain internal to the editorial workflow.",
  },
  pt: {
    eyebrow: "Site publico",
    emptyState: "Ainda nao ha artigos publicados.",
    status: "Visualizando a superficie publica em portugues.",
    title: "Public site with cms",
    description:
      "Os artigos publicados no CMS aparecem aqui. Conteudos em rascunho ou revisao permanecem internos ao fluxo editorial.",
  },
} as const;

const getPublishedArticles = async (
  locale: SupportedLocaleCode,
): Promise<Article[]> => {
  const payload = await getPayload({
    config,
  });
  const { docs } = await payload.find({
    collection: "articles",
    depth: 0,
    limit: 6,
    locale,
    overrideAccess: false,
    sort: "-publishedAt",
    where: {
      status: {
        equals: PUBLISHED_STATUS,
      },
    },
  });

  return docs;
};

export default async function LocaleHomePage({ params }: LocalePageProps) {
  noStore();

  const { locale } = await params;

  if (!isSupportedLocale(locale)) {
    notFound();
  }

  const [copy, articles] = await Promise.all([
    Promise.resolve(copyByLocale[locale]),
    getPublishedArticles(locale),
  ]);

  return (
    <Layout locale={locale}>
      <div className="space-y-10">
        <section className="space-y-4">
          <p className="text-sm font-medium uppercase tracking-[0.2em] text-slate-500">
            {copy.eyebrow}
          </p>
          <p className="inline-flex rounded-full bg-slate-100 px-3 py-1 text-sm text-slate-700">
            {copy.status}
          </p>
          <h1 className="text-3xl font-semibold tracking-tight text-slate-950">
            {copy.title}
          </h1>
          <p className="max-w-2xl text-base text-slate-600">
            {copy.description}
          </p>
        </section>

        <section className="space-y-4">
          <div className="flex items-center justify-between gap-4">
            <h2 className="text-2xl font-semibold tracking-tight text-slate-950">
              {locale === "pt" ? "Artigos publicados" : "Published articles"}
            </h2>
            <p className="text-sm text-slate-500">
              {articles.length}{" "}
              {locale === "pt" ? "visiveis publicamente" : "visible publicly"}
            </p>
          </div>

          {articles.length > 0 ? (
            <div className="grid gap-4 md:grid-cols-2">
              {articles.map((article) => (
                <article
                  key={article.id}
                  className="rounded-3xl border border-slate-200 bg-slate-50 p-6 shadow-sm"
                >
                  <p className="text-xs font-medium uppercase tracking-[0.2em] text-slate-500">
                    {article.publishedAt
                      ? new Date(article.publishedAt).toLocaleDateString(locale)
                      : locale === "pt"
                        ? "Publicado"
                        : "Published"}
                  </p>
                  <h3 className="mt-3 text-xl font-semibold tracking-tight text-slate-950">
                    {article.title}
                  </h3>
                  {article.excerpt ? (
                    <p className="mt-3 text-sm leading-6 text-slate-600">
                      {article.excerpt}
                    </p>
                  ) : (
                    <p className="mt-3 text-sm leading-6 text-slate-600">
                      {article.body.slice(0, 160)}
                      {article.body.length > 160 ? "..." : ""}
                    </p>
                  )}
                </article>
              ))}
            </div>
          ) : (
            <div className="rounded-3xl border border-dashed border-slate-300 bg-slate-50 px-6 py-8 text-sm text-slate-600">
              {copy.emptyState}
            </div>
          )}
        </section>
      </div>
    </Layout>
  );
}
