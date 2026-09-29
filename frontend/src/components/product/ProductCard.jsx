import React, { useState } from 'react'
import { Link } from 'react-router-dom'
import { Heart, Star, ShoppingBag, Check } from 'lucide-react'
import { formatCurrency } from '../../utils/formatCurrency'
import { useCart } from '../../context/CartContext'
import RecommendationBadge from '../recommendation/RecommendationBadge'

export default function ProductCard({ product }) {
  const { isInWishlist, toggleWishlist, addToCart } = useCart()
  const [addingToCart, setAddingToCart] = useState(false)
  const [addedJustNow, setAddedJustNow] = useState(false)

  if (!product) return null

  const isSaved = isInWishlist(product.product_id)

  const handleWishlistClick = async (e) => {
    e.preventDefault()
    e.stopPropagation()
    try {
      await toggleWishlist(product.product_id)
    } catch {
      // Wishlist toggle error handled by context
    }
  }

  const handleQuickAddCart = async (e) => {
    e.preventDefault()
    e.stopPropagation()
    if (addingToCart || addedJustNow) return
    setAddingToCart(true)
    try {
      const defaultSize = product.sizes?.[0] || 'M'
      const defaultColor = product.colors?.[0] || 'Default'
      await addToCart(product.product_id, 1, defaultSize, defaultColor)
      setAddedJustNow(true)
      setTimeout(() => setAddedJustNow(false), 2000)
    } catch {
      // Handled by context
    } finally {
      setAddingToCart(false)
    }
  }

  return (
    <div className="group relative bg-white rounded-2xl border border-neutral-200/70 overflow-hidden hover:border-neutral-300 hover:shadow-xl hover:shadow-indigo-900/5 transition-all duration-300 flex flex-col justify-between">
      {/* Product Image Link */}
      <Link to={`/products/${product.product_id}`} className="block relative aspect-[4/5] overflow-hidden bg-neutral-100">
        <img
          src={product.image_url}
          alt={product.name}
          loading="lazy"
          className="w-full h-full object-cover object-center group-hover:scale-105 transition-transform duration-500 ease-out"
          onError={(e) => {
            // Fallback image placeholder
            e.currentTarget.src = `https://picsum.photos/seed/${product.product_id}/400/500`
          }}
        />

        {/* Wishlist Button Overlay */}
        <button
          onClick={handleWishlistClick}
          className={`absolute top-3 right-3 p-2 rounded-full backdrop-blur-md shadow-sm transition-all duration-200 z-10 ${
            isSaved
              ? 'bg-rose-50 text-rose-600 scale-105'
              : 'bg-white/80 hover:bg-white text-neutral-600 hover:text-rose-600 hover:scale-110'
          }`}
          aria-label={isSaved ? 'Remove from wishlist' : 'Save to wishlist'}
        >
          <Heart className={`w-4 h-4 ${isSaved ? 'fill-rose-600 stroke-rose-600' : ''}`} />
        </button>

        {/* Discount Badge */}
        {product.discount_percent > 0 && (
          <span className="absolute top-3 left-3 bg-rose-600 text-white text-[10px] font-extrabold uppercase px-2 py-0.5 rounded-full tracking-wider shadow-xs">
            {product.discount_percent}% OFF
          </span>
        )}

        {/* Quick Add To Cart Hover Button */}
        <div className="absolute inset-x-3 bottom-3 opacity-0 group-hover:opacity-100 transition-opacity duration-200 pointer-events-none group-hover:pointer-events-auto">
          <button
            onClick={handleQuickAddCart}
            disabled={addingToCart || !product.is_available}
            className={`w-full py-2.5 px-4 rounded-xl text-xs font-bold flex items-center justify-center gap-2 shadow-lg transition-all ${
              !product.is_available
                ? 'bg-neutral-300 text-neutral-500 cursor-not-allowed'
                : addedJustNow
                ? 'bg-emerald-600 text-white'
                : 'bg-neutral-900 hover:bg-indigo-600 text-white'
            }`}
          >
            {addedJustNow ? (
              <>
                <Check className="w-3.5 h-3.5" /> Added to Cart
              </>
            ) : addingToCart ? (
              'Adding...'
            ) : !product.is_available ? (
              'Out of Stock'
            ) : (
              <>
                <ShoppingBag className="w-3.5 h-3.5" /> Quick Add
              </>
            )}
          </button>
        </div>
      </Link>

      {/* Product Information */}
      <div className="p-3.5 sm:p-4 flex flex-col flex-1 justify-between gap-2.5">
        <div>
          {/* Brand & Rating */}
          <div className="flex items-center justify-between text-xs mb-1">
            <span className="font-bold text-[11px] tracking-wider uppercase text-neutral-400 truncate max-w-[130px]">
              {product.brand || 'StyleSense'}
            </span>
            {product.rating > 0 && (
              <span className="inline-flex items-center gap-1 font-semibold text-neutral-700 bg-neutral-100 px-1.5 py-0.5 rounded-md text-[11px]">
                <Star className="w-3 h-3 fill-amber-400 stroke-amber-400" />
                {product.rating.toFixed(1)}
              </span>
            )}
          </div>

          {/* Product Title */}
          <Link to={`/products/${product.product_id}`} className="block">
            <h3 className="text-xs sm:text-sm font-semibold text-neutral-800 hover:text-indigo-600 transition-colors line-clamp-1">
              {product.name}
            </h3>
          </Link>

          {/* Recommendation Reason Pill (if provided) */}
          {(product.recommendation_reason || product.recommendation_score) && (
            <div className="mt-1.5">
              <RecommendationBadge
                reason={product.recommendation_reason}
                score={product.recommendation_score}
              />
            </div>
          )}
        </div>

        {/* Pricing */}
        <div className="flex items-baseline gap-2 pt-1 border-t border-neutral-100">
          <span className="text-sm sm:text-base font-bold text-neutral-900">
            {formatCurrency(product.discounted_price || product.price)}
          </span>
          {product.discount_percent > 0 && (
            <span className="text-xs text-neutral-400 line-through">
              {formatCurrency(product.price)}
            </span>
          )}
        </div>
      </div>
    </div>
  )
}
