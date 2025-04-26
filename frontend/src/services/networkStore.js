import { create } from 'zustand';
import { networkAPI } from './api';

const useNetworkStore = create((set, get) => ({
  nodes: [],
  edges: [],
  layout: 'spring',
  layoutParams: {},
  positions: [],
  isLoading: false,
  error: null,
  recommendation: null,

  // Set network data
  setNetworkData: (nodes, edges) => {
    set({ nodes, edges });
  },

  // Set layout type
  setLayout: (layout) => {
    set({ layout });
  },

  // Set layout parameters
  setLayoutParams: (layoutParams) => {
    set({ layoutParams });
  },

  // Calculate layout
  calculateLayout: async () => {
    const { nodes, edges, layout, layoutParams } = get();
    
    if (!nodes.length) {
      set({ error: 'No nodes provided' });
      return false;
    }

    set({ isLoading: true, error: null });
    try {
      const response = await networkAPI.calculateLayout(
        nodes, 
        edges, 
        layout, 
        layoutParams
      );
      
      set({ 
        positions: response.data.nodes,
        isLoading: false,
        error: null
      });
      
      return true;
    } catch (error) {
      set({ 
        isLoading: false, 
        error: error.response?.data?.detail || 'Layout calculation failed'
      });
      return false;
    }
  },

  // Get layout recommendation
  getLayoutRecommendation: async (description, purpose) => {
    set({ isLoading: true, error: null, recommendation: null });
    try {
      const response = await networkAPI.recommendLayout(description, purpose);
      
      set({ 
        recommendation: response.data,
        isLoading: false,
        error: null
      });
      
      return response.data;
    } catch (error) {
      set({ 
        isLoading: false, 
        error: error.response?.data?.detail || 'Layout recommendation failed',
        recommendation: null
      });
      return null;
    }
  },

  // Apply recommended layout
  applyRecommendedLayout: () => {
    const { recommendation } = get();
    
    if (!recommendation) {
      set({ error: 'No recommendation available' });
      return false;
    }

    set({ 
      layout: recommendation.recommended_layout,
      layoutParams: recommendation.recommended_parameters || {}
    });
    
    return get().calculateLayout();
  },

  // Clear all data
  clearData: () => {
    set({
      nodes: [],
      edges: [],
      positions: [],
      recommendation: null,
      error: null
    });
  }
}));

export default useNetworkStore;
