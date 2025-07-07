/**
 * MCP (Model Context Protocol) client for interacting with the MCP server.
 * This client provides methods for using MCP tools and accessing MCP resources.
 */

import axios from 'axios';

// API URL
const API_URL = 'http://localhost:8000';
const MCP_URL = `${API_URL}/mcp`;

/**
 * MCP client for interacting with the network visualization MCP server.
 */
class MCPClient {
  /**
   * Use an MCP tool.
   * 
   * @param {string} toolName - Name of the tool to use
   * @param {object} args - Arguments for the tool
   * @returns {Promise<object>} - Tool response
   */
  async useTool(toolName, args = {}) {
    try {
      console.log(`Using MCP tool: ${toolName}`, args);
      
      // Get token from localStorage
      const token = localStorage.getItem('token');
      if (!token) {
        console.error('No token found, cannot use MCP tool');
        throw new Error('Authentication required');
      }
      
      // Call MCP tool endpoint
      const response = await axios.post(
        `${MCP_URL}/tools/${toolName}`,
        { arguments: args },
        {
          headers: {
            Authorization: `Bearer ${token}`
          }
        }
      );
      
      console.log(`MCP tool ${toolName} response:`, response.data);
      return response.data.result;
    } catch (error) {
      console.error(`Error using MCP tool ${toolName}:`, error);
      throw error;
    }
  }
  
  /**
   * Access an MCP resource.
   * 
   * @param {string} resourceUri - URI of the resource to access
   * @returns {Promise<object>} - Resource data
   */
  async accessResource(resourceUri) {
    try {
      console.log(`Accessing MCP resource: ${resourceUri}`);
      
      // Get token from localStorage
      const token = localStorage.getItem('token');
      if (!token) {
        console.error('No token found, cannot access MCP resource');
        throw new Error('Authentication required');
      }
      
      // Call MCP resource endpoint
      const response = await axios.get(
        `${MCP_URL}${resourceUri}`,
        {
          headers: {
            Authorization: `Bearer ${token}`
          }
        }
      );
      
      console.log(`MCP resource ${resourceUri} response:`, response.data);
      return response.data;
    } catch (error) {
      console.error(`Error accessing MCP resource ${resourceUri}:`, error);
      throw error;
    }
  }
  
  /**
   * Get the MCP server manifest.
   * 
   * @returns {Promise<object>} - MCP server manifest
   */
  async getManifest() {
    try {
      console.log('Getting MCP server manifest');
      
      // Call MCP manifest endpoint
      const response = await axios.get(`${MCP_URL}/manifest`);
      
      console.log('MCP server manifest:', response.data);
      return response.data;
    } catch (error) {
      console.error('Error getting MCP server manifest:', error);
      throw error;
    }
  }
  
  /**
   * Change the layout algorithm for the network visualization.
   * 
   * @param {string} layoutType - Type of layout algorithm
   * @param {object} layoutParams - Parameters for the layout algorithm
   * @returns {Promise<object>} - Updated network positions
   */
  async changeLayout(layoutType, layoutParams = {}) {
    return this.useTool('change_layout', {
      layout_type: layoutType,
      layout_params: layoutParams
    });
  }
  
  /**
   * Calculate centrality metrics for nodes in the graph.
   * 
   * @param {string} centralityType - Type of centrality to calculate
   * @returns {Promise<object>} - Centrality values for nodes
   */
  async calculateCentrality(centralityType) {
    return this.useTool('calculate_centrality', {
      centrality_type: centralityType
    });
  }
  
  /**
   * Highlight specific nodes in the network.
   * 
   * @param {string[]} nodeIds - List of node IDs to highlight
   * @param {string} highlightColor - Color to use for highlighting
   * @returns {Promise<object>} - Updated node colors
   */
  async highlightNodes(nodeIds, highlightColor = '#ff0000') {
    return this.useTool('highlight_nodes', {
      node_ids: nodeIds,
      highlight_color: highlightColor
    });
  }
  
  /**
   * Change visual properties of nodes or edges.
   * 
   * @param {string} propertyType - Type of property to change
   * @param {string} propertyValue - Value to set for the property
   * @param {object} propertyMapping - Optional mapping of node/edge IDs to property values
   * @returns {Promise<object>} - Updated visual properties
   */
  async changeVisualProperties(propertyType, propertyValue, propertyMapping = {}) {
    return this.useTool('change_visual_properties', {
      property_type: propertyType,
      property_value: propertyValue,
      property_mapping: propertyMapping
    });
  }
  
  /**
   * Get information about the current network.
   * 
   * @returns {Promise<object>} - Network information
   */
  async getNetworkInfo() {
    return this.useTool('get_network_info', {});
  }
  
  /**
   * Get information about specific nodes in the network.
   * 
   * @param {string[]} nodeIds - List of node IDs to get information for
   * @returns {Promise<object>} - Node information
   */
  async getNodeInfo(nodeIds) {
    return this.useTool('get_node_info', {
      node_ids: nodeIds
    });
  }
  
  /**
   * Get the current network data.
   * 
   * @returns {Promise<object>} - Network data
   */
  async getNetworkData() {
    return this.accessResource('/resources/network');
  }
}

// Create and export a singleton instance
const mcpClient = new MCPClient();
export default mcpClient;
