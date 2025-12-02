import React, { useState, useEffect } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";
import { Cloud, Mail, ArrowRight, Loader2 } from "lucide-react";
import { toast } from "sonner";
import { validateEmail } from "../utils/helpers";

const OTPInput = ({ value, onChange, onComplete }) => {
  const inputRefs = React.useRef([]);
  const hasCalledComplete = React.useRef(false); // FIX: Prevent multiple calls

  useEffect(() => {
    // FIX: Only call onComplete once when we have 6 digits
    if (value.length === 6 && !hasCalledComplete.current && onComplete) {
      hasCalledComplete.current = true;
      onComplete(value);
    }

    // Reset the flag when value changes (e.g., user edits)
    if (value.length < 6) {
      hasCalledComplete.current = false;
    }
  }, [value, onComplete]);

  const handleInputChange = (index, e) => {
    const digit = e.target.value.slice(-1);
    if (!/\d/.test(digit) && e.target.value !== "") return;

    const newValue = value.split("");
    newValue[index] = digit;
    const newValueStr = newValue.join("");
    onChange(newValueStr);

    // Move to next input if digit entered
    if (digit && index < 5) {
      inputRefs.current[index + 1]?.focus();
    }
  };

  const handleKeyDown = (index, e) => {
    if (e.key === "Backspace" && !value[index] && index > 0) {
      inputRefs.current[index - 1]?.focus();
    }
  };

  const handlePaste = (e) => {
    e.preventDefault();
    const pastedData = e.clipboardData.getData("text").slice(0, 6);
    if (/^\d{6}$/.test(pastedData)) {
      onChange(pastedData);
      inputRefs.current[5]?.focus();
    }
  };

  return (
    <div className="flex justify-center space-x-2" onPaste={handlePaste}>
      {Array.from({ length: 6 }).map((_, index) => (
        <input
          key={index}
          ref={(el) => (inputRefs.current[index] = el)}
          type="text"
          inputMode="numeric"
          pattern="[0-9]"
          maxLength="1"
          value={value[index] || ""}
          onChange={(e) => handleInputChange(index, e)}
          onKeyDown={(e) => handleKeyDown(index, e)}
          className="w-12 h-14 text-center text-2xl font-bold bg-accent border-2 border-border rounded-lg focus:border-primary focus:outline-none transition-colors"
        />
      ))}
    </div>
  );
};

