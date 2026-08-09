import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { login, register } from "../api/client";
import { LogIn, UserPlus, AlertCircle, ArrowRight } from "lucide-react";
import "./AuthPage.css";

export default function AuthPage() {
  const navigate = useNavigate();
  const [isLogin, setIsLogin] = useState(true);
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [err, setErr] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setErr("");
    setLoading(true);

    try {
      if (isLogin) {
        await login(username, password);
        // Successful login redirects to landing page
        navigate("/");
      } else {
        await register(username, email, password);
        // Successful registration auto-toggles to login and shows message
        setIsLogin(true);
        setErr("");
        alert("Registration successful! Please login.");
      }
    } catch (error) {
      const msg = error.response?.data?.detail || "Authentication request failed.";
      setErr(msg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-page">
      <div className="auth-card glass-card animate-fade-in-up">
        <div className="auth-card__header">
          <div className="auth-card__icon">
            {isLogin ? <LogIn size={22} /> : <UserPlus size={22} />}
          </div>
          <h2>{isLogin ? "Welcome back" : "Create account"}</h2>
          <p className="auth-card__sub text-muted">
            {isLogin
              ? "Sign in to access your data analysis workspace"
              : "Sign up to start profiling and querying datasets"}
          </p>
        </div>

        {err && (
          <div className="auth-error animate-fade-in">
            <AlertCircle size={16} />
            <span>{err}</span>
          </div>
        )}

        <form className="auth-form" onSubmit={handleSubmit}>
          <div className="form-group">
            <label htmlFor="username">Username</label>
            <input
              id="username"
              type="text"
              required
              placeholder="Enter your username"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              disabled={loading}
            />
          </div>

          {!isLogin && (
            <div className="form-group animate-fade-in">
              <label htmlFor="email">Email address</label>
              <input
                id="email"
                type="email"
                required
                placeholder="you@example.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                disabled={loading}
              />
            </div>
          )}

          <div className="form-group">
            <label htmlFor="password">Password</label>
            <input
              id="password"
              type="password"
              required
              placeholder="••••••••"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              disabled={loading}
            />
          </div>

          <button
            type="submit"
            className="btn btn-primary btn-lg btn-block auth-submit-btn"
            disabled={loading}
          >
            {loading ? "Please wait..." : isLogin ? "Sign In" : "Register"}
            {!loading && <ArrowRight size={16} />}
          </button>
        </form>

        <div className="auth-card__footer">
          <button
            type="button"
            className="btn btn-link"
            onClick={() => {
              setIsLogin(!isLogin);
              setErr("");
            }}
            disabled={loading}
          >
            {isLogin ? "Don't have an account? Sign up" : "Already have an account? Log in"}
          </button>
        </div>
      </div>
    </div>
  );
}
