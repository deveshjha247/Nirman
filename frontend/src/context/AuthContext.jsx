import React, { useState, useEffect, createContext, useContext } from 'react';
import { authAPI, setAuthToken } from '../lib/api';

const AuthContext = createContext(null);

export const useAuth = () => useContext(AuthContext);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(localStorage.getItem('token'));
  const [loading, setLoading] = useState(true);

  const fetchUser = async (authToken) => {
    try {
      setAuthToken(authToken);
      const response = await authAPI.getMe();
      setUser(response.data);
      return response.data;
    } catch (error) {
      localStorage.removeItem('token');
      setToken(null);
      setUser(null);
      setAuthToken(null);
      return null;
    }
  };

  useEffect(() => {
    const verifyToken = async () => {
      if (token) {
        await fetchUser(token);
      }
      setLoading(false);
    };
    verifyToken();
  }, [token]);

  const login = async (email, password) => {
    const response = await authAPI.login(email, password);
    const { access_token, user } = response.data;
    localStorage.setItem('token', access_token);
    setToken(access_token);
    setAuthToken(access_token);
    setUser(user);
    return user;
  };

  const register = async (email, name, password, referralCode = null) => {
    const response = await authAPI.register(email, name, password, referralCode);
    const { access_token, user } = response.data;
    localStorage.setItem('token', access_token);
    setToken(access_token);
    setAuthToken(access_token);
    setUser(user);
    return user;
  };

  const logout = () => {
    localStorage.removeItem('token');
    setToken(null);
    setUser(null);
    setAuthToken(null);
  };

  const refreshUser = async () => {
    if (token) {
      return await fetchUser(token);
    }
    return null;
  };

  return (
    <AuthContext.Provider value={{ user, token, login, register, logout, loading, refreshUser }}>
      {children}
    </AuthContext.Provider>
  );
};

export default AuthContext;