const LoginPage = ({ isEnroll = false }) => {
  const [step, setStep] = useState("email"); // 'email', 'otp', 'enroll'
  const [email, setEmail] = useState("");
  const [name, setName] = useState("");
  const [otp, setOtp] = useState("");
  const [loading, setLoading] = useState(false);
  const [isVerifying, setIsVerifying] = useState(false); // FIX: Prevent multiple verification calls
  const { sendOTP, verifyOTP, enroll, login, isAuthenticated } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  useEffect(() => {
    if (isAuthenticated) {
      navigate("/dashboard");
    }
  }, [isAuthenticated, navigate]);

  const handleSendOTP = async (e) => {
    e.preventDefault();
    if (!validateEmail(email)) {
      toast.error("Please enter a valid email address");
      return;
    }

    setLoading(true);
    const success = await sendOTP(email);
    if (success) {
      setStep("otp");
    }
    setLoading(false);
  };

  const handleVerifyOTP = async () => {
    // FIX: Prevent multiple simultaneous verification attempts
    if (isVerifying || otp.length !== 6) {
      if (otp.length !== 6) {
        toast.error("Please enter a 6-digit OTP");
      }
      return;
    }

    setIsVerifying(true);
    setLoading(true);

    const result = await verifyOTP(email, otp);
    if (result) {
      if (result.exists) {
        // User exists, proceed with login
        const success = await login(email);
        if (success) {
          navigate("/dashboard");
        }
      } else {
        // New user, proceed with enrollment
        setStep("enroll");
      }
    } else {
      // FIX: Clear OTP on failure so user can try again
      setOtp("");
    }

    setLoading(false);
    setIsVerifying(false);
  };

  const handleEnroll = async (e) => {
    e.preventDefault();
    if (!name.trim()) {
      toast.error("Please enter your name");
      return;
    }

    setLoading(true);
    const success = await enroll(email, name.trim());
    if (success) {
      navigate("/dashboard");
    }
    setLoading(false);
  };

  const handleResendOTP = async () => {
    setLoading(true);
    setOtp(""); // FIX: Clear OTP input when resending
    await sendOTP(email);
    setLoading(false);
  };

  return (
    <div className="min-h-screen flex items-center justify-center gradient-bg">
      <div className="w-full max-w-md mx-4">
        {/* Logo */}
        <div className="text-center mb-8">
          <div className="flex items-center justify-center mb-4">
            <Cloud className="w-12 h-12 text-white mr-3" />
            <h1 className="text-3xl font-bold text-white">CloudDrive</h1>
          </div>
          <p className="text-white/80">Your files, everywhere you are</p>
        </div>

        {/* Form Card */}
        <div className="bg-card rounded-2xl shadow-2xl p-8 animate-scale-in">
          {/* Email Step */}
          {step === "email" && (
            <div className="space-y-6">
              <div className="text-center">
                <h2 className="text-2xl font-bold mb-2">
                  {isEnroll ? "Create Account" : "Welcome Back"}
                </h2>
                <p className="text-muted-foreground">
                  Enter your email to{" "}
                  {isEnroll ? "create an account" : "sign in"}
                </p>
              </div>

              <form onSubmit={handleSendOTP} className="space-y-4">
                <div className="relative">
                  <Mail className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-muted-foreground" />
                  <input
                    type="email"
                    placeholder="Enter your email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    className="w-full pl-12 pr-4 py-3 bg-accent border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary transition-all"
                    required
                  />
                </div>

                <button
                  type="submit"
                  disabled={loading || !email}
                  className="w-full bg-primary text-primary-foreground py-3 rounded-lg font-medium hover:bg-primary/90 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center"
                >
                  {loading ? (
                    <Loader2 className="w-5 h-5 animate-spin" />
                  ) : (
                    <>
                      Continue
                      <ArrowRight className="w-5 h-5 ml-2" />
                    </>
                  )}
                </button>
              </form>
            </div>
          )}

          {/* OTP Step */}
          {step === "otp" && (
            <div className="space-y-6">
              <div className="text-center">
                <h2 className="text-2xl font-bold mb-2">Verify Email</h2>
                <p className="text-muted-foreground mb-4">
                  Enter the 6-digit code sent to
                </p>
                <p className="font-medium text-primary">{email}</p>
              </div>

              <div className="space-y-6">
                <OTPInput
                  value={otp}
                  onChange={setOtp}
                  onComplete={handleVerifyOTP}
                />

                <button
                  onClick={handleVerifyOTP}
                  disabled={loading || otp.length !== 6}
                  className="w-full bg-primary text-primary-foreground py-3 rounded-lg font-medium hover:bg-primary/90 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center"
                >
                  {loading ? (
                    <Loader2 className="w-5 h-5 animate-spin" />
                  ) : (
                    "Verify OTP"
                  )}
                </button>

                <div className="text-center">
                  <button
                    onClick={handleResendOTP}
                    disabled={loading}
                    className="text-sm text-primary hover:underline disabled:opacity-50"
                  >
                    Didn't receive code? Resend OTP
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* Enroll Step */}
          {step === "enroll" && (
            <div className="space-y-6">
              <div className="text-center">
                <h2 className="text-2xl font-bold mb-2">Complete Setup</h2>
                <p className="text-muted-foreground">
                  Enter your name to complete your account
                </p>
              </div>

              <form onSubmit={handleEnroll} className="space-y-4">
                <div className="relative">
                  <input
                    type="text"
                    placeholder="Enter your name"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    className="w-full px-4 py-3 bg-accent border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary transition-all"
                    required
                    autoFocus
                  />
                </div>

                <button
                  type="submit"
                  disabled={loading || !name.trim()}
                  className="w-full bg-primary text-primary-foreground py-3 rounded-lg font-medium hover:bg-primary/90 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center"
                >
                  {loading ? (
                    <Loader2 className="w-5 h-5 animate-spin" />
                  ) : (
                    "Create Account"
                  )}
                </button>
              </form>
            </div>
          )}

          {/* Back button */}
          {step !== "email" && (
            <div className="mt-6 text-center">
              <button
                onClick={() => {
                  setStep("email");
                  setOtp("");
                }}
                className="text-sm text-muted-foreground hover:text-foreground transition-colors"
              >
                ← Back to email
              </button>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="mt-8 text-center">
          <p className="text-white/60 text-sm">
            {isEnroll ? "Already have an account? " : "Don't have an account? "}
            <a
              href={isEnroll ? "/login" : "/enroll"}
              className="text-white hover:text-white/80 font-medium transition-colors"
            >
              {isEnroll ? "Sign in" : "Sign up"}
            </a>
          </p>
        </div>
      </div>
    </div>
  );
};

export default LoginPage;
