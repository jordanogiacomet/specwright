import Link from "next/link";

type ContentDetailPageProps = {
  params: Promise<{ contentId: string }>;
};

const fieldCards = [
  {
    label: "Content type",
    value: "Placeholder entry",
  },
  {
    label: "Workflow owner",
    value: "Editorial team",
  },
  {
    label: "Destination",
    value: "Admin and public surfaces",
  },
  {
    label: "Mutation state",
    value: "Read-only shell",
  },
];

const localeStatuses = [
  {
    locale: "English",
    state: "Ready for authoring",
  },
  {
    locale: "Portuguese",
    state: "Awaiting localized content",
  },
];

const workflowStates = ["Draft structure", "Review handoff", "Scheduled publish"];

const formatContentTitle = (value: string): string =>
  value
    .split("-")
    .filter(Boolean)
    .map((segment) => segment.charAt(0).toUpperCase() + segment.slice(1))
    .join(" ");

export default async function ContentDetailPage({
  params,
}: ContentDetailPageProps) {
  const { contentId } = await params;
  const contentTitle = formatContentTitle(contentId) || "Content entry";

  return (
    <div className="space-y-6">
      <section className="rounded-[2rem] border border-slate-200 bg-white p-8 shadow-sm shadow-slate-200/60">
        <Link
          href="/content"
          className="text-sm font-medium text-slate-500 transition hover:text-slate-900"
        >
          Back to content
        </Link>

        <div className="mt-5 flex flex-wrap gap-3">
          <p className="rounded-full bg-sky-100 px-3 py-1 text-sm font-medium text-sky-900">
            Detail placeholder
          </p>
          <p className="rounded-full bg-slate-100 px-3 py-1 text-sm text-slate-700">
            {contentId}
          </p>
        </div>

        <div className="mt-5 max-w-3xl space-y-3">
          <h1 className="text-3xl font-semibold tracking-tight text-slate-950">
            {contentTitle}
          </h1>
          <p className="text-base leading-7 text-slate-600">
            This placeholder detail view reserves space for authoring fields,
            localized readiness, and publication controls without implementing
            content updates in this story.
          </p>
        </div>
      </section>

      <div className="grid gap-6 xl:grid-cols-[minmax(0,2fr)_minmax(18rem,1fr)]">
        <article className="rounded-[2rem] border border-slate-200 bg-white p-8 shadow-sm shadow-slate-200/60">
          <div className="flex flex-col gap-3 md:flex-row md:items-end md:justify-between">
            <div>
              <p className="text-sm font-medium uppercase tracking-[0.2em] text-slate-500">
                Entry detail
              </p>
              <h2 className="mt-2 text-2xl font-semibold tracking-tight text-slate-950">
                Field canvas
              </h2>
            </div>
            <p className="text-sm text-slate-500">CRUD deferred to later stories</p>
          </div>

          <div className="mt-6 grid gap-4 md:grid-cols-2">
            {fieldCards.map((card) => (
              <div
                key={card.label}
                className="rounded-[1.5rem] border border-slate-200 bg-slate-50 p-4"
              >
                <p className="text-xs font-medium uppercase tracking-[0.18em] text-slate-500">
                  {card.label}
                </p>
                <p className="mt-2 text-lg font-semibold tracking-tight text-slate-950">
                  {card.value}
                </p>
              </div>
            ))}
          </div>

          <section className="mt-6 rounded-[1.75rem] border border-dashed border-slate-300 bg-slate-50 p-6">
            <p className="text-sm font-medium uppercase tracking-[0.2em] text-slate-500">
              Body and modules
            </p>
            <div className="mt-5 space-y-3">
              <div className="h-4 w-5/6 rounded-full bg-slate-200" />
              <div className="h-4 w-full rounded-full bg-slate-200" />
              <div className="h-4 w-4/5 rounded-full bg-slate-200" />
              <div className="h-24 rounded-[1.5rem] bg-white" />
            </div>
          </section>
        </article>

        <aside className="space-y-6">
          <section className="rounded-[2rem] border border-slate-200 bg-white p-6 shadow-sm shadow-slate-200/60">
            <p className="text-sm font-medium uppercase tracking-[0.2em] text-slate-500">
              Workflow
            </p>
            <ul className="mt-4 space-y-3">
              {workflowStates.map((state, index) => (
                <li
                  key={state}
                  className="rounded-[1.25rem] bg-slate-100 px-4 py-3 text-sm text-slate-700"
                >
                  <span className="mr-2 font-semibold text-slate-950">
                    {index + 1}.
                  </span>
                  {state}
                </li>
              ))}
            </ul>
          </section>

          <section className="rounded-[2rem] border border-slate-200 bg-white p-6 shadow-sm shadow-slate-200/60">
            <p className="text-sm font-medium uppercase tracking-[0.2em] text-slate-500">
              Localization
            </p>
            <div className="mt-4 space-y-3">
              {localeStatuses.map((item) => (
                <div
                  key={item.locale}
                  className="rounded-[1.25rem] border border-slate-200 bg-slate-50 px-4 py-3"
                >
                  <p className="font-medium text-slate-950">{item.locale}</p>
                  <p className="mt-1 text-sm text-slate-600">{item.state}</p>
                </div>
              ))}
            </div>
          </section>
        </aside>
      </div>
    </div>
  );
}
