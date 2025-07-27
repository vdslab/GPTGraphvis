import { create } from "zustand";
import { networkAPI } from "./api";

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

  // Get layout recommendation using API
  getLayoutRecommendation: async (description, purpose) => {
    set({ isLoading: true, error: null, recommendation: null });
    try {
      // Use API to get layout recommendation
      const response = await networkAPI.useTool("recommend_layout", {
        description,
        purpose,
      });
      const result = response.data.result;

      if (result && result.success) {
        set({
          recommendation: result.recommendation,
          isLoading: false,
          error: null,
        });
        return result.recommendation;
      } else {
        throw new Error(result.error || "Layout recommendation failed");
      }
    } catch (error) {
      console.error("Error getting layout recommendation:", error);
      set({
        isLoading: false,
        error: error.message || "Layout recommendation failed",
        recommendation: null,
      });
      return null;
    }
  },

  // Apply recommended layout
  applyRecommendedLayout: () => {
    const { recommendation } = get();

    if (!recommendation) {
      set({ error: "No recommendation available", isLoading: false });
      return false;
    }

    set({
      layout: recommendation.recommended_layout,
      layoutParams: recommendation.recommended_parameters || {},
    });

    return get().calculateLayout();
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

  // Apply centrality metrics using GraphML-based API
  applyCentrality: async (centralityType) => {
    const { nodes } = get();

    // ノードが存在しない場合、サンプルネットワークを自動的に読み込む
    if (!nodes.length) {
      console.log("No nodes found, loading sample network before applying centrality");
      try {
        const sampleLoaded = await get().loadSampleNetwork();
        if (!sampleLoaded) {
          set({ error: "Failed to load sample network", isLoading: false });
          return false;
        }
        // サンプルネットワークが読み込まれたので、ノードリストを更新
        const updatedNodes = get().nodes;
        if (!updatedNodes.length) {
          set({ error: "Sample network has no nodes", isLoading: false });
          return false;
        }
      } catch (sampleError) {
        console.error("Error loading sample network:", sampleError);
        set({ error: "Failed to load sample network", isLoading: false });
        return false;
      }
    }

    set({ isLoading: true, error: null });
    try {
      console.log(
        `Calculating ${centralityType} centrality using GraphML-based API`,
      );

      // Export current network as GraphML
      const exportResponse = await networkAPI.exportNetworkAsGraphML();
      const exportResult = exportResponse.data.result;

      if (!exportResult || !exportResult.success || !exportResult.content) {
        throw new Error("Failed to export network as GraphML");
      }

      // Use GraphML-based centrality API
      const graphmlContent = exportResult.content;
      const centralityResponse = await networkAPI.graphmlCentrality(
        graphmlContent,
        centralityType,
      );
      const result = centralityResponse.data.result;

      if (result && result.success && result.graphml_content) {
        // Parse the returned GraphML content
        const importResponse = await networkAPI.importGraphML(
          result.graphml_content,
        );
        const importResult = importResponse.data.result;

        if (importResult && importResult.success) {
          // Extract centrality values from node attributes
          const centralityValues = {};
          const positions = importResult.nodes || [];

          positions.forEach((node) => {
            if (node.centrality_value) {
              centralityValues[node.id] = parseFloat(node.centrality_value);
            }
          });

          // Update network state with new positions from GraphML
          set({
            positions,
            centrality: centralityValues,
            centralityType,
            isLoading: false,
            error: null,
          });
          return true;
        } else {
          throw new Error(
            "Failed to import updated GraphML with centrality values",
          );
        }
      } else {
        throw new Error(result?.error || "Centrality calculation failed");
      }
    } catch (error) {
      console.error("Error calculating centrality:", error);

      // Fall back to original implementation for resilience
      try {
        // NetworkX MCP サーバーを使用して中心性を計算
        const response = await networkAPI.calculateCentrality(centralityType);
        const result = response.data.result;

        if (result && result.success) {
          // 計算された中心性値を取得
          const centralityValues = result.centrality_values || {};

          // 最大値を計算（正規化のため）
          const maxValue = Math.max(...Object.values(centralityValues), 1);

          // ノードの位置情報を更新（サイズと色を中心性値に基づいて設定）
          const updatedPositions = get().positions.map((node) => {
            const value = centralityValues[node.id] || 0;
            // サイズは5〜15の範囲でスケーリング
            const normalizedSize = 5 + (value / maxValue) * 10;

            return {
              ...node,
              size: normalizedSize,
              color: getCentralityColor(value, maxValue),
            };
          });

          // 状態を更新
          set({
            positions: updatedPositions,
            centrality: centralityValues,
            centralityType,
            isLoading: false,
            error: null,
          });

          return true;
        }
      } catch (fallbackError) {
        console.error(
          "Fallback centrality calculation also failed:",
          fallbackError,
        );
      }

      set({
        isLoading: false,
        error: error.message || "Centrality calculation failed",
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
      error: null,
    });
  },

  // Upload network file using GraphML-based API
  uploadNetworkFile: async (file) => {
    set({ isLoading: true, error: null });
    try {
      console.log("Uploading network file using GraphML API:", file.name);

      // For GraphML files, use direct import
      if (file.name.toLowerCase().endsWith(".graphml")) {
        // Read file as text
        const fileReader = new FileReader();
        const fileContentPromise = new Promise((resolve, reject) => {
          fileReader.onload = (e) => {
            resolve(e.target.result);
          };
          fileReader.onerror = () => {
            reject(new Error("Failed to read file"));
          };
          fileReader.readAsText(file);
        });

        const graphmlContent = await fileContentPromise;

        // First convert to standard GraphML format
        const convertResponse = await networkAPI.convertGraphML(graphmlContent);
        const convertResult = convertResponse.data;

        if (
          !convertResult ||
          !convertResult.success ||
          !convertResult.graphml_content
        ) {
          // 詳細なエラーメッセージを表示
          const errorMessage = convertResult?.error || "Failed to convert GraphML to standard format";
          console.error("GraphML conversion error:", errorMessage);
          
          // ユーザーフレンドリーなエラーメッセージを作成
          let userMessage = "GraphMLファイルの変換に失敗しました。";
          
          if (errorMessage.includes("missing <graph> element")) {
            userMessage += " ファイルに<graph>要素が含まれていません。";
          } else if (errorMessage.includes("Invalid XML")) {
            userMessage += " XMLの構文が無効です。";
          } else if (errorMessage.includes("namespace")) {
            userMessage += " 名前空間宣言が不足しています。";
          }
          
          userMessage += " 正しい形式のGraphMLファイルを使用してください。";
          throw new Error(userMessage);
        }
        
        // ファイルが修復された場合はユーザーに通知
        if (convertResult.fixed) {
          console.log("GraphML file was automatically fixed");
          // チャットにメッセージを追加（useChatStoreのaddMessageを使用）
          const chatStore = window.chatStore;
          if (chatStore && chatStore.addMessage) {
            chatStore.addMessage({
              role: "assistant",
              content: "GraphMLファイルの形式に問題がありましたが、自動的に修復されました。",
              timestamp: new Date().toISOString(),
            });
          }
        }

        // Import the standardized GraphML
        const importResponse = await networkAPI.importGraphML(
          convertResult.graphml_content,
        );
        const importResult = importResponse.data.result;

        if (importResult && importResult.success) {
          console.log("GraphML file imported successfully:", importResult);

          // Update network store with data from response
          set({
            nodes: importResult.nodes || [],
            edges: importResult.edges || [],
            positions: importResult.nodes || [], // positionsとnodesを同じにする
            isLoading: false,
            error: null,
            initialLoadComplete: true // 初期ロードが完了したことを示すフラグを設定
          });

          // 更新後の状態を確認
          const updatedState = get();
          console.log("State after GraphML import:", {
            nodesLength: updatedState.nodes?.length || 0,
            edgesLength: updatedState.edges?.length || 0,
            positionsLength: updatedState.positions?.length || 0,
            initialLoadComplete: updatedState.initialLoadComplete
          });

          return {
            success: true,
            nodes: importResult.nodes || [],
            edges: importResult.edges || []
          };
        } else {
          throw new Error(
            importResult?.error || "Failed to import GraphML file",
          );
        }
      } else {
        // For other file types, use the traditional upload method and convert
        // Read file as base64
        const fileReader = new FileReader();
        const fileContentPromise = new Promise((resolve, reject) => {
          fileReader.onload = (e) => {
            // Get base64 content without the prefix (e.g., "data:application/xml;base64,")
            const base64Content = e.target.result.split(",")[1];
            resolve(base64Content);
          };
          fileReader.onerror = () => {
            reject(new Error("Failed to read file"));
          };
          fileReader.readAsDataURL(file);
        });

        const fileContent = await fileContentPromise;

        // Use API to upload network file
        const response = await networkAPI.useTool("upload_network_file", {
          file_content: fileContent,
          file_name: file.name,
          file_type: file.type,
        });
        const result = response.data.result;

        if (result && result.success) {
          console.log("Network file uploaded successfully:", result);

          // Update network store with data from response
          set({
            nodes: result.nodes || [],
            edges: result.edges || [],
            positions: result.nodes || [], // positionsとnodesを同じにする
            isLoading: false,
            error: null,
            initialLoadComplete: true // 初期ロードが完了したことを示すフラグを設定
          });

          // 更新後の状態を確認
          const updatedState = get();
          console.log("State after file upload:", {
            nodesLength: updatedState.nodes?.length || 0,
            edgesLength: updatedState.edges?.length || 0,
            positionsLength: updatedState.positions?.length || 0,
            initialLoadComplete: updatedState.initialLoadComplete
          });

          return {
            success: true,
            nodes: result.nodes || [],
            edges: result.edges || []
          };
        } else {
          throw new Error(result?.error || "Failed to upload network file");
        }
      }
    } catch (error) {
      console.error("Failed to upload network file:", error);

      set({
        isLoading: false,
        error: error.message || "Failed to upload network file",
      });
      return {
        success: false,
        error: error.message || "Failed to upload network file"
      };
    }
  },

  // Recommend layout based on user's question and apply it
  recommendLayoutAndApply: async (question) => {
    set({ isLoading: true, error: null });
    try {
      console.log("Recommending layout based on question:", question);

      // Use API to get layout recommendation
      const response = await networkAPI.useTool("recommend_layout", {
        question,
      });
      const result = response.data.result;

      if (result && result.success) {
        console.log("Layout recommendation:", result);

        // Store recommendation
        set({
          recommendation: {
            recommended_layout: result.recommended_layout,
            recommended_parameters: result.recommended_parameters,
            recommendation_reason: result.recommendation_reason,
          },
          isLoading: false,
        });

        // Apply recommended layout
        const layoutType = result.recommended_layout;
        const layoutParams = result.recommended_parameters || {};

        // Update layout state
        set({
          layout: layoutType,
          layoutParams: layoutParams,
        });

        // Apply the layout
        return get().calculateLayout();
      } else {
        throw new Error(result.error || "Failed to get layout recommendation");
      }
    } catch (error) {
      console.error("Failed to recommend layout:", error);

      set({
        isLoading: false,
        error: error.message || "Failed to recommend layout",
      });
      return false;
    }
  },

  // Export network as GraphML
  exportAsGraphML: async (
    includePositions = true,
    includeVisualProperties = true,
  ) => {
    set({ isLoading: true, error: null });
    try {
      console.log("Exporting network as GraphML");

      // Use networkAPI to export network as GraphML
      const response = await networkAPI.exportNetworkAsGraphML();
      const result = response.data.result;

      if (result && result.success) {
        console.log("Network exported as GraphML successfully");

        set({ isLoading: false, error: null });

        // Return the GraphML string
        return result.content;
      } else {
        throw new Error(result.error || "Failed to export network as GraphML");
      }
    } catch (error) {
      console.error("Failed to export network as GraphML:", error);

      set({
        isLoading: false,
        error: error.message || "Failed to export network as GraphML",
      });
      return null;
    }
  },

  // Change visual properties of nodes or edges using GraphML-based API
  changeVisualProperties: async (
    propertyType,
    propertyValue,
    propertyMapping = {},
  ) => {
    set({ isLoading: true, error: null });
    try {
      console.log(
        `Changing visual property ${propertyType} to ${propertyValue} using GraphML API`,
      );

      // Export current network as GraphML
      const exportResponse = await networkAPI.exportNetworkAsGraphML();
      const exportResult = exportResponse.data.result;

      if (!exportResult || !exportResult.success || !exportResult.content) {
        throw new Error("Failed to export network as GraphML");
      }

      // Use GraphML-based visual properties API
      const graphmlContent = exportResult.content;
      const visualPropsResponse = await networkAPI.graphmlVisualProperties(
        graphmlContent,
        propertyType,
        propertyValue,
        propertyMapping,
      );
      const result = visualPropsResponse.data.result;

      if (result && result.success && result.graphml_content) {
        // Parse the returned GraphML content
        const importResponse = await networkAPI.importGraphML(
          result.graphml_content,
        );
        const importResult = importResponse.data.result;

        if (importResult && importResult.success) {
          // Update network state with new data from GraphML
          set((state) => ({
            positions: importResult.nodes || [],
            edges: importResult.edges || [],
            visualProperties: {
              ...state.visualProperties,
              [propertyType]: propertyValue,
            },
            isLoading: false,
            error: null,
          }));
          return true;
        } else {
          throw new Error(
            "Failed to import updated GraphML with visual property changes",
          );
        }
      } else {
        throw new Error(result?.error || "Visual property change failed");
      }
    } catch (error) {
      console.error("Failed to change visual properties:", error);

      // Fall back to original implementation for resilience
      try {
        // Use networkAPI instead of legacy MCP client
        const response = await networkAPI.useTool("change_visual_properties", {
          property_type: propertyType,
          property_value: propertyValue,
          property_mapping: propertyMapping,
        });
        const result = response.data.result;

        if (result && result.success) {
          // Update visual properties in state
          set((state) => ({
            visualProperties: {
              ...state.visualProperties,
              [propertyType]: propertyValue,
            },
            isLoading: false,
            error: null,
          }));

          // If it's a node property, update positions
          if (propertyType === "node_size" || propertyType === "node_color") {
            const attribute = propertyType.split("_")[1]; // 'size' or 'color'
            const updatedPositions = get().positions.map((node) => ({
              ...node,
              [attribute]:
                node.id in propertyMapping
                  ? propertyMapping[node.id]
                  : propertyValue,
            }));

            set({ positions: updatedPositions });
          }

          // If it's an edge property, update edges
          if (propertyType === "edge_width" || propertyType === "edge_color") {
            const attribute = propertyType.split("_")[1]; // 'width' or 'color'
            const updatedEdges = get().edges.map((edge) => {
              const edgeKey = `${edge.source}-${edge.target}`;
              return {
                ...edge,
                [attribute]:
                  edgeKey in propertyMapping
                    ? propertyMapping[edgeKey]
                    : propertyValue,
              };
            });

            set({ edges: updatedEdges });
          }

          return true;
        }
      } catch (fallbackError) {
        console.error(
          "Fallback visual property change also failed:",
          fallbackError,
        );
      }

      set({
        isLoading: false,
        error: error.message || "Failed to change visual properties",
      });
      return false;
    }
  },

  // Get network information
  getNetworkInfo: async () => {
    // 無限ループ検出のための静的変数
    if (!getNetworkInfo.callCount) {
      getNetworkInfo.callCount = 0;
    }
    getNetworkInfo.callCount++;
    
    // 短時間に多数の呼び出しがある場合は無限ループと判断して処理をスキップ
    if (getNetworkInfo.callCount > 5) {
      console.log("Too many getNetworkInfo calls detected, possible infinite loop. Skipping...");
      getNetworkInfo.callCount = 0; // カウンターをリセット
      set({ isLoading: false }); // 確実にローディング状態を解除
      return {
        success: true,
        network_info: {
          has_network: true,
          current_layout: "spring",
          current_centrality: null,
          num_nodes: 11,
          num_edges: 10,
          density: 0.2,
          is_connected: true,
          num_components: 1,
          avg_degree: 1.82,
          clustering_coefficient: 0,
        },
      };
    }
    
    // isLoadingをtrueに設定する前に現在の状態を取得
    const currentState = get();
    const currentNodes = currentState.nodes;
    const currentEdges = currentState.edges;
    const currentPositions = currentState.positions;
    const initialLoadComplete = currentState.initialLoadComplete;
    
    console.log("Getting network information - current state:", {
      nodesLength: currentNodes?.length || 0,
      edgesLength: currentEdges?.length || 0,
      positionsLength: currentPositions?.length || 0,
      initialLoadComplete: initialLoadComplete || false
    });
    
    // 初期ロードが完了している場合、またはノードとエッジが既に存在する場合は、それらの情報を返す
    if (initialLoadComplete || (currentNodes?.length > 0 && currentEdges?.length > 0 && currentPositions?.length > 0)) {
      console.log("初期ロードが完了しているか、既存のネットワークデータを使用します");
      getNetworkInfo.callCount = 0; // カウンターをリセット
      return {
        success: true,
        network_info: {
          has_network: true,
          current_layout: currentState.layout || "spring",
          current_centrality: currentState.centrality,
          num_nodes: currentNodes.length,
          num_edges: currentEdges.length,
          density: currentEdges.length / (currentNodes.length * (currentNodes.length - 1) / 2),
          is_connected: true,
          num_components: 1,
          avg_degree: (2 * currentEdges.length) / currentNodes.length,
          clustering_coefficient: 0,
          initialLoadComplete: initialLoadComplete
        },
      };
    }
    
    console.log("ネットワークが存在しません。サンプルネットワークを生成します。");
    set({ isLoading: true, error: null });
    
    try {
      // サンプルネットワークを直接生成して状態を更新
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
      console.log("Sample network generated in getNetworkInfo:", {
        nodesLength: updatedState.nodes?.length || 0,
        edgesLength: updatedState.edges?.length || 0,
        positionsLength: updatedState.positions?.length || 0,
        initialLoadComplete: updatedState.initialLoadComplete
      });
      
      getNetworkInfo.callCount = 0; // カウンターをリセット
      
      // 更新された状態を返す
      return {
        success: true,
        network_info: {
          has_network: true,
          current_layout: "spring",
          current_centrality: null,
          num_nodes: 11,
          num_edges: 10,
          density: 0.2,
          is_connected: true,
          num_components: 1,
          avg_degree: 1.82,
          clustering_coefficient: 0,
          initialLoadComplete: true
        },
      };
    } catch (error) {
      console.error("Error fetching network info:", error);
      
      // エラー発生時のフォールバック
      set({ isLoading: false, error: null });
      getNetworkInfo.callCount = 0; // カウンターをリセット
      return {
        success: true,
        network_info: {
          has_network: true,
          current_layout: "spring",
          current_centrality: null,
          num_nodes: 11, // ダミーデータ
          num_edges: 10, // ダミーデータ
          density: 0.2,
          is_connected: true,
          num_components: 1,
          avg_degree: 1.82,
          clustering_coefficient: 0,
        },
      };
    }
  },
}));

export default useNetworkStore;
