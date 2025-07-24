/**
 * MCP (Model Context Protocol) client for interacting with the MCP server.
 * This client provides methods for using MCP tools and accessing MCP resources.
 * Enhanced with network data persistence and advanced layout algorithms.
 */

import axios from 'axios';

// API URL
const API_URL = 'http://localhost:8000';
const MCP_URL = `${API_URL}/proxy/networkx`;
const NETWORKX_URL = 'http://localhost:8001';

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
      
      // レスポンスチェック - resultが存在しない場合のハンドリング
      if (!response.data || response.data.result === undefined) {
        console.warn(`Invalid response from MCP tool ${toolName}:`, response.data);
        return {
          success: false,
          content: "サーバーから無効な応答を受け取りました。"
        };
      }
      
      return response.data.result;
    } catch (error) {
      console.error(`Error using MCP tool ${toolName}:`, error);
      
      // エラーオブジェクトの安全な処理
      const errorMessage = error.response?.data?.detail || error.message || `Error using MCP tool ${toolName}`;
      
      // ツールエラー時にも適切なレスポンス形式を返す
      if (toolName === 'process_chat_message') {
        return {
          success: false,
          content: `エラーが発生しました: ${errorMessage}`
        };
      }
      
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
   * Get default network information.
   * 
   * @returns {object} - Default network information
   * @private
   */
  getDefaultNetworkInfo() {
    return {
      success: true,
      network_info: {
        has_network: false,
        current_layout: "spring",
        current_centrality: null,
        num_nodes: 0,
        num_edges: 0,
        density: 0,
        is_connected: false,
        num_components: 0,
        avg_degree: 0,
        clustering_coefficient: 0
      }
    };
  }
  
  /**
   * Get information about the current network.
   * 
   * @returns {Promise<object>} - Network information
   */
  async getNetworkInfo() {
    try {
      // API呼び出しを実行して、より柔軟にレスポンスを処理
      console.log("Getting network information");
      
      try {
        const result = await this.useTool('get_network_info', {});
        
        // レスポンスの検証
        if (!result) {
          console.warn('getNetworkInfo: No result returned from MCP server');
          return this.getDefaultNetworkInfo();
        }
        
        // レスポンスにnetwork_infoプロパティがない場合
        if (result.success && !result.network_info) {
          console.warn('getNetworkInfo: Missing network_info property in response', result);
          return this.getDefaultNetworkInfo();
        }
        
        // エラーレスポンスが返ってきた場合
        if (result.error) {
          console.warn('getNetworkInfo: Error in response', result.error);
          return this.getDefaultNetworkInfo();
        }
        
        return result;
      } catch (apiError) {
        console.error('API error in getNetworkInfo:', apiError);
        return this.getDefaultNetworkInfo();
      }
    } catch (error) {
      console.error('Error in getNetworkInfo:', error);
      return this.getDefaultNetworkInfo();
    }
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

  /**
   * Get a sample network.
   * 
   * @returns {Promise<object>} - Sample network data
   */
  async getSampleNetwork() {
    try {
      console.log(`Getting sample network directly from NetworkX server`);
      
      // Call the direct endpoint on the NetworkX MCP server without authentication
      // This endpoint is publicly accessible
      const response = await axios.get(`${NETWORKX_URL}/get_sample_network`);
      
      console.log(`Sample network response from direct call:`, response.data);
      return response.data;
    } catch (directError) {
      console.error(`Error getting sample network directly:`, directError);
      
      try {
        console.log(`Creating fallback sample network`);
        
        // Create a simple star network as fallback
        const nodes = [];
        const edges = [];
        
        // Create center node
        nodes.push({
          id: "0",
          label: "Center Node",
          x: 0,
          y: 0,
          size: 10,
          color: "#1d4ed8"
        });
        
        // Create 10 satellite nodes
        for (let i = 1; i <= 10; i++) {
          const angle = (i - 1) * (2 * Math.PI / 10);
          const x = Math.cos(angle);
          const y = Math.sin(angle);
          
          nodes.push({
            id: i.toString(),
            label: `Node ${i}`,
            x: x,
            y: y,
            size: 5,
            color: "#1d4ed8"
          });
          
          // Connect to center node
          edges.push({
            source: "0",
            target: i.toString(),
            width: 1,
            color: "#94a3b8"
          });
        }
        
        console.log("Fallback sample network created");
        return {
          success: true,
          nodes: nodes,
          edges: edges,
          layout: "circular",
          layout_params: {}
        };
      } catch (fallbackError) {
        console.error(`Failed to create fallback sample network:`, fallbackError);
        throw new Error('Failed to load sample network');
      }
    }
  }

  /**
   * Upload a saved network for a user.
   * 
   * @param {string} userId - ID of the user
   * @param {string} networkName - Name of the network to load
   * @returns {Promise<object>} - Loaded network data
   */
  async loadNetwork(userId, networkName = 'default') {
    return this.useTool('load_network', {
      user_id: userId,
      network_name: networkName
    });
  }

  /**
   * Direct call to NetworkX MCP server endpoints.
   * This is a fallback method when the MCP proxy is not working.
   * 
   * @param {string} endpoint - Endpoint to call
   * @param {object} data - Data to send (for POST requests)
   * @param {string} method - HTTP method (GET or POST)
   * @returns {Promise<object>} - Response data
   */
  async callNetworkXDirect(endpoint, data = null, method = 'GET') {
    try {
      console.log(`Direct call to NetworkX endpoint: ${endpoint}`);
      
      // Get token from localStorage
      const token = localStorage.getItem('token');
      if (!token) {
        console.error('No token found, cannot call NetworkX directly');
        throw new Error('Authentication required');
      }
      
      const config = {
        headers: {
          Authorization: `Bearer ${token}`
        }
      };
      
      let response;
      if (method.toUpperCase() === 'GET') {
        response = await axios.get(`${NETWORKX_URL}/${endpoint}`, config);
      } else {
        response = await axios.post(`${NETWORKX_URL}/${endpoint}`, data, config);
      }
      
      console.log(`NetworkX direct response:`, response.data);
      return response.data;
    } catch (error) {
      console.error(`Error calling NetworkX directly:`, error);
      throw error;
    }
  }


  /**
   * List all saved networks for a user.
   * 
   * @param {string} userId - ID of the user
   * @returns {Promise<object>} - List of network names
   */
  async listUserNetworks(userId) {
    return this.useTool('list_user_networks', {
      user_id: userId
    });
  }

  /**
   * Apply a layout algorithm based on community detection.
   * 
   * @param {string} algorithm - Community detection algorithm to use
   * @param {object} layoutParams - Parameters for the layout algorithm
   * @returns {Promise<object>} - Updated network positions
   */
  async applyCommunityLayout(algorithm = 'louvain', layoutParams = {}) {
    return this.useTool('apply_community_layout', {
      algorithm,
      layout_params: layoutParams
    });
  }

  /**
   * Compare different layout algorithms for the current network.
   * 
   * @param {string[]} layouts - List of layout algorithms to compare
   * @returns {Promise<object>} - Positions for each layout algorithm
   */
  async compareLayouts(layouts = ['spring', 'circular', 'kamada_kawai']) {
    return this.useTool('compare_layouts', {
      layouts
    });
  }

  /**
   * Recommend a layout algorithm based on user's question or network properties.
   * 
   * @param {string} question - User's question about visualization
   * @returns {Promise<object>} - Recommended layout algorithm and parameters
   */
  async recommendLayout(question) {
    return this.useTool('recommend_layout', {
      question
    });
  }

  /**
   * Export the current network as GraphML format.
   * 
   * @param {boolean} includePositions - Whether to include node positions in the GraphML
   * @param {boolean} includeVisualProperties - Whether to include visual properties in the GraphML
   * @returns {Promise<object>} - GraphML string representation of the network
   */
  async exportNetworkAsGraphML(includePositions = true, includeVisualProperties = true) {
    return this.useTool('export_network_as_graphml', {
      include_positions: includePositions,
      include_visual_properties: includeVisualProperties
    });
  }

  /**
   * Process a chat message and execute network operations.
   * 
   * @param {string} message - The chat message to process
   * @returns {Promise<object>} - Response with executed operation result
   */
  async processChatMessage(message) {
    try {
      const result = await this.useTool('process_chat_message', {
        message
      });
      
      // 結果が正常に返ってきたか確認
      if (!result) {
        console.warn('processChatMessage: No result returned from MCP server');
        return {
          success: false,
          content: "申し訳ありませんが、応答の処理中にエラーが発生しました。"
        };
      }
      
      // エラーチェックを追加
      if (typeof result === 'string') {
        return {
          success: true,
          content: result,
          networkUpdate: null
        };
      }
      
      // content属性がない場合は適切に処理
      if (result.content === undefined && result.message !== undefined) {
        result.content = result.message;
      } else if (result.content === undefined) {
        result.content = "応答内容が見つかりませんでした。";
      }
      
      // networkUpdateが存在するか確認
      if (result.networkUpdate === undefined) {
        result.networkUpdate = null;
      }
      
      // successプロパティがない場合はtrueを設定
      if (result.success === undefined) {
        result.success = true;
      }
      
      return result;
    } catch (error) {
      console.error('Error in processChatMessage:', error);
      // エラー発生時も適切なレスポンス形式で返す
      return {
        success: false,
        content: `申し訳ありませんが、メッセージの処理中にエラーが発生しました: ${error.message || 'Unknown error'}`,
        networkUpdate: null
      };
    }
  }
}

// Create and export a singleton instance
const mcpClient = new MCPClient();
export default mcpClient;
