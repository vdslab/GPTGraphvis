import { create } from 'zustand';
import mcpClient from './mcpClient';

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

  // Calculate layout using MCP client
  calculateLayout: async () => {
    const { nodes, layout, layoutParams } = get();
    
    if (!nodes.length) {
      set({ error: 'No nodes provided' });
      return false;
    }

    set({ isLoading: true, error: null });
    try {
      // Use MCP client to calculate layout
      const result = await mcpClient.changeLayout(layout, layoutParams || {});
      
      if (result && result.success) {
        set({ 
          positions: result.positions || [],
          isLoading: false,
          error: null
        });
        return true;
      } else {
        throw new Error(result.error || 'Layout calculation failed');
      }
    } catch (error) {
      console.error('Error calculating layout:', error);
      set({ 
        isLoading: false, 
        error: error.message || 'Layout calculation failed'
      });
      return false;
    }
  },

  // Apply layout using MCP client
  applyLayout: async () => {
    // This function now uses the same implementation as calculateLayout
    return get().calculateLayout();
  },

  // Get layout recommendation using MCP client
  getLayoutRecommendation: async (description, purpose) => {
    set({ isLoading: true, error: null, recommendation: null });
    try {
      // Use MCP client to get layout recommendation
      const result = await mcpClient.useTool('recommend_layout', {
        description,
        purpose
      });
      
      if (result && result.success) {
        set({ 
          recommendation: result.recommendation,
          isLoading: false,
          error: null
        });
        return result.recommendation;
      } else {
        throw new Error(result.error || 'Layout recommendation failed');
      }
    } catch (error) {
      console.error('Error getting layout recommendation:', error);
      set({ 
        isLoading: false, 
        error: error.message || 'Layout recommendation failed',
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

  // Load sample network using MCP client
  loadSampleNetwork: async () => {
    set({ isLoading: true, error: null });
    try {
      console.log("Attempting to load sample network using MCP client");
      
      // Use MCP client to get sample network
      const result = await mcpClient.useTool('get_sample_network', {});
      
      if (result && result.success) {
        console.log("Sample network loaded successfully:", result);
        set({ 
          nodes: result.nodes || [],
          edges: result.edges || [],
          isLoading: false,
          error: null
        });
        
        // Calculate layout for the sample network
        return get().calculateLayout();
      } else {
        throw new Error(result.error || 'Failed to load sample network');
      }
    } catch (error) {
      console.error("Failed to load sample network:", error);
      
      set({ 
        isLoading: false, 
        error: error.message || 'Failed to load sample network'
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
  },
  
  // Upload network file using MCP client
  uploadNetworkFile: async (file) => {
    set({ isLoading: true, error: null });
    try {
      console.log("Uploading network file using MCP client:", file.name);
      
      // Create form data for file upload
      const formData = new FormData();
      formData.append('file', file);
      
      // Use MCP client to upload network file
      const result = await mcpClient.useTool('upload_network_file', {
        file_name: file.name,
        file_type: file.type,
        file_size: file.size
      });
      
      if (result && result.success) {
        console.log("Network file uploaded successfully:", result);
        
        // Update network store with data from response
        set({ 
          nodes: result.nodes || [],
          edges: result.edges || [],
          isLoading: false,
          error: null
        });
        
        // Calculate layout for the uploaded network
        return get().calculateLayout();
      } else {
        throw new Error(result.error || 'Failed to upload network file');
      }
    } catch (error) {
      console.error("Failed to upload network file:", error);
      
      set({ 
        isLoading: false, 
        error: error.message || 'Failed to upload network file'
      });
      return false;
    }
  }
}));

export default useNetworkStore;
