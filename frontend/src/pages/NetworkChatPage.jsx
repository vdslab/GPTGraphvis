import { useState, useEffect, useRef } from "react";
import ForceGraph2D from "react-force-graph-2d";
import useNetworkStore from "../services/networkStore";
import useChatStore from "../services/chatStore";
import ReactMarkdown from "react-markdown";
import mcpClient from "../services/mcpClient";
import FileUploadButton from "../components/FileUploadButton";

const NetworkChatPage = () => {
  const {
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
  });

  // ネットワーク情報を取得
  useEffect(() => {
    const fetchNetworkInfo = async () => {
      try {
        const info = await getNetworkInfo();
        if (info && info.success) {
          // ネットワークがあるかどうかチェック
          if (info.network_info.has_network) {
            // 通常の処理：中心性情報を更新
            setNetworkState((prevState) => ({
              ...prevState,
              centrality: info.network_info.current_centrality,
            }));
          } else {
            // ネットワークがない場合：サンプルネットワークを生成
            console.log("ネットワークが存在しません。サンプルネットワークを生成します。");
            const result = await mcpClient.getSampleNetwork();
            if (result && result.success) {
              // サンプルネットワークの状態を設定
              useNetworkStore.setState({
                positions: result.nodes.map((node) => ({
                  id: node.id,
                  label: node.label || node.id,
                  x: node.x || 0,
                  y: node.y || 0,
                  size: node.size || 5,
                  color: node.color || "#1d4ed8",
                })),
                edges: result.edges.map((edge) => ({
                  source: edge.source,
                  target: edge.target,
                  width: edge.width || 1,
                  color: edge.color || "#94a3b8",
                })),
                layout: result.layout || "spring",
                layoutParams: result.layout_params || {},
                error: null, // エラーをクリア
              });
            }
          }
        } else if (info && info.error) {
          // API からのエラーレスポンス
          console.error("Network info API error:", info.error);
        }
      } catch (error) {
        console.error("Error fetching network info:", error);
        // エラー発生時もサンプルネットワークを試みる
        try {
          console.log("エラーが発生したため、サンプルネットワークを生成します。");
          const result = await mcpClient.getSampleNetwork();
          if (result && result.success) {
            useNetworkStore.setState({
              positions: result.nodes.map((node) => ({
                id: node.id,
                label: node.label || node.id,
                x: node.x || 0,
                y: node.y || 0,
                size: node.size || 5,
                color: node.color || "#1d4ed8",
              })),
              edges: result.edges.map((edge) => ({
                source: edge.source,
                target: edge.target,
                width: edge.width || 1,
                color: edge.color || "#94a3b8",
              })),
              layout: result.layout || "spring",
              layoutParams: result.layout_params || {},
              error: null, // エラーをクリア
            });
          }
        } catch (fallbackError) {
          console.error("Failed to generate sample network:", fallbackError);
        }
      }
    };

    fetchNetworkInfo();
  }, [getNetworkInfo]);

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
      const errorMessage = error.response?.data?.detail || 
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

        const result = await mcpClient.listUserNetworks(userId);
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

  // Load sample network on component mount
  useEffect(() => {
    const loadNetwork = async () => {
      try {
        console.log("Attempting to load sample network");
        // Check if we have a token
        const token = localStorage.getItem("token");
        if (!token) {
          console.error("No token found, cannot load sample network");
          return;
        }
        console.log("Token found:", token.substring(0, 10) + "...");

        // Try to load sample network directly from NetworkX server
        try {
          console.log(
            "Attempting to load sample network directly from NetworkX server",
          );
          const result =
            await mcpClient.callNetworkXDirect("get_sample_network");
          console.log("Sample network from direct call:", result);

          if (
            result &&
            result.success &&
            result.nodes &&
            result.nodes.length > 0
          ) {
            console.log("Using sample network from direct call");
            // Update network store with data from direct call
            useNetworkStore.setState({
              positions: result.nodes.map((node) => ({
                id: node.id,
                label: node.label || node.id,
                x: node.x || 0,
                y: node.y || 0,
                size: node.size || 5,
                color: node.color || "#1d4ed8",
              })),
              edges: result.edges.map((edge) => ({
                source: edge.source,
                target: edge.target,
                width: edge.width || 1,
                color: edge.color || "#94a3b8",
              })),
              layout: result.layout || "spring",
              layoutParams: result.layout_params || {},
            });
            return;
          }
        } catch (directError) {
          console.error("Error loading sample network directly:", directError);
          console.log("Trying MCP method next");

          // Try to load sample network from MCP
          try {
            console.log("Attempting to load sample network from MCP");
            const result = await mcpClient.getSampleNetwork();
            console.log("Sample network from MCP:", result);

            if (
              result &&
              result.success &&
              result.nodes &&
              result.nodes.length > 0
            ) {
              console.log("Using sample network from MCP");
              // Update network store with data from MCP
              useNetworkStore.setState({
                positions: result.nodes.map((node) => ({
                  id: node.id,
                  label: node.label || node.id,
                  x: node.x || 0,
                  y: node.y || 0,
                  size: node.size || 5,
                  color: node.color || "#1d4ed8",
                })),
                edges: result.edges.map((edge) => ({
                  source: edge.source,
                  target: edge.target,
                  width: edge.width || 1,
                  color: edge.color || "#94a3b8",
                })),
                layout: result.layout || "spring",
                layoutParams: result.layout_params || {},
              });
              return;
            }
          } catch (mcpError) {
            console.error("Error loading sample network from MCP:", mcpError);
            console.log("Falling back to traditional network loading");
          }
        }

        // Fall back to traditional network loading
        const result = await loadSampleNetwork();
        if (result) {
          console.log("Sample network loaded successfully");
        } else {
          console.error("Failed to load sample network");
        }
      } catch (error) {
        console.error("Error loading sample network:", error);
        if (error.response) {
          console.error("Response status:", error.response.status);
          console.error("Response data:", error.response.data);
        }
      }
    };

    loadNetwork();
  }, [loadSampleNetwork]);

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
            calculateLayout();
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
          content: `ネットワークファイルは、ネットワーク可視化パネル上部の「ネットワークファイルをアップロード」ボタンをクリックしてアップロードできます。サポートされている形式には、GraphML、GEXF、GML、JSON、Pajek、EdgeList、およびAdjListが含まれます。または、ファイルを可視化エリアに直接ドラッグアンドドロップすることもできます。`,
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
          <div className="p-4 border-b border-gray-200">
            <h2 className="text-lg font-semibold text-gray-800">
              Network Chat
            </h2>
            <p className="text-sm text-gray-600">
              Chat with the assistant to visualize and analyze networks
            </p>
          </div>

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

          <div className="p-4 border-b border-gray-200 flex flex-wrap justify-between items-center gap-2">
            <div>
              <h2 className="text-lg font-semibold text-gray-800">
                ネットワーク可視化
              </h2>
              <p className="text-sm text-gray-600">
                現在のレイアウト: {layout} / 中心性:{" "}
                {network_state?.centrality || "なし"}
              </p>
            </div>

            {/* Control buttons */}
            <div className="flex flex-wrap gap-2 items-center">
              {/* Single file upload button with proper styling - hidden on mobile */}
              <div className="hidden md:block">
                <FileUploadButton
                  className="bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded-md shadow-md flex items-center space-x-2"
                  buttonText="ネットワークファイルをアップロード"
                  onFileUpload={handleFileUpload}
                />
              </div>

              {/* Layout dropdown */}
              <select
                value={layout}
                onChange={(e) => {
                  setLayout(e.target.value);
                  calculateLayout();
                }}
                className="px-3 py-2 bg-white border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
              >
                <option value="spring">Spring</option>
                <option value="circular">Circular</option>
                <option value="random">Random</option>
                <option value="spectral">Spectral</option>
                <option value="shell">Shell</option>
                <option value="kamada_kawai">Kamada-Kawai</option>
                <option value="fruchterman_reingold">
                  Fruchterman-Reingold
                </option>
              </select>

              {/* Centrality dropdown */}
              <select
                onChange={(e) => {
                  if (e.target.value) {
                    applyCentrality(e.target.value);
                  }
                }}
                className="px-3 py-2 bg-white border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
                defaultValue=""
              >
                <option value="" disabled>
                  中心性を適用
                </option>
                <option value="degree">次数中心性 (Degree)</option>
                <option value="closeness">近接中心性 (Closeness)</option>
                <option value="betweenness">媒介中心性 (Betweenness)</option>
                <option value="eigenvector">
                  固有ベクトル中心性 (Eigenvector)
                </option>
                <option value="pagerank">PageRank</option>
              </select>
            </div>
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
              nodeLabel="label"
              nodeRelSize={6}
              nodeVal={(node) => node.size}
              nodeColor={(node) => node.color}
              linkWidth={(link) => link.width}
              linkColor={(link) => link.color}
              cooldownTicks={100}
              onEngineStop={() => console.log("Layout stabilized")}
            />
          </div>
        </div>
      </div>
    </div>
  );
};

export default NetworkChatPage;
