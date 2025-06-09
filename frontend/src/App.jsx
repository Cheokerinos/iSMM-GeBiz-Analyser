import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter, Route, Routes, Navigate } from 'react-router-dom';
import Dashboard from "./Dashboard"
import Generate from "./Generate"


function App() {
  return(
    <BrowserRouter>
        <Routes>
          <Route path = "/Dashboard" element = {<Dashboard />} />
          <Route path ="/Generate" element = {<Generate/>} />
        </Routes>
      </BrowserRouter>
  )
}

export default App;