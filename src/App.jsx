import React from "react";
import { Routes, Route, Navigate, Outlet } from "react-router-dom";
import { useAuth } from "./contexts/AuthContext";
import LoginPage from "./pages/LoginPage";
import DashboardPage from "./pages/DashboardPage";
import StoragePage from "./pages/StoragePage";
import AdminPage from "./pages/AdminPage";
import AdminAuthPage from "./pages/AdminAuthPage";
import NotFoundPage from "./pages/NotFoundPage";
import Layout from "./components/Layout";
import LoadingSpinner from "./components/LoadingSpinner";

// Protected Route Component for regular users
const ProtectedRoute = () => {
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <LoadingSpinner />
      </div>
    );
  }

  return isAuthenticated ? <Outlet /> : <Navigate to="/login" />;
};

// Admin Protected Route Component - standalone, doesn't need user auth
const AdminProtectedRoute = () => {
  const adminKey = sessionStorage.getItem("adminKey");

  // If no admin key, redirect to admin auth page
  if (!adminKey) {
    return <Navigate to="/admin/auth" replace />;
  }

  return <Outlet />;
};

// Simple Admin Layout (without user auth requirements)
const AdminLayout = () => {
  return (
    <div className="min-h-screen">
      <Outlet />
    </div>
  );
};

function App() {
  return (
    <div className="min-h-screen bg-background text-foreground transition-colors duration-300">
      <Routes>
        {/* Public Routes */}
        <Route path="/login" element={<LoginPage />} />
        <Route path="/enroll" element={<LoginPage isEnroll={true} />} />

        {/* Admin Authentication Route (public - but checks for existing auth) */}
        <Route path="/admin/auth" element={<AdminAuthPage />} />

        {/* Protected User Routes */}
        <Route element={<ProtectedRoute />}>
          <Route element={<Layout />}>
            <Route path="/dashboard" element={<DashboardPage />} />
            <Route path="/dashboard/:folderId" element={<DashboardPage />} />
            <Route path="/storage" element={<StoragePage />} />
          </Route>
        </Route>

        {/* Admin Routes - separate from user auth */}
        <Route element={<AdminProtectedRoute />}>
          <Route element={<AdminLayout />}>
            <Route path="/admin" element={<AdminPage />} />
          </Route>
        </Route>

        {/* Default redirect */}
        <Route path="/" element={<Navigate to="/dashboard" />} />

        {/* 404 */}
        <Route path="*" element={<NotFoundPage />} />
      </Routes>
    </div>
  );
}

export default App;
