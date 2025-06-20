import React, { useState } from "react";
import axios from "axios";
import { useNavigate, Link } from "react-router-dom";
import { setToken } from "./utilities/Auth";
import qs from "qs";
import logo from './assets/SJ_RIMT_Blue_RGB.jpg'

function Spinner() {
  return <div className="w-7 h-7 border-4 border-gray-200 border-t-blue-500 rounded-full animate-spin inline-block align-middle"/>
}

export default function Login() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [errorMsg, setErrorMsg] = useState("");
  const navigate = useNavigate();
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setErrorMsg("");
    setIsLoading(true)
    try {
      const payload = qs.stringify({ username, password });
      const response = await axios.post("http://localhost:8000/login", {
        username,
        password,
        });
      const { access_token, refresh_token } = response.data;
      setToken(access_token);
      localStorage.setItem("accessToken",access_token);
      localStorage.setItem("refreshToken", refresh_token);
      // Redirect to dashboard after login
      navigate("/dashboard");
    } catch (error) {
      console.error("Login failed:", error);
      setErrorMsg("Invalid username or password");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex bg-gray-100 w-full">
        <main className="flex flex-1 items-center justify-center">
        <div className="w-full max-w-md bg-white rounded-lg shadow-md p-6 space-y-4">
            <div className="mb-4 px-4">
              <img src={logo} alt="Company Logo" className="w-75 mx-auto" />
            </div>
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
                disabled = {isLoading}
            >
              {isLoading ? <Spinner /> : "Login"}
            </button>
            <p className="text-sm text-center mt-4">
              Don't have an account?{" "}
              <Link to="/register" className="text-blue-600 hover:underline">
                Register
              </Link>
            </p>
            {/*<button onClick={handleMicrosoftLogin} className="microsoft-login-btn">
              <img src="/ms-logo.svg" alt="MS Logo" style={{ width: "16px", marginRight: "8px" }} />
              Sign in with Microsoft
            </button>
            */}
            </form>
        </div>
        </main>
    </div>
  );
}

function handleMicrosoftLogin() {
  window.location.href = "http://localhost:8000/login/microsoft";
};
