import React from "react";

import "../styles/enrollment.css";
import logo from "../assets/logo.png";

const Enrollment = () => {
  return (
    <div className="enrollment-page">
      <div className="brand-header">
        <img src={logo} alt="Cloud Platform Logo" className="brand-logo" />
        <span className="brand-name">Cloud Platform</span>
      </div>

      <div className="enrollment-card">
        <h2 className="form-title">Create Your Account</h2>
        <p className="form-subtitle">
          Join our platform and start managing your files in our cloud
          infrastructure today.
        </p>

        <form className="enrollment-form" onSubmit={(e) => e.preventDefault()}>
          <div className="input-group">
            <label htmlFor="fullName">Full Name</label>
            <input
              type="text"
              id="fullName"
              name="fullName"
              placeholder="Chewi clinton"
              required
            />
          </div>

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
            Sign Up and Continue
          </button>
        </form>

        <p className="link-text">
          Already have an account? <a href="/login">Sign In</a>
        </p>
      </div>
    </div>
  );
};

export default Enrollment;
