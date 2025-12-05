// src/pages/LoginPage.jsx
import React, { useState, useEffect } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";
import { Mail, ArrowRight, Loader2 } from "lucide-react";
import { toast } from "sonner";
import { validateEmail } from "../utils/helpers";
import logo from "../img/logo.png"; // Your FileSphere logo

// OTP Input Component (unchanged — perfect as-is)
const OTPInput = ({ value, onChange, onComplete }) => {
  const inputRefs = React.useRef([]);
  const hasCalledComplete = React.useRef(false);

  useEffect(() => {
    if (value.length === 6 && !hasCalledComplete.current && onComplete) {
      hasCalledComplete.current = true;
      onComplete(value);
    }
    if (value.length < 6) hasCalledComplete.current = false;
  }, [value, onComplete]);

  const handleInputChange = (index, e) => {
    const digit = e.target.value.slice(-1);
    if (!/\d/.test(digit) && e.target.value !== "") return;

    const newValue = value.split("");
    newValue[index] = digit;
    const newValueStr = newValue.join("");
    onChange(newValueStr);

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
    const pasted = e.clipboardData.getData("text").slice(0, 6);
    if (/^\d{6}$/.test(pasted)) {
      onChange(pasted);
      inputRefs.current[5]?.focus();
    }
  };

  return (
    <div className="flex justify-center space-x-3" onPaste={handlePaste}>
      {Array.from({ length: 6 }).map((_, i) => (
        <input
          key={i}
          ref={(el) => (inputRefs.current[i] = el)}
          type="text"
          inputMode="numeric"
          maxLength="1"
          value={value[i] || ""}
          onChange={(e) => handleInputChange(i, e)}
          onKeyDown={(e) => handleKeyDown(i, e)}
          className="w-14 h-14 text-center text-2xl font-bold bg-muted/50 border-2 border-border rounded-xl focus:border-primary focus:outline-none transition-all"
        />
      ))}
    </div>
  );
};

