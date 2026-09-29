import api from './api'

export const wishlistService = {
  async getWishlist() {
    const res = await api.get('/wishlist')
    return res.data?.data?.wishlist || []
  },

  async addToWishlist(productId) {
    const res = await api.post('/wishlist', { product_id: productId })
    return res.data
  },

  async removeFromWishlist(productId) {
    const res = await api.delete(`/wishlist/${productId}`)
    return res.data
  },

  async getWishlistRecommendations(topK = 10) {
    const res = await api.get('/wishlist/recommendations', {
      params: { top_k: topK },
    })
    return res.data?.data?.recommendations || []
  },
}
