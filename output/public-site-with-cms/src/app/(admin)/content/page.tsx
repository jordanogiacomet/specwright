import Link from "next/link";

const contentItems = [
  {
    href: "/content/homepage-hero",
    status: "Draft",
    surface: "Public site",
    title: "Homepage Hero",
    type: "Landing page module",
    updatedAt: "Updated 2h ago",
  },
  {
    href: "/content/spring-campaign",
    status: "In review",
    surface: "Campaign page",
    title: "Spring Campaign",
    type: "Article feature",
    updatedAt: "Updated 6h ago",
  },
  {
    href: "/content/editorial-calendar",
    status: "Scheduled",
    surface: "Editorial program",
    title: "Editorial Calendar",
    type: "Planning document",
    updatedAt: "Updated yesterday",
  },
];

const summaryCards = [
  {
    label: "Visible routes",
    value: "3",
  },
  {
    label: "Placeholder entries",
    value: `${contentItems.length}`,
  },
  {
    label: "Public capability",
    value: "Enabled",
  },
];

export default function ContentPage() {
  return (
    <div className="space-y-6">
      <section className="rounded-[2rem] border border-slate-200 bg-white p-8 shadow-sm shadow-slate-200/60">
        <div className="flex flex-col gap-6 lg:flex-row lg:items-end lg:justify-between">
          <div className="max-w-3xl space-y-3">
            <p className="text-sm font-medium uppercase tracking-[0.2em] text-slate-500">
              Content
            </p>
            <h1 className="text-3xl font-semibold tracking-tight text-slate-950">
              Editorial queue shell
            </h1>
            <p className="text-base leading-7 text-slate-600">
              This route establishes the admin content surface with placeholder
              list and detail patterns. It is intentionally static until CRUD
              stories wire real CMS data into the shell.
            </p>
          </div>

          <div className="grid gap-3 sm:grid-cols-3">
            {summaryCards.map((card) => (
              <div
                key={card.label}
                className="rounded-[1.5rem] bg-slate-100 px-4 py-4 text-left"
              >
                <p className="text-xs font-medium uppercase tracking-[0.18em] text-slate-500">
                  {card.label}
                </p>
                <p className="mt-2 text-2xl font-semibold tracking-tight text-slate-950">
                  {card.value}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <div className="grid gap-6 xl:grid-cols-[minmax(0,2fr)_minmax(18rem,1fr)]">
        <section className="rounded-[2rem] border border-slate-200 bg-white p-8 shadow-sm shadow-slate-200/60">
          <div className="flex items-center justify-between gap-4">
            <div>
              <p className="text-sm font-medium uppercase tracking-[0.2em] text-slate-500">
                Content list
              </p>
              <h2 className="mt-2 text-2xl font-semibold tracking-tight text-slate-950">
                Placeholder entries
              </h2>
            </div>
            <p className="text-sm text-slate-500">No persistence in this story</p>
          </div>

          <div className="mt-6 space-y-4">
            {contentItems.map((item) => (
              <Link
                key={item.href}
                href={item.href}
                className="group block rounded-[1.75rem] border border-slate-200 bg-slate-50 p-5 transition hover:border-slate-300 hover:bg-white"
              >
                <div className="flex flex-wrap items-center gap-3">
                  <span className="rounded-full bg-slate-950 px-3 py-1 text-xs font-medium uppercase tracking-[0.18em] text-white">
                    {item.status}
                  </span>
                  <span className="text-xs font-medium uppercase tracking-[0.18em] text-slate-500">
                    {item.surface}
                  </span>
                </div>
                <div className="mt-4 flex flex-col gap-3 md:flex-row md:items-end md:justify-between">
                  <div>
                    <h3 className="text-xl font-semibold tracking-tight text-slate-950">
                      {item.title}
                    </h3>
                    <p className="mt-2 text-sm leading-6 text-slate-600">
                      {item.type}
                    </p>
                  </div>
                  <div className="text-sm text-slate-500">
                    <p>{item.updatedAt}</p>
                    <p className="mt-1 font-medium text-slate-700 group-hover:text-slate-950">
                      Open placeholder detail
                    </p>
                  </div>
                </div>
              </Link>
            ))}
          </div>
        </section>

        <aside className="space-y-6">
          <section className="rounded-[2rem] border border-slate-200 bg-white p-6 shadow-sm shadow-slate-200/60">
            <p className="text-sm font-medium uppercase tracking-[0.2em] text-slate-500">
              Detail view
            </p>
            <h2 className="mt-2 text-xl font-semibold tracking-tight text-slate-950">
              Ready for deeper routing
            </h2>
            <p className="mt-3 text-sm leading-6 text-slate-600">
              Each entry opens a placeholder detail page so the editorial shell
              can be reviewed before real authoring fields are added.
            </p>
          </section>

          <section className="rounded-[2rem] border border-dashed border-slate-300 bg-slate-50 p-6">
            <p className="text-sm font-medium uppercase tracking-[0.2em] text-slate-500">
              Next stories
            </p>
            <ul className="mt-4 space-y-3 text-sm leading-6 text-slate-600">
              <li>Connect list rows to CMS collections and filters.</li>
              <li>Replace placeholder counts with live editorial metrics.</li>
              <li>Populate detail panes with authored fields and actions.</li>
            </ul>
          </section>
        </aside>
      </div>
    </div>
  );
}
