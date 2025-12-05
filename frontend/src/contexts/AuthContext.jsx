import React, { createContext, useContext, useState, useEffect } from 'react'
import { authAPI } from '../services/api'
import { toast } from 'sonner'

const AuthContext = createContext({})

export const useAuth = () => {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null)
  const [isLoading, setIsLoading] = useState(true)
  const [isAuthenticated, setIsAuthenticated] = useState(false)

  useEffect(() => {
    const token = localStorage.getItem('auth_token')
    const userData = localStorage.getItem('user')
    
    if (token && userData) {
      setUser(JSON.parse(userData))
      setIsAuthenticated(true)
    }
    setIsLoading(false)
  }, [])

  const sendOTP = async (email) => {
    try {
      const response = await authAPI.sendOTP(email)
      if (response.data.success) {
        toast.success('OTP sent to your email')
        return true
      }
    } catch (error) {
      toast.error(error.response?.data?.error || 'Failed to send OTP')
    }
    return false
  }

  const verifyOTP = async (email, otp) => {
    try {
      const response = await authAPI.verifyOTP(email, otp)
      if (response.data.success) {
        return response.data.data
      }
    } catch (error) {
      toast.error(error.response?.data?.error || 'Invalid OTP')
    }
    return null
  }

  const enroll = async (email, name) => {
    try {
      const response = await authAPI.enroll(email, name)
      if (response.data.success) {
        const { token, user: userData } = response.data.data
        localStorage.setItem('auth_token', token)
        localStorage.setItem('user', JSON.stringify(userData))
        setUser(userData)
        setIsAuthenticated(true)
        toast.success('Account created successfully!')
        return true
      }
    } catch (error) {
      toast.error(error.response?.data?.error || 'Enrollment failed')
    }
    return false
  }

  const login = async (email) => {
    try {
      const response = await authAPI.login(email)
      if (response.data.success) {
        const { token, user: userData } = response.data.data
        localStorage.setItem('auth_token', token)
        localStorage.setItem('user', JSON.stringify(userData))
        setUser(userData)
        setIsAuthenticated(true)
        toast.success('Welcome back!')
        return true
      }
    } catch (error) {
      toast.error(error.response?.data?.error || 'Login failed')
    }
    return false
  }

  const logout = async () => {
    try {
      await authAPI.logout()
    } catch (error) {
      console.error('Logout error:', error)
    } finally {
      localStorage.removeItem('auth_token')
      localStorage.removeItem('user')
      setUser(null)
      setIsAuthenticated(false)
      window.location.href = '/login'
    }
  }

  const value = {
    user,
    isLoading,
    isAuthenticated,
    sendOTP,
    verifyOTP,
    enroll,
    login,
    logout,
  }

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  )
}