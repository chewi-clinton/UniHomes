// src/components/AdminHeader.jsx
import React, { useState } from "react";
import { LogOut, Menu, Moon, Sun } from "lucide-react";
import { useNavigate, useLocation } from "react-router-dom";
import { useTheme } from "../contexts/ThemeContext";
import { toast } from "sonner";
import logo from "../img/logo.png";

const AdminHeader = ({ onMenuClick }) => {
  const navigate = useNavigate();
  const location = useLocation();
  const { theme, toggleTheme } = useTheme();
  const [isLoggingOut, setIsLoggingOut] = useState(false);

  const handleLogout = () => {
    if (isLoggingOut) return;
    setIsLoggingOut(true);
    sessionStorage.removeItem("adminKey");
    toast.success("Admin session ended");
    setTimeout(() => navigate("/admin/auth"), 300);
  };

  const navItems = [
    { path: "/admin", label: "Dashboard" },
    { path: "/admin/nodes", label: "Nodes" },
    { path: "/admin/payments", label: "Payments" },
  ];

  const currentPath = location.pathname;

  return (
    <header className="sticky top-0 z-40 bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 border-b border-border">
      <div className="flex items-center justify-between px-6 py-4">
        {/* Left: Logo + Name + Mobile Menu */}
        <div className="flex items-center space-x-6">
          <button
            onClick={onMenuClick}
            className="lg:hidden p-2 rounded-lg hover:bg-accent transition-colors"
          >
            <Menu className="w-5 h-5" />
          </button>

          <div className="flex items-center space-x-3">
            <img
              src={logo}
              alt="FileSphere"
              className="w-9 h-9 object-contain"
            />
            <h1 className="text-xl font-bold hidden sm:block">FileSphere</h1>
          </div>
        </div>

        {/* Center: Navigation with Animated Underline */}
        <nav className="hidden md:flex items-center space-x-8">
          {navItems.map(({ path, label }) => {
            const isActive = currentPath === path;

            return (
              <button
                key={path}
                onClick={() => navigate(path)}
                className="relative px-3 py-2 text-sm font-medium transition-colors duration-200 hover:text-foreground"
              >
                <span
                  className={
                    isActive ? "text-foreground" : "text-muted-foreground"
                  }
                >
                  {label}
                </span>

                {/* Animated Underline */}
                <span
                  className={`absolute bottom-0 left-0 h-0.5 bg-primary transition-all duration-300 ease-out ${
                    isActive ? "w-full" : "w-0 group-hover:w-full"
                  }`}
                />
              </button>
            );
          })}
        </nav>

        {/* Right: Theme Toggle + Logout */}
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

          {/* Logout Button */}
          <button
            onClick={handleLogout}
            disabled={isLoggingOut}
            className="flex items-center space-x-2 px-4 py-2 bg-destructive/10 text-destructive hover:bg-destructive/20 rounded-lg transition-colors disabled:opacity-50 font-medium"
          >
            <LogOut className="w-4 h-4" />
            <span className="hidden sm:inline">Logout</span>
          </button>
        </div>
      </div>

      {/* Mobile Bottom Navigation with Underline */}
      <nav className="md:hidden border-t border-border bg-background/95 backdrop-blur">
        <div className="flex justify-around py-3">
          {navItems.map(({ path, label }) => {
            const isActive = currentPath === path;

            return (
              <button
                key={path}
                onClick={() => navigate(path)}
                className="relative px-4 py-2 text-sm font-medium transition-colors"
              >
                <span
                  className={
                    isActive ? "text-primary" : "text-muted-foreground"
                  }
                >
                  {label}
                </span>
                {isActive && (
                  <span className="absolute bottom-0 left-0 right-0 h-0.5 bg-primary" />
                )}
              </button>
            );
          })}
        </div>
      </nav>
    </header>
  );
};

export default AdminHeader;
