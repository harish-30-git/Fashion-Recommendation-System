import api from './api'

export const authService = {
  async register(data) {
    const res = await api.post('/auth/register', data)
    return res.data
  },

  async login(credentials) {
    const res = await api.post('/auth/login', credentials)
    return res.data
  },

  async getProfile() {
    const res = await api.get('/auth/me')
    return res.data
  },
}
