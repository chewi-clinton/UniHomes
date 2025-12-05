export const formatFileSize = (bytes) => {
  if (bytes === 0) return '0 Bytes'
  
  const k = 1024
  const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

export const formatDate = (dateString) => {
  const date = new Date(dateString)
  const now = new Date()
  const diffTime = Math.abs(now - date)
  const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24))
  
  if (diffDays === 1) return 'Today'
  if (diffDays === 2) return 'Yesterday'
  if (diffDays <= 7) return `${diffDays - 1} days ago`
  
  return date.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  })
}

export const getFileType = (filename) => {
  const extension = filename.split('.').pop().toLowerCase()
  
  const fileTypes = {
    // Images
    'jpg': 'image', 'jpeg': 'image', 'png': 'image', 'gif': 'image', 
    'svg': 'image', 'webp': 'image', 'bmp': 'image',
    
    // Documents
    'pdf': 'pdf',
    'doc': 'doc', 'docx': 'doc',
    'xls': 'xls', 'xlsx': 'xls',
    'ppt': 'ppt', 'pptx': 'ppt',
    'txt': 'txt',
    
    // Videos
    'mp4': 'video', 'avi': 'video', 'mov': 'video', 
    'wmv': 'video', 'flv': 'video', 'mkv': 'video',
    
    // Audio
    'mp3': 'audio', 'wav': 'audio', 'flac': 'audio', 
    'aac': 'audio', 'ogg': 'audio',
    
    // Archives
    'zip': 'zip', 'rar': 'zip', '7z': 'zip', 
    'tar': 'zip', 'gz': 'zip',
  }
  
  return fileTypes[extension] || 'file'
}

export const generateFileIcon = (fileType) => {
  const icons = {
    'image': '📷',
    'pdf': '📄',
    'doc': '📝',
    'xls': '📊',
    'ppt': '📋',
    'txt': '📄',
    'video': '🎬',
    'audio': '🎵',
    'zip': '📦',
    'folder': '📁',
    'file': '📄'
  }
  
  return icons[fileType] || icons['file']
}

export const debounce = (func, wait) => {
  let timeout
  return function executedFunction(...args) {
    const later = () => {
      clearTimeout(timeout)
      func(...args)
    }
    clearTimeout(timeout)
    timeout = setTimeout(later, wait)
  }
}

export const copyToClipboard = (text) => {
  navigator.clipboard.writeText(text).then(() => {
    // Success message would be handled by the calling component
  }).catch(err => {
    console.error('Failed to copy text: ', err)
  })
}

export const validateEmail = (email) => {
  const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
  return re.test(email)
}

export const generateId = () => {
  return Math.random().toString(36).substr(2, 9)
}