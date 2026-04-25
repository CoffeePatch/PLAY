import { createContext, useContext, useState, useCallback } from "react"

/**
 * Toast Context for displaying notifications
 */
const ToastContext = createContext()

/**
 * Toast Provider - wrap your app with this
 */
export function ToastProvider({ children }) {
  const [toasts, setToasts] = useState([])

  const addToast = useCallback(
    (message, type = "info", duration = 4000) => {
      const id = Date.now()
      const newToast = { id, message, type }

      setToasts((prev) => [...prev, newToast])

      // Auto-remove after duration
      if (duration > 0) {
        setTimeout(() => {
          removeToast(id)
        }, duration)
      }

      return id
    },
    []
  )

  const removeToast = useCallback((id) => {
    setToasts((prev) => prev.filter((toast) => toast.id !== id))
  }, [])

  const success = useCallback((message, duration) => addToast(message, "success", duration), [addToast])
  const error = useCallback((message, duration) => addToast(message, "error", duration), [addToast])
  const info = useCallback((message, duration) => addToast(message, "info", duration), [addToast])
  const warning = useCallback((message, duration) => addToast(message, "warning", duration), [addToast])

  const value = {
    toasts,
    addToast,
    removeToast,
    success,
    error,
    info,
    warning,
  }

  return <ToastContext.Provider value={value}>{children}</ToastContext.Provider>
}

/**
 * Hook to use toast notifications
 */
export function useToast() {
  const context = useContext(ToastContext)
  if (!context) {
    throw new Error("useToast must be used within ToastProvider")
  }
  return context
}
