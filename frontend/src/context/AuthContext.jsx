import { createContext, useContext, useEffect, useState } from 'react'

const API_BASE = 'http://127.0.0.1:8000'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [token, setToken] = useState(() => localStorage.getItem('travelmind_token') || null)
  const [loading, setLoading] = useState(true)

  // Hydrate user info from backend on mount
  useEffect(() => {
    async function fetchMe() {
      if (!token) {
        setLoading(false)
        return
      }
      try {
        const res = await fetch(`${API_BASE}/auth/me`, {
          headers: { Authorization: `Bearer ${token}` },
        })
        if (res.ok) {
          const userData = await res.json()
          setUser(userData)
        } else {
          // Token expired or invalid
          logout()
        }
      } catch (err) {
        console.error('Failed to fetch user context:', err)
      } finally {
        setLoading(false)
      }
    }
    fetchMe()
  }, [token])

  const login = async (email, password) => {
    const res = await fetch(`${API_BASE}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
    })
    const data = await res.json()
    if (!res.ok) {
      throw new Error(data.detail || 'Login failed')
    }
    setToken(data.access_token)
    setUser(data.user)
    localStorage.setItem('travelmind_token', data.access_token)
    return data.user
  }

  const signup = async (full_name, email, password) => {
    const res = await fetch(`${API_BASE}/auth/signup`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ full_name, email, password }),
    })
    const data = await res.json()
    if (!res.ok) {
      throw new Error(data.detail || 'Signup failed')
    }
    setToken(data.access_token)
    setUser(data.user)
    localStorage.setItem('travelmind_token', data.access_token)
    return data.user
  }

  const logout = () => {
    setToken(null)
    setUser(null)
    localStorage.removeItem('travelmind_token')
  }

  return (
    <AuthContext.Provider value={{ user, token, loading, login, signup, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}
