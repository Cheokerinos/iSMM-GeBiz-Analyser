import React, { useState } from "react";
import axios from "axios";
import { useNavigate, Link } from "react-router-dom";
import { setToken } from "./utilities/Auth";
import qs from "qs";

export default function Login() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [errorMsg, setErrorMsg] = useState("");
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setErrorMsg("");
    try {
      const payload = qs.stringify({ username, password });
      const response = await axios.post(
        "http://localhost:8000/login",
          payload,
          { headers: { "Content-Type": "application/x-www-form-urlencoded" } }
        );
      const token = response.data.access_token;
      setToken(token);
      // Redirect to dashboard after login
      navigate("/dashboard");
    } catch (error) {
      console.error("Login failed:", error);
      setErrorMsg("Invalid username or password");
    }
  };

  return (
    <div className="min-h-screen flex bg-gray-100 w-full">
        <main className="flex flex-1 items-center justify-center">
        <div className="w-full max-w-md bg-white rounded-lg shadow-md p-6 space-y-4">
            <h2 className="text-2xl font-bold text-center">Login</h2>
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
            {errorMsg && (
                <p className="text-sm text-red-600">{errorMsg}</p>
            )}
            <button
                type="submit"
                className="w-full bg-blue-600 text-white py-2 rounded-md hover:bg-blue-700"
            >
                Login
            </button>
            <p className="text-sm text-center mt-4">
              Don't have an account?{" "}
              <Link to="/register" className="text-blue-600 hover:underline">
                Register
              </Link>
            </p>
            </form>
        </div>
        </main>
    </div>
  );
}