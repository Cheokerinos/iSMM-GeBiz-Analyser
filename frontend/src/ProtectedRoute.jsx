import React from "react";
import { Navigate } from "react-router-dom";

const ProtectedRoute = ({ children }) => {
  const access_token = localStorage.getItem("accessToken");
  return access_token ? children : <Navigate to="/" replace />;
};

export default ProtectedRoute;