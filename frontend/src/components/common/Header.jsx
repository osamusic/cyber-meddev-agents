import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';

const Header = () => {
  const { isAuthenticated, isAdmin, logout, user } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <header className="bg-blue-800 text-white shadow-md">
      <div className="container mx-auto px-4 py-4 flex justify-between items-center">
        <Link to="/" className="text-xl font-bold">
          Medical Device Cybersecurity Expert System
        </Link>
        
        <nav>
          <ul className="flex space-x-6">
            {isAuthenticated ? (
              <>
                <li>
                  <Link to="/guidelines" className="hover:text-blue-200">
                    Guidelines
                  </Link>
                </li>
                
                <li>
                  <Link to="/documents/search" className="hover:text-blue-200">
                    Document Search
                  </Link>
                </li>
                
                {isAdmin && (
                  <li className="relative group">
                    <button className="hover:text-blue-200">
                      Admin Menu
                    </button>
                    <ul className="absolute right-0 mt-2 w-48 bg-white text-gray-800 rounded shadow-lg hidden group-hover:block z-10">
                      <li>
                        <Link 
                          to="/admin" 
                          className="block px-4 py-2 hover:bg-blue-100"
                        >
                          Dashboard
                        </Link>
                      </li>
                      <li>
                        <Link 
                          to="/admin/users" 
                          className="block px-4 py-2 hover:bg-blue-100"
                        >
                          User Management
                        </Link>
                      </li>
                      <li>
                        <Link 
                          to="/admin/documents" 
                          className="block px-4 py-2 hover:bg-blue-100"
                        >
                          Document Management
                        </Link>
                      </li>
                    </ul>
                  </li>
                )}
                
                <li className="flex items-center">
                  <span className="mr-4">{user?.username}</span>
                  <button 
                    onClick={handleLogout}
                    className="bg-red-600 hover:bg-red-700 px-3 py-1 rounded"
                  >
                    Logout
                  </button>
                </li>
              </>
            ) : (
              <>
                <li>
                  <Link to="/login" className="hover:text-blue-200">
                    Login
                  </Link>
                </li>
                <li>
                  <Link to="/register" className="hover:text-blue-200">
                    Register
                  </Link>
                </li>
              </>
            )}
          </ul>
        </nav>
      </div>
    </header>
  );
};

export default Header;