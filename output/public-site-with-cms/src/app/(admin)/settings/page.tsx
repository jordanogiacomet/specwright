const settingAreas = [
  "Editorial defaults",
  "Publishing controls",
  "Delivery preferences",
];

export default function SettingsPage() {
  return (
    <div className="space-y-6">
      <section className="rounded-[2rem] border border-slate-200 bg-white p-8 shadow-sm shadow-slate-200/60">
        <p className="text-sm font-medium uppercase tracking-[0.2em] text-slate-500">
          Settings
        </p>
        <h1 className="mt-3 text-3xl font-semibold tracking-tight text-slate-950">
          Platform settings placeholder
        </h1>
        <p className="mt-3 max-w-3xl text-base leading-7 text-slate-600">
          This reserved area anchors future editorial and delivery settings
          without expanding the scope into real configuration management.
        </p>
      </section>

      <div className="grid gap-4 lg:grid-cols-3">
        {settingAreas.map((area) => (
          <section
            key={area}
            className="rounded-[2rem] border border-slate-200 bg-white p-6 shadow-sm shadow-slate-200/60"
          >
            <p className="text-xs font-medium uppercase tracking-[0.18em] text-slate-500">
              Reserved area
            </p>
            <h2 className="mt-3 text-xl font-semibold tracking-tight text-slate-950">
              {area}
            </h2>
            <div className="mt-5 space-y-3">
              <div className="h-4 w-4/5 rounded-full bg-slate-200" />
              <div className="h-4 w-full rounded-full bg-slate-200" />
              <div className="h-4 w-3/5 rounded-full bg-slate-200" />
            </div>
          </section>
        ))}
      </div>
    </div>
  );
}
