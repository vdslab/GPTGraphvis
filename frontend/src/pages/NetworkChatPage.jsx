import { useState, useEffect, useRef } from "react";
import ForceGraph2D from "react-force-graph-2d";
import useNetworkStore from "../services/networkStore";
import useChatStore from "../services/chatStore";
import ReactMarkdown from "react-markdown";
import mcpClient from "../services/mcpClient";
import FileUploadButton from "../components/FileUploadButton";

const NetworkChatPage = () => {
  const {
    nodes,
    edges,
    positions,
    layout,
    isLoading,
    error,
    loadSampleNetwork,
    calculateLayout,
    setLayout,
    setLayoutParams,
    applyCentrality,
    uploadNetworkFile,
    changeVisualProperties,
    getNetworkInfo,
  } = useNetworkStore();

  // ネットワーク状態を保持
  const [network_state, setNetworkState] = useState({
    centrality: null,
    centralityDescription: null,
    isApplyingCentrality: false,
    currentCentralityName: "",
  });

  // ネットワーク情報を取得
  // ネットワーク情報を取得するuseEffectは削除し、初期化ロジックを一元化

  const { messages, sendMessage, isProcessing, addMessage } = useChatStore();

  const [inputMessage, setInputMessage] = useState("");
  const [graphData, setGraphData] = useState({ nodes: [], links: [] });
  const [fileUploadError, setFileUploadError] = useState(null);
  const [isDragging, setIsDragging] = useState(false);
  const graphRef = useRef();
  const messagesEndRef = useRef();

  // Handle file upload
  const handleFileUpload = async (file) => {
    setFileUploadError(null);

    // Check if file is provided
    if (!file) {
      setFileUploadError("No file selected");
      return;
    }

    // Check file extension
    const fileExtension = file.name.split(".").pop().toLowerCase();
    const supportedFormats = [
      "graphml",
      "gexf",
      "gml",
      "json",
      "net",
      "edgelist",
      "adjlist",
    ];

    if (!supportedFormats.includes(fileExtension)) {
      setFileUploadError(
        `Unsupported file format: .${fileExtension}. Supported formats: ${supportedFormats.join(", ")}`,
      );
      return;
    }

    try {
      // Upload file - より堅牢なエラーハンドリング
      console.log(`Attempting to upload network file: ${file.name}`);

      // ファイルが空でないことを確認
      if (file.size === 0) {
        setFileUploadError("File is empty");
        return;
      }

      // アップロード処理
      const result = await uploadNetworkFile(file);

      // 結果の検証を強化
      if (result && result.success === true) {
        console.log("Network file uploaded and processed successfully");

        // Add a system message to the chat
        addMessage({
          role: "assistant",
          content: `Network file "${file.name}" uploaded and processed successfully.`,
          timestamp: new Date().toISOString(),
        });
      } else if (result && result.error) {
        // エラーメッセージが結果オブジェクトに含まれている場合
        console.error("Failed to process network file:", result.error);
        setFileUploadError(result.error);
      } else {
        // 一般的なエラーの場合
        console.error("Failed to process network file: Unknown error");
        setFileUploadError("Failed to process network file");
      }
    } catch (error) {
      console.error("Error uploading network file:", error);
      // より詳細なエラーメッセージを提供
      const errorMessage =
        error.response?.data?.detail ||
        error.message ||
        "Error uploading network file";
      setFileUploadError(errorMessage);

      // チャットにエラーメッセージを追加
      addMessage({
        role: "assistant",
        content: `ファイルのアップロード中にエラーが発生しました: ${errorMessage}`,
        timestamp: new Date().toISOString(),
        error: true,
      });
    }
  };

  // Handle file drop
  const handleFileDrop = (e) => {
    e.preventDefault();
    setIsDragging(false);

    // Get the dropped file
    const file = e.dataTransfer.files[0];
    if (file) {
      handleFileUpload(file);
    }
  };

  // Handle drag events
  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  // Load user's saved networks
  useEffect(() => {
    const loadUserNetworks = async () => {
      try {
        const userId = localStorage.getItem("userId");
        if (!userId) {
          console.log("No user ID found, skipping network list loading");
          return;
        }

        // APIサーバーを経由してユーザーのネットワークリストを取得
        const result = await mcpClient.useTool("list_user_networks", { user_id: userId });
        if (result.success) {
          console.log("Loaded user networks:", result.networks);
        } else {
          console.error("Failed to load user networks:", result.error);
        }
      } catch (error) {
        console.error("Error loading user networks:", error);
      }
    };

    loadUserNetworks();
  }, []);

  // 初期ネットワーク読み込み - コンポーネントマウント時に一度だけ実行
  useEffect(() => {
    console.log("NetworkChatPage: Initial network load effect triggered");
    console.log("Current state:", {
      nodesLength: nodes?.length || 0,
      edgesLength: edges?.length || 0,
      positionsLength: positions?.length || 0,
      isLoading
    });
    
    // 既にネットワークデータが完全に読み込まれている場合はスキップ
    if (positions?.length > 0 && edges?.length > 0 && nodes?.length > 0) {
      console.log("NetworkChatPage: Complete network data already exists, skipping initial load");
      return;
    }

    // 直接サンプルネットワークを生成する関数
    const generateSampleNetwork = () => {
      console.log("NetworkChatPage: Generating sample network directly");
      
      // サンプルネットワークを直接生成
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
      setNetworkState((prevState) => ({
        ...prevState,
        centrality: null,
      }));
      
      return { sampleNodes, sampleEdges, samplePositions };
    };

    const loadInitialNetwork = async () => {
      try {
        console.log("NetworkChatPage: Loading initial network data");
        // トークンの確認
        const token = localStorage.getItem("token");
        if (!token) {
          console.error("NetworkChatPage: No token found, cannot load initial network");
          return;
        }

        try {
          // mcpClient.getSampleNetworkを使用してサンプルネットワークを読み込む
          console.log("NetworkChatPage: Loading sample network via MCP client");
          const result = await mcpClient.getSampleNetwork();
          
          if (result && result.success) {
            console.log("NetworkChatPage: Sample network loaded successfully via MCP client");
            
            // 状態を直接更新 - 重要: 他の関数が呼び出されないようにするため、完全な状態を一度に設定
            useNetworkStore.setState({
              nodes: result.nodes || [],
              edges: result.edges || [],
              positions: result.nodes || [], // positionsとnodesを同じにする
              layout: result.layout || "spring",
              isLoading: false,
              error: null,
              // 以下のフラグを追加して、他の関数が不必要に呼び出されないようにする
              initialLoadComplete: true
            });
            
            // 更新後の状態を確認 - 直接storeから取得して確実に最新の状態を確認
            const currentState = useNetworkStore.getState();
            console.log("NetworkChatPage: State after sample network loading:", {
              nodesLength: currentState.nodes?.length || 0,
              edgesLength: currentState.edges?.length || 0,
              positionsLength: currentState.positions?.length || 0,
              isLoading: currentState.isLoading,
              initialLoadComplete: currentState.initialLoadComplete
            });
            
            return;
          }
        } catch (mcpError) {
          console.error("NetworkChatPage: Error loading sample network via MCP client:", mcpError);
          console.log("NetworkChatPage: Falling back to direct sample network generation");
        }

        // MCPクライアントでの読み込みに失敗した場合、サンプルネットワークを直接生成
        console.log("NetworkChatPage: Generating sample network directly");
        const { sampleNodes, sampleEdges, samplePositions } = generateSampleNetwork();
        
        // 状態を直接更新 - 重要: 他の関数が呼び出されないようにするため、完全な状態を一度に設定
        useNetworkStore.setState({
          nodes: sampleNodes,
          edges: sampleEdges,
          positions: samplePositions,
          layout: "spring",
          isLoading: false,
          error: null,
          // 以下のフラグを追加して、他の関数が不必要に呼び出されないようにする
          initialLoadComplete: true
        });
        
        console.log("NetworkChatPage: Sample network generated successfully:", {
          nodesLength: sampleNodes.length,
          edgesLength: sampleEdges.length,
          positionsLength: samplePositions.length
        });
        
        // 更新後の状態を確認 - 直接storeから取得して確実に最新の状態を確認
        const currentState = useNetworkStore.getState();
        console.log("NetworkChatPage: State after sample network generation:", {
          nodesLength: currentState.nodes?.length || 0,
          edgesLength: currentState.edges?.length || 0,
          positionsLength: currentState.positions?.length || 0,
          isLoading: currentState.isLoading,
          initialLoadComplete: currentState.initialLoadComplete
        });
      } catch (error) {
        console.error("NetworkChatPage: Error loading initial network:", error);
        
        // エラーが発生した場合でも、サンプルネットワークを生成して表示
        try {
          console.log("NetworkChatPage: Attempting to generate fallback sample network after error");
          const { sampleNodes, sampleEdges, samplePositions } = generateSampleNetwork();
          
          useNetworkStore.setState({
            nodes: sampleNodes,
            edges: sampleEdges,
            positions: samplePositions,
            layout: "spring",
            isLoading: false,
            error: null,
            initialLoadComplete: true
          });
          
          console.log("NetworkChatPage: Fallback sample network generated successfully");
        } catch (fallbackError) {
          console.error("NetworkChatPage: Failed to generate fallback sample network:", fallbackError);
        }
      }
    };

    loadInitialNetwork();
  }, []); // 依存配列を空にして、コンポーネントマウント時に一度だけ実行されるようにする

  // Convert positions to graph data format for ForceGraph
  useEffect(() => {
    if (positions.length > 0) {
      const graphNodes = positions.map((node) => ({
        id: node.id,
        x: node.x * 100, // Scale for better visualization
        y: node.y * 100,
        label: node.label || node.id,
        // Add any additional properties for visualization
        size: node.size || 5,
        color: node.color || "#1d4ed8",
      }));

      const graphLinks = edges.map((edge) => ({
        source: edge.source,
        target: edge.target,
        // Add any additional properties for visualization
        width: edge.width || 1,
        color: edge.color || "#94a3b8",
      }));

      setGraphData({ nodes: graphNodes, links: graphLinks });
    }
  }, [positions, edges]);

  // Scroll to bottom of messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // Process network updates from chat messages
  useEffect(() => {
    // Check if there are any messages
    if (messages.length === 0) return;

    // Get the most recent message
    const lastMessage = messages[messages.length - 1];

    // Check if it's an assistant message with a network update
    if (lastMessage.role === "assistant" && lastMessage.networkUpdate) {
      console.log(
        "Processing network update from message:",
        lastMessage.networkUpdate,
      );

      const { type, ...updateData } = lastMessage.networkUpdate;

      // Handle different types of updates
      switch (type) {
        case "layout":
          // Update layout
          if (updateData.layout) {
            console.log(`Applying layout: ${updateData.layout}`);
            setLayout(updateData.layout);
            if (updateData.layoutParams) {
              setLayoutParams(updateData.layoutParams);
            }
            // APIリクエストを送信しないようにコメントアウト
            // calculateLayout();
            console.log("Layout update received, but calculateLayout() call skipped to prevent infinite loop");
          }
          break;

        case "centrality":
          // Apply centrality
          if (updateData.centralityType) {
            console.log(`Applying centrality: ${updateData.centralityType}`);
            applyCentrality(updateData.centralityType);
          }
          break;

        case "visualProperty":
          // Change visual properties
          if (updateData.propertyType && updateData.propertyValue) {
            console.log(
              `Changing visual property: ${updateData.propertyType} to ${updateData.propertyValue}`,
            );
            changeVisualProperties(
              updateData.propertyType,
              updateData.propertyValue,
              updateData.propertyMapping || {},
            );
          }
          break;

        default:
          console.log("Unknown network update type:", type);
      }
    }
  }, [
    messages,
    setLayout,
    setLayoutParams,
    calculateLayout,
    applyCentrality,
    changeVisualProperties,
  ]);

  // Handle message submission
  const handleSubmit = async (e) => {
    e.preventDefault();

    // Prevent double submission
    if (!inputMessage.trim() || isProcessing) {
      return;
    }

    // Clear input field immediately for better UX
    const messageToSend = inputMessage;
    setInputMessage("");

    try {
      // Check if the message is asking about uploading a file
      const uploadFileKeywords = [
        "upload",
        "file",
        "import",
        "network file",
        "アップロード",
        "ファイル",
        "インポート",
        "ネットワークファイル",
      ];
      const isAskingAboutUpload = uploadFileKeywords.some((keyword) =>
        messageToSend.toLowerCase().includes(keyword),
      );

      // 中心性に関する質問かどうかを確認
      const centralityKeywords = [
        "centrality",
        "中心性",
        "重要度",
        "重要なノード",
        "ノードの大きさ",
        "重要",
        "中心",
      ];
      const isAskingAboutCentrality = centralityKeywords.some((keyword) =>
        messageToSend.toLowerCase().includes(keyword),
      );

      if (isAskingAboutUpload) {
        // First, add the user message to the chat store
        addMessage({
          role: "user",
          content: messageToSend,
          timestamp: new Date().toISOString(),
        });

        // Add assistant response about file upload
        addMessage({
          role: "assistant",
          content: `ネットワークファイルは、ネットワーク可視化パネル右上の「Upload Network File」ボタンをクリックしてアップロードできます。サポートされている形式には、GraphML、GEXF、GML、JSON、Pajek、EdgeList、およびAdjListが含まれます。または、ファイルを可視化エリアに直接ドラッグアンドドロップすることもできます。`,
          timestamp: new Date().toISOString(),
        });
      } else {
        console.log("Sending message to chat API:", messageToSend);
        // For all other messages, use the sendMessage function from chatStore
        const response = await sendMessage(messageToSend);

        // 中心性に関する質問の場合、ユーザーにフィードバックを提供
        if (isAskingAboutCentrality && response && response.networkUpdate) {
          console.log("Centrality update received:", response.networkUpdate);
        }
      }
    } catch (error) {
      console.error("Error sending message:", error);

      // Only add error message if user message was already added
      if (
        messages.some((m) => m.role === "user" && m.content === messageToSend)
      ) {
        addMessage({
          role: "assistant",
          content:
            "申し訳ありませんが、リクエストの処理中にエラーが発生しました。後でもう一度お試しください。",
          timestamp: new Date().toISOString(),
          error: true,
        });
      }
    }
  };

  return (
    <div className="h-screen flex flex-col">
      <div className="flex-1 flex flex-col md:flex-row overflow-hidden">
        {/* Left side - Chat panel */}
        <div className="w-full md:w-2/5 lg:w-1/3 flex flex-col bg-white border-r border-gray-200">
          {/* Messages area */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            {messages.map((message, index) => (
              <div
                key={index}
                className={`flex ${message.role === "user" ? "justify-end" : "justify-start"} mb-4`}
              >
                {/* Avatar for assistant */}
                {message.role === "assistant" && (
                  <div className="flex-shrink-0 h-8 w-8 rounded-full bg-blue-500 flex items-center justify-center mr-2">
                    <svg
                      className="h-5 w-5 text-white"
                      fill="none"
                      viewBox="0 0 24 24"
                      stroke="currentColor"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M9.75 3.104v5.714a2.25 2.25 0 01-.659 1.591L5 14.5M9.75 3.104c-.251.023-.501.05-.75.082m.75-.082a24.301 24.301 0 014.5 0m0 0v5.714a2.25 2.25 0 001.5 2.25m0 0v2.8a2.25 2.25 0 01-1.5 2.25m0 0a2.25 2.25 0 01-1.5 0M5 14.5v2.8a2.25 2.25 0 002.25 2.25h9A2.25 2.25 0 0018.5 17.3v-2.8a2.25 2.25 0 00-2.25-2.25h-.75m-6 0h6"
                      />
                    </svg>
                  </div>
                )}

                <div
                  className={`max-w-3/4 p-3 rounded-lg ${
                    message.role === "user"
                      ? "bg-blue-100 text-blue-900"
                      : "bg-gray-100 text-gray-900"
                  }`}
                >
                  <div className="prose prose-sm max-w-none">
                    <ReactMarkdown>{message.content}</ReactMarkdown>
                  </div>

                  {/* Timestamp - would be added if messages had timestamps */}
                  {message.timestamp && (
                    <div className="text-xs text-gray-500 mt-1">
                      {new Date(message.timestamp).toLocaleTimeString()}
                    </div>
                  )}
                </div>
              </div>
            ))}
            <div ref={messagesEndRef} />

            {/* Typing indicator */}
            {isProcessing && (
              <div className="flex justify-start mb-4">
                <div className="flex-shrink-0 h-8 w-8 rounded-full bg-blue-500 flex items-center justify-center mr-2">
                  <svg
                    className="h-5 w-5 text-white"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M9.75 3.104v5.714a2.25 2.25 0 01-.659 1.591L5 14.5M9.75 3.104c-.251.023-.501.05-.75.082m.75-.082a24.301 24.301 0 014.5 0m0 0v5.714a2.25 2.25 0 001.5 2.25m0 0v2.8a2.25 2.25 0 01-1.5 2.25m0 0a2.25 2.25 0 01-1.5 0M5 14.5v2.8a2.25 2.25 0 002.25 2.25h9A2.25 2.25 0 0018.5 17.3v-2.8a2.25 2.25 0 00-2.25-2.25h-.75m-6 0h6"
                    />
                  </svg>
                </div>
                <div className="bg-gray-100 p-3 rounded-lg">
                  <div className="flex space-x-1">
                    <div className="w-2 h-2 bg-gray-500 rounded-full animate-bounce"></div>
                    <div className="w-2 h-2 bg-gray-500 rounded-full animate-bounce delay-100"></div>
                    <div className="w-2 h-2 bg-gray-500 rounded-full animate-bounce delay-200"></div>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Input area */}
          <div className="p-4 border-t border-gray-200">
            <form onSubmit={handleSubmit} className="flex">
              <input
                type="text"
                value={inputMessage}
                onChange={(e) => setInputMessage(e.target.value)}
                placeholder="Type your message..."
                className="flex-1 px-4 py-2 border border-gray-300 rounded-l-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                disabled={isProcessing}
              />
              <button
                type="submit"
                className="px-4 py-2 bg-blue-600 text-white rounded-r-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50"
                disabled={!inputMessage.trim() || isProcessing}
              >
                <svg
                  className="h-5 w-5"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8"
                  />
                </svg>
              </button>
            </form>
            {fileUploadError && (
              <div className="mt-2 text-red-500 text-sm">{fileUploadError}</div>
            )}
          </div>
        </div>

        {/* Right side - Network visualization panel */}
        <div className="w-full md:flex-1 flex flex-col bg-white">
          {/* Fixed position upload button for mobile */}
          <div className="md:hidden fixed bottom-4 right-4 z-10">
            <FileUploadButton
              className="bg-blue-600 hover:bg-blue-700 text-white font-bold py-3 px-3 rounded-full shadow-lg flex items-center justify-center"
              buttonText="Upload"
              onFileUpload={handleFileUpload}
              iconOnly={true}
            />
          </div>

          {/* Desktop upload button - always visible */}
          <div style={{ position: 'absolute', top: '1rem', right: '1rem', zIndex: 50 }}>
            <FileUploadButton
              className="bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded shadow-lg flex items-center justify-center"
              buttonText="Upload Network File"
              onFileUpload={handleFileUpload}
            />
          </div>

          {/* Graph visualization */}
          <div
            className={`flex-1 relative ${isDragging ? "bg-blue-50" : ""}`}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleFileDrop}
          >
            {/* Drag and drop instruction */}
            <div className="absolute top-2 left-1/2 transform -translate-x-1/2 bg-white bg-opacity-75 px-3 py-1 rounded-full text-sm text-gray-600 shadow-sm border border-gray-200 z-10">
              Drag & drop network file here
            </div>
            {isLoading && (
              <div className="absolute inset-0 flex items-center justify-center bg-white bg-opacity-75 z-10">
                <div className="flex flex-col items-center">
                  <div className="w-12 h-12 border-4 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
                  <p className="mt-2 text-blue-500">Loading...</p>
                </div>
              </div>
            )}

            {/* 中心性適用時のアニメーション表示 */}
            {network_state.isApplyingCentrality && (
              <div className="absolute inset-0 flex items-center justify-center bg-white bg-opacity-40 z-10">
                <div className="flex flex-col items-center">
                  <div className="w-16 h-16 border-4 border-blue-600 border-t-transparent rounded-full animate-spin"></div>
                  <p className="mt-2 text-blue-600 font-semibold">
                    {network_state.currentCentralityName}を適用中...
                  </p>
                  <p className="text-sm text-blue-500">
                    ノードの大きさが中心性値に応じて変化します
                  </p>
                </div>
              </div>
            )}

            {error && (
              <div className="absolute inset-0 flex items-center justify-center bg-white bg-opacity-75 z-10">
                <div
                  className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative"
                  role="alert"
                >
                  <strong className="font-bold">Error: </strong>
                  <span className="block sm:inline">{error}</span>
                </div>
              </div>
            )}

            {isDragging && (
              <div className="absolute inset-0 flex items-center justify-center bg-blue-50 bg-opacity-90 z-10 border-2 border-blue-500 border-dashed">
                <div className="text-blue-500 text-xl font-semibold">
                  Drop your network file here
                </div>
              </div>
            )}

            <ForceGraph2D
              ref={graphRef}
              graphData={graphData}
              nodeLabel={(node) => {
                // ノードの基本情報を表示
                let label = `${node.label || node.id}`;
                
                // 中心性値がある場合は表示
                if (network_state.centrality) {
                  label += `\n中心性値: ${node.size ? ((node.size - 5) / 10).toFixed(2) : "不明"}`;
                }
                
                // ノードの属性情報を表示
                for (const [key, value] of Object.entries(node)) {
                  // id, label, x, y, size, colorは基本情報なのでスキップ
                  if (!['id', 'label', 'x', 'y', 'size', 'color', '__indexColor', 'index', 'vx', 'vy', 'fx', 'fy'].includes(key)) {
                    label += `\n${key}: ${value}`;
                  }
                }
                
                return label;
              }}
              nodeRelSize={6}
              nodeVal={(node) => node.size}
              nodeColor={(node) => node.color}
              linkWidth={(link) => link.width}
              linkColor={(link) => link.color}
              cooldownTicks={100}
              onEngineStop={() => console.log("Layout stabilized")}
              // ノードクリック時の処理
              onNodeClick={(node) => {
                console.log("Node clicked:", node);
                
                // ノードの属性情報を収集
                let nodeInfo = `**ノード「${node.label || node.id}」の情報**\n\n`;
                
                // 中心性値がある場合は表示
                if (network_state.centrality) {
                  const centralityValue = ((node.size - 5) / 10).toFixed(3);
                  nodeInfo += `中心性値: ${centralityValue}\n\n`;
                  
                  // 重要度の判定
                  const importance = node.size > 12
                    ? "非常に重要"
                    : node.size > 9
                      ? "比較的重要"
                      : node.size > 7
                        ? "平均的な重要度"
                        : "あまり重要でない";
                  
                  nodeInfo += `このノードは${importance}位置にあります。\n\n`;
                }
                
                // その他の属性情報を表示
                nodeInfo += "**属性情報:**\n";
                for (const [key, value] of Object.entries(node)) {
                  // id, label, x, y, size, colorは基本情報なのでスキップ
                  if (!['id', 'label', 'x', 'y', 'size', 'color', '__indexColor', 'index', 'vx', 'vy', 'fx', 'fy'].includes(key)) {
                    nodeInfo += `- ${key}: ${value}\n`;
                  }
                }
                
                // 基本情報も表示
                nodeInfo += "\n**基本情報:**\n";
                nodeInfo += `- ID: ${node.id}\n`;
                nodeInfo += `- ラベル: ${node.label || node.id}\n`;
                nodeInfo += `- サイズ: ${node.size}\n`;
                nodeInfo += `- 色: ${node.color}\n`;
                nodeInfo += `- 位置: (${node.x.toFixed(2)}, ${node.y.toFixed(2)})\n`;
                
                addMessage({
                  role: "assistant",
                  content: nodeInfo,
                  timestamp: new Date().toISOString(),
                });
              }}
              // ホバー効果の追加
              nodeCanvasObject={(node, ctx) => {
                const size = node.size || 5;
                // サイズに応じたフォントサイズ（高い中心性値を持つノードのラベルを大きく表示）
                // const fontSize = (12 + (node.size - 5) * 0.5) / globalScale;
                // ノードの描画
                ctx.beginPath();
                ctx.arc(node.x, node.y, size, 0, 2 * Math.PI);
                ctx.fillStyle = node.color || "#1d4ed8";
                ctx.fill();

                // ノード周囲の発光効果（中心性が高いものほど強く光る）
                if (network_state.centrality && node.size > 7) {
                  const glowSize = size * 1.5;
                  const glowOpacity = (node.size - 5) / 10; // 中心性の正規化値（0〜1）

                  ctx.beginPath();
                  ctx.arc(node.x, node.y, glowSize, 0, 2 * Math.PI);
                  ctx.fillStyle = `rgba(66, 153, 225, ${glowOpacity * 0.4})`; // 青色の発光効果
                  ctx.fill();
                }
              }}
            />
          </div>
        </div>
      </div>
    </div>
  );
};

export default NetworkChatPage;
