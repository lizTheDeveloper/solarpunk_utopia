/**
 * Auth Context - Simple session-based authentication
 *
 * Manages user login state and provides auth functions to the app.
 */

import React, { createContext, useContext, useState, useEffect } from 'react';
import axios from 'axios';

interface User {
  id: string;
  name: string;
  email?: string | null;
  created_at: string;
  last_login?: string | null;
  settings: Record<string, any>;
}

interface AuthContextType {
  user: User | null;
  token: string | null;
  loading: boolean;
  login: (name: string) => Promise<void>;
  logout: () => void;
  isAuthenticated: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

const AUTH_TOKEN_KEY = 'solarpunk_auth_token';
const AUTH_USER_KEY = 'solarpunk_auth_user';

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  // Load auth from localStorage on mount
  useEffect(() => {
    const loadAuth = async () => {
      const storedToken = localStorage.getItem(AUTH_TOKEN_KEY);
      const storedUser = localStorage.getItem(AUTH_USER_KEY);

      if (storedToken && storedUser) {
        try {
          // Verify token is still valid
          const response = await axios.get('/auth/me', {
            headers: { Authorization: `Bearer ${storedToken}` }
          });

          setToken(storedToken);
          setUser(response.data);
        } catch (error) {
          // Token invalid or expired, clear storage
          console.log('Stored session expired, clearing auth');
          localStorage.removeItem(AUTH_TOKEN_KEY);
          localStorage.removeItem(AUTH_USER_KEY);
        }
      }

      setLoading(false);
    };

    loadAuth();
  }, []);

  const login = async (name: string) => {
    try {
      const response = await axios.post('/auth/register', { name });
      const { user: newUser, token: newToken } = response.data;

      setUser(newUser);
      setToken(newToken);

      // Persist to localStorage
      localStorage.setItem(AUTH_TOKEN_KEY, newToken);
      localStorage.setItem(AUTH_USER_KEY, JSON.stringify(newUser));
    } catch (error) {
      console.error('Login failed:', error);
      throw error;
    }
  };

  const logout = () => {
    setUser(null);
    setToken(null);
    localStorage.removeItem(AUTH_TOKEN_KEY);
    localStorage.removeItem(AUTH_USER_KEY);
  };

  const value: AuthContextType = {
    user,
    token,
    loading,
    login,
    logout,
    isAuthenticated: !!user && !!token,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
