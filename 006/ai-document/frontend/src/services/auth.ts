import api from './api';
import { User, LoginForm, RegisterForm, Token } from '@/types';

export const authService = {
  // 用户登录
  async login(data: LoginForm): Promise<Token> {
    const formData = new FormData();
    formData.append('username', data.username);
    formData.append('password', data.password);
    
    const response = await api.post<Token>('/auth/login', formData, {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
    });
    return response.data;
  },

  // 用户注册
  async register(data: RegisterForm): Promise<User> {
    const response = await api.post<User>('/auth/register', data);
    return response.data;
  },

  // 获取当前用户信息
  async getCurrentUser(): Promise<User> {
    const response = await api.get<User>('/auth/me');
    return response.data;
  },

  // 登出
  logout() {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
  },

  // 检查是否已登录
  isAuthenticated(): boolean {
    return !!localStorage.getItem('token');
  },

  // 获取存储的用户信息
  getStoredUser(): User | null {
    const userStr = localStorage.getItem('user');
    return userStr ? JSON.parse(userStr) : null;
  },

  // 存储用户信息
  storeUser(user: User) {
    localStorage.setItem('user', JSON.stringify(user));
  },

  // 存储token
  storeToken(token: string) {
    localStorage.setItem('token', token);
  },
};
