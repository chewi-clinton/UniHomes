import React from 'react'

const LoadingSpinner = ({ size = 'md', className = '' }) => {
  const sizeClasses = {
    sm: 'w-4 h-4',
    md: 'w-8 h-8',
    lg: 'w-12 h-12',
    xl: 'w-16 h-16',
  }

  return (
    <div className={`flex items-center justify-center ${className}`}>
      <div className={`${sizeClasses[size]} animate-spin`}>
        <div className="w-full h-full border-2 border-primary border-t-transparent rounded-full"></div>
      </div>
    </div>
  )
}

// Skeleton loader for files
export const FileSkeleton = ({ count = 6 }) => {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
      {Array.from({ length: count }).map((_, index) => (
        <div key={index} className="bg-card border rounded-lg p-4 animate-pulse">
          <div className="w-12 h-12 bg-muted rounded-lg mb-3"></div>
          <div className="h-4 bg-muted rounded mb-2"></div>
          <div className="h-3 bg-muted rounded w-2/3"></div>
        </div>
      ))}
    </div>
  )
}

// Skeleton loader for list view
export const ListSkeleton = ({ count = 10 }) => {
  return (
    <div className="space-y-2">
      {Array.from({ length: count }).map((_, index) => (
        <div key={index} className="bg-card border rounded-lg p-3 animate-pulse flex items-center space-x-4">
          <div className="w-10 h-10 bg-muted rounded"></div>
          <div className="flex-1">
            <div className="h-4 bg-muted rounded mb-1 w-1/3"></div>
            <div className="h-3 bg-muted rounded w-1/4"></div>
          </div>
          <div className="h-3 bg-muted rounded w-20"></div>
        </div>
      ))}
    </div>
  )
}

export default LoadingSpinner