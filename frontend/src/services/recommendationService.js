import api from './api'

export const recommendationService = {
  async getPersonalized(topK = 10) {
    const res = await api.get('/recommendations/personalized', {
      params: { top_k: topK },
    })
    return res.data?.data?.recommendations || []
  },

  async getSimilar(productId, topK = 10) {
    const res = await api.get(`/recommendations/similar/${productId}`, {
      params: { top_k: topK },
    })
    return res.data?.data?.similar_products || []
  },

  async getTrending(category = null, topK = 20) {
    const res = await api.get('/recommendations/trending', {
      params: {
        ...(category ? { category } : {}),
        top_k: topK,
      },
    })
    return res.data?.data?.trending_products || []
  },

  async getComplementary(productId, topK = 6) {
    const res = await api.get(`/recommendations/complementary/${productId}`, {
      params: { top_k: topK },
    })
    return res.data?.data?.complementary_products || []
  },
}
