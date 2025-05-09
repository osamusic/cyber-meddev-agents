import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';

const Register = () => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [passwordError, setPasswordError] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const { register, error } = useAuth();
  const navigate = useNavigate();

  const validateForm = () => {
    setPasswordError('');
    
    if (password !== confirmPassword) {
      setPasswordError('パスワードが一致しません');
      return false;
    }
    
    if (password.length < 6) {
      setPasswordError('パスワードは6文字以上である必要があります');
      return false;
    }
    
    return true;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!validateForm()) {
      return;
    }
    
    setIsSubmitting(true);
    
    try {
      const success = await register(username, password);
      if (success) {
        navigate('/guidelines');
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="max-w-md mx-auto bg-white rounded-lg shadow-md overflow-hidden mt-16">
      <div className="px-6 py-8">
        <h2 className="text-2xl font-bold text-center text-gray-800 mb-8">
          アカウント登録
        </h2>
        
        {error && (
          <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
            {error}
          </div>
        )}
        
        <form onSubmit={handleSubmit}>
          <div className="mb-6">
            <label 
              htmlFor="username" 
              className="block text-gray-700 font-medium mb-2"
            >
              ユーザー名
            </label>
            <input
              type="text"
              id="username"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              className="w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              required
            />
          </div>
          
          <div className="mb-6">
            <label 
              htmlFor="password" 
              className="block text-gray-700 font-medium mb-2"
            >
              パスワード
            </label>
            <input
              type="password"
              id="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              required
            />
          </div>
          
          <div className="mb-6">
            <label 
              htmlFor="confirmPassword" 
              className="block text-gray-700 font-medium mb-2"
            >
              パスワード（確認）
            </label>
            <input
              type="password"
              id="confirmPassword"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              className="w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              required
            />
            {passwordError && (
              <p className="text-red-600 text-sm mt-1">{passwordError}</p>
            )}
          </div>
          
          <button
            type="submit"
            disabled={isSubmitting}
            className={`w-full py-2 px-4 rounded-lg text-white font-medium ${
              isSubmitting 
                ? 'bg-blue-400 cursor-not-allowed' 
                : 'bg-blue-600 hover:bg-blue-700'
            }`}
          >
            {isSubmitting ? '登録中...' : '登録'}
          </button>
        </form>
        
        <div className="mt-6 text-center">
          <p className="text-gray-600">
            すでにアカウントをお持ちの場合は{' '}
            <Link to="/login" className="text-blue-600 hover:underline">
              ログイン
            </Link>
            してください。
          </p>
        </div>
      </div>
    </div>
  );
};

export default Register;