const LoginPage = ({ isEnroll = false }) => {
  const [step, setStep] = useState("email");
  const [email, setEmail] = useState("");
  const [name, setName] = useState("");
  const [otp, setOtp] = useState("");
  const [loading, setLoading] = useState(false);
  const [isVerifying, setIsVerifying] = useState(false);

  const { sendOTP, verifyOTP, enroll, login, isAuthenticated } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    if (isAuthenticated) navigate("/dashboard");
  }, [isAuthenticated, navigate]);

  const handleSendOTP = async (e) => {
    e.preventDefault();
    if (!validateEmail(email)) return toast.error("Please enter a valid email");

    setLoading(true);
    const success = await sendOTP(email);
    if (success) setStep("otp");
    setLoading(false);
  };

  const handleVerifyOTP = async () => {
    if (isVerifying || otp.length !== 6) return;
    setIsVerifying(true);
    setLoading(true);

    const result = await verifyOTP(email, otp);
    if (result) {
      if (result.exists) {
        await login(email);
        navigate("/dashboard");
      } else {
        setStep("enroll");
      }
    } else {
      setOtp("");
    }
    setLoading(false);
    setIsVerifying(false);
  };

  const handleEnroll = async (e) => {
    e.preventDefault();
    if (!name.trim()) return toast.error("Please enter your name");

    setLoading(true);
    const success = await enroll(email, name.trim());
    if (success) navigate("/dashboard");
    setLoading(false);
  };

  const handleResendOTP = async () => {
    setLoading(true);
    setOtp("");
    await sendOTP(email);
    setLoading(false);
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-950 p-4">
      <div className="w-full max-w-md">
        {/* Logo + Brand */}
        <div className="text-center mb-10">
          <img
            src={logo}
            alt="FileSphere"
            className="w-24 h-24 mx-auto mb-4 rounded-2xl shadow-2xl"
          />
          <h1 className="text-4xl font-bold text-white tracking-tight">
            FileSphere
          </h1>
          <p className="text-white/60 mt-2">
            Secure cloud storage, reimagined.
          </p>
        </div>

        {/* Auth Card */}
        <div className="bg-white/10 backdrop-blur-xl border border-white/20 rounded-2xl shadow-2xl p-8">
          {/* Email Step */}
          {step === "email" && (
            <div className="space-y-8">
              <div className="text-center">
                <h2 className="text-2xl font-bold text-white">
                  {isEnroll ? "Create Your Account" : "Welcome Back"}
                </h2>
                <p className="text-white/70 mt-2">
                  Enter your email to {isEnroll ? "get started" : "sign in"}
                </p>
              </div>

              <form onSubmit={handleSendOTP} className="space-y-5">
                <div className="relative">
                  <Mail className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-white/60" />
                  <input
                    type="email"
                    placeholder="you@example.com"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    className="w-full pl-12 pr-4 py-4 bg-white/10 border border-white/30 rounded-xl text-white placeholder-white/50 focus:outline-none focus:ring-2 focus:ring-primary transition-all"
                    required
                  />
                </div>

                <button
                  type="submit"
                  disabled={loading || !email}
                  className="w-full bg-primary hover:bg-primary/90 text-white font-semibold py-4 rounded-xl transition-all disabled:opacity-50 flex items-center justify-center space-x-2"
                >
                  {loading ? (
                    <Loader2 className="w-5 h-5 animate-spin" />
                  ) : (
                    <>
                      <span>Continue</span>
                      <ArrowRight className="w-5 h-5" />
                    </>
                  )}
                </button>
              </form>
            </div>
          )}

          {/* OTP Step */}
          {step === "otp" && (
            <div className="space-y-8">
              <div className="text-center">
                <h2 className="text-2xl font-bold text-white">
                  Check Your Email
                </h2>
                <p className="text-white/70 mt-2">We sent a 6-digit code to</p>
                <p className="text-primary font-medium mt-1">{email}</p>
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
                  className="w-full bg-primary hover:bg-primary/90 text-white font-semibold py-4 rounded-xl transition-all disabled:opacity-50"
                >
                  {loading ? (
                    <Loader2 className="w-5 h-5 animate-spin mx-auto" />
                  ) : (
                    "Verify & Continue"
                  )}
                </button>

                <button
                  onClick={handleResendOTP}
                  disabled={loading}
                  className="w-full text-white/70 hover:text-white text-sm underline transition-colors"
                >
                  Didn’t receive it? Resend code
                </button>
              </div>
            </div>
          )}

          {/* Enroll Step */}
          {step === "enroll" && (
            <div className="space-y-8">
              <div className="text-center">
                <h2 className="text-2xl font-bold text-white">Almost There!</h2>
                <p className="text-white/70 mt-2">Tell us your name</p>
              </div>

              <form onSubmit={handleEnroll} className="space-y-5">
                <input
                  type="text"
                  placeholder="Your full name"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  className="w-full px-5 py-4 bg-white/10 border border-white/30 rounded-xl text-white placeholder-white/50 focus:outline-none focus:ring-2 focus:ring-primary transition-all"
                  autoFocus
                  required
                />

                <button
                  type="submit"
                  disabled={loading || !name.trim()}
                  className="w-full bg-primary hover:bg-primary/90 text-white font-semibold py-4 rounded-xl transition-all disabled:opacity-50"
                >
                  {loading ? (
                    <Loader2 className="w-5 h-5 animate-spin mx-auto" />
                  ) : (
                    "Complete Account"
                  )}
                </button>
              </form>
            </div>
          )}

          {/* Back Link */}
          {step !== "email" && (
            <button
              onClick={() => {
                setStep("email");
                setOtp("");
              }}
              className="mt-6 text-white/60 hover:text-white text-sm underline w-full text-center block"
            >
              ← Change email
            </button>
          )}
        </div>

        {/* Footer */}
        <div className="mt-8 text-center">
          <p className="text-white/50 text-sm">
            {isEnroll ? "Already have an account? " : "New to FileSphere? "}
            <a
              href={isEnroll ? "/login" : "/enroll"}
              className="text-white font-medium hover:underline"
            >
              {isEnroll ? "Sign in" : "Create account"}
            </a>
          </p>
        </div>
      </div>
    </div>
  );
};

export default LoginPage;
