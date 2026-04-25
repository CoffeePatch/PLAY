import { useToast } from "../context/ToastContext"

/**
 * Single toast notification component
 */
function Toast({ message, type, onClose }) {
  const typeStyles = {
    success: {
      bg: "bg-green-50",
      border: "border-green-200",
      text: "text-green-900",
      icon: "✓",
      iconBg: "bg-green-100",
    },
    error: {
      bg: "bg-red-50",
      border: "border-red-200",
      text: "text-red-900",
      icon: "✕",
      iconBg: "bg-red-100",
    },
    info: {
      bg: "bg-blue-50",
      border: "border-blue-200",
      text: "text-blue-900",
      icon: "ℹ",
      iconBg: "bg-blue-100",
    },
    warning: {
      bg: "bg-amber-50",
      border: "border-amber-200",
      text: "text-amber-900",
      icon: "⚠",
      iconBg: "bg-amber-100",
    },
  }

  const style = typeStyles[type] || typeStyles.info

  return (
    <div
      className={`flex items-start gap-3 rounded-lg border ${style.bg} ${style.border} p-4 shadow-md animate-in fade-in slide-in-from-top-2 duration-300`}
    >
      <div className={`flex-shrink-0 flex h-6 w-6 items-center justify-center rounded-full ${style.iconBg} text-sm font-bold ${style.text}`}>
        {style.icon}
      </div>
      <div className="flex-1">
        <p className={`text-sm font-medium ${style.text}`}>{message}</p>
      </div>
      <button
        onClick={onClose}
        className="flex-shrink-0 inline-flex text-gray-400 hover:text-stone-900 focus:outline-none transition"
      >
        <span className="sr-only">Close</span>
        <span className="text-xl">×</span>
      </button>
    </div>
  )
}

/**
 * Toast container - displays all active toasts
 */
export function ToastContainer() {
  const { toasts, removeToast } = useToast()

  return (
    <div className="fixed top-4 right-4 z-50 space-y-3 pointer-events-none">
      {toasts.map((toast) => (
        <div key={toast.id} className="pointer-events-auto">
          <Toast
            message={toast.message}
            type={toast.type}
            onClose={() => removeToast(toast.id)}
          />
        </div>
      ))}
    </div>
  )
}
