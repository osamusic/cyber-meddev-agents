import React, { createContext, useState, useEffect, useContext } from 'react';
import PropTypes from 'prop-types';
import axiosClient from '../api/axiosClient';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const checkAuth = async () => {
      const token = localStorage.getItem('token');
      if (!token) {
        setLoading(false);
        return;
      }

      try {
        const response = await axiosClient.get('/me');
        setUser(response.data);
      } catch (err) {
        console.error('Authentication error:', err);
        localStorage.removeItem('token');
      } finally {
        setLoading(false);
      }
    };

    checkAuth();
  }, []);

  const login = async (username, password) => {
    try {
      setLoading(true);
      setError(null);
      
      console.log('ログイン試行:', username);
      
      const formData = new URLSearchParams();
      formData.append('username', username);
      formData.append('password', password);
      
      const response = await axiosClient.post('/token', formData.toString(), {
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded'
        }
      });
      
      if (response.data && response.data.access_token) {
        console.log('ログイン成功: トークンを保存します');
        localStorage.setItem('token', response.data.access_token);
        
        try {
          const userResponse = await axiosClient.get('/me');
          setUser(userResponse.data);
          console.log('ユーザー情報を取得しました:', userResponse.data);
        } catch (userErr) {
          console.error('ユーザー情報取得エラー:', userErr);
          setUser({ username });
        }
        
        return true;
      } else {
        console.error('トークンが返却されませんでした');
        setError('認証サーバーからトークンが返却されませんでした');
        return false;
      }
    } catch (err) {
      console.error('ログインエラー:', err);
      setError(err.response?.data?.detail || 'ログイン中にエラーが発生しました');
      return false;
    } finally {
      setLoading(false);
    }
  };

  const register = async (username, password, adminCode = null) => {
    setError(null);
    try {
      const registerData = {
        username,
        password,
      };
      
      if (adminCode) {
        registerData.admin_code = adminCode;
      }
      
      await axiosClient.post('/register', registerData);
      
      return await login(username, password);
    } catch (err) {
      console.error('Registration error:', err);
      setError(err.response?.data?.detail || '登録に失敗しました');
      return false;
    }
  };

  const logout = () => {
    localStorage.removeItem('token');
    setUser(null);
  };

  const value = {
    user,
    loading,
    error,
    login,
    register,
    logout,
    isAuthenticated: !!user,
    isAdmin: user?.is_admin || false,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

AuthProvider.propTypes = {
  children: PropTypes.node.isRequired
};

export default AuthContext;
