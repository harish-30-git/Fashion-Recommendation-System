import React, { useState } from 'react'
import { Link } from 'react-router-dom'
import { ShoppingBag, ArrowRight, CheckCircle2, ShieldCheck } from 'lucide-react'
import { useCart } from '../context/CartContext'
import { useAuth } from '../context/AuthContext'
import CartItem from '../components/cart/CartItem'
import CartSummary from '../components/cart/CartSummary'

export default function CartPage() {
  const { cart, updateQuantity, removeFromCart, refreshCart } = useCart()
  const { isAuthenticated } = useAuth()
  const [checkoutSuccess, setCheckoutSuccess] = useState(false)
  const [checkingOut, setCheckingOut] = useState(false)

  const items = cart?.items || []
  const hasOutOfStock = items.some((item) => item.in_stock === false)

  const handleCheckout = () => {
    setCheckingOut(true)
    setTimeout(() => {
      setCheckingOut(false)
      setCheckoutSuccess(true)
      refreshCart()
    }, 1200)
  }

  if (!isAuthenticated) {
    return (
      <div className="max-w-7xl mx-auto px-4 py-20 text-center">
        <div className="w-16 h-16 rounded-full bg-neutral-100 text-neutral-400 flex items-center justify-center mx-auto mb-4">
          <ShoppingBag className="w-8 h-8" />
        </div>
        <h2 className="text-xl sm:text-2xl font-serif font-bold text-neutral-900 mb-2">
          Your Shopping Bag is Waiting
        </h2>
        <p className="text-xs sm:text-sm text-neutral-500 max-w-sm mx-auto mb-6">
          Sign in to view items saved in your bag, receive personalized offers, and sync across devices.
        </p>
        <Link
          to="/login"
          className="inline-flex items-center gap-2 px-6 py-3 rounded-full bg-neutral-900 hover:bg-indigo-600 text-white text-xs sm:text-sm font-bold shadow-md transition-all"
        >
          Sign In to Access Bag <ArrowRight className="w-4 h-4" />
        </Link>
      </div>
    )
  }

  if (checkoutSuccess) {
    return (
      <div className="max-w-2xl mx-auto px-4 py-20 text-center">
        <div className="w-16 h-16 rounded-full bg-emerald-100 text-emerald-600 flex items-center justify-center mx-auto mb-4 animate-in zoom-in-50">
          <CheckCircle2 className="w-9 h-9" />
        </div>
        <h2 className="text-2xl sm:text-3xl font-serif font-bold text-neutral-900 mb-2">
          Order Placed Successfully!
        </h2>
        <p className="text-xs sm:text-sm text-neutral-500 max-w-md mx-auto mb-6 leading-relaxed">
          Thank you for shopping with StyleSense! Your order has been registered in the database, and interaction weights have been updated to further personalize your future recommendations.
        </p>
        <div className="flex justify-center gap-3">
          <Link
            to="/products"
            onClick={() => setCheckoutSuccess(false)}
            className="px-6 py-3 rounded-full bg-neutral-900 hover:bg-indigo-600 text-white text-xs sm:text-sm font-bold shadow-md transition-all"
          >
            Continue Shopping
          </Link>
          <Link
            to="/profile"
            className="px-6 py-3 rounded-full bg-neutral-100 hover:bg-neutral-200 text-neutral-800 text-xs sm:text-sm font-bold transition-all"
          >
            View Style Analytics
          </Link>
        </div>
      </div>
    )
  }

  if (items.length === 0) {
    return (
      <div className="max-w-7xl mx-auto px-4 py-20 text-center">
        <div className="w-16 h-16 rounded-full bg-neutral-100 text-neutral-400 flex items-center justify-center mx-auto mb-4">
          <ShoppingBag className="w-8 h-8" />
        </div>
        <h2 className="text-xl sm:text-2xl font-serif font-bold text-neutral-900 mb-2">
          Your Shopping Bag is Empty
        </h2>
        <p className="text-xs sm:text-sm text-neutral-500 max-w-sm mx-auto mb-6">
          Explore our trending styles or personalized recommendations to discover products that fit your wardrobe.
        </p>
        <Link
          to="/products"
          className="inline-flex items-center gap-2 px-6 py-3 rounded-full bg-neutral-900 hover:bg-indigo-600 text-white text-xs sm:text-sm font-bold shadow-md transition-all"
        >
          Explore Trending Styles <ArrowRight className="w-4 h-4" />
        </Link>
      </div>
    )
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 sm:py-12">
      <div className="mb-8 pb-4 border-b border-neutral-200 flex items-baseline justify-between">
        <div>
          <h1 className="text-2xl sm:text-3xl font-serif font-bold text-neutral-900 tracking-tight">
            Shopping Bag
          </h1>
          <p className="text-xs sm:text-sm text-neutral-500 mt-1">
            {cart.item_count || items.length} {items.length === 1 ? 'item' : 'items'} in your bag
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-10">
        {/* Left: Cart Items List */}
        <div className="lg:col-span-2 bg-white rounded-2xl border border-neutral-200/80 p-5 sm:p-6 shadow-xs divide-y divide-neutral-100">
          {items.map((item) => (
            <CartItem
              key={`${item.product_id}-${item.size}-${item.color}`}
              item={item}
              onUpdateQuantity={updateQuantity}
              onRemove={removeFromCart}
            />
          ))}
        </div>

        {/* Right: Order Summary */}
        <div className="lg:col-span-1">
          <div className="sticky top-28">
            <CartSummary
              subtotal={cart.total || 0}
              itemCount={cart.item_count || items.length}
              onCheckout={handleCheckout}
              loading={checkingOut}
              hasOutOfStock={hasOutOfStock}
            />
          </div>
        </div>
      </div>
    </div>
  )
}
