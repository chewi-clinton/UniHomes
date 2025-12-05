import React, { useEffect, useRef } from 'react'

const ContextMenu = ({ x, y, onClose, children }) => {
  const menuRef = useRef(null)

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (menuRef.current && !menuRef.current.contains(event.target)) {
        onClose()
      }
    }

    const handleEscape = (event) => {
      if (event.key === 'Escape') {
        onClose()
      }
    }

    document.addEventListener('mousedown', handleClickOutside)
    document.addEventListener('keydown', handleEscape)
    
    return () => {
      document.removeEventListener('mousedown', handleClickOutside)
      document.removeEventListener('keydown', handleEscape)
    }
  }, [onClose])

  // Adjust position to keep menu within viewport
  const adjustPosition = () => {
    const menu = menuRef.current
    if (!menu) return { x, y }

    const rect = menu.getBoundingClientRect()
    const viewportWidth = window.innerWidth
    const viewportHeight = window.innerHeight

    let adjustedX = x
    let adjustedY = y

    // Adjust horizontal position
    if (x + rect.width > viewportWidth) {
      adjustedX = viewportWidth - rect.width - 10
    }

    // Adjust vertical position
    if (y + rect.height > viewportHeight) {
      adjustedY = viewportHeight - rect.height - 10
    }

    return { x: Math.max(10, adjustedX), y: Math.max(10, adjustedY) }
  }

  const position = adjustPosition()

  return (
    <div
      ref={menuRef}
      className="fixed z-50 min-w-[180px] bg-popover border border-border rounded-lg shadow-lg py-1 animate-scale-in"
      style={{
        left: position.x,
        top: position.y,
      }}
    >
      {children}
    </div>
  )
}

export default ContextMenu