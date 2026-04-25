import { formatPaiseToRupees } from "../utils/formatting"

/**
 * Balance card component displaying available, held, and total balance
 * @param {object} balance - Balance object with available_paise, held_paise, total_paise
 * @param {boolean} loading - Loading state
 * @param {string} error - Error message if any
 * @param {function} onRefresh - Optional refresh callback
 */
export default function BalanceCard({ balance, loading, error, onRefresh }) {
  const balanceCards = [
    {
      title: "Available",
      value: balance.available_paise,
      tone: "bg-emerald-100 text-emerald-900",
      description: "Ready to payout",
    },
    {
      title: "Held",
      value: balance.held_paise,
      tone: "bg-amber-100 text-amber-900",
      description: "Processing payouts",
    },
    {
      title: "Total",
      value: balance.total_paise,
      tone: "bg-sky-100 text-sky-900",
      description: "Account balance",
    },
  ]

  if (error) {
    return (
      <section className="rounded-2xl border border-red-200 bg-red-50 p-5">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="font-semibold text-red-900">Balance Error</h3>
            <p className="mt-1 text-sm text-red-800">{error}</p>
          </div>
          {onRefresh && (
            <button
              onClick={onRefresh}
              className="rounded-lg bg-red-200 px-3 py-1 text-sm font-medium text-red-900 hover:bg-red-300 transition"
            >
              Retry
            </button>
          )}
        </div>
      </section>
    )
  }

  return (
    <section className="grid gap-4 sm:grid-cols-3">
      {balanceCards.map((card) => (
        <article
          key={card.title}
          className={`rounded-2xl p-4 ${card.tone} transition ${loading ? "opacity-50" : ""}`}
        >
          <div className="flex items-start justify-between">
            <div className="flex-1">
              <p className="text-xs font-semibold uppercase tracking-[0.14em]">
                {card.title}
              </p>
              <p className="mt-3 text-2xl font-semibold">
                {loading ? (
                  <span className="inline-block h-8 w-24 animate-pulse rounded bg-current opacity-20" />
                ) : (
                  formatPaiseToRupees(card.value)
                )}
              </p>
              <p className="mt-2 text-xs opacity-75">{card.description}</p>
            </div>
          </div>
        </article>
      ))}
    </section>
  )
}
