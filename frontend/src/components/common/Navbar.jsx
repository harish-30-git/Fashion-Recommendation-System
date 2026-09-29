import React, { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import {
  Sparkles,
  Search,
  Heart,
  ShoppingBag,
  User,
  LogOut,
  Menu,
  X,
  Compass,
} from 'lucide-react'
import { useAuth } from '../../context/AuthContext'
import { useCart } from '../../context/CartContext'

export default function Navbar() {
  const { user, isAuthenticated, logout } = useAuth()
  const { cartCount, wishlistCount } = useCart()
  const [searchQuery, setSearchQuery] = useState('')
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)
  const [profileDropdownOpen, setProfileDropdownOpen] = useState(false)
  const navigate = useNavigate()

  const handleSearchSubmit = (e) => {
    e.preventDefault()
    if (searchQuery.trim()) {
      navigate(`/products?q=${encodeURIComponent(searchQuery.trim())}`)
      setSearchQuery('')
      setMobileMenuOpen(false)
    }
  }

  const categories = [
    { name: 'All Products', path: '/products' },
    { name: 'Topwear', path: '/products?category=Topwear' },
    { name: 'Bottomwear', path: '/products?category=Bottomwear' },
    { name: 'Footwear', path: '/products?category=Footwear' },
    { name: 'Ethnic', path: '/products?category=Ethnic' },
    { name: 'Bags', path: '/products?category=Bags' },
    { name: 'Accessories', path: '/products?category=Accessories' },
  ]

  return (
    <header className="sticky top-0 z-50 bg-white/95 backdrop-blur-md border-b border-neutral-200/80 transition-all">
      {/* Top Banner */}
      <div className="bg-gradient-to-r from-indigo-900 via-indigo-800 to-purple-900 text-white text-xs py-1.5 px-4 text-center font-medium tracking-wide">
        <span className="inline-flex items-center gap-1.5">
          <Sparkles className="w-3.5 h-3.5 text-amber-300" />
          Powered by StyleSense Hybrid AI Recommendation Engine — Personalized for You
        </span>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16 sm:h-20 gap-4">
          {/* Logo */}
          <Link to="/" className="flex items-center gap-2 group flex-shrink-0">
            <div className="w-9 h-9 sm:w-10 sm:h-10 rounded-xl bg-gradient-to-tr from-indigo-600 to-violet-600 flex items-center justify-center text-white shadow-md shadow-indigo-200 group-hover:scale-105 transition-transform">
              <Sparkles className="w-5 h-5" />
            </div>
            <div className="flex flex-col">
              <span className="font-serif text-xl sm:text-2xl font-bold tracking-tight text-neutral-900">
                Style<span className="text-indigo-600">Sense</span>
              </span>
              <span className="text-[10px] tracking-widest text-neutral-400 font-medium uppercase -mt-1">
                AI Fashion Discovery
              </span>
            </div>
          </Link>

          {/* Search Bar - Desktop */}
          <form
            onSubmit={handleSearchSubmit}
            className="hidden md:flex flex-1 max-w-lg relative items-center mx-4"
          >
            <div className="relative w-full">
              <input
                type="text"
                placeholder="Search styles, brands, cotton shirts, blazers..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full bg-neutral-100 hover:bg-neutral-100/80 focus:bg-white text-neutral-800 placeholder-neutral-400 text-sm pl-11 pr-4 py-2.5 rounded-full border border-transparent focus:border-indigo-500 focus:outline-none focus:ring-4 focus:ring-indigo-100 transition-all"
              />
              <Search className="w-4 h-4 text-neutral-400 absolute left-4 top-1/2 -translate-y-1/2 pointer-events-none" />
            </div>
          </form>

          {/* Right Navigation Actions */}
          <div className="flex items-center gap-1 sm:gap-2">
            {/* Wishlist Button */}
            <Link
              to="/wishlist"
              className="p-2 sm:p-2.5 rounded-full text-neutral-600 hover:text-rose-600 hover:bg-rose-50 transition-colors relative"
              title="Wishlist"
            >
              <Heart className="w-5 h-5 sm:w-6 sm:h-6" />
              {wishlistCount > 0 && (
                <span className="absolute top-1 right-1 w-4 h-4 rounded-full bg-rose-600 text-white text-[10px] font-bold flex items-center justify-center animate-pulse">
                  {wishlistCount}
                </span>
              )}
            </Link>

            {/* Cart Button */}
            <Link
              to="/cart"
              className="p-2 sm:p-2.5 rounded-full text-neutral-600 hover:text-indigo-600 hover:bg-indigo-50 transition-colors relative"
              title="Shopping Cart"
            >
              <ShoppingBag className="w-5 h-5 sm:w-6 sm:h-6" />
              {cartCount > 0 && (
                <span className="absolute top-1 right-1 w-4 h-4 rounded-full bg-indigo-600 text-white text-[10px] font-bold flex items-center justify-center">
                  {cartCount}
                </span>
              )}
            </Link>

            {/* Profile Dropdown */}
            {isAuthenticated ? (
              <div className="relative">
                <button
                  onClick={() => setProfileDropdownOpen(!profileDropdownOpen)}
                  className="flex items-center gap-2 p-1.5 sm:px-3 sm:py-1.5 rounded-full border border-neutral-200 hover:border-neutral-300 bg-white hover:bg-neutral-50 transition-all text-xs font-semibold text-neutral-800"
                >
                  <div className="w-7 h-7 rounded-full bg-gradient-to-tr from-indigo-500 to-purple-600 text-white flex items-center justify-center text-xs font-bold">
                    {user?.full_name?.charAt(0) || user?.username?.charAt(0) || 'U'}
                  </div>
                  <span className="hidden sm:inline-block max-w-[90px] truncate">
                    {user?.full_name?.split(' ')[0] || user?.username}
                  </span>
                </button>

                {profileDropdownOpen && (
                  <div
                    className="absolute right-0 mt-2 w-52 bg-white rounded-2xl shadow-xl border border-neutral-100 py-2 z-50 animate-in fade-in zoom-in-95 duration-100"
                    onClick={() => setProfileDropdownOpen(false)}
                  >
                    <div className="px-4 py-2 border-b border-neutral-100">
                      <p className="text-xs font-medium text-neutral-400">Signed in as</p>
                      <p className="text-sm font-bold text-neutral-800 truncate">{user?.email}</p>
                    </div>
                    <Link
                      to="/profile"
                      className="flex items-center gap-2.5 px-4 py-2.5 text-sm text-neutral-700 hover:bg-indigo-50 hover:text-indigo-600 transition-colors"
                    >
                      <User className="w-4 h-4" />
                      Taste Profile & Analytics
                    </Link>
                    <Link
                      to="/wishlist"
                      className="flex items-center gap-2.5 px-4 py-2.5 text-sm text-neutral-700 hover:bg-rose-50 hover:text-rose-600 transition-colors"
                    >
                      <Heart className="w-4 h-4" />
                      My Wishlist
                    </Link>
                    <button
                      onClick={logout}
                      className="w-full flex items-center gap-2.5 px-4 py-2.5 text-sm text-red-600 hover:bg-red-50 transition-colors text-left"
                    >
                      <LogOut className="w-4 h-4" />
                      Sign Out
                    </button>
                  </div>
                )}
              </div>
            ) : (
              <div className="flex items-center gap-2">
                <Link
                  to="/login"
                  className="text-xs sm:text-sm font-semibold text-neutral-700 hover:text-indigo-600 px-3 py-2 rounded-lg transition-colors"
                >
                  Log in
                </Link>
                <Link
                  to="/register"
                  className="bg-neutral-900 hover:bg-indigo-600 text-white text-xs sm:text-sm font-semibold px-4 py-2 rounded-full transition-all shadow-sm"
                >
                  Sign up
                </Link>
              </div>
            )}

            {/* Mobile menu button */}
            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="md:hidden p-2 rounded-lg text-neutral-600 hover:bg-neutral-100"
            >
              {mobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
            </button>
          </div>
        </div>

        {/* Category Navigation Bar - Desktop */}
        <nav className="hidden md:flex items-center gap-8 py-2.5 border-t border-neutral-100 overflow-x-auto text-xs font-semibold uppercase tracking-wider text-neutral-600">
          {categories.map((cat) => (
            <Link
              key={cat.name}
              to={cat.path}
              className="hover:text-indigo-600 transition-colors whitespace-nowrap"
            >
              {cat.name}
            </Link>
          ))}
        </nav>
      </div>

      {/* Mobile Drawer Menu */}
      {mobileMenuOpen && (
        <div className="md:hidden bg-white border-b border-neutral-200 px-4 pt-2 pb-6 space-y-4">
          <form onSubmit={handleSearchSubmit} className="relative">
            <input
              type="text"
              placeholder="Search products..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full bg-neutral-100 text-neutral-800 text-sm pl-10 pr-4 py-2 rounded-full border border-neutral-200"
            />
            <Search className="w-4 h-4 text-neutral-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
          </form>

          <div className="grid grid-cols-2 gap-2 text-sm font-medium">
            {categories.map((cat) => (
              <Link
                key={cat.name}
                to={cat.path}
                onClick={() => setMobileMenuOpen(false)}
                className="px-3 py-2 rounded-lg hover:bg-neutral-100 text-neutral-700"
              >
                {cat.name}
              </Link>
            ))}
          </div>
        </div>
      )}
    </header>
  )
}
