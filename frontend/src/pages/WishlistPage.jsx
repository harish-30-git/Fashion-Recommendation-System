import React, { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { Heart, ArrowRight, Sparkles, Trash2, ShoppingBag } from 'lucide-react'
import { wishlistService } from '../services/wishlistService'
import { useAuth } from '../context/AuthContext'
import { useCart } from '../context/CartContext'
import { formatCurrency } from '../utils/formatCurrency'
import RecommendationRow from '../components/recommendation/RecommendationRow'
import ErrorMessage from '../components/common/ErrorMessage'

export default function WishlistPage() {
  const { isAuthenticated } = useAuth()
  const { addToCart, toggleWishlist } = useCart()

  const [wishlistItems, setWishlistItems] = useState([])
  const [wishlistRecs, setWishlistRecs] = useState([])
  const [loading, setLoading] = useState(true)
  const [loadingRecs, setLoadingRecs] = useState(true)
  const [error, setError] = useState(null)
  const [movingId, setMovingId] = useState(null)

  const fetchWishlistData = async () => {
    if (!isAuthenticated) {
      setLoading(false)
      setLoadingRecs(false)
      return
    }

    setLoading(true)
    setError(null)
    try {
      const items = await wishlistService.getWishlist()
      setWishlistItems(items)

      if (items.length > 0) {
        try {
          const recs = await wishlistService.getWishlistRecommendations(10)
          setWishlistRecs(recs)
        } catch {
          // Safe fallback
        } finally {
          setLoadingRecs(false)
        }
      } else {
        setLoadingRecs(false)
      }
    } catch {
      setError('Failed to load wishlist items.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchWishlistData()
  }, [isAuthenticated])

  const handleMoveToCart = async (product) => {
    setMovingId(product.product_id)
    try {
      await addToCart(product.product_id, 1, product.sizes?.[0] || 'M', product.colors?.[0] || 'Default')
      await toggleWishlist(product.product_id)
      setWishlistItems((prev) => prev.filter((p) => p.product_id !== product.product_id))
    } catch {
      // Error handled
    } finally {
      setMovingId(null)
    }
  }

  const handleRemove = async (productId) => {
    try {
      await toggleWishlist(productId)
      setWishlistItems((prev) => prev.filter((p) => p.product_id !== productId))
    } catch {
      // Error handled
    }
  }

  if (!isAuthenticated) {
    return (
      <div className="max-w-7xl mx-auto px-4 py-20 text-center">
        <div className="w-16 h-16 rounded-full bg-rose-50 text-rose-500 flex items-center justify-center mx-auto mb-4">
          <Heart className="w-8 h-8 fill-rose-500" />
        </div>
        <h2 className="text-xl sm:text-2xl font-serif font-bold text-neutral-900 mb-2">
          Your Wishlist is Empty
        </h2>
        <p className="text-xs sm:text-sm text-neutral-500 max-w-sm mx-auto mb-6">
          Sign in to save items you love, track price drops, and get personalized recommendations based on your wishlist.
        </p>
        <Link
          to="/login"
          className="inline-flex items-center gap-2 px-6 py-3 rounded-full bg-neutral-900 hover:bg-indigo-600 text-white text-xs sm:text-sm font-bold shadow-md transition-all"
        >
          Sign In to Access Wishlist <ArrowRight className="w-4 h-4" />
        </Link>
      </div>
    )
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 sm:py-12 space-y-12">
      {/* Title Bar */}
      <div className="pb-4 border-b border-neutral-200">
        <h1 className="text-2xl sm:text-3xl font-serif font-bold text-neutral-900 tracking-tight">
          My Saved Wishlist
        </h1>
        <p className="text-xs sm:text-sm text-neutral-500 mt-1">
          {wishlistItems.length} {wishlistItems.length === 1 ? 'item' : 'items'} saved
        </p>
      </div>

      {error && <ErrorMessage message={error} onRetry={fetchWishlistData} />}

      {/* Wishlist Items Grid */}
      {loading ? (
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-6 animate-pulse">
          {Array.from({ length: 4 }).map((_, idx) => (
            <div key={idx} className="h-80 bg-neutral-200 rounded-2xl" />
          ))}
        </div>
      ) : wishlistItems.length === 0 ? (
        <div className="text-center py-16 px-4 bg-white rounded-2xl border border-neutral-200/80">
          <div className="w-14 h-14 rounded-full bg-rose-50 text-rose-500 flex items-center justify-center mx-auto mb-3">
            <Heart className="w-7 h-7" />
          </div>
          <h3 className="text-base font-bold text-neutral-900 mb-1">No items in your wishlist yet</h3>
          <p className="text-xs text-neutral-500 max-w-sm mx-auto mb-6">
            Tap the heart icon on any product to save it here for later.
          </p>
          <Link
            to="/products"
            className="inline-flex items-center gap-2 px-5 py-2.5 rounded-full bg-neutral-900 hover:bg-indigo-600 text-white text-xs font-bold transition-all shadow-xs"
          >
            Explore Catalog <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>
      ) : (
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4 sm:gap-6">
          {wishlistItems.map((product) => (
            <div
              key={product.product_id}
              className="bg-white rounded-2xl border border-neutral-200 overflow-hidden flex flex-col justify-between group shadow-xs hover:shadow-md transition-shadow"
            >
              {/* Product Image */}
              <div className="relative aspect-[4/5] bg-neutral-100 overflow-hidden">
                <Link to={`/products/${product.product_id}`}>
                  <img
                    src={product.image_url}
                    alt={product.name}
                    className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                  />
                </Link>
                <button
                  onClick={() => handleRemove(product.product_id)}
                  className="absolute top-3 right-3 p-2 rounded-full bg-white/80 hover:bg-white text-neutral-500 hover:text-rose-600 backdrop-blur-md shadow-xs transition-colors"
                  aria-label="Remove item"
                >
                  <Trash2 className="w-3.5 h-3.5" />
                </button>
              </div>

              {/* Product Info */}
              <div className="p-4 space-y-3 flex-1 flex flex-col justify-between">
                <div>
                  <span className="text-[10px] font-extrabold tracking-wider uppercase text-neutral-400 block mb-1">
                    {product.brand}
                  </span>
                  <Link to={`/products/${product.product_id}`}>
                    <h3 className="text-xs sm:text-sm font-semibold text-neutral-800 hover:text-indigo-600 line-clamp-1">
                      {product.name}
                    </h3>
                  </Link>
                  <div className="flex items-baseline gap-2 pt-2">
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

                {/* Move to Cart Button */}
                <button
                  onClick={() => handleMoveToCart(product)}
                  disabled={movingId === product.product_id || !product.is_available}
                  className="w-full py-2.5 px-3 rounded-xl bg-neutral-900 hover:bg-indigo-600 disabled:bg-neutral-200 disabled:text-neutral-400 text-white font-bold text-xs flex items-center justify-center gap-1.5 transition-colors shadow-xs"
                >
                  {movingId === product.product_id ? (
                    'Moving...'
                  ) : !product.is_available ? (
                    'Out of Stock'
                  ) : (
                    <>
                      <ShoppingBag className="w-3.5 h-3.5" /> Move to Bag
                    </>
                  )}
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Wishlist Recommendations Section */}
      {wishlistItems.length > 0 && (
        <RecommendationRow
          title="Inspired by Your Wishlist"
          subtitle="Products sharing similar style attributes with items you've saved"
          badgeText="Wishlist Similarity"
          products={wishlistRecs}
          loading={loadingRecs}
        />
      )}
    </div>
  )
}
