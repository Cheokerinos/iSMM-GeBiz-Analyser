import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter, Route, Routes, Navigate } from 'react-router-dom';
import Dashboard from "./Dashboard"
import Generate from "./Generate"
import Login from "./Login"
import Register from "./Register"


function App() {
  return(
    <BrowserRouter>
        <Routes>
          <Route path = "/" element = {<Login />} />
          <Route path = "/Register" element ={<Register />} / >
          <Route path = "/Dashboard" element = {<Dashboard />} />
          <Route path ="/Generate" element = {<Generate/>} />
          <Route path="*" element={<Navigate to="/" />} />
        </Routes>
      </BrowserRouter>
  )
}

export default App;