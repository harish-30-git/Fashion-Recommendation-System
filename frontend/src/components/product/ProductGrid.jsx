import React from 'react'
import ProductCard from './ProductCard'
import { ProductGridSkeleton } from '../common/LoadingSkeleton'
import { Sparkles, PackageOpen } from 'lucide-react'

export default function ProductGrid({
  products = [],
  loading = false,
  emptyMessage = 'No products found matching your criteria.',
}) {
  if (loading) {
    return <ProductGridSkeleton count={8} />
  }

  if (!products || products.length === 0) {
    return (
      <div className="text-center py-16 px-4 bg-white rounded-2xl border border-neutral-200/80 my-6">
        <div className="w-14 h-14 rounded-full bg-neutral-100 text-neutral-400 flex items-center justify-center mx-auto mb-3">
          <PackageOpen className="w-7 h-7" />
        </div>
        <h4 className="text-base font-bold text-neutral-800 mb-1">No products found</h4>
        <p className="text-xs text-neutral-500 max-w-sm mx-auto">{emptyMessage}</p>
      </div>
    )
  }

  return (
    <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4 sm:gap-6">
      {products.map((product) => (
        <ProductCard key={product.product_id} product={product} />
      ))}
    </div>
  )
}
