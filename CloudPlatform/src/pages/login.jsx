import React from "react";
import "../styles/login.css";
import logo from "../assets/logo.png";

const Login = () => {
  return (
    <div className="login-page">
      <div className="brand-header">
        <img src={logo} alt="Cloud Platform Logo" className="brand-logo" />
        <span className="brand-name">Cloud Platform</span>
      </div>

      <div className="login-card">
        <h2 className="form-title">Sign In to Your Account</h2>
        <p className="form-subtitle">
          Enter your email to receive a one-time passcode.
        </p>

        <form className="login-form" onSubmit={(e) => e.preventDefault()}>
          <div className="input-group">
            <label htmlFor="email">Email Address</label>
            <input
              type="email"
              id="email"
              name="email"
              placeholder="you@example.com"
              required
            />
          </div>

          <button type="submit" className="submit-btn">
            Send Verification Code
          </button>
        </form>
      </div>
    </div>
  );
};

export default Login;
