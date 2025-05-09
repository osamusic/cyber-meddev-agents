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
          医療機器サイバーセキュリティ専門家システム
        </Link>
        
        <nav>
          <ul className="flex space-x-6">
            {isAuthenticated ? (
              <>
                <li>
                  <Link to="/guidelines" className="hover:text-blue-200">
                    ガイドライン
                  </Link>
                </li>
                
                {isAdmin && (
                  <li className="relative group">
                    <button className="hover:text-blue-200">
                      管理者メニュー
                    </button>
                    <ul className="absolute right-0 mt-2 w-48 bg-white text-gray-800 rounded shadow-lg hidden group-hover:block z-10">
                      <li>
                        <Link 
                          to="/admin" 
                          className="block px-4 py-2 hover:bg-blue-100"
                        >
                          ダッシュボード
                        </Link>
                      </li>
                      <li>
                        <Link 
                          to="/admin/users" 
                          className="block px-4 py-2 hover:bg-blue-100"
                        >
                          ユーザー管理
                        </Link>
                      </li>
                      <li>
                        <Link 
                          to="/admin/documents" 
                          className="block px-4 py-2 hover:bg-blue-100"
                        >
                          ドキュメント管理
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
                    ログアウト
                  </button>
                </li>
              </>
            ) : (
              <>
                <li>
                  <Link to="/login" className="hover:text-blue-200">
                    ログイン
                  </Link>
                </li>
                <li>
                  <Link to="/register" className="hover:text-blue-200">
                    登録
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
