import React, { useState, useEffect } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { ChevronRight, Home } from 'lucide-react'
import { filesAPI } from '../services/api'

const Breadcrumb = ({ folderId }) => {
  const [path, setPath] = useState([])
  const navigate = useNavigate()

  useEffect(() => {
    if (folderId) {
      loadFolderPath(folderId)
    } else {
      setPath([])
    }
  }, [folderId])

  const loadFolderPath = async (id) => {
    try {
      // This would need to be implemented in your backend
      // For now, we'll create a simple path structure
      const response = await filesAPI.listFiles()
      if (response.data.success) {
        // Mock path loading - in real app, this would come from API
        setPath([
          { id: 'root', name: 'Home' },
          { id: folderId, name: 'Current Folder' }
        ])
      }
    } catch (error) {
      console.error('Error loading folder path:', error)
    }
  }

  return (
    <nav className="flex items-center space-x-2 text-sm mb-6">
      <Link
        to="/dashboard"
        className="flex items-center space-x-1 text-muted-foreground hover:text-foreground transition-colors"
      >
        <Home className="w-4 h-4" />
        <span>Home</span>
      </Link>
      
      {path.slice(1).map((folder, index) => (
        <React.Fragment key={folder.id}>
          <ChevronRight className="w-4 h-4 text-muted-foreground" />
          <Link
            to={`/dashboard/${folder.id}`}
            className="text-muted-foreground hover:text-foreground transition-colors"
          >
            {folder.name}
          </Link>
        </React.Fragment>
      ))}
    </nav>
  )
}

export default Breadcrumb