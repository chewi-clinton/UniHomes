// src/components/Header.jsx
import React, { useState, useEffect } from "react";
import {
  Menu,
  Search as SearchIcon,
  Moon,
  Sun,
  UserCircle,
  LogOut,
  Settings,
  User,
} from "lucide-react";
import { useAuth } from "../contexts/AuthContext";
import { useTheme } from "../contexts/ThemeContext";
import { useParams, useNavigate } from "react-router-dom";
import { filesAPI } from "../services/api";
import { toast } from "sonner";
import logo from "../img/logo.png"; // Your FileSphere logo

const Header = ({ onMenuClick, onSearch }) => {
  const [searchQuery, setSearchQuery] = useState("");
  const [allFiles, setAllFiles] = useState([]);
  const [loading, setLoading] = useState(false);
  const [showUserMenu, setShowUserMenu] = useState(false);

  const { folderId } = useParams();
  const { user, logout } = useAuth();
  const { theme, toggleTheme } = useTheme();
  const navigate = useNavigate();

  // Load files when folder changes
  useEffect(() => {
    loadCurrentFolderContents();
  }, [folderId]);

  const loadCurrentFolderContents = async () => {
    try {
      setLoading(true);
      const response = await filesAPI.listFiles(folderId);
      if (response.data.success) {
        const data = response.data.data;
        const folders = (data.folders || []).map((f) => ({
          id: f.folder_id,
          name: f.folder_name,
          type: "folder",
          created_at: f.created_at,
          file_count: f.file_count,
        }));
        const files = (data.files || []).map((f) => ({
          id: f.file_id,
          name: f.filename,
          type: "file",
          size: f.file_size,
          mime_type: f.mime_type,
          created_at: f.created_at,
          is_shared: f.is_shared,
        }));
        const combined = [...folders, ...files];
        setAllFiles(combined);
        setSearchQuery("");
        onSearch?.(combined);
      }
    } catch (err) {
      toast.error("Failed to load folder contents");
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (!searchQuery.trim()) {
      onSearch?.(allFiles);
      return;
    }
    const filtered = allFiles.filter((item) =>
      item.name.toLowerCase().includes(searchQuery.toLowerCase())
    );
    onSearch?.(filtered);
  }, [searchQuery, allFiles, onSearch]);

  const handleLogout = async () => {
    setShowUserMenu(false);
    await logout();
  };

  return (
    <header className="sticky top-0 z-30 bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 border-b border-border">
      <div className="flex items-center justify-between px-4 py-3">
        {/* Left: Logo + Search */}
        <div className="flex items-center space-x-4">
          {/* Mobile Menu */}
          <button
            onClick={onMenuClick}
            className="lg:hidden p-2 rounded-lg hover:bg-accent transition-colors"
          >
            <Menu className="w-5 h-5" />
          </button>

          {/* Logo + Brand */}
          <div className="flex items-center space-x-3">
            <img
              src={logo}
              alt="FileSphere"
              className="w-8 h-8 object-contain rounded"
            />
            <h1 className="hidden md:block text-xl font-bold">FileSphere</h1>
          </div>
        </div>

        {/* Right: Theme + User Menu */}
        <div className="flex items-center space-x-3">
          {/* Theme Toggle */}
          <button
            onClick={toggleTheme}
            className="p-2 rounded-lg hover:bg-accent transition-colors"
            aria-label="Toggle theme"
          >
            {theme === "light" ? (
              <Moon className="w-5 h-5" />
            ) : (
              <Sun className="w-5 h-5" />
            )}
          </button>

          {/* User Menu */}
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

            {showUserMenu && (
              <div className="absolute right-0 mt-2 w-56 bg-popover border border-border rounded-lg shadow-lg py-2 z-50">
                <div className="px-4 py-3 border-b border-border">
                  <p className="text-sm font-semibold">{user?.name}</p>
                  <p className="text-xs text-muted-foreground">{user?.email}</p>
                </div>

                <button
                  onClick={() => {
                    setShowUserMenu(false);
                    navigate("/storage");
                  }}
                  className="w-full px-4 py-2 text-left text-sm hover:bg-accent transition-colors flex items-center space-x-3"
                >
                  <Settings className="w-4 h-4" />
                  <span>Storage</span>
                </button>

                {user?.role === "admin" && (
                  <button
                    onClick={() => {
                      setShowUserMenu(false);
                      navigate("/admin");
                    }}
                    className="w-full px-4 py-2 text-left text-sm hover:bg-accent transition-colors flex items-center space-x-3"
                  >
                    <User className="w-4 h-4" />
                    <span>Admin Panel</span>
                  </button>
                )}

                <div className="border-t border-border mt-2 pt-2">
                  <button
                    onClick={handleLogout}
                    className="w-full px-4 py-2 text-left text-sm hover:bg-accent transition-colors flex items-center space-x-3 text-destructive"
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
  );
};

export default Header;
