/**
 * Sidebar component with merchant selector
 * @param {string} selectedMerchantId - Currently selected merchant ID
 * @param {function} onMerchantChange - Callback when merchant selection changes
 */
export default function Sidebar({
  merchants,
  merchantsLoading,
  merchantsError,
  selectedMerchantId,
  onMerchantChange,
}) {
  const selectedMerchant = merchants.find((m) => m.id === selectedMerchantId)

  return (
    <aside className="relative overflow-hidden rounded-3xl border border-stone-200 bg-stone-50 p-6 shadow-sm h-fit sticky top-8">
      <div className="pointer-events-none absolute -right-16 -top-16 h-40 w-40 rounded-full bg-orange-200/40 blur-2xl" />
      <div className="pointer-events-none absolute -bottom-20 -left-12 h-48 w-48 rounded-full bg-teal-200/40 blur-2xl" />

      <div className="relative space-y-6">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.2em] text-stone-500">Merchant</p>
          <h2 className="mt-2 text-2xl font-semibold text-stone-900">Payout Console</h2>
        </div>

        <label className="block space-y-2">
          <span className="text-sm font-medium text-stone-700">Select merchant</span>
          <select
            value={selectedMerchantId}
            onChange={(e) => onMerchantChange(e.target.value)}
            disabled={merchantsLoading || merchants.length === 0}
            className="w-full rounded-xl border border-stone-300 bg-white px-3 py-2 text-sm text-stone-900 outline-none ring-orange-300 transition focus:ring-2"
          >
            {merchantsLoading && <option value="">Loading merchants...</option>}
            {!merchantsLoading && merchants.length === 0 && (
              <option value="">No merchants found</option>
            )}
            {merchants.map((merchant) => (
              <option key={merchant.id} value={merchant.id}>
                {merchant.name}
              </option>
            ))}
          </select>
        </label>

        {merchantsError && (
          <div className="rounded-2xl border border-red-200 bg-red-50 p-3">
            <p className="text-xs font-medium text-red-900">Failed to load merchants.</p>
          </div>
        )}

        {selectedMerchant && (
          <div className="rounded-2xl bg-white p-4 ring-1 ring-stone-200">
            <p className="text-xs font-semibold uppercase tracking-[0.16em] text-stone-500">
              Current Merchant
            </p>
            <p className="mt-2 text-sm font-medium text-stone-900">{selectedMerchant.name}</p>
            <p className="mt-1 text-xs text-stone-500 font-mono">{selectedMerchant.id}</p>
          </div>
        )}

        <div className="rounded-2xl bg-white p-4 ring-1 ring-stone-200">
          <p className="text-xs font-semibold uppercase tracking-[0.16em] text-stone-500">API</p>
          <p className="mt-2 text-sm text-stone-700">
            Base URL is configured through Vite env and loaded via Axios interceptors.
          </p>
        </div>
      </div>
    </aside>
  )
}
