import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter, Route, Routes, Navigate } from 'react-router-dom';
import Dashboard from "./Dashboard"
import Generate from "./Generate"
import Login from "./Login"
import Register from "./Register"
import ProtectedRoute from "./ProtectedRoute";
import Tables from "./Tables";
import SessionTimeout from "./utilities/SessionTimeout";


function App() {
  return(
    <SessionTimeout>
          <Routes>
            <Route path = "/" element = {<Login />} />
            <Route path = "/Register" element ={<Register />} / >
            <Route path="/dashboard" element={
            <ProtectedRoute>
              <Dashboard />
            </ProtectedRoute>
            } />

            <Route path="/generate" element={
              <ProtectedRoute>
                <Generate />
              </ProtectedRoute>
            } />

            <Route path="/tables" element={
              <ProtectedRoute>
                <Tables />
              </ProtectedRoute>
            } />
            <Route path="*" element={<Navigate to="/" />} />
          </Routes>
      </SessionTimeout>
  )
}

export default App;