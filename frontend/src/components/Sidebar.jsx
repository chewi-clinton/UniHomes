import React from "react";
import { Link, useLocation } from "react-router-dom";
import {
  Folder,
  HardDrive,
  Trash2,
  Users,
  Server,
  Cloud,
  Home,
} from "lucide-react";
import { useAuth } from "../contexts/AuthContext";
import StorageProgress from "./StorageProgress";

const Sidebar = ({ isOpen, onClose }) => {
  const location = useLocation();
  const { user } = useAuth();

  const navigation = [
    { name: "Dashboard", href: "/dashboard", icon: Home },
    { name: "Files", href: "/dashboard", icon: Folder },
    { name: "Shared with Me", href: "/shared", icon: Users }, // Added this line
    { name: "Storage", href: "/storage", icon: HardDrive },
  ];

  const adminNavigation = [
    { name: "Admin Panel", href: "/admin", icon: Server },
  ];

  const isActive = (path) => {
    return (
      location.pathname === path || location.pathname.startsWith(path + "/")
    );
  };

  return (
    <>
      {/* Mobile sidebar */}
      <div
        className={`fixed inset-y-0 left-0 z-50 w-64 bg-card border-r transform transition-transform duration-300 ease-in-out lg:hidden ${
          isOpen ? "translate-x-0" : "-translate-x-full"
        }`}
      >
        <SidebarContent
          navigation={navigation}
          adminNavigation={adminNavigation}
          isActive={isActive}
          user={user}
          onClose={onClose}
        />
      </div>

      {/* Desktop sidebar */}
      <div className="hidden lg:fixed lg:inset-y-0 lg:left-0 lg:z-40 lg:w-64 lg:bg-card lg:border-r">
        <SidebarContent
          navigation={navigation}
          adminNavigation={adminNavigation}
          isActive={isActive}
          user={user}
        />
      </div>
    </>
  );
};

const SidebarContent = ({
  navigation,
  adminNavigation,
  isActive,
  user,
  onClose,
}) => {
  return (
    <div className="flex flex-col h-full">
      {/* Logo */}
      <div className="flex items-center h-16 px-6 border-b">
        <Cloud className="w-8 h-8 text-primary mr-3" />
        <span className="text-xl font-bold">CloudDrive</span>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-4 py-6 space-y-2">
        {navigation.map((item) => {
          const Icon = item.icon;
          return (
            <Link
              key={item.name}
              to={item.href}
              onClick={onClose}
              className={`flex items-center px-4 py-2.5 rounded-lg text-sm font-medium transition-all duration-200 ${
                isActive(item.href)
                  ? "bg-primary text-primary-foreground shadow-lg"
                  : "text-muted-foreground hover:bg-accent hover:text-accent-foreground"
              }`}
            >
              <Icon className="w-5 h-5 mr-3" />
              {item.name}
            </Link>
          );
        })}

        {/* Admin section */}
        {user &&
          (user.role === "admin" || user.email === "admin@clouddrive.com") && (
            <div className="pt-4 mt-4 border-t">
              <p className="px-4 mb-2 text-xs font-medium text-muted-foreground uppercase tracking-wider">
                Admin
              </p>
              {adminNavigation.map((item) => {
                const Icon = item.icon;
                return (
                  <Link
                    key={item.name}
                    to={item.href}
                    onClick={onClose}
                    className={`flex items-center px-4 py-2.5 rounded-lg text-sm font-medium transition-all duration-200 ${
                      isActive(item.href)
                        ? "bg-primary text-primary-foreground shadow-lg"
                        : "text-muted-foreground hover:bg-accent hover:text-accent-foreground"
                    }`}
                  >
                    <Icon className="w-5 h-5 mr-3" />
                    {item.name}
                  </Link>
                );
              })}
            </div>
          )}
      </nav>

      {/* Storage progress */}
      <div className="p-4 border-t">
        <StorageProgress />
      </div>
    </div>
  );
};

export default Sidebar;
