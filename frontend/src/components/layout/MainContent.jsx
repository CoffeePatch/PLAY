import { useBalance } from "../../hooks/useBalance"
import { useLedger } from "../../hooks/useLedger"
import { usePayoutHistory } from "../../hooks/usePayoutHistory"
import BalanceCard from "../BalanceCard"
import LedgerTable from "../LedgerTable"
import PayoutForm from "../PayoutForm"
import PayoutHistoryTable from "../PayoutHistoryTable"

/**
 * Main content area displaying balance and ledger information
 * @param {string} merchantId - Selected merchant ID
 */
export default function MainContent({ merchantId }) {
  // Fetch balance data with polling
  const {
    balance,
    loading: balanceLoading,
    error: balanceError,
    refetch: refetchBalance,
  } = useBalance(merchantId)

  // Fetch ledger data with pagination and polling
  const {
    entries,
    currentPage,
    totalPages,
    loading: ledgerLoading,
    error: ledgerError,
    nextPage,
    prevPage,
    refetch: refetchLedger,
    hasNextPage,
    hasPrevPage,
  } = useLedger(merchantId)

  const {
    payouts,
    currentPage: payoutsPage,
    totalPages: payoutsTotalPages,
    loading: payoutsLoading,
    error: payoutsError,
    nextPage: nextPayoutPage,
    prevPage: prevPayoutPage,
    refetch: refetchPayouts,
  } = usePayoutHistory(merchantId)

  const handlePayoutSubmitted = () => {
    refetchBalance()
    refetchLedger()
    refetchPayouts()
  }

  if (!merchantId) {
    return (
      <main className="space-y-6 rounded-3xl border border-stone-200 bg-white p-6 shadow-sm">
        <header className="flex flex-wrap items-end justify-between gap-4">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.2em] text-stone-500">
              Dashboard
            </p>
            <h1 className="mt-2 text-3xl font-semibold text-stone-900">
              Merchant Operations
            </h1>
          </div>
        </header>
        <section className="rounded-2xl border border-dashed border-stone-300 bg-stone-50 p-5">
          <h2 className="text-lg font-semibold text-stone-900">Select a merchant to continue</h2>
          <p className="mt-2 text-sm text-stone-700">
            Once a merchant is selected, balance, ledger, payout form, and payout history will load automatically.
          </p>
        </section>
      </main>
    )
  }

  return (
    <main className="space-y-6 rounded-3xl border border-stone-200 bg-white p-6 shadow-sm">
      {/* Header */}
      <header className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.2em] text-stone-500">
            Dashboard
          </p>
          <h1 className="mt-2 text-3xl font-semibold text-stone-900">
            Merchant Operations
          </h1>
        </div>
        <span className="rounded-xl bg-stone-900 px-4 py-2 text-sm font-medium text-white">
          Live Dashboard
        </span>
      </header>

      {/* Balance Cards */}
      <BalanceCard
        balance={balance}
        loading={balanceLoading}
        error={balanceError}
        onRefresh={refetchBalance}
      />

      {/* Ledger Table */}
      <LedgerTable
        entries={entries}
        loading={ledgerLoading}
        error={ledgerError}
        currentPage={currentPage}
        totalPages={totalPages}
        hasNextPage={hasNextPage}
        hasPrevPage={hasPrevPage}
        onNextPage={nextPage}
        onPrevPage={prevPage}
        onRefresh={refetchLedger}
      />

      <section className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_minmax(0,1fr)]">
        <PayoutForm
          merchantId={merchantId}
          availableBalance={balance.available_paise}
          onPayoutSubmitted={handlePayoutSubmitted}
        />
        <PayoutHistoryTable
          payouts={payouts}
          loading={payoutsLoading}
          error={payoutsError}
          currentPage={payoutsPage}
          totalPages={payoutsTotalPages}
          onNextPage={nextPayoutPage}
          onPrevPage={prevPayoutPage}
          onRefresh={refetchPayouts}
        />
      </section>
    </main>
  )
}
