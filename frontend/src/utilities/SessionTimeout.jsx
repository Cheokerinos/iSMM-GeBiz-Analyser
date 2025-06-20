import React, { useEffect, useState, useCallback, useRef } from 'react';
import { useLocation } from 'react-router-dom';
import { jwtDecode } from 'jwt-decode';

const PUBLIC_PATHS = ['/', '/register'];

export default function SessionTimeout({ children }) {
  const [showWarning, setShowWarning] = useState(false);
  const location = useLocation();
  const timersRef = useRef({ warnTimer: null, logoutTimer: null });

  const clearTimers = () => {
    if (timersRef.current.warnTimer)  clearTimeout(timersRef.current.warnTimer);
    if (timersRef.current.logoutTimer) clearTimeout(timersRef.current.logoutTimer);
    timersRef.current = { warnTimer: null, logoutTimer: null };
  };


  const scheduleTimers = useCallback(() => {
    clearTimers();

    const token = localStorage.getItem('accessToken');
    if (!token) return;

    let payload;
    try {
      payload = jwtDecode(token);
    } catch {
      // bad token -> force logout
      localStorage.removeItem('accessToken');
      window.location.href = '/';
      return;
    }

    const now    = Math.floor(Date.now() / 1000);
    const warnIn = (payload.exp - now - 120) * 1000; // ms until 2 min before expiry
    console.log("Now:", now, "Exp:", payload.exp, "warnIn:", warnIn / 1000, "seconds");
    if (warnIn <= 0) {
      // already past the warning window -> log out now
      localStorage.removeItem('accessToken');
      window.location.href = '/';
      return;
    }


    timersRef.current.warnTimer = setTimeout(() => {
      setShowWarning(true);
    }, warnIn);

    timersRef.current.logoutTimer = setTimeout(() => {
      localStorage.removeItem('accessToken');
      localStorage.removeItem('refreshToken');
      window.location.href = '/';
    }, warnIn + 30_000);
  }, []);

  useEffect(() => {
    // if we’re on a PUBLIC_PATH, don’t schedule anything
    if (PUBLIC_PATHS.includes(location.pathname)) {
      clearTimers();
      setShowWarning(false);
      return;
    }
    const cleanup = scheduleTimers();
    return cleanup;
  }, [location.pathname, scheduleTimers]);

  const extendSession = async () => {
    setShowWarning(false);
    clearTimers();
    const refresh_token = localStorage.getItem('refreshToken');
    console.log("Attempting refresh with token:", refresh_token);
    if (!refresh_token) {
      window.location.href = '/';
      return;
    }
  
    try {
      const res = await fetch('http://localhost:8000/refresh_token', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ refresh_token }),
      });
  
      if (!res.ok) throw new Error('Refresh failed');
  
      const { access_token, refresh_token: newRefresh } = await res.json();
  
      localStorage.setItem('accessToken', access_token);
      localStorage.setItem('refreshToken', newRefresh);
  
      scheduleTimers();
    } catch (err) {
      console.error('Session refresh failed:', err);
      localStorage.removeItem('accessToken');
      localStorage.removeItem('refreshToken');
      window.location.href = '/';
    }
  };

  if (PUBLIC_PATHS.includes(location.pathname)) {
    return <>{children}</>;
  }

  return (
    <>
      {children}
      {showWarning && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white p-6 rounded shadow-lg max-w-sm text-center space-y-4">
            <h2 className="text-xl font-bold">Session expiring soon</h2>
            <p>Your session will expire in 2 minutes. Extend?</p>
            <button
              className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
              onClick={extendSession}
            >
              Extend Session
            </button>
          </div>
        </div>
      )}
    </>
  );
}