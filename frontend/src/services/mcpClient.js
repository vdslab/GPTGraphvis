/**
 * MCP (Model Context Protocol) client for interacting with MCP servers.
 * This client provides methods for using MCP tools and accessing MCP resources.
 * Enhanced with network data persistence and advanced layout algorithms.
 * Supports multiple MCP servers including the NetworkX MCP server.
 */

import axios from 'axios';
import mcpConfig from '../mcp-config.json';

// Default API URL for backward compatibility
const DEFAULT_API_URL = 'http://localhost:8000';
const DEFAULT_MCP_URL = `${DEFAULT_API_URL}/mcp`;

/**
 * MCP client for interacting with multiple MCP servers.
 */
class MCPClient {
  constructor() {
    this.servers = mcpConfig.servers || [];
    this.currentServer = this.servers.length > 0 ? this.servers[0] : null;
  }

  /**
   * Set the current MCP server by name.
   * 
   * @param {string} serverName - Name of the server to use
   * @returns {boolean} - Whether the server was found and set
   */
  setCurrentServer(serverName) {
    const server = this.servers.find(s => s.name === serverName);
    if (server) {
      this.currentServer = server;
      console.log(`Set current MCP server to: ${server.name}`);
      return true;
    }
    console.error(`MCP server not found: ${serverName}`);
    return false;
  }

  /**
   * Get the current MCP server URL.
   * 
   * @returns {string} - URL of the current MCP server
   */
  getCurrentServerUrl() {
    return this.currentServer ? this.currentServer.url : DEFAULT_MCP_URL;
  }

