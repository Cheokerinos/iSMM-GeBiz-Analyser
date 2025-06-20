import React, { useState } from "react";
import axios from "axios";
import { useNavigate, Link } from "react-router-dom";
import { toast, ToastContainer } from "react-toastify";
import "react-toastify/dist/ReactToastify.css";
import logo from './assets/SJ_RIMT_Blue_RGB.jpg'

function Spinner() {
    return <div className="w-7 h-7 border-4 border-gray-200 border-t-blue-500 rounded-full animate-spin inline-block align-middle"/>
  }

export default function Register() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [email, setEmail] = useState("");
  const [errorMsg, setErrorMsg] = useState("");
  const [successMsg, setSuccessMsg] = useState("");
  const [isLoading, setIsLoading] = useState(false)
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setErrorMsg("");
    setSuccessMsg("");
    setIsLoading(true)
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!emailRegex.test(email)) {
            toast.error("Invalid email address.");
            return;
        }
    const passwordError = validatePassword(password);
        if (passwordError) {
            toast.error(passwordError);
            return;
        }
    try {
      const response = await axios.post("http://localhost:8000/register", {
        username,
        password,
        email,
      });
      setSuccessMsg("Registration successful! Redirecting to login...");
      setTimeout(() => navigate("/"), 1500);
    } catch (err) {
        console.error("Registration failed:", err);
  
        if (err.response?.status === 422) {
          const msgs = err.response.data.detail.map((e) => e.msg);
          msgs.forEach(msg => toast.error(msg));
        } else if (err.response?.data?.detail) {
          toast.error(err.response.data.detail);
        } else {
          toast.error("Registration failed. Please try again.");
        }
      } finally {
        setIsLoading(false);
      }
    };

  const validatePassword = (password) => {
    if (password.length < 8) return "Password must be at least 8 characters";
    if (!/\d/.test(password)) return "Password must include a number";
    if (!/[a-z]/.test(password)) return "Password must include a lowercase letter";
    if (!/[A-Z]/.test(password)) return "Password must have an uppercase letter";
    if (!/[^A-Za-z0-9]/.test(password)) return "Password must include a special character";
    return null;
  };
  
  const handleMicrosoftLogin = () => {
    // Redirect to Azure AD login or your Microsoft auth endpoint
    window.location.href = "https://login.microsoftonline.com/{tenant-id}/oauth2/v2.0/authorize?client_id={client-id}&response_type=code&redirect_uri=http://localhost:5173/auth/callback&response_mode=query&scope=openid email profile&state=12345";
  };

  return (
    <div className="min-h-screen flex bg-gray-100 w-full">
      <ToastContainer position="top-right" autoClose={3000} />
      <main className="flex flex-1 items-center justify-center">
        <div className="w-full max-w-md bg-white rounded-lg shadow-md p-4 space-y-0">
            <div className="mb-4 px-4">
            <img src={logo} alt="Company Logo" className="w-75 mx-auto" />
            </div>
          <h2 className="text-2xl font-bold text-center">Register</h2>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700">
                Username
              </label>
              <input
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                className="mt-1 block w-full border border-gray-300 rounded-md p-2"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">
                Email
              </label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="mt-1 block w-full border border-gray-300 rounded-md p-2"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">
                Password
              </label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="mt-1 block w-full border border-gray-300 rounded-md p-2"
                required
              />
            </div>
            {errorMsg && <p className="text-sm text-red-600">{errorMsg}</p>}
            {successMsg && (
              <p className="text-sm text-green-600">{successMsg}</p>
            )}
            <button
                type="submit"
                className="w-full bg-green-600 text-white py-2 rounded-md hover:bg-green-700 flex justify-center items-center"
                disabled={isLoading}
            >
                {isLoading ? <Spinner /> : "Register"}
            </button>
            <p className="text-sm text-center mt-4">
              Already have an account?{" "}
              <Link to="/" className="text-blue-600 hover:underline">
                Login
              </Link>
            </p>
          </form>
        </div>
      </main>
    </div>
  );
}
