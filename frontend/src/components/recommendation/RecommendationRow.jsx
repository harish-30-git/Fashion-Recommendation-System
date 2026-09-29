import React, { useRef } from 'react'
import { Sparkles, ChevronLeft, ChevronRight } from 'lucide-react'
import ProductCard from '../product/ProductCard'
import { ProductCardSkeleton } from '../common/LoadingSkeleton'

export default function RecommendationRow({
  title,
  subtitle,
  badgeText = 'AI Match',
  products = [],
  loading = false,
}) {
  const scrollContainerRef = useRef(null)

  const scroll = (direction) => {
    if (scrollContainerRef.current) {
      const scrollAmount = 320 * 2
      scrollContainerRef.current.scrollBy({
        left: direction === 'left' ? -scrollAmount : scrollAmount,
        behavior: 'smooth',
      })
    }
  }

  if (!loading && (!products || products.length === 0)) {
    return null
  }

  return (
    <section className="py-8 sm:py-10">
      {/* Header */}
      <div className="flex items-end justify-between mb-6 px-1">
        <div>
          {badgeText && (
            <div className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-indigo-50 border border-indigo-200 text-indigo-700 text-[11px] font-bold tracking-wide uppercase mb-2">
              <Sparkles className="w-3 h-3 text-indigo-600" />
              {badgeText}
            </div>
          )}
          <h2 className="text-xl sm:text-2xl font-serif font-bold text-neutral-900 tracking-tight">
            {title}
          </h2>
          {subtitle && <p className="text-xs sm:text-sm text-neutral-500 mt-1">{subtitle}</p>}
        </div>

        {/* Scroll Controls (Desktop) */}
        <div className="hidden sm:flex items-center gap-2">
          <button
            onClick={() => scroll('left')}
            className="p-2 rounded-full border border-neutral-200 hover:border-neutral-300 bg-white hover:bg-neutral-50 text-neutral-700 transition-colors shadow-xs"
            aria-label="Scroll left"
          >
            <ChevronLeft className="w-4 h-4" />
          </button>
          <button
            onClick={() => scroll('right')}
            className="p-2 rounded-full border border-neutral-200 hover:border-neutral-300 bg-white hover:bg-neutral-50 text-neutral-700 transition-colors shadow-xs"
            aria-label="Scroll right"
          >
            <ChevronRight className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Horizontal Tray */}
      <div
        ref={scrollContainerRef}
        className="flex gap-4 sm:gap-6 overflow-x-auto pb-4 pt-1 px-1 scrollbar-none snap-x snap-mandatory"
        style={{ scrollbarWidth: 'none', msOverflowStyle: 'none' }}
      >
        {loading
          ? Array.from({ length: 5 }).map((_, idx) => (
              <div key={idx} className="min-w-[220px] sm:min-w-[260px] snap-start flex-shrink-0">
                <ProductCardSkeleton />
              </div>
            ))
          : products.map((product) => (
              <div
                key={product.product_id}
                className="min-w-[220px] sm:min-w-[260px] max-w-[260px] snap-start flex-shrink-0"
              >
                <ProductCard product={product} />
              </div>
            ))}
      </div>
    </section>
  )
}