  /**
   * Get authentication headers for the current server.
   * 
   * @returns {object} - Headers object with authentication
   */
  getAuthHeaders() {
    // Get token from localStorage for JWT auth
    const token = localStorage.getItem('token');
    const headers = {};
    
    if (this.currentServer && this.currentServer.auth) {
      // Basic auth for servers with username/password
      const { username, password } = this.currentServer.auth;
      if (username && password) {
        const base64Credentials = btoa(`${username}:${password}`);
        headers['Authorization'] = `Basic ${base64Credentials}`;
      }
    } else if (token) {
      // JWT auth for servers without explicit auth config
      headers['Authorization'] = `Bearer ${token}`;
    }
    
    return headers;
  }
  /**
   * Use an MCP tool.
   * 
   * @param {string} toolName - Name of the tool to use
   * @param {object} args - Arguments for the tool
   * @returns {Promise<object>} - Tool response
   */
  async useTool(toolName, args = {}, serverName = null) {
    try {
      // Set server if specified
      if (serverName) {
        this.setCurrentServer(serverName);
      }
      
      console.log(`Using MCP tool: ${toolName} on server: ${this.currentServer?.name}`, args);
      
      // Get server URL
      const serverUrl = this.getCurrentServerUrl();
      
      // Get auth headers
      const headers = this.getAuthHeaders();
      
      // Call MCP tool endpoint
      const response = await axios.post(
        `${serverUrl}/tools/${toolName}`,
        { arguments: args },
        { headers }
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
  async accessResource(resourceUri, serverName = null) {
    try {
      // Set server if specified
      if (serverName) {
        this.setCurrentServer(serverName);
      }
      
      console.log(`Accessing MCP resource: ${resourceUri} on server: ${this.currentServer?.name}`);
      
      // Get server URL
      const serverUrl = this.getCurrentServerUrl();
      
      // Get auth headers
      const headers = this.getAuthHeaders();
      
      // Call MCP resource endpoint
      const response = await axios.get(
        `${serverUrl}${resourceUri}`,
        { headers }
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
  async getManifest(serverName = null) {
    try {
      // Set server if specified
      if (serverName) {
        this.setCurrentServer(serverName);
      }
      
      console.log(`Getting MCP server manifest for: ${this.currentServer?.name}`);
      
      // Get server URL
      const serverUrl = this.getCurrentServerUrl();
      
      // Get auth headers
      const headers = this.getAuthHeaders();
      
      // Call MCP manifest endpoint
      const response = await axios.get(`${serverUrl}/manifest`, { headers });
      
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
  async changeLayout(layoutType, layoutParams = {}, serverName = null) {
    return this.useTool('change_layout', {
      layout_type: layoutType,
      layout_params: layoutParams
    }, serverName);
  }
  
  /**
   * Calculate centrality metrics for nodes in the graph.
   * 
   * @param {string} centralityType - Type of centrality to calculate
   * @returns {Promise<object>} - Centrality values for nodes
   */
  async calculateCentrality(centralityType, serverName = null) {
    return this.useTool('calculate_centrality', {
      centrality_type: centralityType
    }, serverName);
  }
  
  /**
   * Highlight specific nodes in the network.
   * 
   * @param {string[]} nodeIds - List of node IDs to highlight
   * @param {string} highlightColor - Color to use for highlighting
   * @returns {Promise<object>} - Updated node colors
   */
  async highlightNodes(nodeIds, highlightColor = '#ff0000', serverName = null) {
    return this.useTool('highlight_nodes', {
      node_ids: nodeIds,
      highlight_color: highlightColor
    }, serverName);
  }
  
  /**
   * Change visual properties of nodes or edges.
   * 
   * @param {string} propertyType - Type of property to change
   * @param {string} propertyValue - Value to set for the property
   * @param {object} propertyMapping - Optional mapping of node/edge IDs to property values
   * @returns {Promise<object>} - Updated visual properties
   */
  async changeVisualProperties(propertyType, propertyValue, propertyMapping = {}, serverName = null) {
    return this.useTool('change_visual_properties', {
      property_type: propertyType,
      property_value: propertyValue,
      property_mapping: propertyMapping
    }, serverName);
  }
  
  /**
   * Get information about the current network.
   * 
   * @returns {Promise<object>} - Network information
   */
  async getNetworkInfo(serverName = null) {
    return this.useTool('get_network_info', {}, serverName);
  }
  
  /**
   * Get information about specific nodes in the network.
   * 
   * @param {string[]} nodeIds - List of node IDs to get information for
   * @returns {Promise<object>} - Node information
   */
  async getNodeInfo(nodeIds, serverName = null) {
    return this.useTool('get_node_info', {
      node_ids: nodeIds
    }, serverName);
  }
  
  /**
   * Get the current network data.
   * 
   * @returns {Promise<object>} - Network data
   */
  async getNetworkData(serverName = null) {
    return this.accessResource('/resources/network', serverName);
  }

  /**
   * Get a sample network.
   * 
   * @returns {Promise<object>} - Sample network data
   */
  async getSampleNetwork(serverName = null) {
    return this.useTool('get_sample_network', {}, serverName);
  }

  /**
   * Save the current network data for a user.
   * 
   * @param {string} userId - ID of the user
   * @param {string} networkName - Name to save the network as
   * @returns {Promise<object>} - Success status and message
   */
  async saveNetwork(userId, networkName = 'default', serverName = null) {
    return this.useTool('save_network', {
      user_id: userId,
      network_name: networkName
    }, serverName);
  }

  /**
   * Load a saved network for a user.
   * 
   * @param {string} userId - ID of the user
   * @param {string} networkName - Name of the network to load
   * @returns {Promise<object>} - Loaded network data
   */
  async loadNetwork(userId, networkName = 'default', serverName = null) {
    return this.useTool('load_network', {
      user_id: userId,
      network_name: networkName
    }, serverName);
  }

  /**
   * List all saved networks for a user.
   * 
   * @param {string} userId - ID of the user
   * @returns {Promise<object>} - List of network names
   */
  async listUserNetworks(userId, serverName = null) {
    return this.useTool('list_user_networks', {
      user_id: userId
    }, serverName);
  }

  /**
   * Apply a layout algorithm based on community detection.
   * 
   * @param {string} algorithm - Community detection algorithm to use
   * @param {object} layoutParams - Parameters for the layout algorithm
   * @returns {Promise<object>} - Updated network positions
   */
  async applyCommunityLayout(algorithm = 'louvain', layoutParams = {}, serverName = null) {
    return this.useTool('apply_community_layout', {
      algorithm,
      layout_params: layoutParams
    }, serverName);
  }

  /**
   * Compare different layout algorithms for the current network.
   * 
   * @param {string[]} layouts - List of layout algorithms to compare
   * @returns {Promise<object>} - Positions for each layout algorithm
   */
  async compareLayouts(layouts = ['spring', 'circular', 'kamada_kawai'], serverName = null) {
    return this.useTool('compare_layouts', {
      layouts
    }, serverName);
  }

  /**
   * Recommend a layout algorithm based on user's question or network properties.
   * 
   * @param {string} question - User's question about visualization
   * @returns {Promise<object>} - Recommended layout algorithm and parameters
   */
  async recommendLayout(question, serverName = null) {
    return this.useTool('recommend_layout', {
      question
    }, serverName);
  }

  /**
   * Export the current network as GraphML format.
   * 
   * @param {boolean} includePositions - Whether to include node positions in the GraphML
   * @param {boolean} includeVisualProperties - Whether to include visual properties in the GraphML
   * @returns {Promise<object>} - GraphML string representation of the network
   */
  async exportNetworkAsGraphML(includePositions = true, includeVisualProperties = true, serverName = null) {
    return this.useTool('export_network_as_graphml', {
      include_positions: includePositions,
      include_visual_properties: includeVisualProperties
    }, serverName);
  }

  /**
   * Process a chat message and execute network operations.
   * 
   * @param {string} message - The chat message to process
   * @returns {Promise<object>} - Response with executed operation result
   */
  async processChatMessage(message, serverName = null) {
    return this.useTool('process_chat_message', {
      message
    }, serverName);
  }
}

// Create and export a singleton instance
const mcpClient = new MCPClient();
export default mcpClient;
