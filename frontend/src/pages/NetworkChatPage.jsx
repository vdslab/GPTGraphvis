import { useState, useEffect, useRef } from 'react';
import ForceGraph2D from 'react-force-graph-2d';
import useNetworkStore from '../services/networkStore';
import useChatStore from '../services/chatStore';
import ReactMarkdown from 'react-markdown';
import mcpClient from '../services/mcpClient';
import FileUploadButton from '../components/FileUploadButton';

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
    changeVisualProperties
  } = useNetworkStore();
  
  const {
    messages,
    sendMessage,
    isProcessing,
    addMessage
  } = useChatStore();
  
  const [inputMessage, setInputMessage] = useState('');
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
    const fileExtension = file.name.split('.').pop().toLowerCase();
    const supportedFormats = ['graphml', 'gexf', 'gml', 'json', 'net', 'edgelist', 'adjlist'];
    
    if (!supportedFormats.includes(fileExtension)) {
      setFileUploadError(`Unsupported file format: .${fileExtension}. Supported formats: ${supportedFormats.join(', ')}`);
      return;
    }
    
    try {
      // Upload file
      const result = await uploadNetworkFile(file);
      if (result) {
        console.log("Network file uploaded and processed successfully");
        
        // Add a system message to the chat
        addMessage({
          role: 'assistant',
          content: `Network file "${file.name}" uploaded and processed successfully.`,
          timestamp: new Date().toISOString()
        });
      } else {
        console.error("Failed to process network file");
        setFileUploadError("Failed to process network file");
      }
    } catch (error) {
      console.error("Error uploading network file:", error);
      setFileUploadError(error.message || "Error uploading network file");
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
        const userId = localStorage.getItem('userId');
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
        const token = localStorage.getItem('token');
        if (!token) {
          console.error("No token found, cannot load sample network");
          return;
        }
        console.log("Token found:", token.substring(0, 10) + "...");
        
        // Try to load sample network from MCP
        try {
          console.log("Attempting to load sample network from MCP");
          const result = await mcpClient.getSampleNetwork();
          console.log("Sample network from MCP:", result);
          
          if (result && result.success && result.nodes && result.nodes.length > 0) {
            console.log("Using sample network from MCP");
            // Update network store with data from MCP
            useNetworkStore.setState({
              positions: result.nodes.map(node => ({
                id: node.id,
                label: node.label || node.id,
                x: node.x || 0,
                y: node.y || 0,
                size: node.size || 5,
                color: node.color || '#1d4ed8'
              })),
              edges: result.edges.map(edge => ({
                source: edge.source,
                target: edge.target,
                width: edge.width || 1,
                color: edge.color || '#94a3b8'
              })),
              layout: result.layout || 'spring',
              layoutParams: result.layout_params || {}
            });
            return;
          }
        } catch (mcpError) {
          console.error("Error loading sample network from MCP:", mcpError);
          console.log("Falling back to traditional network loading");
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
      const graphNodes = positions.map(node => ({
        id: node.id,
        x: node.x * 100, // Scale for better visualization
        y: node.y * 100,
        label: node.label || node.id,
        // Add any additional properties for visualization
        size: node.size || 5,
        color: node.color || '#1d4ed8'
      }));
      
      const graphLinks = edges.map(edge => ({
        source: edge.source,
        target: edge.target,
        // Add any additional properties for visualization
        width: edge.width || 1,
        color: edge.color || '#94a3b8'
      }));
      
      setGraphData({ nodes: graphNodes, links: graphLinks });
    }
  }, [positions, edges]);
  
  // Scroll to bottom of messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);
  
  // Process network updates from chat messages
  useEffect(() => {
    // Check if there are any messages
    if (messages.length === 0) return;
    
    // Get the most recent message
    const lastMessage = messages[messages.length - 1];
    
    // Check if it's an assistant message with a network update
    if (lastMessage.role === 'assistant' && lastMessage.networkUpdate) {
      console.log("Processing network update from message:", lastMessage.networkUpdate);
      
      const { type, ...updateData } = lastMessage.networkUpdate;
      
      // Handle different types of updates
      switch (type) {
        case 'layout':
          // Update layout
          if (updateData.layout) {
            setLayout(updateData.layout);
            if (updateData.layoutParams) {
              setLayoutParams(updateData.layoutParams);
            }
            calculateLayout();
          }
          break;
          
        case 'centrality':
          // Apply centrality
          if (updateData.centralityType) {
            applyCentrality(updateData.centralityType);
          }
          break;
          
        case 'visualProperty':
          // Change visual properties
          if (updateData.propertyType && updateData.propertyValue) {
            changeVisualProperties(
              updateData.propertyType, 
              updateData.propertyValue, 
              updateData.propertyMapping || {}
            );
          }
          break;
          
        default:
          console.log("Unknown network update type:", type);
      }
    }
  }, [messages, setLayout, setLayoutParams, calculateLayout, applyCentrality, changeVisualProperties]);
  
  // Handle message submission
  const handleSubmit = async (e) => {
    e.preventDefault();
    
    // Prevent double submission
    if (!inputMessage.trim() || isProcessing) {
      return;
    }
    
    // Clear input field immediately for better UX
    const messageToSend = inputMessage;
    setInputMessage('');
    
    try {
      // Check if the message is asking about uploading a file
      const uploadFileKeywords = ['upload', 'file', 'import', 'network file', 'アップロード', 'ファイル', 'インポート', 'ネットワークファイル'];
      const isAskingAboutUpload = uploadFileKeywords.some(keyword => messageToSend.toLowerCase().includes(keyword));
      
      if (isAskingAboutUpload) {
        // First, add the user message to the chat store
        addMessage({
          role: 'user',
          content: messageToSend,
          timestamp: new Date().toISOString()
        });
        
        // Add assistant response about file upload
        addMessage({
          role: 'assistant',
          content: `You can upload a network file by clicking the "Upload Network File" button at the top of the network visualization panel. Supported formats include GraphML, GEXF, GML, JSON, Pajek, EdgeList, and AdjList. You can also drag and drop a file directly onto the visualization area.`,
          timestamp: new Date().toISOString()
        });
      } else {
        // For all other messages, use the sendMessage function from chatStore
        await sendMessage(messageToSend);
      }
    } catch (error) {
      console.error("Error sending message:", error);
      
      // Only add error message if user message was already added
      if (messages.some(m => m.role === 'user' && m.content === messageToSend)) {
        addMessage({
          role: 'assistant',
          content: "Sorry, I encountered an error processing your request. Please try again later.",
          timestamp: new Date().toISOString(),
          error: true
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
            <h2 className="text-lg font-semibold text-gray-800">Network Chat</h2>
            <p className="text-sm text-gray-600">
              Chat with the assistant to visualize and analyze networks
            </p>
          </div>
          
          {/* Messages area */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            {messages.map((message, index) => (
              <div 
                key={index} 
                className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'} mb-4`}
              >
                {/* Avatar for assistant */}
                {message.role === 'assistant' && (
                  <div className="flex-shrink-0 h-8 w-8 rounded-full bg-blue-500 flex items-center justify-center mr-2">
                    <svg className="h-5 w-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.75 3.104v5.714a2.25 2.25 0 01-.659 1.591L5 14.5M9.75 3.104c-.251.023-.501.05-.75.082m.75-.082a24.301 24.301 0 014.5 0m0 0v5.714a2.25 2.25 0 001.5 2.25m0 0v2.8a2.25 2.25 0 01-1.5 2.25m0 0a2.25 2.25 0 01-1.5 0M5 14.5v2.8a2.25 2.25 0 002.25 2.25h9A2.25 2.25 0 0018.5 17.3v-2.8a2.25 2.25 0 00-2.25-2.25h-.75m-6 0h6" />
                    </svg>
                  </div>
                )}
                
                <div 
                  className={`max-w-3/4 p-3 rounded-lg ${
                    message.role === 'user' 
                      ? 'bg-blue-100 text-blue-900' 
                      : 'bg-gray-100 text-gray-900'
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
                  <svg className="h-5 w-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.75 3.104v5.714a2.25 2.25 0 01-.659 1.591L5 14.5M9.75 3.104c-.251.023-.501.05-.75.082m.75-.082a24.301 24.301 0 014.5 0m0 0v5.714a2.25 2.25 0 001.5 2.25m0 0v2.8a2.25 2.25 0 01-1.5 2.25m0 0a2.25 2.25 0 01-1.5 0M5 14.5v2.8a2.25 2.25 0 002.25 2.25h9A2.25 2.25 0 0018.5 17.3v-2.8a2.25 2.25 0 00-2.25-2.25h-.75m-6 0h6" />
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
            <form 
              onSubmit={handleSubmit} 
              className="flex"
            >
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
                <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
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
              <h2 className="text-lg font-semibold text-gray-800">Network Visualization</h2>
              <p className="text-sm text-gray-600">
                Current Layout: {layout}
              </p>
            </div>
            
            {/* Control buttons */}
            <div className="flex flex-wrap gap-2 items-center">
              {/* Single file upload button with proper styling - hidden on mobile */}
              <div className="hidden md:block">
                <FileUploadButton 
                  className="bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded-md shadow-md flex items-center space-x-2" 
                  buttonText="Upload Network File" 
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
                <option value="fruchterman_reingold">Fruchterman-Reingold</option>
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
                <option value="" disabled>Apply Centrality</option>
                <option value="degree">Degree</option>
                <option value="closeness">Closeness</option>
                <option value="betweenness">Betweenness</option>
                <option value="eigenvector">Eigenvector</option>
                <option value="pagerank">PageRank</option>
              </select>
            </div>
          </div>
          
          {/* Graph visualization */}
          <div 
            className={`flex-1 relative ${isDragging ? 'bg-blue-50' : ''}`}
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
                <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative" role="alert">
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
              onEngineStop={() => console.log('Layout stabilized')}
            />
          </div>
        </div>
      </div>
    </div>
  );
};

export default NetworkChatPage;
