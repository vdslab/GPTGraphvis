import { create } from 'zustand';
import { networkAPI } from '../lib/api';
import type { NetworkStore, Network } from '../lib/types';

export const useNetworkStore = create<NetworkStore>((set, get) => ({
  networks: [],
  currentNetwork: null,
  isLoading: false,

  fetchNetworks: async () => {
    set({ isLoading: true });
    try {
      const response = await networkAPI.getNetworks();
      const networks: Network[] = response.data;
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
      const response = await networkAPI.getNetwork(id);
      const network: Network = response.data;
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
      const response = await networkAPI.createNetwork({
        name: data.name || 'Untitled Network',
        nodes_data: data.nodes_data || '[]',
        edges_data: data.edges_data || '[]',
        layout_data: data.layout_data || '{}',
        metadata: data.metadata || '{}',
      });
      const newNetwork: Network = response.data;
      
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
      const response = await networkAPI.updateNetwork(id, data);
      const updatedNetwork: Network = response.data;
      
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
      await networkAPI.deleteNetwork(id);
      
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