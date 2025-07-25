import { create } from 'zustand';
import type { NetworkStore, Network } from '../lib/types';

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

export const useNetworkStore = create<NetworkStore>((set, get) => ({
  networks: [],
  currentNetwork: null,
  isLoading: false,

  fetchNetworks: async () => {
    set({ isLoading: true });
    try {
      const networks: Network[] = await makeRequest('/network');
      set({ networks });
    } catch (error) {
      console.error('Fetch networks error:', error);
      throw error;
    } finally {
      set({ isLoading: false });
    }
  },

  fetchNetwork: async (id: number) => {
    set({ isLoading: true });
    try {
      const network: Network = await makeRequest(`/network/${id}`);
      set({ currentNetwork: network });
    } catch (error) {
      console.error('Fetch network error:', error);
      throw error;
    } finally {
      set({ isLoading: false });
    }
  },

  createNetwork: async (data: Partial<Network>) => {
    set({ isLoading: true });
    try {
      const newNetwork: Network = await makeRequest('/network', {
        method: 'POST',
        body: JSON.stringify({
          name: data.name || 'Untitled Network',
          nodes_data: data.nodes_data || '[]',
          edges_data: data.edges_data || '[]',
          layout_data: data.layout_data || '{}',
          metadata: data.metadata || '{}',
        }),
      });
      
      const { networks } = get();
      set({ networks: [...networks, newNetwork], currentNetwork: newNetwork });
    } catch (error) {
      console.error('Create network error:', error);
      throw error;
    } finally {
      set({ isLoading: false });
    }
  },

  updateNetwork: async (id: number, data: Partial<Network>) => {
    set({ isLoading: true });
    try {
      const updatedNetwork: Network = await makeRequest(`/network/${id}`, {
        method: 'PUT',
        body: JSON.stringify(data),
      });
      
      const { networks, currentNetwork } = get();
      const updatedNetworks = networks.map(n => n.id === id ? updatedNetwork : n);
      
      set({ 
        networks: updatedNetworks,
        currentNetwork: currentNetwork?.id === id ? updatedNetwork : currentNetwork
      });
    } catch (error) {
      console.error('Update network error:', error);
      throw error;
    } finally {
      set({ isLoading: false });
    }
  },

  deleteNetwork: async (id: number) => {
    set({ isLoading: true });
    try {
      await makeRequest(`/network/${id}`, {
        method: 'DELETE',
      });
      
      const { networks, currentNetwork } = get();
      const filteredNetworks = networks.filter(n => n.id !== id);
      
      set({ 
        networks: filteredNetworks,
        currentNetwork: currentNetwork?.id === id ? null : currentNetwork
      });
    } catch (error) {
      console.error('Delete network error:', error);
      throw error;
    } finally {
      set({ isLoading: false });
    }
  },

  setCurrentNetwork: (network: Network | null) => {
    set({ currentNetwork: network });
  },
}));