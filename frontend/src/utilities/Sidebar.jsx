import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import logo from '../assets/SJ Brand Mark_RGB_Blue.jpg'
import { X } from 'lucide-react';

export default function Sidebar() {
  const navigate = useNavigate();
  const [isCollapsed, setIsCollapsed] = useState(true);

  const handleLogout = () => {
    localStorage.clear();
    navigate('/');
  };

  const handleDashboard = () => {
    navigate('/Dashboard');
  };

  const handleHistory = () => {
    navigate('/History');
  };

  const handleGenerate = () => {
    navigate('/Generate');
  };

  const handleChangePassword = () => {
    navigate('/change-password');
  };

  const toggleSidebar = () => {
    setIsCollapsed(!isCollapsed);
  };

  return (
    <div className="flex">
      <aside
        className={`
          transition-width duration-300
          bg-white border-r shadow h-screen
          ${isCollapsed ? 'w-8' : 'w-48'}
          flex flex-col justify-between h-full
        `}
      >
        <div className='flex justify-end'>
        <button
          onClick={toggleSidebar}
          className={`
            mt-2 ml-1 p-1 rounded 
            hover:bg-gray-100 active:bg-gray-200
            focus:outline-none mr-1
          `}
        >
          {isCollapsed ? (
            <div className="flex flex-col space-y-1">
              <span className="block w-4 h-0.5 bg-gray-800" />
              <span className="block w-4 h-0.5 bg-gray-800" />
              <span className="block w-4 h-0.5 bg-gray-800" />
            </div>
          ) : (
            <X className="text-gray-800 w-5 h-5" />
          )}
        </button>
        </div>

        {!isCollapsed && (
          <nav className="mt-2 flex-1 flex flex-col space-y-1 px-4">
            <button
              onClick={handleDashboard}
              className="text-left text-gray-700 hover:bg-gray-100 px-2 py-1 rounded"
            >
              Dashboard
            </button>

            <button
              onClick={handleGenerate}
              className="text-left text-gray-700 hover:bg-gray-100 px-2 py-1 rounded"
            >
              Scrape Tenders
            </button>

            <button
              onClick={handleHistory}
              className="text-left text-gray-700 hover:bg-gray-100 px-2 py-1 rounded"
            >
              History
            </button>

            <button
              onClick={handleChangePassword}
              className="text-left text-gray-700 hover:bg-gray-100 px-2 py-1 rounded"
            >
              Change Password
            </button>

            <button
              onClick={handleLogout}
              className="text-left text-red-600 hover:bg-red-50 px-2 py-1 rounded"
            >
              Logout
            </button>
          </nav>
        )}
        {!isCollapsed && (
        <div className="mb-4 px-4">
            <img src={logo} alt="Company Logo" className="w-25 mx-auto" />
        </div>
        )}
      </aside>
    </div>
  );
}