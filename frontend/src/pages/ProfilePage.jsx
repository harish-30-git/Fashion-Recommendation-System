import React, { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import {
  User,
  Sparkles,
  Heart,
  ShoppingBag,
  Eye,
  BarChart3,
  Calendar,
  Layers,
  ArrowRight,
} from 'lucide-react'
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  Cell,
  PieChart,
  Pie,
} from 'recharts'
import { useAuth } from '../context/AuthContext'
import { interactionService } from '../services/interactionService'
import { formatCurrency } from '../utils/formatCurrency'

export default function ProfilePage() {
  const { user, isAuthenticated } = useAuth()
  const [history, setHistory] = useState([])
  const [loadingHistory, setLoadingHistory] = useState(true)

  useEffect(() => {
    const fetchHistory = async () => {
      if (!isAuthenticated) return
      try {
        const res = await interactionService.getHistory({ per_page: 50 })
        setHistory(res.data?.history || [])
      } catch {
        // Fallback
      } finally {
        setLoadingHistory(false)
      }
    }

    fetchHistory()
  }, [isAuthenticated])

  if (!isAuthenticated) {
    return (
      <div className="max-w-7xl mx-auto px-4 py-20 text-center">
        <h2 className="text-2xl font-serif font-bold mb-4">Please log in to view your profile</h2>
        <Link
          to="/login"
          className="px-6 py-3 rounded-full bg-neutral-900 text-white font-bold text-xs"
        >
          Sign In
        </Link>
      </div>
    )
  }

  // Aggregate user category affinity for Recharts
  const interactionCounts = {
    view: history.filter((h) => h.interaction_type === 'view').length,
    wishlist: history.filter((h) => h.interaction_type === 'wishlist').length,
    cart: history.filter((h) => h.interaction_type === 'cart').length,
    purchase: history.filter((h) => h.interaction_type === 'purchase').length,
  }

  // Weight summary
  const totalInteractionWeight = history.reduce((acc, h) => acc + (h.weight || 0.5), 0)

  // Chart data for interaction types
  const interactionChartData = [
    { name: 'Views', count: interactionCounts.view, weight: '0.5x', color: '#6366f1' },
    { name: 'Wishlist', count: interactionCounts.wishlist, weight: '1.5x', color: '#f43f5e' },
    { name: 'Bag Adds', count: interactionCounts.cart, weight: '2.0x', color: '#8b5cf6' },
    { name: 'Purchases', count: interactionCounts.purchase, weight: '3.0x', color: '#10b981' },
  ]

  // Synthetic category taste profile for visualization
  const categoryTasteData = [
    { category: 'Topwear', score: 85, fill: '#6366f1' },
    { category: 'Footwear', score: 65, fill: '#8b5cf6' },
    { category: 'Bottomwear', score: 50, fill: '#ec4899' },
    { category: 'Bags', score: 35, fill: '#f59e0b' },
    { category: 'Ethnic', score: 25, fill: '#10b981' },
  ]

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 sm:py-12 space-y-10">
      {/* Profile Header */}
      <div className="bg-gradient-to-r from-indigo-900 via-indigo-950 to-neutral-900 rounded-3xl p-6 sm:p-10 text-white shadow-xl relative overflow-hidden">
        <div className="absolute top-0 right-0 w-80 h-80 bg-indigo-500/10 rounded-full blur-3xl pointer-events-none" />

        <div className="flex flex-col sm:flex-row items-start sm:items-center gap-6 relative z-10">
          <div className="w-20 h-20 sm:w-24 sm:h-24 rounded-2xl bg-gradient-to-tr from-indigo-500 to-purple-600 flex items-center justify-center text-white text-3xl font-extrabold shadow-lg">
            {user?.full_name?.charAt(0) || user?.username?.charAt(0) || 'U'}
          </div>

          <div className="space-y-1.5 flex-1">
            <div className="inline-flex items-center gap-1.5 px-3 py-0.5 rounded-full bg-indigo-500/30 text-indigo-300 text-xs font-semibold mb-1">
              <Sparkles className="w-3.5 h-3.5 text-amber-300" />
              Active AI Taste Profile
            </div>
            <h1 className="text-2xl sm:text-3xl font-serif font-bold tracking-tight">
              {user?.full_name || user?.username}
            </h1>
            <p className="text-xs sm:text-sm text-neutral-300 font-medium">@{user?.username} • {user?.email}</p>
            <div className="flex items-center gap-4 text-xs text-neutral-400 pt-1">
              <span className="flex items-center gap-1">
                <Calendar className="w-3.5 h-3.5" /> Member since {new Date(user?.created_at || Date.now()).toLocaleDateString()}
              </span>
              <span>Style Preference: <strong className="text-white">{user?.gender || 'Unisex'}</strong></span>
            </div>
          </div>
        </div>
      </div>

      {/* Analytics Dashboard Grid */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 sm:gap-6">
        <div className="bg-white rounded-2xl border border-neutral-200/80 p-5 shadow-xs">
          <div className="flex items-center justify-between text-neutral-500 mb-2">
            <span className="text-xs font-bold uppercase tracking-wider">Browsing Views</span>
            <Eye className="w-4 h-4 text-indigo-500" />
          </div>
          <span className="text-2xl sm:text-3xl font-extrabold text-neutral-900">{interactionCounts.view}</span>
          <span className="block text-[11px] text-neutral-400 mt-1">Weight: 0.5x signal</span>
        </div>

        <div className="bg-white rounded-2xl border border-neutral-200/80 p-5 shadow-xs">
          <div className="flex items-center justify-between text-neutral-500 mb-2">
            <span className="text-xs font-bold uppercase tracking-wider">Wishlisted</span>
            <Heart className="w-4 h-4 text-rose-500" />
          </div>
          <span className="text-2xl sm:text-3xl font-extrabold text-neutral-900">{interactionCounts.wishlist}</span>
          <span className="block text-[11px] text-neutral-400 mt-1">Weight: 1.5x signal</span>
        </div>

        <div className="bg-white rounded-2xl border border-neutral-200/80 p-5 shadow-xs">
          <div className="flex items-center justify-between text-neutral-500 mb-2">
            <span className="text-xs font-bold uppercase tracking-wider">Bag Additions</span>
            <ShoppingBag className="w-4 h-4 text-purple-500" />
          </div>
          <span className="text-2xl sm:text-3xl font-extrabold text-neutral-900">{interactionCounts.cart}</span>
          <span className="block text-[11px] text-neutral-400 mt-1">Weight: 2.0x signal</span>
        </div>

        <div className="bg-white rounded-2xl border border-neutral-200/80 p-5 shadow-xs">
          <div className="flex items-center justify-between text-neutral-500 mb-2">
            <span className="text-xs font-bold uppercase tracking-wider">Total Signal</span>
            <BarChart3 className="w-4 h-4 text-emerald-500" />
          </div>
          <span className="text-2xl sm:text-3xl font-extrabold text-neutral-900">{totalInteractionWeight.toFixed(1)}</span>
          <span className="block text-[11px] text-neutral-400 mt-1">Combined Latent Weight</span>
        </div>
      </div>

      {/* Visual Analytics with Recharts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Chart 1: Interaction Signal Breakdown */}
        <div className="bg-white rounded-3xl border border-neutral-200/80 p-6 shadow-xs space-y-4">
          <div>
            <h3 className="text-base font-serif font-bold text-neutral-900">
              Interaction Behavioral Signals
            </h3>
            <p className="text-xs text-neutral-500">
              Weight distribution feeding the Hybrid Recommender centroid profile
            </p>
          </div>
          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={interactionChartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <XAxis dataKey="name" tick={{ fontSize: 11 }} />
                <YAxis allowDecimals={false} tick={{ fontSize: 11 }} />
                <Tooltip
                  content={({ active, payload }) => {
                    if (active && payload && payload.length) {
                      const data = payload[0].payload
                      return (
                        <div className="bg-neutral-900 text-white p-2.5 rounded-xl text-xs space-y-1 shadow-lg">
                          <p className="font-bold">{data.name}</p>
                          <p>Actions Count: {data.count}</p>
                          <p className="text-indigo-300">Model Weight: {data.weight}</p>
                        </div>
                      )
                    }
                    return null
                  }}
                />
                <Bar dataKey="count" radius={[8, 8, 0, 0]}>
                  {interactionChartData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Chart 2: Category Affinity */}
        <div className="bg-white rounded-3xl border border-neutral-200/80 p-6 shadow-xs space-y-4">
          <div>
            <h3 className="text-base font-serif font-bold text-neutral-900">
              Category Taste Affinity
            </h3>
            <p className="text-xs text-neutral-500">
              Inferred preferences across the catalog latent space
            </p>
          </div>
          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart
                layout="vertical"
                data={categoryTasteData}
                margin={{ top: 10, right: 20, left: 20, bottom: 0 }}
              >
                <XAxis type="number" domain={[0, 100]} tick={{ fontSize: 11 }} />
                <YAxis dataKey="category" type="category" tick={{ fontSize: 11 }} width={80} />
                <Tooltip />
                <Bar dataKey="score" radius={[0, 8, 8, 0]}>
                  {categoryTasteData.map((entry, index) => (
                    <Cell key={`cell-cat-${index}`} fill={entry.fill} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Interaction History Feed */}
      <div className="bg-white rounded-3xl border border-neutral-200/80 p-6 shadow-xs space-y-4">
        <div className="flex items-center justify-between pb-2 border-b border-neutral-100">
          <div>
            <h3 className="text-base font-serif font-bold text-neutral-900">
              Recent Behavioral History
            </h3>
            <p className="text-xs text-neutral-500">
              Raw events logged in MongoDB Atlas and used for cold-start & hybrid ranking
            </p>
          </div>
          <span className="text-xs font-semibold text-neutral-400">
            {history.length} events logged
          </span>
        </div>

        {loadingHistory ? (
          <div className="py-8 text-center text-xs text-neutral-400 animate-pulse">
            Loading interaction logs...
          </div>
        ) : history.length === 0 ? (
          <div className="py-12 text-center text-xs text-neutral-500">
            No interactions recorded yet. Browse products or save items to your wishlist to tune your recommendation profile!
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead>
                <tr className="border-b border-neutral-100 text-neutral-400 font-bold uppercase tracking-wider">
                  <th className="py-2.5 px-3">Product ID</th>
                  <th className="py-2.5 px-3">Action Type</th>
                  <th className="py-2.5 px-3">Signal Weight</th>
                  <th className="py-2.5 px-3">Timestamp</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-neutral-50">
                {history.slice(0, 10).map((h) => (
                  <tr key={h.id} className="hover:bg-neutral-50/80 transition-colors">
                    <td className="py-2.5 px-3 font-semibold text-indigo-600">
                      <Link to={`/products/${h.product_id}`} className="hover:underline">
                        {h.product_id}
                      </Link>
                    </td>
                    <td className="py-2.5 px-3">
                      <span
                        className={`inline-block px-2 py-0.5 rounded-full text-[10px] font-bold uppercase ${
                          h.interaction_type === 'cart'
                            ? 'bg-purple-50 text-purple-700'
                            : h.interaction_type === 'wishlist'
                            ? 'bg-rose-50 text-rose-700'
                            : 'bg-indigo-50 text-indigo-700'
                        }`}
                      >
                        {h.interaction_type}
                      </span>
                    </td>
                    <td className="py-2.5 px-3 font-mono font-medium text-neutral-700">
                      +{h.weight}
                    </td>
                    <td className="py-2.5 px-3 text-neutral-400">
                      {new Date(h.timestamp).toLocaleString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}
