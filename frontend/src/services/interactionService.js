import api from './api'

export const interactionService = {
  async log(productId, interactionType, sessionId = null) {
    try {
      const res = await api.post('/interactions', {
        product_id: productId,
        interaction_type: interactionType,
        session_id: sessionId,
      })
      return res.data
    } catch {
      // Non-blocking interaction log
      return null
    }
  },

  async getHistory(params = {}) {
    const res = await api.get('/interactions/history', { params })
    return res.data
  },
}
