import { useEffect } from "react"

import { apiClient } from "./api/client"
import MainContent from "./components/layout/MainContent"
import Sidebar from "./components/layout/Sidebar"

function App() {
  useEffect(() => {
    // Warm up HTTP client and surface configuration issues early in development.
    apiClient
      .get("/health", { validateStatus: () => true })
      .catch(() => null)
  }, [])

  return (
    <div className="min-h-screen bg-gradient-to-b from-orange-50 via-stone-100 to-teal-50">
      <div className="mx-auto grid w-full max-w-6xl gap-6 px-4 py-8 lg:grid-cols-[300px_1fr] lg:px-6">
        <Sidebar />
        <MainContent />
      </div>
    </div>
  )
}

export default App
