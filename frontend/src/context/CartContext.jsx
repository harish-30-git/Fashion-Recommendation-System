import React, { createContext, useContext, useState, useEffect, useCallback } from 'react'
import { cartService } from '../services/cartService'
import { wishlistService } from '../services/wishlistService'
import { useAuth } from './AuthContext'

const CartContext = createContext(null)

export function CartProvider({ children }) {
  const { isAuthenticated } = useAuth()
  const [cart, setCart] = useState({ items: [], total: 0, item_count: 0 })
  const [wishlistIds, setWishlistIds] = useState(new Set())
  const [loading, setLoading] = useState(false)

  const refreshCart = useCallback(async () => {
    if (!isAuthenticated) {
      setCart({ items: [], total: 0, item_count: 0 })
      return
    }
    try {
      const data = await cartService.getCart()
      setCart(data)
    } catch {
      // Cart fetch fail safe
    }
  }, [isAuthenticated])

  const refreshWishlist = useCallback(async () => {
    if (!isAuthenticated) {
      setWishlistIds(new Set())
      return
    }
    try {
      const items = await wishlistService.getWishlist()
      const ids = new Set(items.map((item) => item.product_id))
      setWishlistIds(ids)
    } catch {
      // Wishlist fetch fail safe
    }
  }, [isAuthenticated])

  useEffect(() => {
    refreshCart()
    refreshWishlist()
  }, [refreshCart, refreshWishlist])

  const addToCart = async (productId, quantity = 1, size = 'M', color = 'Default') => {
    if (!isAuthenticated) {
      throw new Error('Please login to add products to your cart.')
    }
    setLoading(true)
    try {
      const updated = await cartService.addItem(productId, quantity, size, color)
      setCart(updated)
      return updated
    } finally {
      setLoading(false)
    }
  }

  const updateQuantity = async (productId, quantity) => {
    if (!isAuthenticated) return
    setLoading(true)
    try {
      const updated = await cartService.updateQuantity(productId, quantity)
      setCart(updated)
      return updated
    } finally {
      setLoading(false)
    }
  }

  const removeFromCart = async (productId) => {
    if (!isAuthenticated) return
    setLoading(true)
    try {
      const updated = await cartService.removeItem(productId)
      setCart(updated)
      return updated
    } finally {
      setLoading(false)
    }
  }

  const toggleWishlist = async (productId) => {
    if (!isAuthenticated) {
      throw new Error('Please login to save products to your wishlist.')
    }
    const isSaved = wishlistIds.has(productId)
    if (isSaved) {
      await wishlistService.removeFromWishlist(productId)
      setWishlistIds((prev) => {
        const next = new Set(prev)
        next.delete(productId)
        return next
      })
      return false
    } else {
      await wishlistService.addToWishlist(productId)
      setWishlistIds((prev) => new Set(prev).add(productId))
      return true
    }
  }

  const isInWishlist = (productId) => wishlistIds.has(productId)

  return (
    <CartContext.Provider
      value={{
        cart,
        cartCount: cart.item_count || 0,
        wishlistCount: wishlistIds.size,
        loading,
        addToCart,
        updateQuantity,
        removeFromCart,
        toggleWishlist,
        isInWishlist,
        refreshCart,
        refreshWishlist,
      }}
    >
      {children}
    </CartContext.Provider>
  )
}

export const useCart = () => {
  const context = useContext(CartContext)
  if (!context) {
    throw new Error('useCart must be used within a CartProvider')
  }
  return context
}
