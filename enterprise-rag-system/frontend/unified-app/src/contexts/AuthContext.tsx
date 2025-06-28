'use client';

import React, { createContext, useContext, useEffect, useState } from 'react';
import { message } from 'antd';
import { apiClient } from '@/utils/api';

interface User {
  id: number;
  username: string;
  email: string;
  full_name?: string;
  is_superuser: boolean;
  is_active: boolean;
  avatar_url?: string;
  created_at: string;
  last_login?: string;
}

interface AuthContextType {
  user: User | null;
  token: string | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (username: string, password: string) => Promise<boolean>;
  logout: () => void;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const isAuthenticated = !!user && !!token;

  // 初始化认证状态
  useEffect(() => {
    const initAuth = async () => {
      const savedToken = localStorage.getItem('token');
      if (savedToken) {
        setToken(savedToken);
        apiClient.setToken(savedToken);
        
        try {
          const userData = await apiClient.getCurrentUser();
          setUser(userData);
        } catch (error) {
          console.error('获取用户信息失败:', error);
          localStorage.removeItem('token');
          setToken(null);
        }
      }
      setIsLoading(false);
    };

    initAuth();
  }, []);

  const login = async (username: string, password: string): Promise<boolean> => {
    try {
      setIsLoading(true);
      const response = await apiClient.login(username, password);
      
      if (response.access_token && response.user) {
        const { access_token, user: userData } = response;
        
        setToken(access_token);
        setUser(userData);
        localStorage.setItem('token', access_token);
        apiClient.setToken(access_token);
        
        message.success('登录成功');
        return true;
      } else {
        message.error('登录失败：响应数据格式错误');
        return false;
      }
    } catch (error: any) {
      console.error('登录失败:', error);
      const errorMessage = error.response?.data?.detail || error.message || '登录失败';
      message.error(errorMessage);
      return false;
    } finally {
      setIsLoading(false);
    }
  };

  const logout = () => {
    setUser(null);
    setToken(null);
    localStorage.removeItem('token');
    apiClient.setToken(null);
    message.success('已退出登录');
  };

  const refreshUser = async () => {
    if (!token) return;
    
    try {
      const userData = await apiClient.getCurrentUser();
      setUser(userData);
    } catch (error) {
      console.error('刷新用户信息失败:', error);
      logout();
    }
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        isLoading,
        isAuthenticated,
        login,
        logout,
        refreshUser,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
