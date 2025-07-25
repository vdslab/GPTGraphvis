import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { authAPI } from '../lib/api';
import type { AuthStore, User } from '../lib/types';

export const useAuthStore = create<AuthStore>()(
  persist(
    (set, get) => ({
      user: null,
      token: null,
      isLoading: false,

      login: async (username: string, password: string) => {
        set({ isLoading: true });
        try {
          const response = await authAPI.login(username, password);
          const token = response.data.access_token;
          
          localStorage.setItem('token', token);
          set({ token });
          
          await get().getCurrentUser();
          
          // ログイン成功後はダッシュボードにリダイレクト
          window.location.href = '/dashboard';
        } catch (error) {
          console.error('Login error:', error);
          throw error;
        } finally {
          set({ isLoading: false });
        }
      },

      register: async (username: string, password: string) => {
        set({ isLoading: true });
        try {
          await authAPI.register(username, password);
          
          // Auto-login after registration
          await get().login(username, password);
        } catch (error) {
          console.error('Registration error:', error);
          throw error;
        } finally {
          set({ isLoading: false });
        }
      },

      logout: () => {
        localStorage.removeItem('token');
        set({ user: null, token: null });
        window.location.href = '/auth';
      },

      getCurrentUser: async () => {
        const token = localStorage.getItem('token');
        if (!token) return;

        set({ isLoading: true });
        try {
          const response = await authAPI.getCurrentUser();
          const user: User = response.data;
          set({ user, token });
        } catch (error) {
          console.error('Get current user error:', error);
          localStorage.removeItem('token');
          set({ user: null, token: null });
        } finally {
          set({ isLoading: false });
        }
      },
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({
        token: state.token,
        user: state.user,
      }),
    }
  )
);