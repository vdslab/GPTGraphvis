import { create } from 'zustand';
import { networkAPI, networkChatAPI } from './api';

// Helper function to generate colors based on centrality values
const getCentralityColor = (value, maxValue) => {
  // Generate a color from blue (low) to red (high)
  const ratio = value / maxValue;
  const r = Math.floor(255 * ratio);
  const b = Math.floor(255 * (1 - ratio));
  return `rgb(${r}, 70, ${b})`;
};

const useNetworkStore = create((set, get) => ({
  nodes: [],
  edges: [],
  layout: 'spring',
  layoutParams: {},
  positions: [],
  centrality: null,
  centralityType: null,
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

  // Load sample network
  loadSampleNetwork: async () => {
    set({ isLoading: true, error: null });
    try {
      const response = await networkChatAPI.getSampleNetwork();
      
      set({ 
        nodes: response.data.nodes,
        edges: response.data.edges,
        isLoading: false,
        error: null
      });
      
      // Calculate layout for the sample network
      return get().calculateLayout();
    } catch (error) {
      set({ 
        isLoading: false, 
        error: error.response?.data?.detail || 'Failed to load sample network'
      });
      return false;
    }
  },

  // Apply centrality metrics
  applyCentrality: async (centralityType) => {
    const { nodes, edges } = get();
    
    if (!nodes.length) {
      set({ error: 'No nodes provided' });
      return false;
    }

    set({ isLoading: true, error: null });
    try {
      // This would typically be an API call to calculate centrality
      // For now, we'll simulate it by updating node sizes based on degree
      // In a real implementation, this would call a backend endpoint
      
      // Create a map of node degrees
      const degreeMap = {};
      edges.forEach(edge => {
        degreeMap[edge.source] = (degreeMap[edge.source] || 0) + 1;
        degreeMap[edge.target] = (degreeMap[edge.target] || 0) + 1;
      });
      
      // Update positions with centrality values
      const updatedPositions = get().positions.map(node => {
        const degree = degreeMap[node.id] || 0;
        const normalizedValue = Math.max(5, Math.min(15, degree * 2 + 5)); // Scale between 5-15
        
        return {
          ...node,
          size: normalizedValue,
          color: getCentralityColor(degree, Math.max(...Object.values(degreeMap)))
        };
      });
      
      set({ 
        positions: updatedPositions,
        centrality: degreeMap,
        centralityType,
        isLoading: false,
        error: null
      });
      
      return true;
    } catch (error) {
      set({ 
        isLoading: false, 
        error: error.response?.data?.detail || 'Centrality calculation failed'
      });
      return false;
    }
  },

  // Clear all data
  clearData: () => {
    set({
      nodes: [],
      edges: [],
      positions: [],
      centrality: null,
      centralityType: null,
      recommendation: null,
      error: null
    });
  }
}));

export default useNetworkStore;
