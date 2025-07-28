import { create } from "zustand";
import { networkAPI } from "./api";
import useChatStore from "./chatStore";

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
  layout: "spring",
  layoutParams: {},
  positions: [],
  centrality: null,
  centralityType: null,
  isLoading: false, // 初期状態ではロード中ではない
  error: null,
  recommendation: null,
  visualProperties: {
    node_size: 5,
    node_color: "#1d4ed8",
    edge_width: 1,
    edge_color: "#94a3b8",
  },

  // Set network data
  setNetworkData: (nodes, edges) => {
    set({ nodes, edges });
  },

  // Set layout type
  setLayout: (layout) => {
    set({ layout });
  },

  // Set positions
  setPositions: (positions) => {
    set({ positions });
  },

  // Set layout parameters
  setLayoutParams: (layoutParams) => {
    set({ layoutParams });
  },

  // Calculate layout using API
  calculateLayout: async () => {
    // 無限ループ検出のための静的変数
    if (!calculateLayout.callCount) {
      calculateLayout.callCount = 0;
    }
    calculateLayout.callCount++;
    
    // 短時間に多数の呼び出しがある場合は無限ループと判断して処理をスキップ
    if (calculateLayout.callCount > 5) {
      console.log("Too many calculateLayout calls detected, possible infinite loop. Skipping...");
      calculateLayout.callCount = 0; // カウンターをリセット
      set({ isLoading: false }); // 確実にローディング状態を解除
      return true;
    }
    
    // 現在の状態を取得
    let { nodes, positions, layout, layoutParams, initialLoadComplete } = get();

    // 現在の状態をログ出力
    console.log("Current state in calculateLayout:", {
      nodesLength: nodes?.length || 0,
      positionsLength: positions?.length || 0,
      callCount: calculateLayout.callCount,
      initialLoadComplete: initialLoadComplete || false
    });

    // 初期ロードが完了している場合、または既にノードとpositionsが存在する場合は、レイアウト計算をスキップ
    if (initialLoadComplete || (positions?.length > 0 && nodes?.length > 0 && positions.length === nodes.length)) {
      console.log("Initial load complete or positions and nodes already exist, skipping layout calculation");
      // 確実にisLoadingをfalseに設定
      set({ isLoading: false });
      calculateLayout.callCount = 0; // カウンターをリセット
      return true;
    }
    
    // ノードが存在しない場合、サンプルネットワークを直接生成
    if (!nodes?.length) {
      console.log("No nodes found, generating sample network directly in calculateLayout");
      try {
        // サンプルネットワークを読み込む前にisLoadingをtrueに設定
        set({ isLoading: true, error: null });
        
        // サンプルネットワークを直接生成（非同期APIを使わない）
        const sampleNodes = [];
        const sampleEdges = [];
        const samplePositions = [];
        
        // 中心ノード
        sampleNodes.push({
          id: "0",
          label: "Center Node",
        });
        
        // 中心ノードの位置
        samplePositions.push({
          id: "0",
          label: "Center Node",
          x: 0,
          y: 0,
          size: 8,
          color: "#1d4ed8",
        });
        
        // 10個の衛星ノード
        for (let i = 1; i <= 10; i++) {
          sampleNodes.push({
            id: i.toString(),
            label: `Node ${i}`,
          });
          
          // 中心ノードとの接続
          sampleEdges.push({
            source: "0",
            target: i.toString(),
          });
          
          // 円形に配置
          const angle = (i - 1) * (2 * Math.PI / 10);
          samplePositions.push({
            id: i.toString(),
            label: `Node ${i}`,
            x: Math.cos(angle),
            y: Math.sin(angle),
            size: 5,
            color: "#1d4ed8",
          });
        }
        
        // 状態を直接更新
        set({
          nodes: sampleNodes,
          edges: sampleEdges,
          positions: samplePositions,
          layout: "spring",
          isLoading: false,
          error: null,
          initialLoadComplete: true // 初期ロードが完了したことを示すフラグを設定
        });
        
        console.log("Sample network generated directly in calculateLayout:", {
          nodesCount: sampleNodes.length,
          edgesCount: sampleEdges.length,
          positionsCount: samplePositions.length,
          initialLoadComplete: true
        });
        
        // 更新後の状態を確認
        const updatedState = get();
        console.log("State after sample network generation:", {
          nodesLength: updatedState.nodes?.length || 0,
          edgesLength: updatedState.edges?.length || 0,
          positionsLength: updatedState.positions?.length || 0,
          initialLoadComplete: updatedState.initialLoadComplete
        });
        
        calculateLayout.callCount = 0; // カウンターをリセット
        return true;
      } catch (error) {
        console.error("Error generating sample network in calculateLayout:", error);
        set({ error: "Failed to generate sample network", isLoading: false });
        calculateLayout.callCount = 0; // カウンターをリセット
        return false;
      }
    }

    // APIリクエストを送信せず、直接グリッドレイアウトを生成
    console.log("Generating grid layout directly without API request");
    set({ isLoading: true, error: null });
    
    try {
      // 既存のノードに基づいてグリッドレイアウトを生成
      const positions = nodes.map((node, index) => {
        const cols = Math.ceil(Math.sqrt(nodes.length));
        const row = Math.floor(index / cols);
        const col = index % cols;
        return {
          id: node.id,
          label: node.label || node.id,
          x: (col / cols) * 2 - 1,
          y: (row / cols) * 2 - 1,
          size: 5,
          color: "#1d4ed8",
        };
      });

      // 状態を更新
      set({
        positions,
        isLoading: false,
        error: null,
        initialLoadComplete: true // 初期ロードが完了したことを示すフラグを設定
      });
      
      console.log("Grid layout generated successfully:", {
        nodesCount: nodes.length,
        positionsCount: positions.length
      });
      
      calculateLayout.callCount = 0; // カウンターをリセット
      return true;
    } catch (error) {
      console.error("Error generating grid layout:", error);
      set({
        isLoading: false,
        error: "Failed to generate grid layout",
      });
      calculateLayout.callCount = 0; // カウンターをリセット
      return false;
    }
  },

  // Apply layout using MCP client with GraphML
  applyLayout: async () => {
    const { nodes, layout, layoutParams } = get();

    // ノードが存在しない場合、サンプルネットワークを自動的に読み込む
    if (!nodes.length) {
      console.log("No nodes found in applyLayout, generating static sample network directly");
      // 静的なサンプルネットワークを直接生成する関数
      const generateStaticSampleNetwork = () => {
        console.log("Generating static sample network directly in applyLayout");
        const sampleNodes = [];
        const sampleEdges = [];
        const samplePositions = [];
        
        // 中心ノード
        sampleNodes.push({
          id: "0",
          label: "Center Node",
        });
        
        // 中心ノードの位置
        samplePositions.push({
          id: "0",
          label: "Center Node",
          x: 0,
          y: 0,
          size: 8,
          color: "#1d4ed8",
        });
        
        // 10個の衛星ノード
        for (let i = 1; i <= 10; i++) {
          sampleNodes.push({
            id: i.toString(),
            label: `Node ${i}`,
          });
          
          // 中心ノードとの接続
          sampleEdges.push({
            source: "0",
            target: i.toString(),
          });
          
          // 円形に配置
          const angle = (i - 1) * (2 * Math.PI / 10);
          samplePositions.push({
            id: i.toString(),
            label: `Node ${i}`,
            x: Math.cos(angle),
            y: Math.sin(angle),
            size: 5,
            color: "#1d4ed8",
          });
        }
        
        // 状態を直接更新
        set({
          nodes: sampleNodes,
          edges: sampleEdges,
          positions: samplePositions,
          layout: "spring",
          isLoading: false,
          error: null,
          initialLoadComplete: true // 初期ロードが完了したことを示すフラグを設定
        });
        
        return true;
      };
      
      // 静的なサンプルネットワークを直接生成
      const sampleGenerated = generateStaticSampleNetwork();
      if (!sampleGenerated) {
        set({ error: "Failed to generate sample network", isLoading: false });
        return false;
      }
      
      // 更新されたノードを取得
      const updatedNodes = get().nodes;
      if (!updatedNodes.length) {
        set({ error: "Sample network has no nodes", isLoading: false });
        return false;
      }
      
      // サンプルネットワークが生成されたので、レイアウト計算はスキップ
      return true;
    }

    // 既存のノードに基づいてグリッドレイアウトを生成（APIリクエストを送信しない）
    console.log("Generating grid layout directly for existing nodes without API request");
    set({ isLoading: true, error: null });
    
    try {
      // グリッドレイアウトを生成
      const positions = nodes.map((node, index) => {
        const cols = Math.ceil(Math.sqrt(nodes.length));
        const row = Math.floor(index / cols);
        const col = index % cols;
        return {
          id: node.id,
          label: node.label || node.id,
          x: (col / cols) * 2 - 1,
          y: (row / cols) * 2 - 1,
          size: 5,
          color: "#1d4ed8",
        };
      });

      // 状態を更新
      set({
        positions,
        isLoading: false,
        error: null,
        initialLoadComplete: true // 初期ロードが完了したことを示すフラグを設定
      });
      
      console.log("Grid layout generated successfully for existing nodes:", {
        nodesCount: nodes.length,
        positionsCount: positions.length
      });
      
      return true;
    } catch (error) {
      console.error("Error generating grid layout:", error);
      set({
        isLoading: false,
        error: "Failed to generate grid layout",
      });
      return false;
    }
  },


  // Load sample network using API
  loadSampleNetwork: async () => {
    // 無限ループ検出のための静的変数
    if (!loadSampleNetwork.callCount) {
      loadSampleNetwork.callCount = 0;
    }
    loadSampleNetwork.callCount++;
    
    // 短時間に多数の呼び出しがある場合は無限ループと判断して処理をスキップ
    if (loadSampleNetwork.callCount > 5) {
      console.log("Too many loadSampleNetwork calls detected, possible infinite loop. Skipping...");
      loadSampleNetwork.callCount = 0; // カウンターをリセット
      set({ isLoading: false }); // 確実にローディング状態を解除
      return true;
    }
    
    // 既にノードとpositionsが存在する場合、または初期ロードが完了している場合はスキップ
    const currentState = get();
    if (currentState.initialLoadComplete || (currentState.nodes.length > 0 && currentState.positions.length > 0)) {
      console.log("Sample network already loaded or initial load complete, skipping loadSampleNetwork");
      // 確実にisLoadingをfalseに設定
      set({ isLoading: false });
      loadSampleNetwork.callCount = 0; // カウンターをリセット
      return true;
    }
    
    console.log("Generating static sample network in loadSampleNetwork");
    set({ isLoading: true, error: null });
    
    try {
      // 静的なサンプルネットワークを直接生成
      const sampleNodes = [];
      const sampleEdges = [];
      const samplePositions = [];
      
      // 中心ノード
      sampleNodes.push({
        id: "0",
        label: "Center Node",
      });
      
      // 中心ノードの位置
      samplePositions.push({
        id: "0",
        label: "Center Node",
        x: 0,
        y: 0,
        size: 8,
        color: "#1d4ed8",
      });
      
      // 10個の衛星ノード
      for (let i = 1; i <= 10; i++) {
        sampleNodes.push({
          id: i.toString(),
          label: `Node ${i}`,
        });
        
        // 中心ノードとの接続
        sampleEdges.push({
          source: "0",
          target: i.toString(),
        });
        
        // 円形に配置
        const angle = (i - 1) * (2 * Math.PI / 10);
        samplePositions.push({
          id: i.toString(),
          label: `Node ${i}`,
          x: Math.cos(angle),
          y: Math.sin(angle),
          size: 5,
          color: "#1d4ed8",
        });
      }
      
      // 状態を直接更新（同期的に実行）
      set({
        nodes: sampleNodes,
        edges: sampleEdges,
        positions: samplePositions,
        layout: "spring",
        isLoading: false,
        error: null,
        initialLoadComplete: true // 初期ロードが完了したことを示すフラグを設定
      });
      
      // 更新後の状態を確認
      const updatedState = get();
      console.log("Static sample network generated successfully in loadSampleNetwork:", {
        nodes: updatedState.nodes.length,
        edges: updatedState.edges.length,
        positions: updatedState.positions.length,
        initialLoadComplete: updatedState.initialLoadComplete
      });
      
      // 状態が正しく更新されたことを確認
      if (updatedState.nodes.length === 0 || updatedState.positions.length === 0) {
        console.error("Failed to update state with sample network");
        set({
          isLoading: false,
          error: "Failed to update state with sample network",
        });
        loadSampleNetwork.callCount = 0; // カウンターをリセット
        return false;
      }
      
      // 確実にisLoadingをfalseに設定
      set({ isLoading: false });
      loadSampleNetwork.callCount = 0; // カウンターをリセット
      
      // 明示的に更新後の状態を返す
      return {
        success: true,
        nodes: updatedState.nodes,
        edges: updatedState.edges,
        positions: updatedState.positions,
        initialLoadComplete: true
      };
    } catch (error) {
      console.error("Error generating static sample network:", error);
      set({
        isLoading: false,
        error: "Failed to generate sample network",
      });
      loadSampleNetwork.callCount = 0; // カウンターをリセット
      return false;
    }
    
    // 以下のAPIを使用したサンプルネットワーク読み込みは無限ループの原因となるため、
    // 静的なサンプルネットワーク生成に置き換えました
    /*
    try {
      console.log("Attempting to load sample network");

      // Use API to get sample network
      const response = await networkAPI.getSampleNetwork();
      const result = response.data;

      if (result && result.success) {
        console.log("Sample network loaded successfully:", result);
        
        // 確実にノードとエッジが存在することを確認
        if (!result.nodes || result.nodes.length === 0) {
          console.error("Sample network has no nodes");
          throw new Error("Sample network has no nodes");
        }
        
        // 直接positionsも設定する
        const positions = result.nodes.map((node) => ({
          id: node.id,
          label: node.label || node.id,
          x: node.x || Math.random() * 2 - 1, // 位置情報がない場合はランダムな位置を設定
          y: node.y || Math.random() * 2 - 1,
          size: node.size || 5,
          color: node.color || "#1d4ed8",
        }));
        
        // 状態を更新する前に、現在の状態をログ出力
        console.log("Current state before update:", {
          nodes: get().nodes.length,
          edges: get().edges.length,
          positions: get().positions.length
        });
        
        // 状態を更新
        set({
          nodes: result.nodes || [],
          edges: result.edges || [],
          positions: positions, // positionsを直接設定
          layout: result.layout || "spring",
          layoutParams: result.layout_params || {},
          isLoading: false,
          error: null,
        });
        
        // 更新後の状態をログ出力
        console.log("Updated state after loading sample network:", {
          nodes: get().nodes.length,
          edges: get().edges.length,
          positions: get().positions.length
        });
        
        return true; // 成功を返す（calculateLayoutを呼び出さない）
      } else {
        throw new Error(result.error || "Failed to load sample network");
      }
    } catch (error) {
      console.error("Failed to load sample network:", error);

      // Create a fallback sample network if all methods fail
      try {
        console.log("Creating fallback sample network");

        // Create a simple star network as fallback
        const nodes = [];
        const edges = [];
        const positions = [];

        // Create center node
        nodes.push({
          id: "0",
          label: "Center Node",
        });
        
        // Center nodeのposition
        positions.push({
          id: "0",
          label: "Center Node",
          x: 0,
          y: 0,
          size: 8,
          color: "#1d4ed8",
        });

        // Create 10 satellite nodes
        for (let i = 1; i <= 10; i++) {
          nodes.push({
            id: i.toString(),
            label: `Node ${i}`,
          });

          // Connect to center node
          edges.push({
            source: "0",
            target: i.toString(),
          });
          
          // 円形に配置
          const angle = (i - 1) * (2 * Math.PI / 10);
          positions.push({
            id: i.toString(),
            label: `Node ${i}`,
            x: Math.cos(angle),
            y: Math.sin(angle),
            size: 5,
            color: "#1d4ed8",
          });
        }

        console.log("Fallback sample network created");
        set({
          nodes,
          edges,
          positions, // positionsも設定
          layout: "spring",
          isLoading: false,
          error: null,
        });
        
        return true; // 成功を返す（calculateLayoutを呼び出さない）
      } catch (fallbackError) {
        console.error(
          "Failed to create fallback sample network:",
          fallbackError,
        );
        set({
          isLoading: false,
          error: error.message || "Failed to load sample network",
        });
        return false;
      }
    }
    */
  },


  // Apply centrality values to nodes
  applyCentralityValues: (centralityValues, centralityType) => {
    const maxValue = Math.max(...Object.values(centralityValues), 1);
    const updatedPositions = get().positions.map((node) => {
      const value = centralityValues[node.id] || 0;
      // Scale size from 5 to 20
      const normalizedSize = 5 + (value / maxValue) * 15;
      return {
        ...node,
        size: normalizedSize,
        color: getCentralityColor(value, maxValue),
      };
    });
    set({
      positions: updatedPositions,
      centrality: centralityValues,
      centralityType,
    });
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
      error: null,
    });
  },

  // Upload network file using GraphML-based API
  uploadNetworkFile: async (file) => {
    set({ isLoading: true, error: null });
    try {
      const conversationId = useChatStore.getState().currentConversationId;
      console.log(`Uploading file. Conversation ID: ${conversationId}`);

      // networkAPIのuploadGraphMLを呼び出す
      const response = await networkAPI.uploadGraphML(file, conversationId);
      const result = response.data;

      console.log("Upload response from API:", result);

      // 成功時のレスポンス形式を厳密にチェック
      if (result && result.network_id && result.conversation_id) {
        console.log("File uploaded successfully. New data:", result);

        // 新しい会話IDをストアに設定
        useChatStore.getState().setCurrentConversationId(result.conversation_id);
        
        // チャットに成功メッセージを追加
        useChatStore.getState().addMessage({
          role: "assistant",
          content: `ファイル "${file.name}" が正常にアップロードされ、新しいネットワークが作成されました。`,
          timestamp: new Date().toISOString(),
        });

        // 新しく作成されたネットワークのデータを取得してグラフを更新
        const cytoscapeResponse = await networkAPI.getNetworkCytoscape(result.network_id);
        const cytoData = cytoscapeResponse.data;

        if (cytoData && cytoData.elements) {
            set({
                nodes: cytoData.elements.nodes.map(n => n.data),
                edges: cytoData.elements.edges.map(e => e.data),
                positions: cytoData.elements.nodes.map(n => ({ ...n.data, ...n.position })),
                isLoading: false,
                error: null,
                initialLoadComplete: true,
            });
            return { success: true };
        } else {
            throw new Error("Failed to retrieve valid Cytoscape data after upload.");
        }
      } else {
        // APIからのエラーメッセージを優先的に使用
        const errorMessage = result.detail || "Unknown error during file upload process.";
        console.error("File upload failed:", errorMessage);
        throw new Error(errorMessage);
      }
    } catch (error) {
      // エラーオブジェクトから詳細なメッセージを抽出
      const errorMessage =
        error.response?.data?.detail || // FastAPIからの詳細エラー
        error.message || // 一般的なJavaScriptエラー
        "An unknown error occurred during file upload.";

      console.error("Caught error in uploadNetworkFile:", errorMessage);
      
      set({
        isLoading: false,
        error: errorMessage, // ストアに詳細なエラーメッセージを保存
      });

      return {
        success: false,
        error: errorMessage, // 呼び出し元に詳細なエラーメッセージを返す
      };
    }
  },


  // Export network as GraphML
  exportAsGraphML: async () => {
    const { currentConversationId } = useChatStore.getState();
    if (!currentConversationId) {
      set({ error: "No active conversation selected." });
      return null;
    }
    // TODO: conversationIdからnetworkIdを取得する処理が必要
    const networkId = currentConversationId; 

    set({ isLoading: true, error: null });
    try {
      console.log("Exporting network as GraphML");
      const response = await networkAPI.exportNetworkAsGraphML(networkId);
      set({ isLoading: false, error: null });
      return response.data;
    } catch (error) {
      console.error("Failed to export network as GraphML:", error);
      set({
        isLoading: false,
        error: error.message || "Failed to export network as GraphML",
      });
      return null;
    }
  },


  // Get network information
  getNetworkInfo: async () => {
    const { currentConversationId } = useChatStore.getState();
    if (!currentConversationId) {
      set({ error: "No active conversation selected." });
      return null;
    }
    // TODO: conversationIdからnetworkIdを取得する処理が必要
    const networkId = currentConversationId;

    set({ isLoading: true, error: null });
    try {
      const response = await networkAPI.getNetworkCytoscape(networkId);
      const cytoData = response.data;
      if (cytoData && cytoData.elements) {
        const nodes = cytoData.elements.nodes.map(n => n.data);
        const edges = cytoData.elements.edges.map(e => e.data);
        const positions = cytoData.elements.nodes.map(n => ({ ...n.data, ...n.position }));
        set({
          nodes,
          edges,
          positions,
          isLoading: false,
          error: null,
          initialLoadComplete: true,
        });
        return {
          success: true,
          network_info: {
            has_network: true,
            num_nodes: nodes.length,
            num_edges: edges.length,
          },
        };
      } else {
        throw new Error("Failed to retrieve valid Cytoscape data.");
      }
    } catch (error) {
      console.error("Error fetching network info:", error);
      set({ isLoading: false, error: error.message });
      return null;
    }
  },
}));

export default useNetworkStore;
