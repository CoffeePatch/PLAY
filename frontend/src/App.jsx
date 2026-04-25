import { useEffect, useState } from "react"

import { apiClient } from "./api/client"
import MainContent from "./components/layout/MainContent"
import Sidebar from "./components/layout/Sidebar"
import { useMerchants } from "./hooks"

function App() {
  // Manage selected merchant state
  const [selectedMerchantId, setSelectedMerchantId] = useState("")
  const { merchants, loading: merchantsLoading, error: merchantsError } = useMerchants()

  useEffect(() => {
    // Warm up HTTP client and surface configuration issues early in development.
    apiClient
      .get("/health", { validateStatus: () => true })
      .catch(() => null)
  }, [])

  const handleMerchantChange = (merchantId) => {
    setSelectedMerchantId(merchantId)
  }

  useEffect(() => {
    if (!selectedMerchantId && merchants.length > 0) {
      setSelectedMerchantId(merchants[0].id)
    }
  }, [selectedMerchantId, merchants])

  return (
    <div className="min-h-screen bg-gradient-to-b from-orange-50 via-stone-100 to-teal-50">
      <div className="mx-auto grid w-full max-w-6xl gap-6 px-4 py-8 lg:grid-cols-[300px_1fr] lg:px-6">
        <Sidebar
          merchants={merchants}
          merchantsLoading={merchantsLoading}
          merchantsError={merchantsError}
          selectedMerchantId={selectedMerchantId}
          onMerchantChange={handleMerchantChange}
        />
        <MainContent merchantId={selectedMerchantId} />
      </div>
    </div>
  )
}

export default App
