const mediaStages = ["Ingestion queue", "Asset review", "Delivery handoff"];

export default function MediaPage() {
  return (
    <div className="space-y-6">
      <section className="rounded-[2rem] border border-slate-200 bg-white p-8 shadow-sm shadow-slate-200/60">
        <p className="text-sm font-medium uppercase tracking-[0.2em] text-slate-500">
          Media
        </p>
        <h1 className="mt-3 text-3xl font-semibold tracking-tight text-slate-950">
          Media library placeholder
        </h1>
        <p className="mt-3 max-w-3xl text-base leading-7 text-slate-600">
          This shell reserves space for asset ingestion, review, and delivery
          workflows while keeping implementation out of scope for this story.
        </p>
      </section>

      <div className="grid gap-6 xl:grid-cols-[minmax(0,2fr)_minmax(18rem,1fr)]">
        <section className="rounded-[2rem] border border-slate-200 bg-white p-8 shadow-sm shadow-slate-200/60">
          <p className="text-sm font-medium uppercase tracking-[0.2em] text-slate-500">
            Asset canvas
          </p>
          <div className="mt-6 grid gap-4 sm:grid-cols-2">
            {Array.from({ length: 4 }).map((_, index) => (
              <div
                key={index}
                className="rounded-[1.75rem] border border-dashed border-slate-300 bg-slate-50 p-6"
              >
                <div className="h-32 rounded-[1.5rem] bg-white" />
                <div className="mt-4 h-4 w-2/3 rounded-full bg-slate-200" />
                <div className="mt-3 h-4 w-1/2 rounded-full bg-slate-200" />
              </div>
            ))}
          </div>
        </section>

        <aside className="rounded-[2rem] border border-slate-200 bg-white p-6 shadow-sm shadow-slate-200/60">
          <p className="text-sm font-medium uppercase tracking-[0.2em] text-slate-500">
            Workflow stages
          </p>
          <ul className="mt-4 space-y-3">
            {mediaStages.map((stage) => (
              <li
                key={stage}
                className="rounded-[1.25rem] bg-slate-100 px-4 py-3 text-sm text-slate-700"
              >
                {stage}
              </li>
            ))}
          </ul>
        </aside>
      </div>
    </div>
  );
}
