// src/components/AdminLayout.jsx
import React from "react";
import { Outlet } from "react-router-dom";
import AdminHeader from "./AdminHeader";

const AdminLayout = () => {
  return (
    <div className="min-h-screen bg-background text-foreground">
      <AdminHeader />
      <main className="container mx-auto p-6 lg:p-8 max-w-7xl">
        <Outlet />
      </main>
    </div>
  );
};

export default AdminLayout;
