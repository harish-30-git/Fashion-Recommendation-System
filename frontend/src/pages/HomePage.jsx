import React, { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import {
  Sparkles,
  ArrowRight,
  TrendingUp,
  SlidersHorizontal,
  Compass,
  Zap,
  ShoppingBag,
} from 'lucide-react'
import { recommendationService } from '../services/recommendationService'
import { useAuth } from '../context/AuthContext'
import RecommendationRow from '../components/recommendation/RecommendationRow'
import ErrorMessage from '../components/common/ErrorMessage'

export default function HomePage() {
  const { isAuthenticated, user } = useAuth()
  const [trending, setTrending] = useState([])
  const [personalized, setPersonalized] = useState([])
  const [loadingTrending, setLoadingTrending] = useState(true)
  const [loadingPersonalized, setLoadingPersonalized] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    const fetchData = async () => {
      setError(null)
      try {
        const trendingData = await recommendationService.getTrending(null, 12)
        setTrending(trendingData)
      } catch (err) {
        setError('Failed to load catalog data from the server. Ensure the Flask backend is running.')
      } finally {
        setLoadingTrending(false)
      }

      try {
        const personalizedData = await recommendationService.getPersonalized(10)
        setPersonalized(personalizedData)
      } catch {
        // Safe fallback
      } finally {
        setLoadingPersonalized(false)
      }
    }

    fetchData()
  }, [isAuthenticated])

  const categoryCards = [
    {
      name: 'Topwear & Shirts',
      category: 'Topwear',
      image: 'https://images.unsplash.com/photo-1596755094514-f87e34085b2c?auto=format&fit=crop&w=600&q=80',
      count: 'Casual & Formal',
    },
    {
      name: 'Bottomwear & Denim',
      category: 'Bottomwear',
      image: 'https://images.unsplash.com/photo-1542272604-780c96856592?auto=format&fit=crop&w=600&q=80',
      count: 'Jeans & Trousers',
    },
    {
      name: 'Footwear',
      category: 'Footwear',
      image: 'https://images.unsplash.com/photo-1549298916-b41d501d3772?auto=format&fit=crop&w=600&q=80',
      count: 'Sneakers & Formal',
    },
    {
      name: 'Ethnic & Traditional',
      category: 'Ethnic',
      image: 'https://images.unsplash.com/photo-1610030469983-98e550d6193c?auto=format&fit=crop&w=600&q=80',
      count: 'Kurtas & Sarees',
    },
    {
      name: 'Bags & Backpacks',
      category: 'Bags',
      image: 'https://images.unsplash.com/photo-1548036328-c9fa89d128fa?auto=format&fit=crop&w=600&q=80',
      count: 'Leather & Travel',
    },
    {
      name: 'Fashion Accessories',
      category: 'Accessories',
      image: 'https://images.unsplash.com/photo-1523275335684-37898b6baf30?auto=format&fit=crop&w=600&q=80',
      count: 'Watches & Essentials',
    },
  ]

  return (
    <div className="space-y-8 sm:space-y-12 pb-16">
      {/* Hero Banner Section */}
      <section className="relative overflow-hidden bg-gradient-to-b from-indigo-950 via-neutral-900 to-neutral-950 text-white pt-12 sm:pt-20 pb-16 sm:pb-24">
        {/* Subtle background glow */}
        <div className="absolute top-0 right-1/4 w-96 h-96 bg-indigo-500/10 rounded-full blur-3xl pointer-events-none" />
        <div className="absolute bottom-0 left-1/4 w-96 h-96 bg-purple-500/10 rounded-full blur-3xl pointer-events-none" />

        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
          <div className="max-w-3xl space-y-6">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-indigo-500/20 border border-indigo-400/30 text-indigo-300 text-xs font-semibold tracking-wide uppercase">
              <Sparkles className="w-3.5 h-3.5 text-amber-300" />
              Machine Learning Powered Fashion
            </div>

            <h1 className="font-serif text-3xl sm:text-5xl lg:text-6xl font-extrabold tracking-tight text-white leading-tight">
              Personalized Fashion Discovery,{' '}
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-indigo-300 via-purple-300 to-pink-300">
                Tailored for You.
              </span>
            </h1>

            <p className="text-neutral-300 text-sm sm:text-base leading-relaxed max-w-2xl font-normal">
              StyleSense learns from your clicks, wishlist additions, and preferences using hybrid content-based TF-IDF and collaborative filtering algorithms. Discover the perfect look effortlessly.
            </p>

            <div className="flex flex-wrap items-center gap-3 pt-2">
              <Link
                to="/products"
                className="px-6 py-3.5 rounded-full bg-white text-neutral-900 hover:bg-indigo-50 font-bold text-xs sm:text-sm flex items-center gap-2 shadow-xl hover:shadow-indigo-500/20 transition-all hover:scale-102"
              >
                Browse Catalog <ArrowRight className="w-4 h-4" />
              </Link>
              {!isAuthenticated && (
                <Link
                  to="/register"
                  className="px-6 py-3.5 rounded-full bg-neutral-800/80 hover:bg-neutral-800 border border-neutral-700 text-white font-bold text-xs sm:text-sm transition-all"
                >
                  Create Account for Personalized Feed
                </Link>
              )}
            </div>

            {/* AI Architecture Pill Metrics */}
            <div className="grid grid-cols-3 gap-3 pt-6 border-t border-neutral-800/80 max-w-lg">
              <div>
                <span className="block text-lg sm:text-xl font-extrabold text-white">1,000+</span>
                <span className="text-[11px] text-neutral-400">Fashion Items</span>
              </div>
              <div>
                <span className="block text-lg sm:text-xl font-extrabold text-indigo-400">TF-IDF</span>
                <span className="text-[11px] text-neutral-400">Content Cosine Sim</span>
              </div>
              <div>
                <span className="block text-lg sm:text-xl font-extrabold text-purple-400">Hybrid</span>
                <span className="text-[11px] text-neutral-400">Item-Item CF Engine</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Main Container */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-12">
        {error && <ErrorMessage message={error} onRetry={() => window.location.reload()} />}

        {/* Recommended For You Section */}
        <RecommendationRow
          title={
            isAuthenticated
              ? `Recommended For You, ${user?.full_name?.split(' ')[0] || user?.username}`
              : 'Recommended For You'
          }
          subtitle={
            isAuthenticated
              ? 'Computed from your interactions, style preferences, and brand affinity'
              : 'Sign in to personalize your recommendations in real-time'
          }
          badgeText="Hybrid Recommendation Engine"
          products={personalized}
          loading={loadingPersonalized}
        />

        {/* Category Cards Carousel / Grid */}
        <section>
          <div className="mb-6">
            <span className="text-xs font-bold uppercase tracking-wider text-indigo-600 block mb-1">
              Curated Collections
            </span>
            <h2 className="text-xl sm:text-2xl font-serif font-bold text-neutral-900 tracking-tight">
              Shop by Category
            </h2>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3 sm:gap-4">
            {categoryCards.map((cat) => (
              <Link
                key={cat.name}
                to={`/products?category=${cat.category}`}
                className="group relative rounded-2xl overflow-hidden aspect-[3/4] bg-neutral-100 flex flex-col justify-end p-3.5 sm:p-4 text-white shadow-xs hover:shadow-lg transition-all duration-300"
              >
                <img
                  src={cat.image}
                  alt={cat.name}
                  loading="lazy"
                  className="absolute inset-0 w-full h-full object-cover object-center group-hover:scale-110 transition-transform duration-500 ease-out"
                />
                <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-black/30 to-transparent" />
                <div className="relative z-10">
                  <span className="text-[10px] text-indigo-300 uppercase tracking-widest font-semibold block mb-0.5">
                    {cat.count}
                  </span>
                  <h3 className="text-xs sm:text-sm font-bold leading-tight group-hover:text-indigo-200 transition-colors">
                    {cat.name}
                  </h3>
                </div>
              </Link>
            ))}
          </div>
        </section>

        {/* Trending Section */}
        <RecommendationRow
          title="Trending Styles Right Now"
          subtitle="Top rated and high interaction items popular across all shoppers"
          badgeText="Trending Popularity"
          products={trending}
          loading={loadingTrending}
        />

        {/* Value Proposition Callout: How StyleSense AI Works */}
        <section className="bg-gradient-to-br from-indigo-900 via-indigo-950 to-neutral-900 rounded-3xl text-white p-8 sm:p-12 shadow-xl">
          <div className="max-w-3xl mb-8">
            <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-white/10 text-indigo-200 text-xs font-semibold mb-3">
              <Zap className="w-3.5 h-3.5 text-amber-300" />
              Explainable Architecture
            </div>
            <h2 className="font-serif text-2xl sm:text-3xl font-bold tracking-tight text-white mb-3">
              How the StyleSense Recommendation Pipeline Works
            </h2>
            <p className="text-xs sm:text-sm text-neutral-300 leading-relaxed">
              Every recommendation you see is generated by real mathematical algorithms running on our Python backend, avoiding black-box randomness.
            </p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-6">
            <div className="p-5 rounded-2xl bg-white/5 border border-white/10">
              <div className="w-9 h-9 rounded-xl bg-indigo-500/20 text-indigo-300 flex items-center justify-center font-bold mb-3">
                1
              </div>
              <h3 className="text-sm font-bold text-white mb-1.5">TF-IDF Vector Space</h3>
              <p className="text-xs text-neutral-400 leading-relaxed">
                Converts product titles, brands, categories, and colors into 2,161-dimensional unit vectors with cosine similarity matching.
              </p>
            </div>

            <div className="p-5 rounded-2xl bg-white/5 border border-white/10">
              <div className="w-9 h-9 rounded-xl bg-purple-500/20 text-purple-300 flex items-center justify-center font-bold mb-3">
                2
              </div>
              <h3 className="text-sm font-bold text-white mb-1.5">Behavioral Weights</h3>
              <p className="text-xs text-neutral-400 leading-relaxed">
                Applies weighted preferences to your actions: Product Views (0.5), Wishlist (1.5), and Cart Additions (2.0).
              </p>
            </div>

            <div className="p-5 rounded-2xl bg-white/5 border border-white/10">
              <div className="w-9 h-9 rounded-xl bg-emerald-500/20 text-emerald-300 flex items-center justify-center font-bold mb-3">
                3
              </div>
              <h3 className="text-sm font-bold text-white mb-1.5">Diversity Reranking</h3>
              <p className="text-xs text-neutral-400 leading-relaxed">
                Maximal Marginal Relevance (MMR) ensures recommendations aren't just repetitive clones, introducing complementary items.
              </p>
            </div>
          </div>
        </section>
      </div>
    </div>
  )
}
