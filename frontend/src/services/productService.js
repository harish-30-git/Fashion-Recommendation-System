import api from './api'

export const productService = {
  async getProducts(params = {}) {
    const res = await api.get('/products', { params })
    return res.data
  },

  async getProductById(productId) {
    const res = await api.get(`/products/${productId}`)
    return res.data
  },

  async searchProducts(query, params = {}) {
    const res = await api.get('/products/search', {
      params: { q: query, ...params },
    })
    return res.data
  },

  async getCategories() {
    const res = await api.get('/products/categories')
    return res.data?.data?.categories || []
  },

  async getBrands(category = null) {
    const res = await api.get('/products/brands', {
      params: category ? { category } : {},
    })
    return res.data?.data?.brands || []
  },
}
