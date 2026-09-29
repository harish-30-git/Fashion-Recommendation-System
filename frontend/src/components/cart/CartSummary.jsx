import React from 'react'
import { ShieldCheck, ArrowRight, Sparkles } from 'lucide-react'
import { formatCurrency } from '../../utils/formatCurrency'

export default function CartSummary({
  subtotal = 0,
  itemCount = 0,
  onCheckout,
  loading = false,
  hasOutOfStock = false,
}) {
  const shippingFee = subtotal > 1500 ? 0 : 99
  const tax = Math.round(subtotal * 0.05) // 5% GST estimate
  const grandTotal = subtotal + shippingFee + tax

  return (
    <div className="bg-white rounded-2xl border border-neutral-200/80 p-5 sm:p-6 shadow-xs space-y-5">
      <h3 className="font-serif font-bold text-base text-neutral-900 pb-3 border-b border-neutral-100">
        Order Summary
      </h3>

      {/* Breakdown */}
      <div className="space-y-3 text-xs sm:text-sm">
        <div className="flex justify-between text-neutral-600">
          <span>Items Subtotal ({itemCount})</span>
          <span className="font-semibold text-neutral-800">{formatCurrency(subtotal)}</span>
        </div>

        <div className="flex justify-between text-neutral-600">
          <span>Estimated GST (5%)</span>
          <span className="font-semibold text-neutral-800">{formatCurrency(tax)}</span>
        </div>

        <div className="flex justify-between text-neutral-600">
          <span>Standard Delivery</span>
          {shippingFee === 0 ? (
            <span className="font-bold text-emerald-600 uppercase text-xs tracking-wider">
              FREE
            </span>
          ) : (
            <span className="font-semibold text-neutral-800">{formatCurrency(shippingFee)}</span>
          )}
        </div>

        {subtotal < 1500 && (
          <div className="p-2.5 rounded-xl bg-amber-50 text-amber-800 text-xs flex items-center gap-1.5 font-medium">
            <Sparkles className="w-3.5 h-3.5 text-amber-600 flex-shrink-0" />
            Add {formatCurrency(1500 - subtotal)} more for Free Shipping!
          </div>
        )}

        <div className="pt-3 border-t border-neutral-100 flex justify-between items-baseline">
          <span className="text-sm font-bold text-neutral-900">Total Amount</span>
          <span className="text-lg sm:text-xl font-extrabold text-neutral-900">
            {formatCurrency(grandTotal)}
          </span>
        </div>
      </div>

      {/* Checkout Button */}
      <button
        onClick={onCheckout}
        disabled={loading || itemCount === 0 || hasOutOfStock}
        className="w-full py-3.5 px-4 rounded-xl bg-neutral-900 hover:bg-indigo-600 disabled:bg-neutral-200 disabled:text-neutral-400 disabled:cursor-not-allowed text-white font-bold text-sm flex items-center justify-center gap-2 shadow-lg shadow-neutral-900/10 transition-all duration-200"
      >
        {loading ? (
          'Processing...'
        ) : (
          <>
            Proceed to Checkout <ArrowRight className="w-4 h-4" />
          </>
        )}
      </button>

      {/* Security Assurance */}
      <div className="flex items-center justify-center gap-1.5 text-xs text-neutral-400 pt-2">
        <ShieldCheck className="w-4 h-4 text-emerald-500" />
        <span>Bank-grade 256-bit SSL Secure Checkout</span>
      </div>
    </div>
  )
}
