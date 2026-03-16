import type { Metadata } from "next";
import Link from "next/link";
import { unstable_noStore as noStore } from "next/cache";
import { notFound, redirect } from "next/navigation";

import Layout from "@/components/Layout";
import { getLocalizedPathname } from "@/lib/i18n";
import { getArticlePreview } from "@/lib/preview";
import type { Article } from "@/payload-types";

type PreviewPageProps = {
  params: Promise<{ slug: string }>;
  searchParams: Promise<{
    locale?: string | string[];
  }>;
};

type PreviewCopy = {
  accessNote: string;
  backToSite: string;
  badge: string;
  bodyLabel: string;
  previewUrlLabel: string;
  robotsNote: string;
  statusLabel: string;
  statusLabels: Record<Article["status"], string>;
};

export const dynamic = "force-dynamic";
export const runtime = "nodejs";
export const metadata = {
  robots: {
    follow: false,
    index: false,
  },
  title: "Content preview",
} satisfies Metadata;

const copyByLocale: Record<"en" | "pt", PreviewCopy> = {
  en: {
    accessNote: "Authenticated editorial access only",
    backToSite: "Back to public site",
    badge: "Preview mode",
    bodyLabel: "Article body",
    previewUrlLabel: "Preview URL",
    robotsNote: "This route is not indexed and is excluded from the public content surface.",
    statusLabel: "Status",
    statusLabels: {
      archived: "Archived",
      draft: "Draft",
      in_review: "In review",
      published: "Published",
      scheduled: "Scheduled",
    },
  },
  pt: {
    accessNote: "Acesso editorial autenticado",
    backToSite: "Voltar ao site publico",
    badge: "Modo de pre-visualizacao",
    bodyLabel: "Corpo do artigo",
    previewUrlLabel: "URL de pre-visualizacao",
    robotsNote:
      "Esta rota nao e indexada e fica fora da superficie publica de conteudo.",
    statusLabel: "Status",
    statusLabels: {
      archived: "Arquivado",
      draft: "Rascunho",
      in_review: "Em revisao",
      published: "Publicado",
      scheduled: "Agendado",
    },
  },
};

const renderBody = (body: string) => {
  const paragraphs = body
    .split(/\n{2,}/)
    .map((paragraph) => paragraph.trim())
    .filter(Boolean);

  return paragraphs.map((paragraph, index) => (
    <p
      key={`${index}-${paragraph.slice(0, 24)}`}
      className="text-base leading-8 whitespace-pre-wrap text-slate-700"
    >
      {paragraph}
    </p>
  ));
};

export default async function PreviewPage({
  params,
  searchParams,
}: PreviewPageProps) {
  noStore();

  const [{ slug }, resolvedSearchParams] = await Promise.all([params, searchParams]);
  const preview = await getArticlePreview({
    locale: resolvedSearchParams.locale,
    slug,
  });

  if (preview.status === "login-required") {
    redirect("/login");
  }

  if (preview.status === "forbidden" || preview.status === "not-found") {
    notFound();
  }

  const copy = copyByLocale[preview.locale];
  const publicHomePath = getLocalizedPathname("/", preview.locale);

  return (
    <Layout locale={preview.locale}>
      <div className="space-y-10">
        <section className="space-y-5">
          <Link
            href={publicHomePath}
            className="text-sm font-medium text-slate-500 transition hover:text-slate-900"
          >
            {copy.backToSite}
          </Link>

          <div className="flex flex-wrap gap-3">
            <p className="inline-flex rounded-full bg-amber-100 px-3 py-1 text-sm font-medium text-amber-900">
              {copy.badge}
            </p>
            <p className="inline-flex rounded-full bg-slate-100 px-3 py-1 text-sm text-slate-700">
              {copy.accessNote}
            </p>
          </div>

          <div className="space-y-3">
            <h1 className="text-3xl font-semibold tracking-tight text-slate-950">
              {preview.article.title}
            </h1>
            {preview.article.excerpt ? (
              <p className="max-w-3xl text-base text-slate-600">
                {preview.article.excerpt}
              </p>
            ) : null}
            <p className="max-w-3xl text-sm text-slate-500">{copy.robotsNote}</p>
          </div>

          <dl className="grid gap-4 rounded-3xl border border-slate-200 bg-slate-50 p-6 sm:grid-cols-2">
            <div className="space-y-1">
              <dt className="text-xs font-medium uppercase tracking-[0.2em] text-slate-500">
                {copy.statusLabel}
              </dt>
              <dd className="text-sm font-medium text-slate-900">
                {copy.statusLabels[preview.article.status]}
              </dd>
            </div>
            <div className="space-y-1">
              <dt className="text-xs font-medium uppercase tracking-[0.2em] text-slate-500">
                {copy.previewUrlLabel}
              </dt>
              <dd className="break-all font-mono text-xs text-slate-700">
                {preview.previewUrl}
              </dd>
            </div>
          </dl>
        </section>

        <article className="rounded-3xl border border-slate-200 bg-white p-8 shadow-sm">
          <div className="space-y-4">
            <p className="text-sm font-medium uppercase tracking-[0.2em] text-slate-500">
              {copy.bodyLabel}
            </p>
            <div className="space-y-6">{renderBody(preview.article.body)}</div>
          </div>
        </article>
      </div>
    </Layout>
  );
}
