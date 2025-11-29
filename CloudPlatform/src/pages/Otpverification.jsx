import React, { useState, useRef, useEffect } from "react";
import "../styles/otp-verification.css";
// NOTE: Ensure you have a logo.png file in the src/assets folder
import logo from "../assets/logo.png";

const OtpVerification = ({ userEmail = "you@example.com" }) => {
  const [code, setCode] = useState(new Array(6).fill(""));
  const inputRefs = useRef([]);

  useEffect(() => {
    if (inputRefs.current[0]) {
      inputRefs.current[0].focus();
    }
  }, []);

  const handleChange = (element, index) => {
    const value = element.value.slice(-1);

    if (isNaN(value)) return;

    const newCode = [...code];
    newCode[index] = value;
    setCode(newCode);

    if (value !== "" && index < 5) {
      inputRefs.current[index + 1].focus();
    }
  };

  const handleKeyDown = (element, index) => {
    if (element.key === "Backspace" && index > 0 && code[index] === "") {
      inputRefs.current[index - 1].focus();
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    const finalCode = code.join("");
    console.log("Verifying code:", finalCode);
    // Add your verification logic here
  };

  return (
    <div className="verification-page">
      {/* --- BRAND HEADER (ADDED) --- */}
      <div className="brand-header">
        <img src={logo} alt="Cloud Platform Logo" className="brand-logo" />
        <span className="brand-name">Cloud Platform</span>
      </div>

      <div className="verification-card">
        <h2 className="title">Check Your Email</h2>
        <p className="subtitle">We've sent a 6-digit code to **{userEmail}**</p>

        <form onSubmit={handleSubmit}>
          <label className="code-label">Verification Code</label>
          <div className="code-input-container">
            {code.map((data, index) => (
              <input
                key={index}
                className="code-input-field"
                type="text"
                maxLength="1"
                value={data}
                onChange={(e) => handleChange(e.target, index)}
                onKeyDown={(e) => handleKeyDown(e.target, index)}
                ref={(el) => (inputRefs.current[index] = el)}
                aria-label={`Digit ${index + 1} of 6`}
              />
            ))}
          </div>

          <button type="submit" className="submit-btn">
            Verify & Sign In
          </button>
        </form>

        <p className="resend-link">
          Didn't receive the code? <b>Resend</b>
        </p>
      </div>

      {/* The lock and passwordless line has been removed */}
    </div>
  );
};

export default OtpVerification;
