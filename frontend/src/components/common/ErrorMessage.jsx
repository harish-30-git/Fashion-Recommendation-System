import React from 'react'
import { AlertCircle, RefreshCw } from 'lucide-react'

export default function ErrorMessage({ title = 'Something went wrong', message, onRetry }) {
  return (
    <div className="rounded-2xl bg-rose-50 border border-rose-200/80 p-6 text-center max-w-md mx-auto my-8">
      <div className="w-12 h-12 rounded-full bg-rose-100 text-rose-600 flex items-center justify-center mx-auto mb-3">
        <AlertCircle className="w-6 h-6" />
      </div>
      <h3 className="text-sm font-bold text-rose-900 mb-1">{title}</h3>
      <p className="text-xs text-rose-700 leading-relaxed mb-4">
        {message || 'Unable to connect to the backend server. Please check your network or try again.'}
      </p>
      {onRetry && (
        <button
          onClick={onRetry}
          className="inline-flex items-center gap-1.5 px-4 py-2 rounded-full bg-rose-600 hover:bg-rose-700 text-white text-xs font-semibold shadow-xs transition-colors"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          Retry
        </button>
      )}
    </div>
  )
}
