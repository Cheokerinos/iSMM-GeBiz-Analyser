import React, { useState } from "react";
import axios from "axios";
import { useNavigate, Link } from "react-router-dom";

export default function Register() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [email, setEmail] = useState("");
  const [errorMsg, setErrorMsg] = useState("");
  const [successMsg, setSuccessMsg] = useState("");
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setErrorMsg("");
    setSuccessMsg("");
    const passwordError = validatePassword(password);
        if (passwordError) {
        setErrorMsg(passwordError);
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
    } catch (error) {
        console.error("Registration failed:", error);
        const detail = error.response?.data?.detail;
      
        if (Array.isArray(detail)) {
          // FastAPI validation error
          setErrorMsg(detail.map((err) => err.msg).join(" | "));
        } else {
          setErrorMsg(detail || "Registration failed.");
        }
      }
  };

  const validatePassword = (password) => {
    if (password.length < 8) return "Password must be at least 8 characters";
    if (!/\d/.test(password)) return "Password must include a number";
    if (!/[a-zA-Z]/.test(password)) return "Password must include a letter";
    return null;
  };

  return (
    <div className="min-h-screen flex bg-gray-100 w-full">
      <main className="flex flex-1 items-center justify-center">
        <div className="w-full max-w-md bg-white rounded-lg shadow-md p-6 space-y-4">
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
              className="w-full bg-green-600 text-white py-2 rounded-md hover:bg-green-700"
            >
              Register
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