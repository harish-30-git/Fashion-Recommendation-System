import React, { useState, useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
import {
  Heart,
  Star,
  ShoppingBag,
  ShieldCheck,
  Truck,
  RotateCcw,
  Sparkles,
  Check,
  ChevronRight,
  Info,
} from 'lucide-react'
import { productService } from '../services/productService'
import { recommendationService } from '../services/recommendationService'
import { interactionService } from '../services/interactionService'
import { useCart } from '../context/CartContext'
import { useAuth } from '../context/AuthContext'
import { formatCurrency } from '../utils/formatCurrency'
import RecommendationRow from '../components/recommendation/RecommendationRow'
import ErrorMessage from '../components/common/ErrorMessage'

export default function ProductDetailPage() {
  const { id } = useParams()
  const { isInWishlist, toggleWishlist, addToCart } = useCart()
  const { isAuthenticated } = useAuth()

  const [product, setProduct] = useState(null)
  const [selectedImage, setSelectedImage] = useState('')
  const [selectedSize, setSelectedSize] = useState('')
  const [selectedColor, setSelectedColor] = useState('')
  const [quantity, setQuantity] = useState(1)
  const [addingToCart, setAddingToCart] = useState(false)
  const [addedJustNow, setAddedJustNow] = useState(false)

  const [similarProducts, setSimilarProducts] = useState([])
  const [complementaryProducts, setComplementaryProducts] = useState([])
  const [loading, setLoading] = useState(true)
  const [loadingRecs, setLoadingRecs] = useState(true)
  const [error, setError] = useState(null)

  const isSaved = product ? isInWishlist(product.product_id) : false

  useEffect(() => {
    const fetchProductAndRecs = async () => {
      setLoading(true)
      setLoadingRecs(true)
      setError(null)
      try {
        const res = await productService.getProductById(id)
        const p = res.data?.product
        if (!p) {
          setError(`Product with ID '${id}' was not found.`)
          setLoading(false)
          return
        }

        setProduct(p)
        setSelectedImage(p.image_url)
        setSelectedSize(p.sizes?.[0] || 'M')
        setSelectedColor(p.colors?.[0] || 'Default')

        // Log view interaction if authenticated
        if (isAuthenticated) {
          interactionService.log(p.product_id, 'view')
        }

        setLoading(false)

        // Fetch Similar and Complementary in parallel
        try {
          const [similars, comps] = await Promise.all([
            recommendationService.getSimilar(p.product_id, 10),
            recommendationService.getComplementary(p.product_id, 6),
          ])
          setSimilarProducts(similars)
          setComplementaryProducts(comps)
        } catch {
          // Non-blocking recommendation errors
        } finally {
          setLoadingRecs(false)
        }
      } catch (err) {
        setError('Failed to load product details.')
        setLoading(false)
      }
    }

    fetchProductAndRecs()
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }, [id, isAuthenticated])

  const handleAddToCart = async () => {
    if (!product || addingToCart || addedJustNow) return
    setAddingToCart(true)
    try {
      await addToCart(product.product_id, quantity, selectedSize, selectedColor)
      setAddedJustNow(true)
      setTimeout(() => setAddedJustNow(false), 2500)
    } catch {
      // Error handled by CartContext
    } finally {
      setAddingToCart(false)
    }
  }

  const handleWishlist = async () => {
    if (!product) return
    try {
      await toggleWishlist(product.product_id)
    } catch {
      // Error handled by CartContext
    }
  }

  if (loading) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12 animate-pulse space-y-8">
        <div className="h-4 bg-neutral-200 rounded w-1/4" />
        <div className="grid grid-cols-1 md:grid-cols-2 gap-10">
          <div className="aspect-[4/5] bg-neutral-200 rounded-3xl" />
          <div className="space-y-4">
            <div className="h-6 bg-neutral-200 rounded w-1/3" />
            <div className="h-8 bg-neutral-200 rounded w-3/4" />
            <div className="h-6 bg-neutral-200 rounded w-1/4" />
            <div className="h-24 bg-neutral-200 rounded" />
          </div>
        </div>
      </div>
    )
  }

  if (error || !product) {
    return (
      <div className="max-w-7xl mx-auto px-4 py-16">
        <ErrorMessage
          title="Product Not Available"
          message={error}
          onRetry={() => window.location.reload()}
        />
        <div className="text-center mt-4">
          <Link to="/products" className="text-xs font-bold text-indigo-600 hover:underline">
            Back to Catalog
          </Link>
        </div>
      </div>
    )
  }

  const allImages = [product.image_url, ...(product.additional_images || [])].filter(Boolean)

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 sm:py-10 space-y-12">
      {/* Breadcrumbs */}
      <nav className="flex items-center gap-2 text-xs font-medium text-neutral-500">
        <Link to="/" className="hover:text-indigo-600 transition-colors">
          Home
        </Link>
        <ChevronRight className="w-3.5 h-3.5" />
        <Link to="/products" className="hover:text-indigo-600 transition-colors">
          Products
        </Link>
        <ChevronRight className="w-3.5 h-3.5" />
        <Link
          to={`/products?category=${product.category}`}
          className="hover:text-indigo-600 transition-colors"
        >
          {product.category}
        </Link>
        <ChevronRight className="w-3.5 h-3.5" />
        <span className="text-neutral-800 font-semibold truncate max-w-[200px]">
          {product.name}
        </span>
      </nav>

      {/* Main Product Showcase Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-10 lg:gap-14">
        {/* Left: Gallery */}
        <div className="space-y-4">
          {/* Main Large Display */}
          <div className="relative aspect-[4/5] rounded-3xl overflow-hidden bg-neutral-100 border border-neutral-200 shadow-sm">
            <img
              src={selectedImage}
              alt={product.name}
              className="w-full h-full object-cover object-center"
              onError={(e) => {
                e.currentTarget.src = `https://picsum.photos/seed/${product.product_id}/800/1000`
              }}
            />
            {product.discount_percent > 0 && (
              <span className="absolute top-4 left-4 bg-rose-600 text-white text-xs font-extrabold px-3 py-1 rounded-full uppercase tracking-wider shadow-md">
                {product.discount_percent}% OFF
              </span>
            )}
          </div>

          {/* Thumbnail Strip */}
          {allImages.length > 1 && (
            <div className="flex gap-3 overflow-x-auto pb-2">
              {allImages.map((img, idx) => (
                <button
                  key={idx}
                  onClick={() => setSelectedImage(img)}
                  className={`w-20 h-24 rounded-xl overflow-hidden border-2 flex-shrink-0 transition-all ${
                    selectedImage === img
                      ? 'border-indigo-600 ring-2 ring-indigo-100'
                      : 'border-neutral-200 opacity-70 hover:opacity-100'
                  }`}
                >
                  <img src={img} alt="" className="w-full h-full object-cover" />
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Right: Product Actions & Specs */}
        <div className="space-y-6 flex flex-col justify-between">
          <div className="space-y-4">
            {/* Brand & Category */}
            <div className="flex items-center justify-between">
              <span className="text-xs font-extrabold tracking-widest text-indigo-600 uppercase">
                {product.brand}
              </span>
              <span className="text-xs text-neutral-400 font-medium">
                ID: {product.product_id}
              </span>
            </div>

            {/* Title */}
            <h1 className="text-2xl sm:text-3xl font-serif font-bold text-neutral-900 tracking-tight">
              {product.name}
            </h1>

            {/* Ratings Bar */}
            <div className="flex items-center gap-3">
              <div className="flex items-center gap-1.5 bg-neutral-100 px-2.5 py-1 rounded-lg">
                <Star className="w-4 h-4 fill-amber-400 stroke-amber-400" />
                <span className="text-xs font-bold text-neutral-800">
                  {product.rating?.toFixed(1) || '4.2'}
                </span>
              </div>
              <span className="text-xs text-neutral-400 font-medium">
                ({product.review_count || 128} verified customer reviews)
              </span>
              <span className="text-xs font-semibold text-emerald-600 bg-emerald-50 px-2 py-0.5 rounded-full">
                {product.is_available ? 'In Stock' : 'Out of Stock'}
              </span>
            </div>

            {/* Price Box */}
            <div className="flex items-baseline gap-3 pt-2">
              <span className="text-3xl font-black text-neutral-900">
                {formatCurrency(product.discounted_price || product.price)}
              </span>
              {product.discount_percent > 0 && (
                <>
                  <span className="text-base text-neutral-400 line-through">
                    {formatCurrency(product.price)}
                  </span>
                  <span className="text-xs font-bold text-rose-600">
                    Save {formatCurrency(product.price - product.discounted_price)}
                  </span>
                </>
              )}
            </div>

            {/* Sizes Selection */}
            {product.sizes && product.sizes.length > 0 && (
              <div className="pt-2">
                <div className="flex items-center justify-between mb-2">
                  <label className="text-xs font-bold uppercase tracking-wider text-neutral-600">
                    Select Size
                  </label>
                  <span className="text-[11px] text-indigo-600 font-medium hover:underline cursor-pointer">
                    Size Guide
                  </span>
                </div>
                <div className="flex flex-wrap gap-2">
                  {product.sizes.map((s) => (
                    <button
                      key={s}
                      onClick={() => setSelectedSize(s)}
                      className={`min-w-[48px] h-11 px-3 rounded-xl border text-xs font-bold transition-all ${
                        selectedSize === s
                          ? 'border-neutral-900 bg-neutral-900 text-white shadow-xs'
                          : 'border-neutral-200 text-neutral-700 hover:border-neutral-400 bg-white'
                      }`}
                    >
                      {s}
                    </button>
                  ))}
                </div>
              </div>
            )}

            {/* Colors Selection */}
            {product.colors && product.colors.length > 0 && (
              <div className="pt-2">
                <label className="block text-xs font-bold uppercase tracking-wider text-neutral-600 mb-2">
                  Color: <span className="text-neutral-900 font-semibold">{selectedColor}</span>
                </label>
                <div className="flex flex-wrap gap-2">
                  {product.colors.map((c) => (
                    <button
                      key={c}
                      onClick={() => setSelectedColor(c)}
                      className={`px-3 py-1.5 rounded-lg border text-xs font-medium transition-all ${
                        selectedColor === c
                          ? 'border-indigo-600 bg-indigo-50 text-indigo-700 font-bold'
                          : 'border-neutral-200 text-neutral-700 hover:bg-neutral-50'
                      }`}
                    >
                      {c}
                    </button>
                  ))}
                </div>
              </div>
            )}

            {/* Add to Cart & Wishlist Actions */}
            <div className="pt-4 space-y-3">
              <div className="flex gap-3">
                <button
                  onClick={handleAddToCart}
                  disabled={addingToCart || !product.is_available}
                  className={`flex-1 py-4 px-6 rounded-2xl font-bold text-sm flex items-center justify-center gap-2 shadow-lg transition-all duration-200 ${
                    !product.is_available
                      ? 'bg-neutral-200 text-neutral-400 cursor-not-allowed'
                      : addedJustNow
                      ? 'bg-emerald-600 text-white'
                      : 'bg-neutral-900 hover:bg-indigo-600 text-white hover:scale-101 shadow-neutral-900/10'
                  }`}
                >
                  {addedJustNow ? (
                    <>
                      <Check className="w-5 h-5" /> Added to Shopping Bag
                    </>
                  ) : addingToCart ? (
                    'Adding to Bag...'
                  ) : !product.is_available ? (
                    'Out of Stock'
                  ) : (
                    <>
                      <ShoppingBag className="w-5 h-5" /> Add to Shopping Bag
                    </>
                  )}
                </button>

                <button
                  onClick={handleWishlist}
                  className={`p-4 rounded-2xl border transition-all ${
                    isSaved
                      ? 'border-rose-300 bg-rose-50 text-rose-600'
                      : 'border-neutral-200 hover:border-neutral-300 bg-white text-neutral-700 hover:text-rose-600'
                  }`}
                  aria-label={isSaved ? 'Remove from wishlist' : 'Save to wishlist'}
                >
                  <Heart className={`w-5 h-5 ${isSaved ? 'fill-rose-600' : ''}`} />
                </button>
              </div>

              {/* Delivery Features */}
              <div className="grid grid-cols-2 gap-3 pt-3 text-xs text-neutral-500">
                <div className="flex items-center gap-2 p-2.5 rounded-xl bg-neutral-100/70">
                  <Truck className="w-4 h-4 text-neutral-700" />
                  <span>Free express delivery on orders over ₹1,500</span>
                </div>
                <div className="flex items-center gap-2 p-2.5 rounded-xl bg-neutral-100/70">
                  <RotateCcw className="w-4 h-4 text-neutral-700" />
                  <span>Hassle-free 14-day easy returns & exchanges</span>
                </div>
              </div>
            </div>
          </div>

          {/* Description & Attribute Tags */}
          <div className="border-t border-neutral-200 pt-6 space-y-3">
            <h3 className="text-xs font-bold uppercase tracking-wider text-neutral-700">
              Product Details & Attributes
            </h3>
            <p className="text-xs sm:text-sm text-neutral-600 leading-relaxed">
              {product.description}
            </p>

            {product.tags && product.tags.length > 0 && (
              <div className="flex flex-wrap gap-1.5 pt-2">
                {product.tags.map((tag) => (
                  <span
                    key={tag}
                    className="text-[11px] font-medium bg-neutral-100 text-neutral-600 px-2.5 py-1 rounded-md"
                  >
                    #{tag}
                  </span>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Recommendation Section 1: Similar Products (Content-Based Cosine Similarity) */}
      <RecommendationRow
        title="Similar Styles You Might Love"
        subtitle="Identified via TF-IDF textual and fashion attribute cosine similarity"
        badgeText="Content-Based Similarity"
        products={similarProducts}
        loading={loadingRecs}
      />

      {/* Recommendation Section 2: Complementary Products (Outfit Recommendations) */}
      <RecommendationRow
        title="Complete the Look"
        subtitle="Complementary items to build a cohesive outfit ensemble"
        badgeText="Complementary Outfit Styling"
        products={complementaryProducts}
        loading={loadingRecs}
      />
    </div>
  )
}
