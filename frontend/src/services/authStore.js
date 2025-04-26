import { create } from 'zustand';
import { authAPI } from './api';

const useAuthStore = create((set) => ({
  user: null,
  token: localStorage.getItem('token') || null,
  isAuthenticated: !!localStorage.getItem('token'),
  isLoading: false,
  error: null,

  login: async (username, password) => {
    set({ isLoading: true, error: null });
    try {
      const response = await authAPI.login(username, password);
      const { access_token } = response.data;
      
      localStorage.setItem('token', access_token);
      
      // Get user info
      const userResponse = await authAPI.getCurrentUser();
      
      set({ 
        token: access_token,
        user: userResponse.data,
        isAuthenticated: true,
        isLoading: false,
        error: null
      });
      
      return true;
    } catch (error) {
      set({ 
        isLoading: false, 
        error: error.response?.data?.detail || 'Login failed'
      });
      return false;
    }
  },

  register: async (username, password) => {
    set({ isLoading: true, error: null });
    try {
      await authAPI.register(username, password);
      
      // Login after successful registration
      return await useAuthStore.getState().login(username, password);
    } catch (error) {
      set({ 
        isLoading: false, 
        error: error.response?.data?.detail || 'Registration failed'
      });
      return false;
    }
  },

  logout: () => {
    localStorage.removeItem('token');
    set({ 
      user: null,
      token: null,
      isAuthenticated: false
    });
  },

  checkAuth: async () => {
    const token = localStorage.getItem('token');
    if (!token) {
      set({ isAuthenticated: false, user: null });
      return false;
    }

    set({ isLoading: true });
    try {
      const response = await authAPI.getCurrentUser();
      set({ 
        user: response.data,
        isAuthenticated: true,
        isLoading: false
      });
      return true;
    } catch {
      localStorage.removeItem('token');
      set({ 
        user: null,
        token: null,
        isAuthenticated: false,
        isLoading: false
      });
      return false;
    }
  }
}));

export default useAuthStore;
