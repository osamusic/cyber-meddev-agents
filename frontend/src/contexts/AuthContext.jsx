import React, { createContext, useState, useEffect, useContext } from 'react';
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
    setError(null);
    try {
      const response = await axiosClient.post('/auth/token', {
        username,
        password,
      }, {
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded'
        }
      });
      
      const { access_token } = response.data;
      localStorage.setItem('token', access_token);
      
      const userResponse = await axiosClient.get('/me');
      setUser(userResponse.data);
      
      return true;
    } catch (err) {
      console.error('Login error:', err);
      setError(err.response?.data?.detail || 'ログインに失敗しました');
      return false;
    }
  };

  const register = async (username, password) => {
    setError(null);
    try {
      await axiosClient.post('/auth/register', {
        username,
        password,
      });
      
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

export default AuthContext;
