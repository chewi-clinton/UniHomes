import React, { useState, useEffect } from "react";
import { paymentAPI } from "../services/api";
import { toast } from "sonner";
import {
  CreditCard,
  Package,
  Clock,
  CheckCircle,
  XCircle,
  Loader2,
  ArrowRight,
  History,
} from "lucide-react";
import { formatFileSize, formatDate } from "../utils/helpers";

const PaymentPage = () => {
  const [tiers, setTiers] = useState([]);
  const [selectedTier, setSelectedTier] = useState(null);
  const [provider, setProvider] = useState("mtn_momo");
  const [phoneNumber, setPhoneNumber] = useState("");
  const [loading, setLoading] = useState(true);
  const [processing, setProcessing] = useState(false);
  const [currentPayment, setCurrentPayment] = useState(null);
  const [paymentHistory, setPaymentHistory] = useState([]);
  const [showHistory, setShowHistory] = useState(false);

  useEffect(() => {
    loadTiers();
    loadHistory();
  }, []);

  const loadTiers = async () => {
    try {
      setLoading(true);
      const response = await paymentAPI.getTiers();
      if (response.data.success) {
        setTiers(response.data.data.tiers || []);
      }
    } catch (error) {
      toast.error("Failed to load storage tiers");
      console.error("Error loading tiers:", error);
    } finally {
      setLoading(false);
    }
  };

  const loadHistory = async () => {
    try {
      const response = await paymentAPI.getHistory(10);
      if (response.data.success) {
        setPaymentHistory(response.data.data.payments || []);
      }
    } catch (error) {
      console.error("Error loading payment history:", error);
    }
  };

  const handlePurchase = async () => {
    if (!selectedTier) {
      toast.error("Please select a storage tier");
      return;
    }

    if (!phoneNumber.trim()) {
      toast.error("Please enter your phone number");
      return;
    }

    // Validate phone format
    const cleanPhone = phoneNumber.replace(/\s+/g, "");
    if (!/^(\+?237)?[0-9]{9}$/.test(cleanPhone)) {
      toast.error(
        "Invalid phone number format. Use: 237XXXXXXXXX or XXXXXXXXX"
      );
      return;
    }

    try {
      setProcessing(true);
      const response = await paymentAPI.initiatePayment(
        selectedTier.tier_id,
        provider,
        cleanPhone
      );

      if (response.data.success) {
        const paymentData = response.data.data;
        setCurrentPayment(paymentData);
        toast.success(
          "Payment initiated! Please check your phone to complete the payment."
        );

        // Start polling for payment status
        pollPaymentStatus(paymentData.payment_id);
      }
    } catch (error) {
      const errorMsg =
        error.response?.data?.message || "Failed to initiate payment";
      toast.error(errorMsg);
      console.error("Payment error:", error);
    } finally {
      setProcessing(false);
    }
  };

  const pollPaymentStatus = async (paymentId) => {
    let attempts = 0;
    const maxAttempts = 60; // Poll for 5 minutes (every 5 seconds)

    const poll = setInterval(async () => {
      attempts++;

      try {
        const response = await paymentAPI.checkStatus(paymentId);
        if (response.data.success) {
          const { status, storage_added } = response.data.data;

          if (status === "completed") {
            clearInterval(poll);
            setCurrentPayment(null);
            toast.success(
              `Payment successful! ${formatFileSize(
                storage_added
              )} added to your account.`
            );
            loadHistory();
            // Reset form
            setSelectedTier(null);
            setPhoneNumber("");
          } else if (status === "failed" || status === "cancelled") {
            clearInterval(poll);
            setCurrentPayment(null);
            toast.error(`Payment ${status}`);
            loadHistory();
          } else if (attempts >= maxAttempts) {
            clearInterval(poll);
            setCurrentPayment(null);
            toast.error("Payment timeout. Please check your payment history.");
          }
        }
      } catch (error) {
        console.error("Status check error:", error);
      }
    }, 5000); // Check every 5 seconds
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case "completed":
        return <CheckCircle className="w-5 h-5 text-green-500" />;
      case "failed":
      case "cancelled":
        return <XCircle className="w-5 h-5 text-red-500" />;
      case "processing":
      case "pending":
        return <Loader2 className="w-5 h-5 text-yellow-500 animate-spin" />;
      default:
        return <Clock className="w-5 h-5 text-gray-500" />;
    }
  };

  if (loading) {
    return (
      <div className="p-6">
        <div className="max-w-4xl mx-auto">
          <div className="h-8 bg-muted rounded w-1/4 mb-6 animate-pulse"></div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {[1, 2, 3].map((i) => (
              <div key={i} className="h-48 bg-muted rounded-lg animate-pulse" />
            ))}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center space-x-3">
              <div className="p-2 bg-primary/10 rounded-lg">
                <CreditCard className="w-6 h-6 text-primary" />
              </div>
              <h1 className="text-2xl font-bold">Purchase Storage</h1>
            </div>
            <button
              onClick={() => setShowHistory(!showHistory)}
              className="flex items-center space-x-2 px-4 py-2 bg-accent rounded-lg hover:bg-accent/80 transition-colors"
            >
              <History className="w-4 h-4" />
              <span>{showHistory ? "Hide" : "Show"} History</span>
            </button>
          </div>
          <p className="text-muted-foreground">
            Expand your storage with our flexible plans
          </p>
        </div>

        {/* Payment History */}
        {showHistory && paymentHistory.length > 0 && (
          <div className="mb-8 bg-card border rounded-lg p-6">
            <h2 className="text-lg font-semibold mb-4">Recent Payments</h2>
            <div className="space-y-3">
              {paymentHistory.slice(0, 5).map((payment) => (
                <div
                  key={payment.payment_id}
                  className="flex items-center justify-between p-3 bg-accent/50 rounded-lg"
                >
                  <div className="flex items-center space-x-3">
                    {getStatusIcon(payment.status)}
                    <div>
                      <p className="font-medium">{payment.tier_name}</p>
                      <p className="text-sm text-muted-foreground">
                        {formatDate(payment.created_at)}
                      </p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="font-semibold">{payment.amount_xaf} XAF</p>
                    <p className="text-sm text-muted-foreground">
                      {formatFileSize(payment.storage_bytes)}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Current Payment Status */}
        {currentPayment && (
          <div className="mb-8 bg-yellow-500/10 border border-yellow-500/20 rounded-lg p-6">
            <div className="flex items-center space-x-3 mb-4">
              <Loader2 className="w-6 h-6 text-yellow-500 animate-spin" />
              <h2 className="text-lg font-semibold">Payment Processing</h2>
            </div>
            <p className="text-muted-foreground mb-2">
              Transaction Reference: {currentPayment.transaction_ref}
            </p>
            <p className="text-muted-foreground">
              Please check your phone and enter your PIN to complete the
              payment. This page will update automatically once payment is
              confirmed.
            </p>
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Storage Tiers */}
          <div className="lg:col-span-2">
            <h2 className="text-lg font-semibold mb-4">
              Choose Your Storage Plan
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {tiers.map((tier) => (
                <div
                  key={tier.tier_id}
                  onClick={() => setSelectedTier(tier)}
                  className={`bg-card border rounded-lg p-6 cursor-pointer transition-all hover:shadow-lg ${
                    selectedTier?.tier_id === tier.tier_id
                      ? "border-primary ring-2 ring-primary/20"
                      : "border-border"
                  }`}
                >
                  <div className="flex items-start justify-between mb-4">
                    <div>
                      <h3 className="font-bold text-xl mb-1">
                        {tier.display_name}
                      </h3>
                      <p className="text-2xl font-bold text-primary">
                        {tier.price_xaf} XAF
                      </p>
                    </div>
                    <Package className="w-8 h-8 text-primary/50" />
                  </div>
                  <div className="space-y-2 mb-4">
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-muted-foreground">Storage:</span>
                      <span className="font-semibold">
                        {formatFileSize(tier.storage_bytes)}
                      </span>
                    </div>
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-muted-foreground">Price/GB:</span>
                      <span className="font-semibold">
                        {Math.round(tier.price_xaf / tier.storage_gb)} XAF
                      </span>
                    </div>
                  </div>
                  <p className="text-sm text-muted-foreground">
                    {tier.description}
                  </p>
                  {selectedTier?.tier_id === tier.tier_id && (
                    <div className="mt-4 flex items-center space-x-2 text-primary text-sm font-medium">
                      <CheckCircle className="w-4 h-4" />
                      <span>Selected</span>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>

          {/* Payment Form */}
          <div className="lg:col-span-1">
            <div className="bg-card border rounded-lg p-6 sticky top-6">
              <h2 className="text-lg font-semibold mb-6">Payment Details</h2>

              {/* Selected Tier Summary */}
              {selectedTier && (
                <div className="mb-6 p-4 bg-accent/50 rounded-lg">
                  <p className="text-sm text-muted-foreground mb-1">
                    Selected Plan
                  </p>
                  <p className="font-bold text-lg">
                    {selectedTier.display_name}
                  </p>
                  <p className="text-sm text-muted-foreground">
                    +{formatFileSize(selectedTier.storage_bytes)}
                  </p>
                  <div className="mt-3 pt-3 border-t border-border">
                    <div className="flex items-center justify-between">
                      <span className="font-medium">Total</span>
                      <span className="font-bold text-xl text-primary">
                        {selectedTier.price_xaf} XAF
                      </span>
                    </div>
                  </div>
                </div>
              )}

              {/* Provider Selection */}
              <div className="mb-4">
                <label className="block text-sm font-medium mb-2">
                  Payment Provider
                </label>
                <div className="space-y-2">
                  <label className="flex items-center space-x-3 p-3 border rounded-lg cursor-pointer hover:bg-accent/50 transition-colors">
                    <input
                      type="radio"
                      name="provider"
                      value="mtn_momo"
                      checked={provider === "mtn_momo"}
                      onChange={(e) => setProvider(e.target.value)}
                      className="w-4 h-4 text-primary"
                    />
                    <div className="flex-1">
                      <p className="font-medium">MTN Mobile Money</p>
                      <p className="text-xs text-muted-foreground">
                        67X, 650-654, 680-683
                      </p>
                    </div>
                  </label>
                  <label className="flex items-center space-x-3 p-3 border rounded-lg cursor-pointer hover:bg-accent/50 transition-colors">
                    <input
                      type="radio"
                      name="provider"
                      value="orange_money"
                      checked={provider === "orange_money"}
                      onChange={(e) => setProvider(e.target.value)}
                      className="w-4 h-4 text-primary"
                    />
                    <div className="flex-1">
                      <p className="font-medium">Orange Money</p>
                      <p className="text-xs text-muted-foreground">
                        69X, 655-659
                      </p>
                    </div>
                  </label>
                </div>
              </div>

              {/* Phone Number Input */}
              <div className="mb-6">
                <label className="block text-sm font-medium mb-2">
                  Phone Number
                </label>
                <input
                  type="tel"
                  placeholder="237XXXXXXXXX"
                  value={phoneNumber}
                  onChange={(e) => setPhoneNumber(e.target.value)}
                  className="w-full px-4 py-2 bg-accent border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
                />
                <p className="text-xs text-muted-foreground mt-1">
                  Enter your {provider === "mtn_momo" ? "MTN" : "Orange"} Mobile
                  Money number
                </p>
              </div>

              {/* Purchase Button */}
              <button
                onClick={handlePurchase}
                disabled={!selectedTier || processing || currentPayment}
                className="w-full flex items-center justify-center space-x-2 bg-primary text-primary-foreground px-6 py-3 rounded-lg hover:bg-primary/90 transition-colors disabled:opacity-50 disabled:cursor-not-allowed font-semibold"
              >
                {processing ? (
                  <>
                    <Loader2 className="w-5 h-5 animate-spin" />
                    <span>Processing...</span>
                  </>
                ) : (
                  <>
                    <span>Complete Purchase</span>
                    <ArrowRight className="w-5 h-5" />
                  </>
                )}
              </button>

              {/* Info */}
              <div className="mt-4 p-3 bg-blue-500/10 border border-blue-500/20 rounded-lg">
                <p className="text-xs text-muted-foreground">
                  🔒 Secure payment powered by Campay. You will receive a
                  notification to approve the payment on your phone.
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PaymentPage;
