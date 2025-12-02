import React, { useState, useEffect } from 'react'
import { storageAPI } from '../services/api'
import { HardDrive } from 'lucide-react'
import { formatFileSize } from '../utils/helpers'

const StorageProgress = () => {
  const [storage, setStorage] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadStorageInfo()
  }, [])

  const loadStorageInfo = async () => {
    try {
      const response = await storageAPI.getStorageInfo()
      if (response.data.success) {
        setStorage(response.data.data)
      }
    } catch (error) {
      console.error('Failed to load storage info:', error)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="animate-pulse">
        <div className="h-4 bg-muted rounded mb-2"></div>
        <div className="h-2 bg-muted rounded"></div>
      </div>
    )
  }

  if (!storage) return null

  const percentage = Math.round((storage.used / storage.allocated) * 100)
  const isWarning = percentage > 80
  const isDanger = percentage > 95

  return (
    <div>
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center space-x-2">
          <HardDrive className="w-4 h-4 text-muted-foreground" />
          <span className="text-sm font-medium">Storage</span>
        </div>
        <span className="text-xs text-muted-foreground">
          {percentage}%
        </span>
      </div>
      
      <div className="w-full bg-muted rounded-full h-2 mb-1">
        <div 
          className={`h-2 rounded-full transition-all duration-300 ${
            isDanger ? 'bg-destructive' : 
            isWarning ? 'bg-warning' : 
            'bg-primary'
          }`}
          style={{ width: `${Math.min(percentage, 100)}%` }}
        ></div>
      </div>
      
      <div className="flex justify-between text-xs text-muted-foreground">
        <span>{formatFileSize(storage.used)}</span>
        <span>{formatFileSize(storage.allocated)}</span>
      </div>
    </div>
  )
}

export default StorageProgress