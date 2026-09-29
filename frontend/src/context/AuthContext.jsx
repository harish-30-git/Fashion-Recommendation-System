import React, { createContext, useContext, useState, useEffect } from 'react'
import { authService } from '../services/authService'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => {
    const saved = localStorage.getItem('stylesense_user')
    return saved ? JSON.parse(saved) : null
  })
  const [token, setToken] = useState(() => localStorage.getItem('stylesense_token') || null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const initAuth = async () => {
      const storedToken = localStorage.getItem('stylesense_token')
      if (storedToken) {
        try {
          const profile = await authService.getProfile()
          if (profile?.data?.user) {
            setUser(profile.data.user)
            localStorage.setItem('stylesense_user', JSON.stringify(profile.data.user))
          }
        } catch {
          // Token invalid or expired
          logout()
        }
      }
      setLoading(false)
    }

    initAuth()

    const handleExpired = () => {
      logout()
    }
    window.addEventListener('stylesense_auth_expired', handleExpired)
    return () => window.removeEventListener('stylesense_auth_expired', handleExpired)
  }, [])

  const login = async (email, password) => {
    const res = await authService.login({ email, password })
    const { user: userData, access_token } = res.data
    setUser(userData)
    setToken(access_token)
    localStorage.setItem('stylesense_user', JSON.stringify(userData))
    localStorage.setItem('stylesense_token', access_token)
    return userData
  }

  const register = async (formData) => {
    const res = await authService.register(formData)
    const { user: userData, access_token } = res.data
    setUser(userData)
    setToken(access_token)
    localStorage.setItem('stylesense_user', JSON.stringify(userData))
    localStorage.setItem('stylesense_token', access_token)
    return userData
  }

  const logout = () => {
    setUser(null)
    setToken(null)
    localStorage.removeItem('stylesense_user')
    localStorage.removeItem('stylesense_token')
  }

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        isAuthenticated: !!user && !!token,
        loading,
        login,
        register,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = () => {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}
