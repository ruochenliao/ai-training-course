import { create } from 'zustand';
import { User } from '@/types';
import { authService } from '@/services/auth';

interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (username: string, password: string) => Promise<void>;
  register: (username: string, email: string, password: string, fullName?: string) => Promise<void>;
  logout: () => void;
  checkAuth: () => Promise<void>;
}

export const useAuthStore = create<AuthState>((set, get) => ({
  user: authService.getStoredUser(),
  isAuthenticated: authService.isAuthenticated(),
  isLoading: false,

  login: async (username: string, password: string) => {
    set({ isLoading: true });
    try {
      const tokenData = await authService.login({ username, password });
      authService.storeToken(tokenData.access_token);
      
      const user = await authService.getCurrentUser();
      authService.storeUser(user);
      
      set({ user, isAuthenticated: true, isLoading: false });
    } catch (error) {
      set({ isLoading: false });
      throw error;
    }
  },

  register: async (username: string, email: string, password: string, fullName?: string) => {
    set({ isLoading: true });
    try {
      await authService.register({ username, email, password, full_name: fullName });
      set({ isLoading: false });
    } catch (error) {
      set({ isLoading: false });
      throw error;
    }
  },

  logout: () => {
    authService.logout();
    set({ user: null, isAuthenticated: false });
  },

  checkAuth: async () => {
    if (!authService.isAuthenticated()) {
      return;
    }

    try {
      const user = await authService.getCurrentUser();
      authService.storeUser(user);
      set({ user, isAuthenticated: true });
    } catch (error) {
      // Token可能已过期
      authService.logout();
      set({ user: null, isAuthenticated: false });
    }
  },
}));
