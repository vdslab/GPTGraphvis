import { create } from 'zustand';
import useNetworkStore from './networkStore';
import mcpClient from './mcpClient';

const useChatStore = create((set, get) => ({
  messages: [],
  isProcessing: false,
  error: null,
  typingTimeout: null,

  // Parse and execute network operations from chat messages
  executeNetworkOperation: async (message) => {
    console.log("Executing network operation for message:", message);
    const messageLower = message.toLowerCase();
    
    // Get network store functions
    const networkStore = useNetworkStore.getState();
    
    // Define patterns for different operations
    const layoutPatterns = {
      spring: /\b(spring|スプリング)\b/i,
      circular: /\b(circular|円形|サークル)\b/i,
      random: /\b(random|ランダム)\b/i,
      spectral: /\b(spectral|スペクトル)\b/i,
      shell: /\b(shell|シェル)\b/i,
      kamada_kawai: /\b(kamada|kawai|カマダ|カワイ)\b/i,
      fruchterman_reingold: /\b(fruchterman|reingold|フルクターマン|レインゴールド)\b/i
    };
    
    const centralityPatterns = {
      degree: /\b(degree|次数|ディグリー)\b/i,
      closeness: /\b(closeness|近接|クローズネス)\b/i,
      betweenness: /\b(betweenness|媒介|ビトウィーンネス)\b/i,
      eigenvector: /\b(eigenvector|固有ベクトル|アイゲンベクトル)\b/i,
      pagerank: /\b(pagerank|ページランク)\b/i
    };
    
    const colorPatterns = {
      red: /\b(red|赤|レッド)\b/i,
      blue: /\b(blue|青|ブルー)\b/i,
      green: /\b(green|緑|グリーン)\b/i,
      yellow: /\b(yellow|黄|イエロー)\b/i,
      purple: /\b(purple|紫|パープル)\b/i,
      orange: /\b(orange|オレンジ)\b/i,
      black: /\b(black|黒|ブラック)\b/i,
      white: /\b(white|白|ホワイト)\b/i
    };
    
    const colorMap = {
      red: '#ff0000',
      blue: '#0000ff',
      green: '#00ff00',
      yellow: '#ffff00',
      purple: '#800080',
      orange: '#ffa500',
      black: '#000000',
      white: '#ffffff'
    };
    
    // Check for layout change requests
    if (messageLower.includes('layout') || messageLower.includes('レイアウト')) {
      // Check for layout recommendation request
      if (messageLower.includes('recommend') || messageLower.includes('suggestion') || 
          messageLower.includes('おすすめ') || messageLower.includes('提案')) {
        try {
          const result = await networkStore.recommendLayoutAndApply(message);
          if (result) {
            return {
              success: true,
              content: `Based on your request, I recommend using the ${networkStore.recommendation.recommended_layout} layout. ${networkStore.recommendation.recommendation_reason} I've applied this layout to the network.`,
              networkUpdate: {
                type: 'layout',
                layout: networkStore.recommendation.recommended_layout,
                layoutParams: networkStore.recommendation.recommended_parameters || {}
              }
            };
          } else {
            return {
              success: false,
              content: "I couldn't recommend a layout based on your request. Please try again with more specific details about what you want to visualize."
            };
          }
        } catch (error) {
          console.error("Error recommending layout:", error);
          return {
            success: false,
            content: "I'm sorry, I encountered an error trying to recommend a layout. Please try again later."
          };
        }
      }
      
      // Check for specific layout requests
      for (const [layoutType, pattern] of Object.entries(layoutPatterns)) {
        if (pattern.test(messageLower)) {
          try {
            networkStore.setLayout(layoutType);
            const result = await networkStore.calculateLayout();
            
            if (result) {
              return {
                success: true,
                content: `I've changed the layout to ${layoutType}. The network visualization has been updated.`,
                networkUpdate: {
                  type: 'layout',
                  layout: layoutType
                }
              };
            } else {
              return {
                success: false,
                content: `I couldn't apply the ${layoutType} layout. Please try again later.`
              };
            }
          } catch (error) {
            console.error(`Error applying ${layoutType} layout:`, error);
            return {
              success: false,
              content: `I'm sorry, I encountered an error trying to apply the ${layoutType} layout. Please try again later.`
            };
          }
        }
      }
      
      // If no specific layout was mentioned but "layout" was
      return {
        success: true,
        content: "You can use the following layouts: Spring, Circular, Random, Spectral, Shell, Kamada-Kawai, and Fruchterman-Reingold. Just ask me to change to any of these layouts."
      };
    }
    
    // Check for centrality requests
    if (messageLower.includes('centrality') || messageLower.includes('中心性') || 
        messageLower.includes('センタリティ') || messageLower.includes('measure') || 
        messageLower.includes('指標') || messageLower.includes('重要度') || 
        messageLower.includes('重要なノード') || messageLower.includes('ノードの大きさ')) {
      
      // 特定の中心性タイプが明示的に指定されている場合
      for (const [centralityType, pattern] of Object.entries(centralityPatterns)) {
        if (pattern.test(messageLower)) {
          try {
            // 承認キーワードが含まれている場合は直接適用
            const approvalKeywords = ["適用", "実行", "計算", "やって", "ok", "yes", "実施", "お願い"];
            const hasApproval = approvalKeywords.some(keyword => messageLower.includes(keyword));
            
            if (hasApproval) {
              const result = await networkStore.applyCentrality(centralityType);
              
              if (result) {
                return {
                  success: true,
                  content: `${centralityType}中心性を適用しました。ノードのサイズと色は中心性値に基づいて変更されています。`,
                  networkUpdate: {
                    type: 'centrality',
                    centralityType: centralityType
                  }
                };
              } else {
                return {
                  success: false,
                  content: `${centralityType}中心性の適用に失敗しました。後でもう一度お試しください。`
                };
              }
            } else {
              // 承認なしの場合は、中心性の説明と確認を求める
              const centralityInfo = {
                degree: {
                  name: "次数中心性",
                  description: "多くのノードと直接つながっているノードを重要とみなします。SNSで友達が多い人や、交通網で多くの路線が通る駅などが該当します。"
                },
                closeness: {
                  name: "近接中心性",
                  description: "ネットワーク全体の中心に位置し、他のノードへの距離が近いノードを重要とみなします。情報が速く広がる位置にあるノードなどが該当します。"
                },
                betweenness: {
                  name: "媒介中心性",
                  description: "異なるグループを「橋渡し」するノードを重要とみなします。情報や物資の流れを制御できる位置にあるノードが該当します。"
                },
                eigenvector: {
                  name: "固有ベクトル中心性",
                  description: "重要なノードとつながっているノードほど重要とみなします。「重要な人とつながりのある人」が重要という考え方です。"
                },
                pagerank: {
                  name: "PageRank",
                  description: "Googleの検索エンジンで使われる指標で、多くの重要なノードから参照されているノードを重要とみなします。"
                }
              };
              
              const info = centralityInfo[centralityType] || { name: centralityType, description: "ノードの重要度を測る指標です。" };
              
              return {
                success: true,
                content: `${info.name}は${info.description}\n\nこの中心性を適用しますか？「はい」と返信すると、ノードの大きさが中心性に応じて変化します。`,
                recommended_centrality: centralityType
              };
            }
          } catch (error) {
            console.error(`Error processing ${centralityType} centrality request:`, error);
            return {
              success: false,
              content: `${centralityType}中心性の処理中にエラーが発生しました。後でもう一度お試しください。`
            };
          }
        }
      }
      
      // 承認メッセージの場合（「はい」「適用してください」など）
      const approvalKeywords = ["はい", "適用", "お願い", "実行", "計算", "やって", "ok", "yes", "実施"];
      if (approvalKeywords.some(keyword => messageLower.includes(keyword))) {
        // 前回推奨された中心性タイプを取得（実際の実装ではユーザーの対話履歴から取得）
        // ここでは簡易的にstoreから取得
        const previousMessages = get().messages;
        let recommendedCentrality = "degree"; // デフォルト
        
        // 直前のメッセージから推奨された中心性を探す
        for (let i = previousMessages.length - 1; i >= 0; i--) {
          const msg = previousMessages[i];
          if (msg.role === 'assistant' && msg.recommended_centrality) {
            recommendedCentrality = msg.recommended_centrality;
            break;
          }
        }
        
        try {
          const result = await networkStore.applyCentrality(recommendedCentrality);
          
          if (result) {
            return {
              success: true,
              content: `了解しました。${recommendedCentrality}中心性に基づいてノードの大きさを変更しています。大きいノードほど、その中心性指標において重要度が高いことを示しています。`,
              networkUpdate: {
                type: 'centrality',
                centralityType: recommendedCentrality
              }
            };
          } else {
            return {
              success: false,
              content: `中心性の適用に失敗しました。後でもう一度お試しください。`
            };
          }
        } catch (error) {
          console.error(`Error applying centrality:`, error);
          return {
            success: false,
            content: `中心性の適用中にエラーが発生しました。後でもう一度お試しください。`
          };
        }
      }
      
      // 特定の中心性が指定されておらず、「中心性」や「重要度」などの一般的なキーワードが含まれている場合
      try {
        // MCPクライアントを使用して中心性に関するチャット処理を行う
        const result = await mcpClient.processChatMessage(message);
        
        // 中心性の推奨がある場合はそのまま返す
        if (result && result.recommended_centrality) {
          return result;
        }
        
        // それ以外の場合は一般的な中心性の説明を返す
        return {
          success: true,
          content: "ネットワークの重要なノードを分析するには中心性指標が役立ちます。以下の中心性指標から選択できます：\n\n" +
                  "1. **次数中心性（Degree Centrality）**: 多くの直接的なつながりを持つノードを重視します。「人気者」や「ハブ」を見つけるのに適しています。\n\n" +
                  "2. **近接中心性（Closeness Centrality）**: ネットワーク全体への近さを測ります。情報が素早く広がる位置にあるノードを特定するのに適しています。\n\n" +
                  "3. **媒介中心性（Betweenness Centrality）**: 異なるグループ間の「橋渡し」役となるノードを重視します。情報や資源の流れを制御できる位置にあるノードを特定します。\n\n" +
                  "4. **固有ベクトル中心性（Eigenvector Centrality）**: 重要なノードとつながっているノードを重視します。影響力のあるノードを特定するのに適しています。\n\n" +
                  "5. **PageRank**: Googleの検索エンジンで使われる指標で、重要なノードからの参照を重視します。\n\n" +
                  "どの中心性を適用しますか？例えば「次数中心性を適用」のように指定してください。あるいは、ネットワークの特性に基づいて最適な中心性を推奨することもできます。",
          options: ["degree", "closeness", "betweenness", "eigenvector", "pagerank"]
        };
      } catch (error) {
        console.error(`Error processing centrality request:`, error);
        return {
          success: false,
          content: `中心性の処理中にエラーが発生しました。後でもう一度お試しください。`
        };
      }
    }
    
    // Check for color change requests
    if (messageLower.includes('color') || messageLower.includes('色') || 
        messageLower.includes('カラー')) {
      
      // Check if it's for nodes or edges
      const isForNodes = messageLower.includes('node') || messageLower.includes('ノード') || 
                         !messageLower.includes('edge') && !messageLower.includes('エッジ');
      
      const target = isForNodes ? 'nodes' : 'edges';
      const propertyType = isForNodes ? 'node_color' : 'edge_color';
      
      // Check for specific colors
      for (const [colorName, pattern] of Object.entries(colorPatterns)) {
        if (pattern.test(messageLower)) {
          try {
            // Use MCP client to change visual properties
            const result = await networkStore.changeVisualProperties(propertyType, colorMap[colorName]);
            
            if (result) {
              return {
                success: true,
                content: `I've changed the color of the ${target} to ${colorName}.`,
                networkUpdate: {
                  type: 'visualProperty',
                  propertyType: propertyType,
                  propertyValue: colorMap[colorName]
                }
              };
            } else {
              return {
                success: false,
                content: `I couldn't change the color of the ${target} to ${colorName}. Please try again later.`
              };
            }
          } catch (error) {
            console.error(`Error changing ${target} color to ${colorName}:`, error);
            return {
              success: false,
              content: `I'm sorry, I encountered an error trying to change the color of the ${target} to ${colorName}. Please try again later.`
            };
          }
        }
      }
      
      // If no specific color was mentioned but "color" was
      return {
        success: true,
        content: `You can change the color of ${target} to: Red, Blue, Green, Yellow, Purple, Orange, Black, or White. Just ask me to change the color to any of these colors.`
      };
    }
    
    // Check for size change requests
    if (messageLower.includes('size') || messageLower.includes('サイズ') || 
        messageLower.includes('大きさ') || messageLower.includes('太さ')) {
      
      // Check if it's for nodes or edges
      const isForNodes = messageLower.includes('node') || messageLower.includes('ノード') || 
                         !messageLower.includes('edge') && !messageLower.includes('エッジ');
      
      const target = isForNodes ? 'nodes' : 'edges';
      const propertyType = isForNodes ? 'node_size' : 'edge_width';
      
      // Check for increase or decrease
      const isIncrease = messageLower.includes('increase') || messageLower.includes('larger') || 
                         messageLower.includes('bigger') || messageLower.includes('大きく') || 
                         messageLower.includes('太く');
      
      const isDecrease = messageLower.includes('decrease') || messageLower.includes('smaller') || 
                         messageLower.includes('thinner') || messageLower.includes('小さく') || 
                         messageLower.includes('細く');
      
      // Get current value and calculate new value
      const currentValue = isForNodes ? 
        networkStore.visualProperties?.node_size || 5 : 
        networkStore.visualProperties?.edge_width || 1;
      
      let newValue = currentValue;
      
      if (isIncrease) {
        newValue = isForNodes ? Math.min(20, currentValue * 1.5) : Math.min(5, currentValue * 1.5);
      } else if (isDecrease) {
        newValue = isForNodes ? Math.max(2, currentValue / 1.5) : Math.max(0.5, currentValue / 1.5);
      } else {
        // Try to extract a specific size value
        const sizeMatch = messageLower.match(/\b(\d+(\.\d+)?)\b/);
        if (sizeMatch) {
          newValue = parseFloat(sizeMatch[1]);
          // Ensure reasonable limits
          if (isForNodes) {
            newValue = Math.max(2, Math.min(20, newValue));
          } else {
            newValue = Math.max(0.5, Math.min(5, newValue));
          }
        }
      }
      
      // Only proceed if the value has changed
      if (newValue !== currentValue) {
        try {
          // Use MCP client to change visual properties
          const result = await networkStore.changeVisualProperties(propertyType, newValue);
          
          if (result) {
            return {
              success: true,
              content: `I've changed the size of the ${target} to ${newValue}.`,
              networkUpdate: {
                type: 'visualProperty',
                propertyType: propertyType,
                propertyValue: newValue
              }
            };
          } else {
            return {
              success: false,
              content: `I couldn't change the size of the ${target}. Please try again later.`
            };
          }
        } catch (error) {
          console.error(`Error changing ${target} size:`, error);
          return {
            success: false,
            content: `I'm sorry, I encountered an error trying to change the size of the ${target}. Please try again later.`
          };
        }
      }
      
      // If no specific size change was requested but "size" was mentioned
      return {
        success: true,
        content: `You can ask me to increase or decrease the size of ${target}, or specify a specific size value.`
      };
    }
    
    // Check for network information request
    if (messageLower.includes('info') || messageLower.includes('information') || 
        messageLower.includes('statistics') || messageLower.includes('stats') || 
        messageLower.includes('情報') || messageLower.includes('統計')) {
      
      try {
        const result = await networkStore.getNetworkInfo();
        
        if (result && result.success) {
          const info = result.network_info;
          return {
            success: true,
            content: `Network Information:
- Nodes: ${info.num_nodes}
- Edges: ${info.num_edges}
- Density: ${info.density.toFixed(4)}
- Connected: ${info.is_connected ? 'Yes' : 'No'}
- Components: ${info.num_components}
- Average Degree: ${info.avg_degree.toFixed(2)}
- Clustering Coefficient: ${info.clustering_coefficient.toFixed(4)}
- Current Layout: ${info.current_layout}
- Current Centrality: ${info.current_centrality || 'None'}`
          };
        } else {
          return {
            success: false,
            content: "I couldn't retrieve network information. Please try again later."
          };
        }
      } catch (error) {
        console.error("Error getting network information:", error);
        return {
          success: false,
          content: "I'm sorry, I encountered an error trying to retrieve network information. Please try again later."
        };
      }
    }
    
    // Check for help request
    if (messageLower.includes('help') || messageLower.includes('ヘルプ') || 
        messageLower.includes('使い方') || messageLower.includes('how to')) {
      
      return {
        success: true,
        content: `Here are the operations you can perform via chat:

1. Change layout: "Use circular layout" or "Apply Fruchterman-Reingold layout"
2. Get layout recommendation: "Recommend a layout for community detection"
3. Apply centrality: "Show degree centrality" or "Apply betweenness centrality"
4. Change colors: "Make nodes red" or "Change edge color to blue"
5. Change sizes: "Increase node size" or "Make edges thinner"
6. Get network information: "Show network statistics" or "Display network info"

You can also upload network files using the "Upload Network File" button at the top of the visualization panel.`
      };
    }
    
    // If no operation was recognized
    return {
      success: false,
      content: "I'm sorry, I don't understand that request. Type 'help' to see what operations I can perform."
    };
  },

  // Send a message to the chat API
  sendMessage: async (message) => {
    console.log("chatStore.sendMessage called with:", message);
    const { messages } = get();
    console.log("Current messages in store:", messages);
    
    // Add user message to the chat with timestamp
    const userMessage = { 
      role: 'user', 
      content: message,
      timestamp: new Date().toISOString()
    };
    console.log("Adding user message to chat:", userMessage);
    
    // First add the user message to the state directly
    const currentMessages = [...messages];
    const updatedMessagesWithUser = [...currentMessages, userMessage];
    
    console.log("Setting messages directly:", updatedMessagesWithUser);
    set({ 
      messages: updatedMessagesWithUser,
      isProcessing: true,
      error: null
    });
    
    console.log("After direct set, messages:", get().messages);
    
    try {
      console.log("Processing message:", message);
      
      // Use MCP server to process chat message
      const operationResult = await mcpClient.processChatMessage(message);
      console.log("MCP operation result:", operationResult ? operationResult : "No result");
      
      // Create response based on operation result
      let responseContent = "I'm sorry, I don't understand that request. You can ask me about network visualization or uploading network files.";
      let networkUpdate = null;
      
      if (operationResult) {
        // Check if the operation was successful
        if (operationResult.success) {
          responseContent = operationResult.content || "Operation successful";
          networkUpdate = operationResult.networkUpdate || null;
        } else {
          // 安全に処理：operationResult.errorがundefinedの場合のエラー回避
          responseContent = operationResult.content || 
                           (operationResult.error ? operationResult.error : "Failed to process your request.");
        }
      }
      
      // Add assistant response to the chat with timestamp
      const assistantMessage = { 
        role: 'assistant', 
        content: responseContent,
        networkUpdate: networkUpdate,
        timestamp: new Date().toISOString()
      };
      
      console.log("Generated assistant message:", assistantMessage);
      
      console.log("Created assistant message:", assistantMessage);
      
      // Add the message to the state
      set(state => {
        console.log("Updating state with assistant message");
        const updatedMessages = [...state.messages, assistantMessage];
        console.log("Updated messages array:", updatedMessages);
        return { 
          messages: updatedMessages,
          isProcessing: false
        };
      });
      
      console.log("State updated, returning assistant message");
      return assistantMessage;
    } catch (error) {
      console.error("Error sending message:", error);
      console.error("Error type:", error.constructor.name);
      console.error("Error message:", error.message);
      console.error("Error stack:", error.stack);
      
      // Check if it's an authentication error
      if (error.response?.status === 401) {
        console.error("Authentication error when sending message");
        set({ 
          isProcessing: false, 
          error: "Authentication failed. Please log in again."
        });
      } else {
        console.error("Other error type:", error.name);
        console.error("Error response:", error.response || "No response available");
        
        // エラーオブジェクトを安全に処理
        let errorMessage = 'Failed to send message';
        if (error.response && error.response.data && error.response.data.detail) {
          errorMessage = error.response.data.detail;
        } else if (error.message) {
          errorMessage = error.message;
        }
        
        set({ 
          isProcessing: false, 
          error: errorMessage
        });
      }
      
      console.log("Returning null due to error");
      return null;
    }
  },

  // Clear all messages
  clearMessages: () => {
    set({ messages: [], error: null });
  },
  
  // Set typing indicator
  setTypingIndicator: (isTyping) => {
    const { typingTimeout } = get();
    
    // Clear any existing timeout
    if (typingTimeout) {
      clearTimeout(typingTimeout);
    }
    
    if (isTyping) {
      // Set typing indicator and clear it after 30 seconds (failsafe)
      const timeout = setTimeout(() => {
        set({ isProcessing: false });
      }, 30000);
      
      set({ isProcessing: true, typingTimeout: timeout });
    } else {
      set({ isProcessing: false, typingTimeout: null });
    }
  },
  
  // Add a message directly (useful for system messages or local updates)
  addMessage: (message) => {
    if (!message.role || !message.content) {
      console.error("Invalid message format:", message);
      return;
    }
    
    // Add timestamp if not provided
    if (!message.timestamp) {
      message.timestamp = new Date().toISOString();
    }
    
    console.log("Adding message directly:", message);
    console.log("Current messages before adding:", get().messages);
    
    // Create a new message object to avoid reference issues
    const newMessage = { ...message };
    
    // Force a completely new array to avoid reference issues
    const currentMessages = [...get().messages];
    const updatedMessages = [...currentMessages, newMessage];
    
    console.log("Updated messages array after direct add:", updatedMessages);
    console.log("Message count after adding:", updatedMessages.length);
    
    // Set the state with the updated messages
    set(() => {
      console.log("Setting state with messages:", updatedMessages);
      return { messages: updatedMessages };
    });
    
    // Add a small delay and then verify the message was added
    setTimeout(() => {
      console.log("Messages after state update (delayed check):", get().messages);
      console.log("Message count after delay:", get().messages.length);
    }, 100);
    
    return newMessage; // Return the added message for chaining
  },
  
  // Debug function to check the current state of messages
  debugMessages: () => {
    const currentMessages = get().messages;
    console.log("DEBUG - Current messages:", currentMessages);
    console.log("DEBUG - Message count:", currentMessages.length);
    return currentMessages;
  }
}));

export default useChatStore;
