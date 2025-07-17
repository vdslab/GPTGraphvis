import { useState, useEffect, useRef } from 'react';
import ForceGraph2D from 'react-force-graph-2d';
import useNetworkStore from '../services/networkStore';
import useChatStore from '../services/chatStore';
import ReactMarkdown from 'react-markdown';
import mcpClient from '../services/mcpClient';
import FileUploadButton from '../components/FileUploadButton';
// API_URL import removed as part of migration to MCP-based design
// import { useNavigate } from 'react-router-dom';

const NetworkChatPage = () => {
  const { 
    edges, 
    positions, 
    layout, 
    layoutParams, 
    isLoading, 
    error,
    recommendation,
    loadSampleNetwork,
    calculateLayout,
    setLayout,
    setLayoutParams,
    applyCentrality,
    uploadNetworkFile,
    recommendLayoutAndApply,
    exportAsGraphML
  } = useNetworkStore();
  
  const {
    messages,
    sendMessage,
    isProcessing
  } = useChatStore();
  
  const [inputMessage, setInputMessage] = useState('');
  const [graphData, setGraphData] = useState({ nodes: [], links: [] });
  const [fileUploadError, setFileUploadError] = useState(null);
  const [isDragging, setIsDragging] = useState(false);
  const [isComposing, setIsComposing] = useState(false);
  const [savedNetworks, setSavedNetworks] = useState([]);
  const [networkName, setNetworkName] = useState('');
  const [showSaveDialog, setShowSaveDialog] = useState(false);
  const [showLoadDialog, setShowLoadDialog] = useState(false);
  // Removed unused layout-related state variables as part of migration to MCP-based design
  const graphRef = useRef();
  const messagesEndRef = useRef();
  const fileInputRef = useRef(null);
  // const navigate = useNavigate();
  
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
        useChatStore.getState().addMessage({
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
          setSavedNetworks(result.networks || []);
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
  
  // Handle message submission
  const handleSubmit = async (e) => {
    e.preventDefault();
    
    // Debug current messages
    console.log("DEBUG BEFORE SUBMIT - Current messages:", useChatStore.getState().debugMessages());
    
    // Prevent double submission
    if (!inputMessage.trim() || isProcessing) {
      console.log("Preventing submission: empty message or already processing");
      return;
    }
    
    // Clear input field immediately for better UX
    const messageToSend = inputMessage;
    setInputMessage('');
    
    console.log("Submitting message:", messageToSend);
    
    try {
      // First, add the user message to the chat store
      // This prevents the message from being added twice
      useChatStore.getState().addMessage({
        role: 'user',
        content: messageToSend,
        timestamp: new Date().toISOString()
      });
      
      // Check if the message is asking about uploading a file
      const uploadFileKeywords = ['upload', 'file', 'import', 'network file', 'アップロード', 'ファイル', 'インポート', 'ネットワークファイル'];
      const isAskingAboutUpload = uploadFileKeywords.some(keyword => messageToSend.toLowerCase().includes(keyword));
      
      if (isAskingAboutUpload) {
        // Add assistant response about file upload
        useChatStore.getState().addMessage({
          role: 'assistant',
          content: `You can upload a network file by clicking the "Upload Network File" button at the top of the network visualization panel. Supported formats include GraphML, GEXF, GML, JSON, Pajek, EdgeList, and AdjList. You can also drag and drop a file directly onto the visualization area.`,
          timestamp: new Date().toISOString()
        });
      } else if (messageToSend.toLowerCase().includes('recommend') && messageToSend.toLowerCase().includes('layout')) {
        // Handle layout recommendation
        try {
          const result = await recommendLayoutAndApply(messageToSend);
          
          if (result) {
            useChatStore.getState().addMessage({
              role: 'assistant',
              content: `Based on your request, I recommend using the ${recommendation.recommended_layout} layout. ${recommendation.recommendation_reason} I've applied this layout to the network.`,
              timestamp: new Date().toISOString(),
              networkUpdate: {
                type: 'layout',
                layout: recommendation.recommended_layout,
                layoutParams: recommendation.recommended_parameters || {}
              }
            });
          } else {
            useChatStore.getState().addMessage({
              role: 'assistant',
              content: "I couldn't recommend a layout based on your request. Please try again with more specific details about what you want to visualize.",
              timestamp: new Date().toISOString(),
              error: true
            });
          }
        } catch (error) {
          console.error("Error recommending layout:", error);
          
          useChatStore.getState().addMessage({
            role: 'assistant',
            content: "I'm sorry, I encountered an error trying to recommend a layout. Please try again later.",
            timestamp: new Date().toISOString(),
            error: true
          });
        }
      } else {
        // For other messages, generate a response
        // Note: We're not using sendMessage here to avoid adding the user message twice
        try {
          // Simulate a response since we're not using an API
          await new Promise(resolve => setTimeout(resolve, 1000));
          
          // Create a simple response based on the message content
          let responseContent = "I'm sorry, I don't understand that request. You can ask me about network visualization or uploading network files.";
          
          // Simple keyword-based responses
          if (messageToSend.toLowerCase().includes('layout') || messageToSend.toLowerCase().includes('visualize')) {
            responseContent = "You can change the network layout using the dropdown menu at the top of the visualization panel. Available layouts include Spring, Circular, Random, Spectral, and others.";
          } else if (messageToSend.toLowerCase().includes('centrality') || messageToSend.toLowerCase().includes('measure')) {
            responseContent = "You can apply centrality measures to the network using the 'Apply Centrality' dropdown. Available measures include Degree, Closeness, Betweenness, Eigenvector, and PageRank.";
          }
          
          // Add assistant response
          useChatStore.getState().addMessage({
            role: 'assistant',
            content: responseContent,
            timestamp: new Date().toISOString()
          });
        } catch (error) {
          console.error("Error generating response:", error);
          
          useChatStore.getState().addMessage({
            role: 'assistant',
            content: "Sorry, I encountered an error processing your request. Please try again later.",
            timestamp: new Date().toISOString(),
            error: true
          });
        }
      }
    } catch (error) {
      console.error("Error sending message:", error);
      
      useChatStore.getState().addMessage({
        role: 'assistant',
        content: "Sorry, I encountered an error processing your request. Please try again later.",
        timestamp: new Date().toISOString(),
        error: true
      });
    } finally {
      // Clear typing indicator
      useChatStore.getState().setTypingIndicator(false);
    }
  };
  
  return (
    <div className="h-screen flex flex-col">
      {/* Super prominent upload button fixed at the top of the screen */}
      <div className="fixed top-20 left-1/2 transform -translate-x-1/2 z-[9999] shadow-2xl">
        <FileUploadButton 
          className="bg-red-600 hover:bg-red-700 text-white font-bold py-6 px-10 rounded-lg shadow-xl transform hover:scale-105 transition-transform duration-200 flex items-center border-4 border-yellow-300 animate-pulse" 
          buttonText="UPLOAD NETWORK FILE" 
          onFileUpload={handleFileUpload}
        />
      </div>
      
      <div className="flex-1 flex overflow-hidden">
        {/* Left side - Chat panel */}
        <div className="w-1/3 flex flex-col bg-white border-r border-gray-200">
          <div className="p-4 border-b border-gray-200">
            <h2 className="text-lg font-semibold text-gray-800">Network Chat</h2>
            <p className="text-sm text-gray-600">
              Chat with the assistant to visualize and analyze networks
            </p>
          </div>
          
          {/* Messages area */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            {/* Debug message count */}
            <div className="text-xs text-gray-500 mb-2">
              Messages: {messages.length}
            </div>
            
            {/* Emergency file upload button in chat panel */}
            <div className="sticky top-0 mb-4 p-3 bg-red-100 border-4 border-red-500 rounded-lg animate-pulse z-[9999]">
              <div className="font-bold text-red-700 mb-2 text-center text-lg">UPLOAD NETWORK FILE</div>
              <FileUploadButton 
                className="w-full bg-red-600 hover:bg-red-700 text-white font-bold py-4 px-6 rounded-lg shadow-xl transform hover:scale-105 transition-transform duration-200 flex items-center justify-center" 
                buttonText="SELECT FILE" 
                onFileUpload={handleFileUpload}
              />
            </div>
            
            {/* Debug information */}
            <div className="mb-4 p-3 bg-yellow-100 border-2 border-yellow-500 rounded-lg">
              <div className="font-bold text-yellow-700 mb-2">Debug Information</div>
              <div className="text-sm">
                <p>Messages count: {messages.length}</p>
                <p>Messages array: {JSON.stringify(messages)}</p>
                <p>Is processing: {isProcessing ? 'Yes' : 'No'}</p>
              </div>
            </div>
            
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
            <form onSubmit={handleSubmit} className="flex">
              <input
                type="text"
                value={inputMessage}
                onChange={(e) => setInputMessage(e.target.value)}
                onCompositionStart={() => setIsComposing(true)}
                onCompositionEnd={() => setIsComposing(false)}
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
        <div className="flex-1 flex flex-col bg-white">
          <div className="p-4 border-b border-gray-200 flex justify-between items-center">
            <div>
              <h2 className="text-lg font-semibold text-gray-800">Network Visualization</h2>
              <p className="text-sm text-gray-600">
                Current Layout: {layout}
              </p>
            </div>
            
            {/* Control buttons */}
            <div className="flex space-x-2">
              {/* File upload button - Make it extremely prominent with fixed position */}
              <div className="mr-4 relative z-10">
                <FileUploadButton 
                  className="bg-blue-600 hover:bg-blue-700 text-white font-bold py-3 px-6 rounded-lg shadow-lg transform hover:scale-105 transition-transform duration-200 flex items-center border-2 border-blue-300 animate-pulse" 
                  buttonText="Upload Network File" 
                  onFileUpload={handleFileUpload}
                />
              </div>
              
              {/* Fixed position upload button for better visibility */}
              <div className="fixed top-20 right-4 z-[9999] shadow-2xl">
                <FileUploadButton 
                  className="bg-red-600 hover:bg-red-700 text-white font-bold py-6 px-10 rounded-lg shadow-xl transform hover:scale-105 transition-transform duration-200 flex items-center border-4 border-yellow-300 animate-pulse" 
                  buttonText="Upload Network" 
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
                className="px-4 py-2 bg-white border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
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
                className="px-4 py-2 bg-white border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
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
