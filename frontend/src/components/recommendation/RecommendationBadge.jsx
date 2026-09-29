import React from 'react'
import { Sparkles, TrendingUp, Heart, CheckCircle2 } from 'lucide-react'

export default function RecommendationBadge({ reason, score }) {
  if (!reason && !score) return null

  let icon = <Sparkles className="w-3 h-3 text-indigo-500" />
  let bgClass = 'bg-indigo-50 text-indigo-700 border-indigo-200/60'

  if (reason?.toLowerCase().includes('trending')) {
    icon = <TrendingUp className="w-3 h-3 text-amber-500" />
    bgClass = 'bg-amber-50 text-amber-800 border-amber-200/60'
  } else if (reason?.toLowerCase().includes('wishlist')) {
    icon = <Heart className="w-3 h-3 text-rose-500" />
    bgClass = 'bg-rose-50 text-rose-700 border-rose-200/60'
  } else if (reason?.toLowerCase().includes('taste') || reason?.toLowerCase().includes('preferred')) {
    icon = <CheckCircle2 className="w-3 h-3 text-emerald-500" />
    bgClass = 'bg-emerald-50 text-emerald-800 border-emerald-200/60'
  }

  return (
    <div
      className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full border text-[11px] font-medium leading-none ${bgClass}`}
      title={score ? `Confidence score: ${Math.round(score * 100)}%` : undefined}
    >
      {icon}
      <span className="truncate max-w-[200px]">{reason || 'AI Match'}</span>
      {score !== undefined && score !== null && (
        <span className="font-bold opacity-75 ml-0.5">{Math.round(score * 100)}%</span>
      )}
    </div>
  )
}
