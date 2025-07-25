/**
 * MCP (Model Context Protocol) client for interacting with the MCP server.
 * This client provides methods for using MCP tools and accessing MCP resources.
 * Enhanced with network data persistence and advanced layout algorithms.
 */

import axios from "axios";

// API URL
const API_URL = "http://localhost:8000";
const MCP_URL = `${API_URL}/proxy/networkx`;
const NETWORKX_URL = "http://localhost:8001";

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
      const token = localStorage.getItem("token");
      if (!token) {
        console.error("No token found, cannot use MCP tool");
        throw new Error("Authentication required");
      }

      // Call MCP tool endpoint
      const response = await axios.post(
        `${MCP_URL}/tools/${toolName}`,
        { arguments: args },
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        },
      );

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
      console.log(`Accessing MCP resource: ${resourceUri}`);

      // Get token from localStorage
      const token = localStorage.getItem("token");
      if (!token) {
        console.error("No token found, cannot access MCP resource");
        throw new Error("Authentication required");
      }

      // Call MCP resource endpoint
      const response = await axios.get(`${MCP_URL}${resourceUri}`, {
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
      console.log("Getting MCP server manifest");

      // Call MCP manifest endpoint
      const response = await axios.get(`${MCP_URL}/manifest`);

      console.log("MCP server manifest:", response.data);
      return response.data;
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
    return this.useTool("change_layout", {
      layout_type: layoutType,
      layout_params: layoutParams,
    });
  }

  /**
   * Calculate centrality metrics for nodes in the graph.
   *
   * @param {string} centralityType - Type of centrality to calculate
   * @returns {Promise<object>} - Centrality values for nodes
   */
  async calculateCentrality(centralityType) {
    return this.useTool("calculate_centrality", {
      centrality_type: centralityType,
    });
  }

  /**
   * Highlight specific nodes in the network.
   *
   * @param {string[]} nodeIds - List of node IDs to highlight
   * @param {string} highlightColor - Color to use for highlighting
   * @returns {Promise<object>} - Updated node colors
   */
  async highlightNodes(nodeIds, highlightColor = "#ff0000") {
    return this.useTool("highlight_nodes", {
      node_ids: nodeIds,
      highlight_color: highlightColor,
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
  async changeVisualProperties(
    propertyType,
    propertyValue,
    propertyMapping = {},
  ) {
    return this.useTool("change_visual_properties", {
      property_type: propertyType,
      property_value: propertyValue,
      property_mapping: propertyMapping,
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
      // API呼び出しを実行して、より柔軟にレスポンスを処理
      console.log("Getting network information");

      try {
        const result = await this.useTool("get_network_info", {});

        // レスポンスの検証
        if (!result) {
          console.warn("getNetworkInfo: No result returned from MCP server");
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
   * Get information about specific nodes in the network.
   *
   * @param {string[]} nodeIds - List of node IDs to get information for
   * @returns {Promise<object>} - Node information
   */
  async getNodeInfo(nodeIds) {
    return this.useTool("get_node_info", {
      node_ids: nodeIds,
    });
  }

  /**
   * Get the current network data.
   *
   * @returns {Promise<object>} - Network data
   */
  async getNetworkData() {
    return this.accessResource("/resources/network");
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
    return this.useTool("load_network", {
      user_id: userId,
      network_name: networkName,
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
  async callNetworkXDirect(endpoint, data = null, method = "GET") {
    try {
      console.log(`Direct call to NetworkX endpoint: ${endpoint}`);

      // Get token from localStorage
      const token = localStorage.getItem("token");
      if (!token) {
        console.error("No token found, cannot call NetworkX directly");
        throw new Error("Authentication required");
      }

      const config = {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      };

      let response;
      if (method.toUpperCase() === "GET") {
        response = await axios.get(`${NETWORKX_URL}/${endpoint}`, config);
      } else {
        response = await axios.post(
          `${NETWORKX_URL}/${endpoint}`,
          data,
          config,
        );
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
    return this.useTool("list_user_networks", {
      user_id: userId,
    });
  }

  /**
   * Apply a layout algorithm based on community detection.
   *
   * @param {string} algorithm - Community detection algorithm to use
   * @param {object} layoutParams - Parameters for the layout algorithm
   * @returns {Promise<object>} - Updated network positions
   */
  async applyCommunityLayout(algorithm = "louvain", layoutParams = {}) {
    return this.useTool("apply_community_layout", {
      algorithm,
      layout_params: layoutParams,
    });
  }

  /**
   * Compare different layout algorithms for the current network.
   *
   * @param {string[]} layouts - List of layout algorithms to compare
   * @returns {Promise<object>} - Positions for each layout algorithm
   */
  async compareLayouts(layouts = ["spring", "circular", "kamada_kawai"]) {
    return this.useTool("compare_layouts", {
      layouts,
    });
  }

  /**
   * Recommend a layout algorithm based on user's question or network properties.
   *
   * @param {string} question - User's question about visualization
   * @returns {Promise<object>} - Recommended layout algorithm and parameters
   */
  async recommendLayout(question) {
    return this.useTool("recommend_layout", {
      question,
    });
  }

  /**
   * Export the current network as GraphML format.
   *
   * @returns {Promise<object>} - GraphML string representation of the network
   */
  async exportNetworkAsGraphML() {
    return this.useTool("export_graphml", {});
  }

  /**
   * Import a network from GraphML format string.
   *
   * @param {string} graphmlContent - GraphML format string
   * @returns {Promise<object>} - Import result with network data
   */
  async importGraphML(graphmlContent) {
    return this.useTool("import_graphml", {
      graphml_content: graphmlContent,
    });
  }

  /**
   * Convert any GraphML data to the standard format with name, color, size, and description attributes.
   *
   * @param {string} graphmlContent - GraphML content to convert
   * @returns {Promise<object>} - Conversion result with standardized GraphML content
   */
  async convertGraphML(graphmlContent) {
    return this.useTool("convert_graphml", {
      graphml_content: graphmlContent,
    });
  }

  /**
   * Apply a layout algorithm to a network in GraphML format.
   *
   * @param {string} graphmlContent - GraphML format string
   * @param {string} layoutType - Type of layout algorithm
   * @param {object} layoutParams - Parameters for the layout algorithm
   * @returns {Promise<object>} - Updated GraphML content with node positions
   */
  async graphmlLayout(graphmlContent, layoutType, layoutParams = {}) {
    return this.useTool("graphml_layout", {
      graphml_content: graphmlContent,
      layout_type: layoutType,
      layout_params: layoutParams,
    });
  }

  /**
   * Calculate centrality metrics for a network in GraphML format.
   *
   * @param {string} graphmlContent - GraphML format string
   * @param {string} centralityType - Type of centrality to calculate
   * @returns {Promise<object>} - Updated GraphML content with centrality values
   */
  async graphmlCentrality(graphmlContent, centralityType) {
    return this.useTool("graphml_centrality", {
      graphml_content: graphmlContent,
      centrality_type: centralityType,
    });
  }

  /**
   * Get information about specific nodes in a network in GraphML format.
   *
   * @param {string} graphmlContent - GraphML format string
   * @param {string[]} nodeIds - List of node IDs to get information for
   * @returns {Promise<object>} - Node information and updated GraphML content
   */
  async graphmlNodeInfo(graphmlContent, nodeIds) {
    return this.useTool("graphml_node_info", {
      graphml_content: graphmlContent,
      node_ids: nodeIds,
    });
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
    return this.useTool("graphml_highlight_nodes", {
      graphml_content: graphmlContent,
      node_ids: nodeIds,
      highlight_color: highlightColor,
    });
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
    return this.useTool("graphml_visual_properties", {
      graphml_content: graphmlContent,
      property_type: propertyType,
      property_value: propertyValue,
      property_mapping: propertyMapping,
    });
  }

  /**
   * Get information about a network in GraphML format.
   *
   * @param {string} graphmlContent - GraphML format string
   * @returns {Promise<object>} - Network information and updated GraphML content
   */
  async graphmlNetworkInfo(graphmlContent) {
    return this.useTool("graphml_network_info", {
      graphml_content: graphmlContent,
    });
  }

  /**
   * Process a chat message with GraphML data.
   *
   * @param {string} message - The chat message to process
   * @param {string} graphmlContent - GraphML format string (optional)
   * @returns {Promise<object>} - Processing result and updated GraphML content
   */
  async graphmlChat(message, graphmlContent = null) {
    const args = {
      message: message,
    };

    if (graphmlContent) {
      args.graphml_content = graphmlContent;
    }

    return this.useTool("graphml_chat", args);
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
      
      // GraphMLベースのチャット処理を試みる
      if (isCentralityQuery) {
        try {
          console.log("Detected centrality query, trying GraphML-based processing");
          
          // 現在のネットワークをGraphMLとしてエクスポート
          let exportResult;
          try {
            exportResult = await this.exportNetworkAsGraphML();
          } catch (exportError) {
            console.warn("Failed to export network as GraphML:", exportError);
            console.log("Attempting to load sample network before processing centrality query");
            
            // サンプルネットワークを読み込む
            try {
              const sampleNetwork = await this.getSampleNetwork();
              if (sampleNetwork && sampleNetwork.success) {
                console.log("Successfully loaded sample network for centrality processing");
                // サンプルネットワークを読み込んだ後、再度エクスポートを試みる
                exportResult = await this.exportNetworkAsGraphML();
              } else {
                throw new Error("Failed to load sample network");
              }
            } catch (sampleError) {
              console.error("Failed to load sample network:", sampleError);
              throw new Error("No network available for centrality calculation");
            }
          }
          
          if (exportResult && exportResult.success && exportResult.content) {
            console.log("Successfully exported network as GraphML for chat processing");
            
            // GraphMLベースのチャット処理を実行
            const result = await this.graphmlChat(message, exportResult.content);
            
            if (result && result.success) {
              console.log("GraphML chat processing successful");
              
              // GraphMLコンテンツが返された場合、インポートして状態を更新
              if (result.graphml_content) {
                console.log("Importing updated GraphML from chat response");
                const importResult = await this.importGraphML(result.graphml_content);
                
                if (importResult && importResult.success) {
                  console.log("Successfully imported updated GraphML");
                  
                  // 中心性に関する推奨がある場合は、ユーザーに選択を促す
                  if (result.recommended_centrality) {
                    console.log("Centrality recommendation received:", result.recommended_centrality);
                    return {
                      success: true,
                      content: result.content || "ネットワークの分析に基づいて中心性指標を推奨します。",
                      recommended_centrality: result.recommended_centrality,
                      // networkUpdateは含めない - ユーザーの確認を待つ
                    };
                  }
                  
                  // 中心性タイプが指定されていて、かつapply_centralityフラグがtrueの場合のみ適用
                  if ((result.centrality_type || result.recommended_centrality) && result.apply_centrality) {
                    let centralityType = "degree"; // デフォルト
                    if (result.recommended_centrality) {
                      centralityType = result.recommended_centrality;
                    } else if (result.centrality_type) {
                      centralityType = result.centrality_type;
                    }
                    
                    // 中心性を適用するレスポンスを返す
                    return {
                      success: true,
                      content: result.content || "中心性に基づいてノードのサイズが更新されました。",
                      networkUpdate: {
                        type: "centrality",
                        centralityType: centralityType
                      }
                    };
                  }
                  
                  // それ以外の場合は、通常のレスポンスを返す
                  return {
                    success: true,
                    content: result.content || "GraphMLが正常に処理されました。",
                    // networkUpdateは含めない
                  };
                }
              }
              
              // GraphMLコンテンツがない場合は通常のレスポンスを返す
              return {
                success: true,
                content: result.content || "処理が完了しました。",
                networkUpdate: result.networkUpdate || null
              };
            }
          }
        } catch (graphmlError) {
          console.error("Error in GraphML-based chat processing:", graphmlError);
          // エラーが発生した場合は従来の方法にフォールバック
          console.log("Falling back to traditional chat processing");
        }
      }
      
      // 従来の方法でチャットメッセージを処理
      const result = await this.useTool("process_chat_message", {
        message,
      });

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
      
      // ケース3: NetworkXMCP/tools/centrality_chat.pyのprocess_chat_messageからの応答
      // 直接contentフィールドにデータがある場合
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
