import React from 'react'
import { Link } from 'react-router-dom'
import { Trash2, Plus, Minus, AlertCircle } from 'lucide-react'
import { formatCurrency } from '../../utils/formatCurrency'

export default function CartItem({ item, onUpdateQuantity, onRemove }) {
  const isOutOfStock = item.in_stock === false

  return (
    <div className="flex gap-4 sm:gap-6 py-5 border-b border-neutral-100 last:border-0">
      {/* Product Image */}
      <Link
        to={`/products/${item.product_id}`}
        className="w-20 h-24 sm:w-24 sm:h-30 rounded-xl bg-neutral-100 overflow-hidden flex-shrink-0 border border-neutral-200/60"
      >
        <img
          src={item.image_url || `https://picsum.photos/seed/${item.product_id}/200/250`}
          alt={item.name}
          className="w-full h-full object-cover object-center hover:scale-105 transition-transform"
        />
      </Link>

      {/* Item Details */}
      <div className="flex-1 flex flex-col justify-between">
        <div>
          <div className="flex items-start justify-between gap-2">
            <div>
              <p className="text-[11px] font-bold text-neutral-400 uppercase tracking-wider">
                {item.brand || 'StyleSense'}
              </p>
              <Link
                to={`/products/${item.product_id}`}
                className="text-xs sm:text-sm font-semibold text-neutral-800 hover:text-indigo-600 transition-colors line-clamp-1"
              >
                {item.name || `Product ${item.product_id}`}
              </Link>
            </div>
            {/* Price */}
            <span className="text-sm sm:text-base font-bold text-neutral-900 whitespace-nowrap">
              {formatCurrency(item.unit_price * item.quantity)}
            </span>
          </div>

          {/* Size & Color Tags */}
          <div className="flex items-center gap-3 text-xs text-neutral-500 mt-1.5">
            {item.size && (
              <span className="bg-neutral-100 px-2 py-0.5 rounded-md font-medium text-neutral-700">
                Size: <span className="font-bold">{item.size}</span>
              </span>
            )}
            {item.color && item.color !== 'Default' && (
              <span className="bg-neutral-100 px-2 py-0.5 rounded-md font-medium text-neutral-700">
                Color: <span className="font-bold">{item.color}</span>
              </span>
            )}
          </div>

          {/* Out of Stock Warning */}
          {isOutOfStock && (
            <div className="flex items-center gap-1.5 text-xs text-rose-600 font-semibold mt-2">
              <AlertCircle className="w-3.5 h-3.5" />
              Item is currently out of stock. Please remove to proceed.
            </div>
          )}
        </div>

        {/* Quantity Controls & Remove */}
        <div className="flex items-center justify-between mt-4">
          <div className="flex items-center border border-neutral-200 rounded-xl overflow-hidden bg-neutral-50/50">
            <button
              onClick={() => onUpdateQuantity(item.product_id, item.quantity - 1)}
              disabled={item.quantity <= 1}
              className="p-1.5 sm:p-2 text-neutral-600 hover:text-neutral-900 disabled:opacity-30 disabled:cursor-not-allowed hover:bg-neutral-100 transition-colors"
              aria-label="Decrease quantity"
            >
              <Minus className="w-3.5 h-3.5" />
            </button>
            <span className="px-3 text-xs font-bold text-neutral-800 select-none">
              {item.quantity}
            </span>
            <button
              onClick={() => onUpdateQuantity(item.product_id, item.quantity + 1)}
              disabled={item.available_stock && item.quantity >= item.available_stock}
              className="p-1.5 sm:p-2 text-neutral-600 hover:text-neutral-900 disabled:opacity-30 disabled:cursor-not-allowed hover:bg-neutral-100 transition-colors"
              aria-label="Increase quantity"
            >
              <Plus className="w-3.5 h-3.5" />
            </button>
          </div>

          <button
            onClick={() => onRemove(item.product_id)}
            className="text-xs text-neutral-400 hover:text-rose-600 flex items-center gap-1 transition-colors p-1.5"
          >
            <Trash2 className="w-3.5 h-3.5" />
            <span className="hidden sm:inline">Remove</span>
          </button>
        </div>
      </div>
    </div>
  )
}
