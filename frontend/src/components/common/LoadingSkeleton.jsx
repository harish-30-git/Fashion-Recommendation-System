import React from 'react'

export function ProductCardSkeleton() {
  return (
    <div className="bg-white rounded-2xl overflow-hidden border border-neutral-200/80 p-3 shadow-xs animate-pulse">
      <div className="w-full aspect-[4/5] bg-neutral-200 rounded-xl mb-3" />
      <div className="space-y-2">
        <div className="h-3 bg-neutral-200 rounded-sm w-1/3" />
        <div className="h-4 bg-neutral-200 rounded-sm w-3/4" />
        <div className="h-4 bg-neutral-200 rounded-sm w-1/2 pt-1" />
      </div>
    </div>
  )
}

export function ProductGridSkeleton({ count = 8 }) {
  return (
    <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4 sm:gap-6">
      {Array.from({ length: count }).map((_, idx) => (
        <ProductCardSkeleton key={idx} />
      ))}
    </div>
  )
}
