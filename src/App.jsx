import React from 'react'
import { Routes, Route, Navigate, Outlet } from 'react-router-dom'
import { useAuth } from './contexts/AuthContext'
import LoginPage from './pages/LoginPage'
import DashboardPage from './pages/DashboardPage'
import StoragePage from './pages/StoragePage'
import AdminPage from './pages/AdminPage'
import NotFoundPage from './pages/NotFoundPage'
import Layout from './components/Layout'
import LoadingSpinner from './components/LoadingSpinner'

// Protected Route Component
const ProtectedRoute = () => {
  const { isAuthenticated, isLoading } = useAuth()
  
  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <LoadingSpinner />
      </div>
    )
  }
  
  return isAuthenticated ? <Outlet /> : <Navigate to="/login" />
}

// Admin Route Component
const AdminRoute = () => {
  const { user, isAuthenticated, isLoading } = useAuth()
  
  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <LoadingSpinner />
      </div>
    )
  }
  
  const isAdmin = user && (
    user.email === 'admin@clouddrive.com' || 
    user.role === 'admin' ||
    (user.email && ['admin@clouddrive.com'].includes(user.email))
  )
  
  return isAuthenticated && isAdmin ? <Outlet /> : <Navigate to="/dashboard" />
}

function App() {
  return (
    <div className="min-h-screen bg-background text-foreground transition-colors duration-300">
      <Routes>
        {/* Public Routes */}
        <Route path="/login" element={<LoginPage />} />
        <Route path="/enroll" element={<LoginPage isEnroll={true} />} />
        
        {/* Protected Routes */}
        <Route element={<ProtectedRoute />}>
          <Route element={<Layout />}>
            <Route path="/dashboard" element={<DashboardPage />} />
            <Route path="/dashboard/:folderId" element={<DashboardPage />} />
            <Route path="/storage" element={<StoragePage />} />
            
            {/* Admin Routes */}
            <Route element={<AdminRoute />}>
              <Route path="/admin" element={<AdminPage />} />
            </Route>
          </Route>
        </Route>
        
        {/* Redirects */}
        <Route path="/" element={<Navigate to="/dashboard" />} />
        
        {/* 404 Page */}
        <Route path="*" element={<NotFoundPage />} />
      </Routes>
    </div>
  )
}

export default App