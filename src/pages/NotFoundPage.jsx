import React from 'react'
import { Link } from 'react-router-dom'
import { Home, AlertCircle } from 'lucide-react'

const NotFoundPage = () => {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-100 dark:from-gray-900 dark:to-gray-800">
      <div className="text-center max-w-md mx-4">
        <div className="mb-8">
          <div className="w-24 h-24 mx-auto mb-6 bg-white dark:bg-gray-800 rounded-full shadow-lg flex items-center justify-center">
            <AlertCircle className="w-12 h-12 text-red-500" />
          </div>
          
          <h1 className="text-6xl font-bold text-gray-800 dark:text-white mb-4">404</h1>
          <h2 className="text-2xl font-semibold text-gray-700 dark:text-gray-200 mb-4">
            Page Not Found
          </h2>
          <p className="text-gray-600 dark:text-gray-400 mb-8">
            The page you're looking for doesn't exist. It might have been moved, deleted, or you entered the wrong URL.
          </p>
        </div>

        <div className="space-y-4">
          <Link
            to="/dashboard"
            className="inline-flex items-center space-x-2 bg-primary text-primary-foreground px-6 py-3 rounded-lg font-medium hover:bg-primary/90 transition-colors"
          >
            <Home className="w-4 h-4" />
            <span>Go to Dashboard</span>
          </Link>
          
          <div>
            <button
              onClick={() => window.history.back()}
              className="text-muted-foreground hover:text-foreground transition-colors"
            >
              ← Go back
            </button>
          </div>
        </div>

        {/* Decorative elements */}
        <div className="absolute top-10 left-10 w-20 h-20 bg-blue-200 dark:bg-blue-900 rounded-full opacity-20 animate-pulse"></div>
        <div className="absolute bottom-10 right-10 w-16 h-16 bg-indigo-200 dark:bg-indigo-900 rounded-full opacity-20 animate-pulse delay-1000"></div>
      </div>
    </div>
  )
}

export default NotFoundPage