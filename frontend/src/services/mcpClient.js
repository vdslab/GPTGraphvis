/**
 * MCP (Model Context Protocol) client for interacting with the MCP server.
 * This client provides methods for using MCP tools and accessing MCP resources.
 * Enhanced with network data persistence and advanced layout algorithms.
 * 
 * NOTE: This file has been updated to use the API server as a proxy to NetworkXMCP.
 * Direct communication with NetworkXMCP has been removed.
 */

import axios from "axios";
import { networkAPI } from "./api";

// API URL
// APIサーバーのURLのみを定義し、NetworkXMCPサーバーのURLは定義しない
const API_URL = "http://localhost:8000";

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
      console.log(`Using MCP tool via API proxy: ${toolName}`, args);
      
      // Use networkAPI to call the tool via API proxy
      const response = await networkAPI.useTool(toolName, args);
      
      console.log(`MCP tool ${toolName} response:`, response.data);

      // レスポンスチェック - resultが存在しない場合のハンドリング
      if (!response.data || response.data.result === undefined) {
        console.warn(
          `Invalid response from MCP tool ${toolName}:`,
          response.data,
        );
        return {
          success: false,
          content: "サーバーから無効な応答を受け取りました。",
        };
      }

      return response.data.result;
    } catch (error) {
      console.error(`Error using MCP tool ${toolName}:`, error);

      // エラーオブジェクトの安全な処理
      const errorMessage =
        error.response?.data?.detail ||
        error.message ||
        `Error using MCP tool ${toolName}`;

      // ツールエラー時にも適切なレスポンス形式を返す
      if (toolName === "process_chat_message") {
        return {
          success: false,
          content: `エラーが発生しました: ${errorMessage}`,
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
      console.log(`Accessing MCP resource via API proxy: ${resourceUri}`);

      // Get token from localStorage
      const token = localStorage.getItem("token");
      if (!token) {
        console.error("No token found, cannot access MCP resource");
        throw new Error("Authentication required");
      }

      // Call API server endpoint instead of direct NetworkXMCP access
      const response = await axios.get(`${API_URL}/network/resource${resourceUri}`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

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
      console.log("Getting MCP server manifest via API proxy");

      // Call API server endpoint instead of direct NetworkXMCP access
      const response = await networkAPI.useTool("get_manifest", {});
      
      console.log("MCP server manifest:", response.data);
      return response.data.result;
    } catch (error) {
      console.error("Error getting MCP server manifest:", error);
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
    return networkAPI.changeLayout(layoutType, layoutParams)
      .then(response => response.data.result);
  }

  /**
   * Calculate centrality metrics for nodes in the graph.
   *
   * @param {string} centralityType - Type of centrality to calculate
   * @returns {Promise<object>} - Centrality values for nodes
   */
  async calculateCentrality(centralityType) {
    return networkAPI.calculateCentrality(centralityType)
      .then(response => response.data.result);
  }

  /**
   * Highlight specific nodes in the network.
   *
   * @param {string[]} nodeIds - List of node IDs to highlight
   * @param {string} highlightColor - Color to use for highlighting
   * @returns {Promise<object>} - Updated node colors
   */
  async highlightNodes(nodeIds, highlightColor = "#ff0000") {
    const response = await networkAPI.useTool("highlight_nodes", {
      node_ids: nodeIds,
      highlight_color: highlightColor,
    });
    return response.data.result;
  }

  /**
   * Change visual properties of nodes or edges.
   *
   * @param {string} propertyType - Type of property to change
   * @param {string} propertyValue - Value to set for the property
   * @param {object} propertyMapping - Optional mapping of node/edge IDs to property values
   * @returns {Promise<object>} - Updated visual properties
   */
  async changeVisualProperties(
    propertyType,
    propertyValue,
    propertyMapping = {},
  ) {
    const response = await networkAPI.useTool("change_visual_properties", {
      property_type: propertyType,
      property_value: propertyValue,
      property_mapping: propertyMapping,
    });
    return response.data.result;
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
        clustering_coefficient: 0,
      },
    };
  }

  /**
   * Get information about the current network.
   *
   * @returns {Promise<object>} - Network information
   */
  async getNetworkInfo() {
    try {
      console.log("Getting network information via API proxy");

      try {
        const response = await networkAPI.getNetworkInfo();
        const result = response.data.result;

        // レスポンスの検証
        if (!result) {
          console.warn("getNetworkInfo: No result returned from API proxy");
          return this.getDefaultNetworkInfo();
        }

        // レスポンスにnetwork_infoプロパティがない場合
        if (result.success && !result.network_info) {
          console.warn(
            "getNetworkInfo: Missing network_info property in response",
            result,
          );
          return this.getDefaultNetworkInfo();
        }

        // エラーレスポンスが返ってきた場合
        if (result.error) {
          console.warn("getNetworkInfo: Error in response", result.error);
          return this.getDefaultNetworkInfo();
        }

        return result;
      } catch (apiError) {
        console.error("API error in getNetworkInfo:", apiError);
        return this.getDefaultNetworkInfo();
      }
    } catch (error) {
      console.error("Error in getNetworkInfo:", error);
      return this.getDefaultNetworkInfo();
    }
  }



  /**
   * Get a sample network.
   *
   * @returns {Promise<object>} - Sample network data
   */
  async getSampleNetwork() {
    try {
      console.log(`Getting sample network via API proxy`);
      
      // Use networkAPI to get sample network via API proxy
      const response = await networkAPI.getSampleNetwork();
      
      console.log(`Sample network response:`, response.data);
      return response.data;
    } catch (error) {
      console.error(`Error getting sample network:`, error);

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
          color: "#1d4ed8",
        });

        // Create 10 satellite nodes
        for (let i = 1; i <= 10; i++) {
          const angle = (i - 1) * ((2 * Math.PI) / 10);
          const x = Math.cos(angle);
          const y = Math.sin(angle);

          nodes.push({
            id: i.toString(),
            label: `Node ${i}`,
            x: x,
            y: y,
            size: 5,
            color: "#1d4ed8",
          });

          // Connect to center node
          edges.push({
            source: "0",
            target: i.toString(),
            width: 1,
            color: "#94a3b8",
          });
        }

        console.log("Fallback sample network created");
        return {
          success: true,
          nodes: nodes,
          edges: edges,
          layout: "circular",
          layout_params: {},
        };
      } catch (fallbackError) {
        console.error(
          `Failed to create fallback sample network:`,
          fallbackError,
        );
        throw new Error("Failed to load sample network");
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
  async loadNetwork(userId, networkName = "default") {
    const response = await networkAPI.useTool("load_network", {
      user_id: userId,
      network_name: networkName,
    });
    return response.data.result;
  }

  /**
   * Call to NetworkX MCP server endpoints via API proxy.
   * This replaces the direct call method.
   *
   * @param {string} endpoint - Endpoint to call
   * @param {object} data - Data to send (for POST requests)
   * @param {string} method - HTTP method (GET or POST)
   * @returns {Promise<object>} - Response data
   */
  async callNetworkXViaProxy(endpoint, data = null, method = "GET") {
    try {
      console.log(`Calling NetworkX endpoint via API proxy: ${endpoint}`);

      // Use networkAPI to call the endpoint via API proxy
      const response = await networkAPI.useTool("proxy_call", {
        endpoint: endpoint,
        data: data,
        method: method
      });

      console.log(`NetworkX proxy response:`, response.data);
      return response.data.result;
    } catch (error) {
      console.error(`Error calling NetworkX via proxy:`, error);
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
    const response = await networkAPI.useTool("list_user_networks", {
      user_id: userId,
    });
    return response.data.result;
  }



  /**
   * Recommend a layout algorithm based on user's question or network properties.
   *
   * @param {string} question - User's question about visualization
   * @returns {Promise<object>} - Recommended layout algorithm and parameters
   */
  async recommendLayout(question) {
    const response = await networkAPI.useTool("recommend_layout", {
      question,
    });
    return response.data.result;
  }

  /**
   * Export the current network as GraphML format.
   *
   * @returns {Promise<object>} - GraphML string representation of the network
   */
  async exportNetworkAsGraphML() {
    return networkAPI.exportNetworkAsGraphML()
      .then(response => {
        // APIサーバーのプロキシエンドポイントからのレスポンスは response.data.result の形式
        console.log("Export GraphML response:", response.data);
        return response.data.result;
      });
  }

  /**
   * Import a network from GraphML format string.
   *
   * @param {string} graphmlContent - GraphML format string
   * @returns {Promise<object>} - Import result with network data
   */

  /**
   * Apply a layout algorithm to a network in GraphML format.
   *
   * @param {string} graphmlContent - GraphML format string
   * @param {string} layoutType - Type of layout algorithm
   * @param {object} layoutParams - Parameters for the layout algorithm
   * @returns {Promise<object>} - Updated GraphML content with node positions
   */
  async graphmlLayout(graphmlContent, layoutType, layoutParams = {}) {
    return networkAPI.graphmlLayout(graphmlContent, layoutType, layoutParams)
      .then(response => response.data.result);
  }

  /**
   * Calculate centrality metrics for a network in GraphML format.
   *
   * @param {string} graphmlContent - GraphML format string
   * @param {string} centralityType - Type of centrality to calculate
   * @returns {Promise<object>} - Updated GraphML content with centrality values
   */
  async graphmlCentrality(graphmlContent, centralityType) {
    return networkAPI.graphmlCentrality(graphmlContent, centralityType)
      .then(response => response.data.result);
  }

  /**
   * Get information about specific nodes in a network in GraphML format.
   *
   * @param {string} graphmlContent - GraphML format string
   * @param {string[]} nodeIds - List of node IDs to get information for
   * @returns {Promise<object>} - Node information and updated GraphML content
   */
  async graphmlNodeInfo(graphmlContent, nodeIds) {
    const response = await networkAPI.useTool("graphml_node_info", {
      graphml_content: graphmlContent,
      node_ids: nodeIds,
    });
    return response.data.result;
  }

  /**
   * Highlight specific nodes in a network in GraphML format.
   *
   * @param {string} graphmlContent - GraphML format string
   * @param {string[]} nodeIds - List of node IDs to highlight
   * @param {string} highlightColor - Color to use for highlighting
   * @returns {Promise<object>} - Updated GraphML content with highlighted nodes
   */
  async graphmlHighlightNodes(
    graphmlContent,
    nodeIds,
    highlightColor = "#ff0000",
  ) {
    const response = await networkAPI.useTool("graphml_highlight_nodes", {
      graphml_content: graphmlContent,
      node_ids: nodeIds,
      highlight_color: highlightColor,
    });
    return response.data.result;
  }

  /**
   * Change visual properties of nodes or edges in a network in GraphML format.
   *
   * @param {string} graphmlContent - GraphML format string
   * @param {string} propertyType - Type of property to change
   * @param {string} propertyValue - Value to set for the property
   * @param {object} propertyMapping - Optional mapping of node/edge IDs to property values
   * @returns {Promise<object>} - Updated GraphML content with changed visual properties
   */
  async graphmlVisualProperties(
    graphmlContent,
    propertyType,
    propertyValue,
    propertyMapping = {},
  ) {
    return networkAPI.graphmlVisualProperties(graphmlContent, propertyType, propertyValue, propertyMapping)
      .then(response => response.data.result);
  }



  /**
   * Process a chat message and execute network operations.
   *
   * @param {string} message - The chat message to process
   * @returns {Promise<object>} - Response with executed operation result
   */
  async processChatMessage(message) {
    try {
      // 中心性に関する質問かどうかをチェック
      const centralityKeywords = [
        "中心性", "centrality", "重要度", "重要なノード", "ノードの大きさ", 
        "重要", "中心", "センタリティ", "次数", "degree", "近接", "closeness", 
        "媒介", "betweenness", "固有ベクトル", "eigenvector", "pagerank"
      ];
      
      const isCentralityQuery = centralityKeywords.some(
        keyword => message.toLowerCase().includes(keyword)
      );
      
      
      // 従来の方法でチャットメッセージを処理
      const response = await networkAPI.useTool("process_chat_message", {
        message,
      });
      const result = response.data.result;

      // 詳細なレスポンスログ出力（デバッグ用）
      console.log("Process chat message raw response:", JSON.stringify(result));

      // 結果が正常に返ってきたか確認
      if (!result) {
        console.warn("processChatMessage: No result returned from MCP server");
        return {
          success: false,
          content: "申し訳ありませんが、応答の処理中にエラーが発生しました。",
        };
      }

      // エラーチェックを追加
      if (typeof result === "string") {
        return {
          success: true,
          content: result,
          networkUpdate: null,
        };
      }

      // レスポンスフォーマットの互換性向上
      // ケース1: content属性を持つ標準フォーマット
      if (result.content !== undefined) {
        // 既に適切なフォーマットなので、そのまま返す
        return {
          success: result.success !== undefined ? result.success : true,
          content: result.content,
          networkUpdate: result.networkUpdate || null
        };
      }
      
      // ケース2: messageプロパティを持つフォーマット
      if (result.message !== undefined) {
        return {
          success: result.success !== undefined ? result.success : true,
          content: result.message,
          networkUpdate: result.networkUpdate || null
        };
      }
      
      // ケース3: NetworkXMCPからの応答で、推奨中心性情報が含まれる場合
      if (result.success !== undefined && result.recommended_centrality !== undefined) {
        const centralityType = result.recommended_centrality || "degree";
        return {
          success: true,
          content: result.reason || "中心性に基づいてノードの重要度を視覚化します。",
          recommended_centrality: centralityType,
          networkUpdate: {
            type: "centrality",
            centralityType: centralityType
          }
        };
      }
      
      // ケース4: 汎用的なキー変換
      // 一般的に使われる可能性のあるキーをチェック
      const possibleContentKeys = ['text', 'response', 'reply', 'answer', 'result'];
      for (const key of possibleContentKeys) {
        if (result[key] !== undefined && typeof result[key] === 'string') {
          return {
            success: true,
            content: result[key],
            networkUpdate: null
          };
        }
      }

      // ケース5: フォールバック - 最も良い対応として全体をJSON文字列に変換
      if (Object.keys(result).length > 0) {
        // 応答を単純にJSON文字列として返す（デバッグ目的）
        return {
          success: true,
          content: "処理が完了しました。詳細なレスポンス: " + JSON.stringify(result),
          networkUpdate: null
        };
      }

      // どの条件にも合わない場合のデフォルト応答
      return {
        success: true,
        content: "応答を処理しました。",
        networkUpdate: null
      };
    } catch (error) {
      console.error("Error in processChatMessage:", error);
      // エラー発生時も適切なレスポンス形式で返す
      return {
        success: false,
        content: `申し訳ありませんが、メッセージの処理中にエラーが発生しました: ${error.message || "Unknown error"}`,
        networkUpdate: null,
      };
    }
  }
}

// Create and export a singleton instance
const mcpClient = new MCPClient();
export default mcpClient;
