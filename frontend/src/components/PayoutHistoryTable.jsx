import { formatPaiseToRupees, formatShortDate, truncateText } from "../utils/formatting"
import { PAYOUT_STATUS_COLORS } from "../utils/constants"

/**
 * Status badge for payout status
 */
function StatusBadge({ status }) {
  const style = PAYOUT_STATUS_COLORS[status] || PAYOUT_STATUS_COLORS.PENDING

  return (
    <span className={`inline-flex items-center gap-1 rounded-full px-2.5 py-1 text-xs font-semibold ${style.badge}`}>
      <span className="text-[10px]">{style.icon}</span>
      {status}
    </span>
  )
}

/**
 * Payout row component
 */
function PayoutRow({ payout }) {
  const accountDisplay = payout.bank_account?.account_number || payout.bank_account_id || "-"

  return (
    <tr className="border-b border-stone-200 transition hover:bg-stone-50">
      <td className="px-4 py-3 text-sm text-stone-900">
        {formatShortDate(payout.created_at)}
      </td>
      <td className="px-4 py-3 text-right font-semibold text-stone-900">
        {formatPaiseToRupees(payout.amount_paise)}
      </td>
      <td className="px-4 py-3 text-sm text-stone-700 font-mono">
        {truncateText(accountDisplay, 20)}
      </td>
      <td className="px-4 py-3">
        <StatusBadge status={payout.status} />
      </td>
      <td className="px-4 py-3 text-center text-sm font-medium text-stone-700">
        {payout.attempts ?? 0}
      </td>
    </tr>
  )
}

/**
 * Pagination controls
 */
function PaginationControls({ currentPage, totalPages, loading, onPrevious, onNext }) {
  if (totalPages <= 1) return null

  return (
    <div className="flex flex-wrap items-center justify-between gap-4 border-t border-stone-200 pt-4">
      <div className="text-sm text-stone-600">
        Page {currentPage} of {totalPages}
      </div>
      <div className="flex gap-2">
        <button
          onClick={onPrevious}
          disabled={currentPage === 1 || loading}
          className="rounded-lg border border-stone-300 bg-white px-3 py-1 text-sm font-medium text-stone-700 hover:bg-stone-50 disabled:opacity-50 disabled:cursor-not-allowed transition"
        >
          ← Previous
        </button>
        <button
          onClick={onNext}
          disabled={currentPage === totalPages || loading}
          className="rounded-lg border border-stone-300 bg-white px-3 py-1 text-sm font-medium text-stone-700 hover:bg-stone-50 disabled:opacity-50 disabled:cursor-not-allowed transition"
        >
          Next →
        </button>
      </div>
    </div>
  )
}

/**
 * Payout history table component
 * @param {array} payouts - Array of payout records
 * @param {boolean} loading - Loading state
 * @param {string} error - Error message
 * @param {number} currentPage - Current page
 * @param {number} totalPages - Total pages
 * @param {function} onNextPage - Next page handler
 * @param {function} onPrevPage - Previous page handler
 * @param {function} onRefresh - Refresh handler
 */
export default function PayoutHistoryTable({
  payouts,
  loading,
  error,
  currentPage,
  totalPages,
  onNextPage,
  onPrevPage,
  onRefresh,
}) {
  if (error) {
    return (
      <section className="rounded-2xl border border-red-200 bg-red-50 p-5">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="font-semibold text-red-900">Payout History Error</h3>
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
    <section className="rounded-2xl border border-stone-200 bg-white p-0 shadow-sm overflow-hidden">
      <div className="p-5 pb-0">
        <h2 className="text-lg font-semibold text-stone-900">Payout History</h2>
        <p className="mt-1 text-sm text-stone-600">
          Live status updates every 5 seconds
        </p>
      </div>

      {!loading && payouts.length === 0 ? (
        <div className="p-5">
          <p className="text-sm text-stone-600">No payouts yet. Submit your first payout request above.</p>
        </div>
      ) : (
        <>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-stone-200 bg-stone-50">
                  <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-stone-700">
                    Date
                  </th>
                  <th className="px-4 py-3 text-right text-xs font-semibold uppercase tracking-wide text-stone-700">
                    Amount
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-stone-700">
                    Bank Account
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-stone-700">
                    Status
                  </th>
                  <th className="px-4 py-3 text-center text-xs font-semibold uppercase tracking-wide text-stone-700">
                    Attempts
                  </th>
                </tr>
              </thead>
              <tbody>
                {loading && payouts.length === 0 ? (
                  Array.from({ length: 4 }).map((_, i) => (
                    <tr key={`skeleton-${i}`} className="border-b border-stone-200">
                      <td colSpan={5} className="px-4 py-3">
                        <div className="h-4 w-32 animate-pulse rounded bg-stone-200" />
                      </td>
                    </tr>
                  ))
                ) : (
                  payouts.map((payout) => (
                    <PayoutRow key={payout.id || `${payout.created_at}-${payout.amount_paise}`} payout={payout} />
                  ))
                )}
              </tbody>
            </table>
          </div>

          <div className="p-5">
            <PaginationControls
              currentPage={currentPage}
              totalPages={totalPages}
              loading={loading}
              onPrevious={onPrevPage}
              onNext={onNextPage}
            />
          </div>
        </>
      )}
    </section>
  )
}
