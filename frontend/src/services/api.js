import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api'

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Attach JWT access token to every outgoing request if available
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('stylesense_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

// Intercept 401 unauthorized errors (e.g. expired tokens)
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && error.response.status === 401) {
      // Check if it's an expired token error from backend
      const errorCode = error.response.data?.error
      if (errorCode === 'TOKEN_EXPIRED' || errorCode === 'UNAUTHORIZED') {
        localStorage.removeItem('stylesense_token')
        localStorage.removeItem('stylesense_user')
        window.dispatchEvent(new Event('stylesense_auth_expired'))
      }
    }
    return Promise.reject(error)
  }
)

export default api
