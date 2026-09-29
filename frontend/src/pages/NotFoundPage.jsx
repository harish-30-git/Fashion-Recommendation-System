import React from 'react'
import { Link } from 'react-router-dom'
import { Compass, ArrowRight } from 'lucide-react'

export default function NotFoundPage() {
  return (
    <div className="min-h-[70vh] flex items-center justify-center px-4 py-20 text-center">
      <div className="max-w-md space-y-4">
        <div className="w-16 h-16 rounded-full bg-neutral-100 text-neutral-400 flex items-center justify-center mx-auto mb-2">
          <Compass className="w-8 h-8" />
        </div>
        <span className="text-4xl sm:text-5xl font-extrabold text-neutral-900 tracking-tight font-serif">
          404
        </span>
        <h2 className="text-lg sm:text-xl font-bold text-neutral-800">Page Not Found</h2>
        <p className="text-xs sm:text-sm text-neutral-500 leading-relaxed">
          The page or product category you are looking for doesn't exist or has moved.
        </p>
        <div className="pt-2">
          <Link
            to="/"
            className="inline-flex items-center gap-2 px-6 py-3 rounded-full bg-neutral-900 hover:bg-indigo-600 text-white text-xs sm:text-sm font-bold shadow-md transition-all"
          >
            Return to Home <ArrowRight className="w-4 h-4" />
          </Link>
        </div>
      </div>
    </div>
  )
}
