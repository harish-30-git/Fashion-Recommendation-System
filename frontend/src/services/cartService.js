import api from './api'

export const cartService = {
  async getCart() {
    const res = await api.get('/cart')
    return res.data?.data?.cart || { items: [], total: 0 }
  },

  async addItem(productId, quantity = 1, size = 'M', color = 'Default') {
    const res = await api.post('/cart/items', {
      product_id: productId,
      quantity,
      size,
      color,
    })
    return res.data?.data?.cart
  },

  async updateQuantity(productId, quantity) {
    const res = await api.patch(`/cart/items/${productId}`, {
      quantity,
    })
    return res.data?.data?.cart
  },

  async removeItem(productId) {
    const res = await api.delete(`/cart/items/${productId}`)
    return res.data?.data?.cart
  },

  async clearCart() {
    const res = await api.delete('/cart')
    return res.data?.data?.cart
  },
}
