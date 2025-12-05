import { useEffect, useCallback } from 'react'

const useKeyboardShortcuts = (shortcuts, dependencies = []) => {
  const handleKeyPress = useCallback((event) => {
    // Don't handle shortcuts if user is typing in an input
    if (event.target.tagName === 'INPUT' || event.target.tagName === 'TEXTAREA') {
      return
    }

    // Check each shortcut
    shortcuts.forEach(({ key, ctrl = false, shift = false, alt = false, handler }) => {
      const ctrlMatch = ctrl === event.ctrlKey
      const shiftMatch = shift === event.shiftKey
      const altMatch = alt === event.altKey
      const keyMatch = typeof key === 'string' ? event.key.toLowerCase() === key.toLowerCase() : key.test(event.key)

      if (ctrlMatch && shiftMatch && altMatch && keyMatch) {
        event.preventDefault()
        handler(event)
      }
    })
  }, [shortcuts])

  useEffect(() => {
    window.addEventListener('keydown', handleKeyPress)
    return () => {
      window.removeEventListener('keydown', handleKeyPress)
    }
  }, [handleKeyPress, ...dependencies])
}

export default useKeyboardShortcuts