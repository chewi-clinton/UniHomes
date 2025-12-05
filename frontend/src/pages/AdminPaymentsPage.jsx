import React, { useState, useEffect } from "react";
import { paymentAPI } from "../services/api";
import { toast } from "sonner";
import {
  DollarSign,
  Package,
  TrendingUp,
  Clock,
  CheckCircle,
  XCircle,
  Filter,
  Download,
} from "lucide-react";
import { formatFileSize, formatDate } from "../utils/helpers";

const AdminPaymentsPage = () => {
  const [stats, setStats] = useState(null);
  const [payments, setPayments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState("");
  const adminKey = sessionStorage.getItem("adminKey");

  useEffect(() => {
    loadData();
  }, [statusFilter]);

  const loadData = async () => {
    try {
      setLoading(true);
      const [statsRes, paymentsRes] = await Promise.all([
        paymentAPI.getPaymentStats(adminKey),
        paymentAPI.getAllPayments(adminKey, 100, statusFilter),
      ]);

      if (statsRes.data.success) {
        setStats(statsRes.data.data);
      }

      if (paymentsRes.data.success) {
        setPayments(paymentsRes.data.data.payments || []);
      }
    } catch (error) {
      toast.error("Failed to load payment data");
      console.error("Error loading payments:", error);
    } finally {
      setLoading(false);
    }
  };

  const getStatusBadge = (status) => {
    const config = {
      completed: {
        icon: CheckCircle,
        class: "bg-green-500/10 text-green-500",
        label: "Completed",
      },
      pending: {
        icon: Clock,
        class: "bg-yellow-500/10 text-yellow-500",
        label: "Pending",
      },
      processing: {
        icon: Clock,
        class: "bg-blue-500/10 text-blue-500",
        label: "Processing",
      },
      failed: {
        icon: XCircle,
        class: "bg-red-500/10 text-red-500",
        label: "Failed",
      },
      cancelled: {
        icon: XCircle,
        class: "bg-gray-500/10 text-gray-500",
        label: "Cancelled",
      },
    };

    const {
      icon: Icon,
      class: className,
      label,
    } = config[status] || config.pending;

    return (
      <div
        className={`flex items-center space-x-1 px-2 py-1 rounded-full text-xs ${className}`}
      >
        <Icon className="w-3 h-3" />
        <span>{label}</span>
      </div>
    );
  };

  const exportCSV = () => {
    const headers = [
      "Transaction Ref",
      "User",
      "Tier",
      "Amount (XAF)",
      "Provider",
      "Status",
      "Date",
    ];

    const rows = payments.map((p) => [
      p.transaction_ref,
      p.user_email,
      p.tier_name,
      p.amount_xaf,
      p.provider,
      p.status,
      formatDate(p.created_at),
    ]);

    const csv = [headers, ...rows].map((row) => row.join(",")).join("\n");
    const blob = new Blob([csv], { type: "text/csv" });
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `payments_${new Date().toISOString().split("T")[0]}.csv`;
    link.click();
    window.URL.revokeObjectURL(url);
  };

  if (loading) {
    return (
      <div className="p-6">
        <div className="h-8 bg-muted rounded w-1/4 mb-6 animate-pulse"></div>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="h-32 bg-muted rounded-lg animate-pulse" />
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold">Payment Management</h1>
          <p className="text-muted-foreground">
            Monitor and manage all payment transactions
          </p>
        </div>
        <button
          onClick={exportCSV}
          className="flex items-center space-x-2 bg-primary text-primary-foreground px-4 py-2 rounded-lg hover:bg-primary/90 transition-colors"
        >
          <Download className="w-4 h-4" />
          <span>Export CSV</span>
        </button>
      </div>

      {/* Stats Cards */}
      {stats && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
          <div className="bg-card border rounded-lg p-6">
            <div className="flex items-center space-x-3 mb-2">
              <div className="p-2 bg-blue-500/10 rounded-lg">
                <DollarSign className="w-5 h-5 text-blue-500" />
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Total Revenue</p>
                <p className="text-2xl font-bold">
                  {stats.total_revenue_xaf} XAF
                </p>
              </div>
            </div>
          </div>

          <div className="bg-card border rounded-lg p-6">
            <div className="flex items-center space-x-3 mb-2">
              <div className="p-2 bg-green-500/10 rounded-lg">
                <CheckCircle className="w-5 h-5 text-green-500" />
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Completed</p>
                <p className="text-2xl font-bold">{stats.completed_payments}</p>
              </div>
            </div>
          </div>

          <div className="bg-card border rounded-lg p-6">
            <div className="flex items-center space-x-3 mb-2">
              <div className="p-2 bg-yellow-500/10 rounded-lg">
                <Clock className="w-5 h-5 text-yellow-500" />
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Pending</p>
                <p className="text-2xl font-bold">{stats.pending_payments}</p>
              </div>
            </div>
          </div>

          <div className="bg-card border rounded-lg p-6">
            <div className="flex items-center space-x-3 mb-2">
              <div className="p-2 bg-purple-500/10 rounded-lg">
                <Package className="w-5 h-5 text-purple-500" />
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Storage Sold</p>
                <p className="text-2xl font-bold">
                  {formatFileSize(stats.total_storage_sold_bytes)}
                </p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Filter */}
      <div className="bg-card border rounded-lg p-4 mb-4">
        <div className="flex items-center space-x-4">
          <Filter className="w-5 h-5 text-muted-foreground" />
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="px-4 py-2 bg-accent border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
          >
            <option value="">All Payments</option>
            <option value="completed">Completed</option>
            <option value="pending">Pending</option>
            <option value="processing">Processing</option>
            <option value="failed">Failed</option>
            <option value="cancelled">Cancelled</option>
          </select>
          <span className="text-sm text-muted-foreground">
            {payments.length} {payments.length === 1 ? "payment" : "payments"}
          </span>
        </div>
      </div>

      {/* Payments Table */}
      <div className="bg-card border rounded-lg overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-accent">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">
                  Transaction
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">
                  User
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">
                  Plan
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">
                  Amount
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">
                  Provider
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">
                  Status
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">
                  Date
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {payments.length === 0 ? (
                <tr>
                  <td
                    colSpan="7"
                    className="px-6 py-8 text-center text-muted-foreground"
                  >
                    No payments found
                  </td>
                </tr>
              ) : (
                payments.map((payment) => (
                  <tr key={payment.payment_id} className="hover:bg-accent/50">
                    <td className="px-6 py-4">
                      <div>
                        <p className="text-sm font-medium">
                          {payment.transaction_ref}
                        </p>
                        <p className="text-xs text-muted-foreground">
                          {payment.phone_number}
                        </p>
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <p className="text-sm">{payment.user_email}</p>
                    </td>
                    <td className="px-6 py-4">
                      <div>
                        <p className="text-sm font-medium">
                          {payment.tier_name}
                        </p>
                        <p className="text-xs text-muted-foreground">
                          {formatFileSize(payment.storage_bytes)}
                        </p>
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <p className="text-sm font-semibold">
                        {payment.amount_xaf} XAF
                      </p>
                    </td>
                    <td className="px-6 py-4">
                      <p className="text-sm capitalize">
                        {payment.provider.replace("_", " ")}
                      </p>
                    </td>
                    <td className="px-6 py-4">
                      {getStatusBadge(payment.status)}
                    </td>
                    <td className="px-6 py-4">
                      <div>
                        <p className="text-sm">
                          {formatDate(payment.created_at)}
                        </p>
                        {payment.completed_at && (
                          <p className="text-xs text-muted-foreground">
                            Completed: {formatDate(payment.completed_at)}
                          </p>
                        )}
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default AdminPaymentsPage;
