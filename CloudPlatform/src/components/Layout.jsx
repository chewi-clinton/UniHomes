// src/components/Layout.jsx
import React from "react"; // ← REQUIRED in .jsx files with JSX
import { Outlet } from "react-router-dom";
import Header from "./Header"; // ← adjust path if needed

const Layout = () => {
  return (
    <>
      <Header />
      <main style={{ marginTop: "70px" }}>
        <Outlet />
      </main>
    </>
  );
};

export default Layout; // ← This is correct
