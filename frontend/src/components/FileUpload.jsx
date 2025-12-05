import React, { useState } from 'react'
import { X, Upload, File, CheckCircle } from 'lucide-react'

const FileUpload = ({ onClose, onUpload }) => {
  const [uploads, setUploads] = useState([])
  const [isDragging, setIsDragging] = useState(false)

  const handleFileSelect = async (files) => {
    const fileArray = Array.from(files)
    
    const newUploads = fileArray.map((file) => ({
      file,
      id: Math.random().toString(36).substr(2, 9),
      progress: 0,
      status: 'pending',
      error: null,
    }))
    
    setUploads((prev) => [...prev, ...newUploads])
    
    // Start uploading each file
    newUploads.forEach((upload) => {
      handleUpload(upload)
    })
  }

  const handleUpload = async (upload) => {
    try {
      setUploads((prev) =>
        prev.map((u) =>
          u.id === upload.id ? { ...u, status: 'uploading' } : u
        )
      )

      await onUpload(upload.file, (progress) => {
        setUploads((prev) =>
          prev.map((u) =>
            u.id === upload.id ? { ...u, progress } : u
          )
        )
      })

      setUploads((prev) =>
        prev.map((u) =>
          u.id === upload.id ? { ...u, status: 'completed', progress: 100 } : u
        )
      )
    } catch (error) {
      setUploads((prev) =>
        prev.map((u) =>
          u.id === upload.id ? { ...u, status: 'error', error: error.message } : u
        )
      )
    }
  }

  const removeUpload = (id) => {
    setUploads((prev) => prev.filter((u) => u.id !== id))
  }

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes'
    const k = 1024
    const sizes = ['Bytes', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
  }

  const handleDragOver = (e) => {
    e.preventDefault()
    setIsDragging(true)
  }

  const handleDragLeave = (e) => {
    e.preventDefault()
    setIsDragging(false)
  }

  const handleDrop = (e) => {
    e.preventDefault()
    setIsDragging(false)
    handleFileSelect(e.dataTransfer.files)
  }

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 animate-fade-in">
      <div className="bg-card rounded-lg shadow-xl w-full max-w-2xl max-h-[80vh] overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b">
          <h2 className="text-xl font-semibold">Upload Files</h2>
          <button
            onClick={onClose}
            className="p-2 hover:bg-accent rounded-lg transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Upload Area */}
        <div
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          className={`p-12 border-2 border-dashed border-border rounded-lg m-6 text-center transition-colors ${
            isDragging ? 'border-primary bg-primary/5' : 'hover:border-primary/50'
          }`}
        >
          <Upload className="w-12 h-12 mx-auto mb-4 text-muted-foreground" />
          <p className="text-lg font-medium mb-2">
            {isDragging ? 'Drop files here' : 'Drag & drop files here'}
          </p>
          <p className="text-muted-foreground mb-4">or</p>
          <input
            type="file"
            multiple
            onChange={(e) => handleFileSelect(e.target.files)}
            className="hidden"
            id="file-upload"
          />
          <label
            htmlFor="file-upload"
            className="bg-primary text-primary-foreground px-6 py-2 rounded-lg font-medium hover:bg-primary/90 transition-colors cursor-pointer"
          >
            Choose Files
          </label>
        </div>

        {/* Upload Progress */}
        {uploads.length > 0 && (
          <div className="px-6 pb-6">
            <h3 className="font-medium mb-4">Uploading Files</h3>
            <div className="space-y-3 max-h-64 overflow-y-auto">
              {uploads.map((upload) => (
                <div key={upload.id} className="flex items-center space-x-3 p-3 bg-accent rounded-lg">
                  <File className="w-8 h-8 text-muted-foreground flex-shrink-0" />
                  
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium truncate">{upload.file.name}</p>
                    <p className="text-xs text-muted-foreground">
                      {formatFileSize(upload.file.size)}
                    </p>
                    
                    {upload.status === 'uploading' && (
                      <div className="mt-2">
                        <div className="w-full bg-muted rounded-full h-1.5">
                          <div
                            className="bg-primary h-1.5 rounded-full transition-all duration-300"
                            style={{ width: `${upload.progress}%` }}
                          ></div>
                        </div>
                        <p className="text-xs text-muted-foreground mt-1">
                          {upload.progress}% uploaded
                        </p>
                      </div>
                    )}
                    
                    {upload.status === 'completed' && (
                      <div className="flex items-center mt-2 text-green-500">
                        <CheckCircle className="w-4 h-4 mr-1" />
                        <span className="text-xs">Upload complete</span>
                      </div>
                    )}
                    
                    {upload.status === 'error' && (
                      <div className="mt-2">
                        <p className="text-xs text-destructive">{upload.error}</p>
                      </div>
                    )}
                  </div>
                  
                  <button
                    onClick={() => removeUpload(upload.id)}
                    className="p-1 hover:bg-accent rounded transition-colors"
                  >
                    <X className="w-4 h-4" />
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default FileUpload