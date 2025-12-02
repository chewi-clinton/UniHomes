import React, { useState } from 'react'
import { Menu, Search, Moon, Sun, User, LogOut, Settings, UserCircle } from 'lucide-react'
import { useAuth } from '../contexts/AuthContext'
import { useTheme } from '../contexts/ThemeContext'
import { useLocation, useNavigate } from 'react-router-dom'
import { toast } from 'sonner'

const Header = ({ onMenuClick }) => {
  const [searchQuery, setSearchQuery] = useState('')
  const [showUserMenu, setShowUserMenu] = useState(false)
  const { user, logout } = useAuth()
  const { theme, toggleTheme } = useTheme()
  const location = useLocation()
  const navigate = useNavigate()

  const handleSearch = (e) => {
    e.preventDefault()
    if (searchQuery.trim()) {
      toast.info('Search functionality coming soon!')
    }
  }

  const handleLogout = async () => {
    await logout()
  }

  return (
    <header className="sticky top-0 z-30 bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 border-b">
      <div className="flex items-center justify-between px-4 py-3">
        {/* Left side */}
        <div className="flex items-center space-x-4">
          <button
            onClick={onMenuClick}
            className="lg:hidden p-2 rounded-lg hover:bg-accent transition-colors"
          >
            <Menu className="w-5 h-5" />
          </button>
          
          {/* Search */}
          <form onSubmit={handleSearch} className="hidden md:block">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-muted-foreground" />
              <input
                type="text"
                placeholder="Search files..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-10 pr-4 py-2 w-64 bg-accent rounded-lg focus:outline-none focus:ring-2 focus:ring-primary transition-all"
              />
            </div>
          </form>
        </div>

        {/* Right side */}
        <div className="flex items-center space-x-3">
          {/* Theme toggle */}
          <button
            onClick={toggleTheme}
            className="p-2 rounded-lg hover:bg-accent transition-colors"
          >
            {theme === 'light' ? (
              <Moon className="w-5 h-5" />
            ) : (
              <Sun className="w-5 h-5" />
            )}
          </button>

          {/* User menu */}
          <div className="relative">
            <button
              onClick={() => setShowUserMenu(!showUserMenu)}
              className="flex items-center space-x-2 p-2 rounded-lg hover:bg-accent transition-colors"
            >
              <UserCircle className="w-6 h-6" />
              <span className="hidden sm:block text-sm font-medium">
                {user?.name || user?.email}
              </span>
            </button>

            {/* Dropdown menu */}
            {showUserMenu && (
              <div className="absolute right-0 mt-2 w-48 bg-popover border rounded-lg shadow-lg py-2 animate-scale-in">
                <div className="px-4 py-2 border-b">
                  <p className="text-sm font-medium">{user?.name}</p>
                  <p className="text-xs text-muted-foreground">{user?.email}</p>
                </div>
                
                <button
                  onClick={() => {
                    setShowUserMenu(false)
                    navigate('/storage')
                  }}
                  className="w-full px-4 py-2 text-left text-sm hover:bg-accent transition-colors flex items-center space-x-2"
                >
                  <Settings className="w-4 h-4" />
                  <span>Storage</span>
                </button>
                
                {user?.role === 'admin' && (
                  <button
                    onClick={() => {
                      setShowUserMenu(false)
                      navigate('/admin')
                    }}
                    className="w-full px-4 py-2 text-left text-sm hover:bg-accent transition-colors flex items-center space-x-2"
                  >
                    <User className="w-4 h-4" />
                    <span>Admin Panel</span>
                  </button>
                )}
                
                <div className="border-t mt-2 pt-2">
                  <button
                    onClick={handleLogout}
                    className="w-full px-4 py-2 text-left text-sm hover:bg-accent transition-colors flex items-center space-x-2 text-destructive"
                  >
                    <LogOut className="w-4 h-4" />
                    <span>Sign out</span>
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </header>
  )
}

export default Header