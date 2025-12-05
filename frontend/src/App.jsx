import React from "react";
import { Routes, Route, Navigate, Outlet } from "react-router-dom";
import { useAuth } from "./contexts/AuthContext";
import LoginPage from "./pages/LoginPage";
import DashboardPage from "./pages/DashboardPage";
import StoragePage from "./pages/StoragePage";
import PaymentPage from "./pages/PaymentPage";
import AdminPage from "./pages/AdminPage";
import AdminAuthPage from "./pages/AdminAuthPage";
import AdminNodeManagerPage from "./pages/AdminNodeManagerPage";
import AdminPaymentsPage from "./pages/AdminPaymentsPage";
import NotFoundPage from "./pages/NotFoundPage";
import SharedFilesPage from "./pages/SharedFilesPage";
import LoadingSpinner from "./components/LoadingSpinner";

// Layouts
import Layout from "./components/Layout"; // User layout (with Header, Sidebar)
import AdminLayout from "./components/AdminLayout"; // New admin layout (with AdminHeader)

// Protected Route for regular users
const ProtectedRoute = () => {
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <LoadingSpinner />
      </div>
    );
  }

  return isAuthenticated ? <Outlet /> : <Navigate to="/login" replace />;
};

// Admin Protected Route (independent of user auth)
const AdminProtectedRoute = () => {
  const adminKey = sessionStorage.getItem("adminKey");
  return adminKey ? <Outlet /> : <Navigate to="/admin/auth" replace />;
};

function App() {
  return (
    <div className="min-h-screen bg-background text-foreground transition-colors duration-300">
      <Routes>
        {/* Public Routes */}
        <Route path="/login" element={<LoginPage />} />
        <Route path="/enroll" element={<LoginPage isEnroll={true} />} />

        {/* Admin Authentication (public but protected by key check) */}
        <Route path="/admin/auth" element={<AdminAuthPage />} />

        {/* Protected User Routes */}
        <Route element={<ProtectedRoute />}>
          <Route element={<Layout />}>
            <Route path="/dashboard" element={<DashboardPage />} />
            <Route path="/dashboard/:folderId" element={<DashboardPage />} />
            <Route path="/shared" element={<SharedFilesPage />} />
            <Route path="/storage" element={<StoragePage />} />
            <Route path="/purchase" element={<PaymentPage />} />
          </Route>
        </Route>

        {/* Admin Section - completely separate layout & auth */}
        <Route element={<AdminProtectedRoute />}>
          <Route element={<AdminLayout />}>
            <Route path="/admin" element={<AdminPage />} />
            <Route path="/admin/nodes" element={<AdminNodeManagerPage />} />
            <Route path="/admin/payments" element={<AdminPaymentsPage />} />
          </Route>
        </Route>

        {/* Default Redirects */}
        <Route path="/" element={<Navigate to="/dashboard" replace />} />
        <Route path="*" element={<NotFoundPage />} />
      </Routes>
    </div>
  );
}

export default App;
