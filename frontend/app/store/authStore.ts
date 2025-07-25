import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { AuthStore, User } from '../lib/types';

// Note: axios will be available after npm install
// For now, we'll use fetch as a fallback
const makeRequest = async (url: string, options: RequestInit = {}) => {
  const token = localStorage.getItem('token');
  const headers = {
    'Content-Type': 'application/json',
    ...(token && { Authorization: `Bearer ${token}` }),
    ...options.headers,
  };

  const response = await fetch(`http://localhost:8000${url}`, {
    ...options,
    headers,
  });

  if (!response.ok) {
    if (response.status === 401) {
      localStorage.removeItem('token');
      window.location.href = '/login';
    }
    throw new Error(`HTTP error! status: ${response.status}`);
  }

  return response.json();
};

export const useAuthStore = create<AuthStore>()(
  persist(
    (set, get) => ({
      user: null,
      token: null,
      isLoading: false,

      login: async (username: string, password: string) => {
        set({ isLoading: true });
        try {
          const formData = new URLSearchParams();
          formData.append('username', username);
          formData.append('password', password);

          const response = await fetch('http://localhost:8000/auth/token', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: formData,
          });

          if (!response.ok) {
            throw new Error('Login failed');
          }

          const data = await response.json();
          const token = data.access_token;
          
          localStorage.setItem('token', token);
          set({ token });
          
          await get().getCurrentUser();
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
          await makeRequest('/auth/register', {
            method: 'POST',
            body: JSON.stringify({ username, password }),
          });
          
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
        window.location.href = '/login';
      },

      getCurrentUser: async () => {
        const token = localStorage.getItem('token');
        if (!token) return;

        set({ isLoading: true });
        try {
          const user: User = await makeRequest('/auth/users/me');
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