const cards = [
  { title: "Available", value: "Rs 12,450.00", tone: "bg-emerald-100 text-emerald-900" },
  { title: "Held", value: "Rs 3,200.00", tone: "bg-amber-100 text-amber-900" },
  { title: "Total", value: "Rs 15,650.00", tone: "bg-sky-100 text-sky-900" },
]

export default function MainContent() {
  return (
    <main className="space-y-6 rounded-3xl border border-stone-200 bg-white p-6 shadow-sm">
      <header className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.2em] text-stone-500">Dashboard</p>
          <h1 className="mt-2 text-3xl font-semibold text-stone-900">Merchant Operations</h1>
        </div>
        <button className="rounded-xl bg-stone-900 px-4 py-2 text-sm font-medium text-white transition hover:bg-stone-700">
          Request Payout
        </button>
      </header>

      <section className="grid gap-4 sm:grid-cols-3">
        {cards.map((card) => (
          <article key={card.title} className={`rounded-2xl p-4 ${card.tone}`}>
            <p className="text-xs font-semibold uppercase tracking-[0.14em]">{card.title}</p>
            <p className="mt-3 text-2xl font-semibold">{card.value}</p>
          </article>
        ))}
      </section>

      <section className="rounded-2xl border border-dashed border-stone-300 bg-stone-50 p-5">
        <h2 className="text-lg font-semibold text-stone-900">Ready for live API data</h2>
        <p className="mt-2 text-sm text-stone-700">
          This shell is wired for backend integration and will be expanded with balance polling, ledger history, and payout actions in the next tasks.
        </p>
      </section>
    </main>
  )
}
