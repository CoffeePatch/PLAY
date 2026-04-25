import { formatPaiseToRupees, formatShortDate, truncateText } from "../utils/formatting"
import { getColorScheme } from "../utils/constants"

/**
 * Pagination controls component
 */
function PaginationControls({
  currentPage,
  totalPages,
  loading,
  onPrevious,
  onNext,
  onPageChange,
}) {
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
 * Ledger entry row component
 */
function LedgerRow({ entry }) {
  const colorScheme = getColorScheme(entry.entry_type)

  return (
    <tr className="border-b border-stone-200 transition hover:bg-stone-50">
      <td className="px-4 py-3 text-sm text-stone-900">
        {formatShortDate(entry.created_at)}
      </td>
      <td className="px-4 py-3">
        <span className={`inline-block rounded-full px-3 py-1 text-xs font-semibold ${colorScheme.badge}`}>
          {entry.entry_type}
        </span>
      </td>
      <td className="px-4 py-3 text-right font-semibold text-stone-900">
        {entry.entry_type === "CREDIT" || entry.entry_type === "RELEASE" ? "+" : "−"}
        {formatPaiseToRupees(entry.amount_paise)}
      </td>
      <td className="px-4 py-3 text-sm text-stone-700">
        {truncateText(entry.description, 40)}
      </td>
      <td className="px-4 py-3 text-xs text-stone-500 font-mono">
        {entry.reference_id ? truncateText(entry.reference_id, 20) : "—"}
      </td>
    </tr>
  )
}

/**
 * Ledger table component with pagination and color-coding
 * @param {array} entries - Array of ledger entries
 * @param {boolean} loading - Loading state
 * @param {string} error - Error message if any
 * @param {number} currentPage - Current page number
 * @param {number} totalPages - Total number of pages
 * @param {boolean} hasNextPage - Whether next page exists
 * @param {boolean} hasPrevPage - Whether previous page exists
 * @param {function} onNextPage - Next page callback
 * @param {function} onPrevPage - Previous page callback
 * @param {function} onRefresh - Optional refresh callback
 */
export default function LedgerTable({
  entries,
  loading,
  error,
  currentPage,
  totalPages,
  hasNextPage,
  hasPrevPage,
  onNextPage,
  onPrevPage,
  onRefresh,
}) {
  // Error state
  if (error) {
    return (
      <section className="rounded-2xl border border-red-200 bg-red-50 p-5">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="font-semibold text-red-900">Ledger Error</h3>
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

  // Empty state
  if (!loading && entries.length === 0) {
    return (
      <section className="rounded-2xl border border-dashed border-stone-300 bg-stone-50 p-5">
        <h2 className="text-lg font-semibold text-stone-900">No transactions yet</h2>
        <p className="mt-2 text-sm text-stone-600">
          Transaction history will appear here once payouts are processed.
        </p>
      </section>
    )
  }

  return (
    <section className="rounded-2xl border border-stone-200 bg-white p-0 shadow-sm overflow-hidden">
      <div className="p-5 pb-0">
        <h2 className="text-lg font-semibold text-stone-900">Transaction History</h2>
        <p className="mt-1 text-sm text-stone-600">
          Recent ledger entries with automatic refresh every 10s
        </p>
      </div>

      {/* Table */}
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="border-b border-stone-200 bg-stone-50">
              <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-stone-700">
                Date
              </th>
              <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-stone-700">
                Type
              </th>
              <th className="px-4 py-3 text-right text-xs font-semibold uppercase tracking-wide text-stone-700">
                Amount
              </th>
              <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-stone-700">
                Description
              </th>
              <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-stone-700">
                Reference
              </th>
            </tr>
          </thead>
          <tbody>
            {loading && entries.length === 0 ? (
              // Loading skeleton
              Array.from({ length: 5 }).map((_, i) => (
                <tr key={`skeleton-${i}`} className="border-b border-stone-200">
                  <td colSpan={5} className="px-4 py-3">
                    <div className="h-4 w-32 animate-pulse rounded bg-stone-200" />
                  </td>
                </tr>
              ))
            ) : (
              // Actual entries
              entries.map((entry) => (
                <LedgerRow key={entry.id || entry.created_at} entry={entry} />
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      <div className="p-5">
        <PaginationControls
          currentPage={currentPage}
          totalPages={totalPages}
          loading={loading}
          onPrevious={onPrevPage}
          onNext={onNextPage}
        />
      </div>

      {/* Live update indicator */}
      <div className="border-t border-stone-200 bg-stone-50 px-5 py-2">
        <p className="flex items-center gap-2 text-xs text-stone-600">
          <span className="inline-block h-2 w-2 rounded-full bg-green-500 animate-pulse" />
          Auto-refreshing every 10 seconds
        </p>
      </div>
    </section>
  )
}
