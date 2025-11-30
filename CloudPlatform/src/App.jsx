import "./App.css";
import { Routes, Route } from "react-router-dom";

import Layout from "./components/Layout";

import Dashboard from "./pages/Dashboard";
import FileManager from "./pages/FileManager";
import AdminDashboard from "./pages/AdminDashboard";
import Node from "./pages/nodes";
import Login from "./pages/login";
import Enrollment from "./pages/enrollment";
import Otpverification from "./pages/Otpverification";

function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/enrollment" element={<Enrollment />} />
      <Route path="/otp" element={<Otpverification />} />

      <Route element={<Layout />}>
        <Route path="/" element={<Dashboard />} />
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/files" element={<FileManager />} />
        <Route path="/nodes" element={<Node />} />
        <Route path="/admin" element={<AdminDashboard />} />
      </Route>

      <Route path="*" element={<Dashboard />} />
    </Routes>
  );
}

export default App;
