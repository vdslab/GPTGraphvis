import { useState, useEffect, useRef } from 'react';
import ForceGraph2D from 'react-force-graph-2d';
import useNetworkStore from '../services/networkStore';
import useChatStore from '../services/chatStore';
import ReactMarkdown from 'react-markdown';
import mcpClient from '../services/mcpClient';
import { API_URL } from '../services/api';
// import { useNavigate } from 'react-router-dom';

const NetworkChatPage = () => {
  const { 
    edges, 
    positions, 
    layout, 
    layoutParams, 
    isLoading, 
    error,
    loadSampleNetwork,
    calculateLayout,
    setLayout,
    setLayoutParams,
    applyCentrality,
    uploadNetworkFile
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
  const [layoutOptions] = useState([
    { value: 'spring', label: 'Spring' },
    { value: 'circular', label: 'Circular' },
    { value: 'kamada_kawai', label: 'Kamada-Kawai' },
    { value: 'fruchterman_reingold', label: 'Fruchterman-Reingold' },
    { value: 'spectral', label: 'Spectral' },
    { value: 'shell', label: 'Shell' },
    { value: 'spiral', label: 'Spiral' },
    { value: 'community', label: 'Community' }
  ]);
  const [selectedLayout, setSelectedLayout] = useState('spring');
  const graphRef = useRef();
  const messagesEndRef = useRef();
  const fileInputRef = useRef();
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
  
  // Handle file input change
  const handleFileInputChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      handleFileUpload(file);
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
  
  // Handle network save
  const handleSaveNetwork = async () => {
    try {
      if (!networkName.trim()) {
        alert("Please enter a network name");
        return;
      }
      
      const userId = localStorage.getItem('userId') || localStorage.getItem('username');
      if (!userId) {
        alert("User ID not found. Please log in again.");
        return;
      }
      
      const result = await mcpClient.saveNetwork(userId, networkName);
      if (result.success) {
        alert(`Network saved as "${networkName}"`);
        setShowSaveDialog(false);
        setNetworkName('');
        
        // Refresh saved networks list
        const networksResult = await mcpClient.listUserNetworks(userId);
        if (networksResult.success) {
          setSavedNetworks(networksResult.networks || []);
        }
      } else {
        alert(`Failed to save network: ${result.error}`);
      }
    } catch (error) {
      console.error("Error saving network:", error);
      alert(`Error saving network: ${error.message}`);
    }
  };
  
  // Handle network load
  const handleLoadNetwork = async (name) => {
    try {
      const userId = localStorage.getItem('userId') || localStorage.getItem('username');
      if (!userId) {
        alert("User ID not found. Please log in again.");
        return;
      }
      
      const result = await mcpClient.loadNetwork(userId, name);
      if (result.success) {
        alert(`Network "${name}" loaded successfully`);
        setShowLoadDialog(false);
        
        // Update network store with loaded data
        if (result.network_data) {
          const { nodes, edges, layout, layout_params } = result.network_data;
          
          // Update network store
          useNetworkStore.setState({
            positions: nodes.map(node => ({
              id: node.id,
              label: node.label || node.id,
              x: node.x || 0,
              y: node.y || 0,
              size: node.size || 5,
              color: node.color || '#1d4ed8'
            })),
            edges: edges.map(edge => ({
              source: edge.source,
              target: edge.target,
              width: edge.width || 1,
              color: edge.color || '#94a3b8'
            })),
            layout: layout || 'spring',
            layoutParams: layout_params || {}
          });
          
          // Add a system message to the chat
          useChatStore.getState().addMessage({
            role: 'assistant',
            content: `Network "${name}" loaded successfully.`,
            timestamp: new Date().toISOString()
          });
        }
      } else {
        alert(`Failed to load network: ${result.error}`);
      }
    } catch (error) {
      console.error("Error loading network:", error);
      alert(`Error loading network: ${error.message}`);
    }
  };
  
  // Handle layout change
  const handleLayoutChange = async (layoutType) => {
    try {
      setSelectedLayout(layoutType);
      
      let result;
      if (layoutType === 'community') {
        result = await mcpClient.applyCommunityLayout('louvain', { scale: 1.0 });
      } else {
        result = await mcpClient.changeLayout(layoutType);
      }
      
      if (result.success) {
        console.log(`Layout changed to ${layoutType} successfully`);
        
        // Update positions from result
        if (result.positions && result.positions.length > 0) {
          const updatedPositions = positions.map(node => {
            const updatedPos = result.positions.find(p => p.id === node.id);
            if (updatedPos) {
              return {
                ...node,
                x: updatedPos.x,
                y: updatedPos.y
              };
            }
            return node;
          });
          
          // Update network store with new positions
          useNetworkStore.setState({ 
            positions: updatedPositions,
            layout: layoutType
          });
        }
        
        // Add a system message to the chat
        useChatStore.getState().addMessage({
          role: 'assistant',
          content: `Layout changed to ${layoutType}.`,
          timestamp: new Date().toISOString()
        });
      } else {
        console.error(`Failed to change layout: ${result.error}`);
      }
    } catch (error) {
      console.error("Error changing layout:", error);
    }
  };
  
  // Handle compare layouts
  const handleCompareLayouts = async () => {
    try {
      const result = await mcpClient.compareLayouts(['spring', 'circular', 'kamada_kawai', 'fruchterman_reingold']);
      if (result.success) {
        console.log("Layout comparison results:", result);
        
        // Add a system message to the chat with comparison results
        const layoutNames = Object.keys(result.positions);
        const message = `I've compared ${layoutNames.length} different layouts for your network: ${layoutNames.join(', ')}. You can select any of these layouts from the dropdown menu.`;
        
        useChatStore.getState().addMessage({
          role: 'assistant',
          content: message,
          timestamp: new Date().toISOString()
        });
      } else {
        console.error("Failed to compare layouts:", result.error);
      }
    } catch (error) {
      console.error("Error comparing layouts:", error);
    }
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
        
        // Try to load network data from MCP first
        try {
          console.log("Attempting to load network data from MCP");
          const networkData = await mcpClient.getNetworkData();
          console.log("Network data from MCP:", networkData);
          
          if (networkData && networkData.nodes && networkData.nodes.length > 0) {
            console.log("Using network data from MCP");
            // Update network store with data from MCP
            useNetworkStore.setState({
              positions: networkData.nodes.map(node => ({
                id: node.id,
                label: node.label || node.id,
                x: node.x || 0,
                y: node.y || 0,
                size: node.size || 5,
                color: node.color || '#1d4ed8'
              })),
              edges: networkData.edges.map(edge => ({
                source: edge.source,
                target: edge.target,
                width: edge.width || 1,
                color: edge.color || '#94a3b8'
              })),
              layout: networkData.layout || 'spring',
              layoutParams: networkData.layout_params || {}
            });
            return;
          }
        } catch (mcpError) {
          console.error("Error loading network data from MCP:", mcpError);
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
    console.log("Submit handler called with message:", inputMessage);
    console.log("Is processing:", isProcessing);
    
    // Prevent double submission
    if (!inputMessage.trim() || isProcessing) {
      console.log("Message is empty or already processing, not sending");
      return;
    }
    
    // Set processing flag immediately to prevent multiple submissions
    useChatStore.getState().setTypingIndicator(true);
    
    try {
      // Check if we have a token
      const token = localStorage.getItem('token');
      if (!token) {
        console.error("No token found, cannot send message");
        return;
      }
      console.log("Token found when sending message:", token.substring(0, 10) + "...");
      
      // Clear input field immediately for better UX
      setInputMessage('');
      console.log("Input message cleared");
      
      // Set typing indicator
      useChatStore.getState().setTypingIndicator(true);
      
      try {
        // Check if the message is a command to change the layout (in English or Japanese)
        if ((inputMessage.toLowerCase().includes('change') && inputMessage.toLowerCase().includes('layout')) ||
            (inputMessage.includes('レイアウト') && (inputMessage.includes('適応') || inputMessage.includes('変更') || inputMessage.includes('適用')))) {
          console.log("Detected layout change command");
          
          // Determine layout type from message (English or Japanese)
          let layoutType = "spring"; // Default
          const message = inputMessage.toLowerCase();
          
          if (message.includes('circular') || message.includes('円形')) {
            layoutType = "circular";
          } else if (message.includes('random') || message.includes('ランダム')) {
            layoutType = "random";
          } else if (message.includes('spectral') || message.includes('スペクトル')) {
            layoutType = "spectral";
          } else if (message.includes('shell') || message.includes('殻')) {
            layoutType = "shell";
          } else if (message.includes('spring') || message.includes('スプリング')) {
            layoutType = "spring";
          } else if (message.includes('kamada') || message.includes('カマダ')) {
            layoutType = "kamada_kawai";
          } else if (message.includes('fruchterman') || message.includes('フルクターマン')) {
            layoutType = "fruchterman_reingold";
          } else if (message.includes('community') || message.includes('コミュニティ')) {
            layoutType = "community";
          }
          
          console.log(`Using MCP to change layout to ${layoutType}`);
          
          // Try to use MCP client to change layout
          let usedMcp = false;
          try {
            const result = await mcpClient.changeLayout(layoutType);
            console.log("MCP layout change result:", result);
            
            if (result && result.success) {
              usedMcp = true;
              // Add success message to chat
              useChatStore.getState().addMessage({
                role: 'assistant',
                content: `I've changed the layout to ${layoutType}.`,
                timestamp: new Date().toISOString(),
                networkUpdate: {
                  type: 'layout',
                  layout: layoutType,
                  layoutParams: {}
                }
              });
            } else {
              console.warn("MCP returned unsuccessful result, falling back to traditional API");
              throw new Error("MCP unsuccessful");
            }
          } catch (mcpError) {
            console.error("Error using MCP to change layout:", mcpError);
            
            if (!usedMcp) {
              // Fall back to traditional API
              try {
                console.log(`Falling back to traditional API for layout change to ${layoutType}`);
                
                // Use the network/layout API directly
                const response = await fetch(`${API_URL}/network/layout`, {
                  method: 'POST',
                  headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                  },
                  body: JSON.stringify({
                    nodes: positions.map(node => ({ id: node.id, label: node.label })),
                    edges: edges.map(edge => ({ source: edge.source, target: edge.target })),
                    layout: layoutType,
                    layout_params: {}
                  })
                });
                
                if (response.ok) {
                  const data = await response.json();
                  console.log("Traditional API layout change result:", data);
                  
                  // Update positions from API response
                  if (data.nodes && data.nodes.length > 0) {
                    const updatedPositions = positions.map(node => {
                      const updatedNode = data.nodes.find(n => n.id === node.id);
                      if (updatedNode) {
                        return {
                          ...node,
                          x: updatedNode.x,
                          y: updatedNode.y
                        };
                      }
                      return node;
                    });
                    
                    // Update network store
                    useNetworkStore.setState({ 
                      positions: updatedPositions,
                      layout: layoutType
                    });
                  }
                  
                  // Add success message to chat
                  useChatStore.getState().addMessage({
                    role: 'assistant',
                    content: `I've changed the layout to ${layoutType}.`,
                    timestamp: new Date().toISOString(),
                    networkUpdate: {
                      type: 'layout',
                      layout: layoutType,
                      layoutParams: {}
                    }
                  });
                } else {
                  throw new Error(`API returned status ${response.status}`);
                }
              } catch (apiError) {
                console.error("Error using traditional API for layout change:", apiError);
                
                // Fall back to regular chat message
                console.log("Falling back to regular chat message");
                const result = await sendMessage(inputMessage);
                console.log("sendMessage result:", result);
              }
            }
          }
        } 
        // Check if the message is a command to calculate centrality (in English or Japanese)
        else if (inputMessage.toLowerCase().includes('centrality') || inputMessage.includes('中心性')) {
          console.log("Detected centrality calculation command");
          
          // Determine centrality type from message (English or Japanese)
          let centralityType = "degree"; // Default
          const message = inputMessage.toLowerCase();
          
          if (message.includes('closeness') || message.includes('近接')) {
            centralityType = "closeness";
          } else if (message.includes('betweenness') || message.includes('媒介')) {
            centralityType = "betweenness";
          } else if (message.includes('eigenvector') || message.includes('固有ベクトル')) {
            centralityType = "eigenvector";
          } else if (message.includes('pagerank') || message.includes('ページランク')) {
            centralityType = "pagerank";
          } else if (message.includes('degree') || message.includes('次数')) {
            centralityType = "degree";
          }
          
          console.log(`Using MCP to calculate ${centralityType} centrality`);
          
          // Use MCP client to calculate centrality
          try {
            const result = await mcpClient.calculateCentrality(centralityType);
            console.log("MCP centrality calculation result:", result);
            
            // Add success message to chat
            useChatStore.getState().addMessage({
              role: 'assistant',
              content: `I've calculated ${centralityType} centrality for the network.`,
              timestamp: new Date().toISOString(),
              networkUpdate: {
                type: 'centrality',
                centralityType: centralityType
              }
            });
          } catch (mcpError) {
            console.error("Error using MCP to calculate centrality:", mcpError);
            
            // Fall back to regular API
            console.log("Calling sendMessage with:", inputMessage);
            const result = await sendMessage(inputMessage);
            console.log("sendMessage result:", result);
          }
        }
        // For other messages, use the regular API
        else {
          console.log("Calling sendMessage with:", inputMessage);
          const result = await sendMessage(inputMessage);
          console.log("sendMessage result:", result);
        }
        
        // Log current messages state
        console.log("Current messages:", messages);
      } catch (error) {
        console.error("Failed to send message:", error);
        
        // Add error message to chat
        useChatStore.getState().addMessage({
          role: 'assistant',
          content: "Sorry, I encountered an error processing your request. Please try again later.",
          timestamp: new Date().toISOString(),
          error: true
        });
        
        if (error.response) {
          console.error("Response status:", error.response.status);
          console.error("Response data:", error.response.data);
        } else {
          console.error("Error details:", error.message || "Unknown error");
        }
      } finally {
        // Clear typing indicator
        useChatStore.getState().setTypingIndicator(false);
      }
    } catch (error) {
      console.error("Error in handleSubmit:", error);
      setInputMessage(''); // Clear input field even on error
    }
  };
  
  // Handle network updates from chat responses
  useEffect(() => {
    const lastMessage = messages[messages.length - 1];
    if (lastMessage && lastMessage.role === 'assistant' && lastMessage.networkUpdate) {
      const update = lastMessage.networkUpdate;
      
      try {
        if (update.type === 'layout') {
          // Use MCP client to change layout
          mcpClient.changeLayout(update.layout, update.layoutParams || {})
            .then(result => {
              if (result.success) {
                console.log('Layout changed successfully:', result);
                // Update local state to reflect the change
                setLayout(update.layout);
                setLayoutParams(update.layoutParams || {});
                
                // Update positions from MCP result
                if (result.positions && result.positions.length > 0) {
                  const updatedPositions = positions.map(node => {
                    const updatedPos = result.positions.find(p => p.id === node.id);
                    if (updatedPos) {
                      return {
                        ...node,
                        x: updatedPos.x,
                        y: updatedPos.y
                      };
                    }
                    return node;
                  });
                  
                  // Update network store with new positions
                  // This will trigger the useEffect that updates graphData
                  useNetworkStore.setState({ positions: updatedPositions });
                }
              } else {
                console.error('Failed to change layout:', result.error);
              }
            })
            .catch(error => {
              console.error('Error changing layout:', error);
              // Fallback to traditional method
              setLayout(update.layout);
              setLayoutParams(update.layoutParams || {});
              calculateLayout();
            });
        } else if (update.type === 'centrality') {
          // Use MCP client to calculate centrality
          mcpClient.calculateCentrality(update.centralityType)
            .then(result => {
              if (result.success) {
                console.log('Centrality calculated successfully:', result);
                
                // Update node sizes based on centrality values
                if (result.centrality_values) {
                  const centralityValues = result.centrality_values;
                  
                  // Map centrality values to node sizes (scale between 3 and 10)
                  const values = Object.values(centralityValues);
                  const minValue = Math.min(...values);
                  const maxValue = Math.max(...values);
                  const range = maxValue - minValue;
                  
                  const nodeSizeMapping = {};
                  Object.entries(centralityValues).forEach(([nodeId, value]) => {
                    // Scale to range 3-10
                    const normalizedValue = range > 0 
                      ? 3 + ((value - minValue) / range) * 7 
                      : 5;
                    nodeSizeMapping[nodeId] = normalizedValue;
                  });
                  
                  // Apply node sizes using MCP
                  mcpClient.changeVisualProperties('node_size', 5, nodeSizeMapping)
                    .then(propResult => {
                      console.log('Node sizes updated based on centrality:', propResult);
                    })
                    .catch(error => {
                      console.error('Error updating node sizes:', error);
                    });
                }
              } else {
                console.error('Failed to calculate centrality:', result.error);
              }
            })
            .catch(error => {
              console.error('Error calculating centrality:', error);
              // Fallback to traditional method
              applyCentrality(update.centralityType);
            });
        }
      } catch (error) {
        console.error('Error handling network update:', error);
      }
    }
    
    // Handle visualization updates
    if (lastMessage && lastMessage.role === 'assistant' && lastMessage.visualizationUpdate) {
      const update = lastMessage.visualizationUpdate;
      
      try {
        if (update.type === 'highlight' && update.node_ids) {
          // Use MCP client to highlight nodes
          mcpClient.highlightNodes(update.node_ids, update.highlight_color || '#ff0000')
            .then(result => {
              if (result.success) {
                console.log('Nodes highlighted successfully:', result);
              } else {
                console.error('Failed to highlight nodes:', result.error);
              }
            })
            .catch(error => {
              console.error('Error highlighting nodes:', error);
            });
        } else if (update.type === 'visual_properties' && update.property_type) {
          // Use MCP client to change visual properties
          mcpClient.changeVisualProperties(
            update.property_type,
            update.property_value,
            update.property_mapping || {}
          )
            .then(result => {
              if (result.success) {
                console.log('Visual properties changed successfully:', result);
              } else {
                console.error('Failed to change visual properties:', result.error);
              }
            })
            .catch(error => {
              console.error('Error changing visual properties:', error);
            });
        } else if (update.type === 'show_nodes') {
          // Use MCP client to show/hide nodes by changing their size
          const visible = update.visible;
          const nodeSize = visible ? 5 : 0; // Set size to 0 to hide nodes
          
          mcpClient.changeVisualProperties('node_size', nodeSize, {})
            .then(result => {
              if (result.success) {
                console.log(`Nodes ${visible ? 'shown' : 'hidden'} successfully:`, result);
              } else {
                console.error(`Failed to ${visible ? 'show' : 'hide'} nodes:`, result.error);
              }
            })
            .catch(error => {
              console.error(`Error ${visible ? 'showing' : 'hiding'} nodes:`, error);
            });
        }
      } catch (error) {
        console.error('Error handling visualization update:', error);
      }
    }
  }, [messages, positions, setLayout, setLayoutParams, calculateLayout, applyCentrality]);
  
  return (
<div className="h-screen flex flex-col">
  <div className="flex-1 flex overflow-hidden">
    {/* Left side - Chat panel */}
    <div className="w-1/4 flex flex-col bg-white border-r border-gray-200">
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
                    <div className="text-xs text-gray-500 mt-1 text-right">
                      {new Date(message.timestamp).toLocaleTimeString()}
                    </div>
                  )}
                </div>
                
                {/* Avatar for user */}
                {message.role === 'user' && (
                  <div className="flex-shrink-0 h-8 w-8 rounded-full bg-indigo-500 flex items-center justify-center ml-2">
                    <svg className="h-5 w-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                    </svg>
                  </div>
                )}
              </div>
            ))}
            
            {/* Typing indicator */}
            {isProcessing && (
              <div className="flex justify-start mb-4">
                <div className="flex-shrink-0 h-8 w-8 rounded-full bg-blue-500 flex items-center justify-center mr-2">
                  <svg className="h-5 w-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.75 3.104v5.714a2.25 2.25 0 01-.659 1.591L5 14.5M9.75 3.104c-.251.023-.501.05-.75.082m.75-.082a24.301 24.301 0 014.5 0m0 0v5.714a2.25 2.25 0 001.5 2.25m0 0v2.8a2.25 2.25 0 01-1.5 2.25m0 0a2.25 2.25 0 01-1.5 0M5 14.5v2.8a2.25 2.25 0 002.25 2.25h9A2.25 2.25 0 0018.5 17.3v-2.8a2.25 2.25 0 00-2.25-2.25h-.75m-6 0h6" />
                  </svg>
                </div>
                <div className="p-3 rounded-lg bg-gray-100">
                  <div className="flex space-x-1">
                    <div className="w-2 h-2 rounded-full bg-gray-400 animate-bounce" style={{ animationDelay: '0ms' }}></div>
                    <div className="w-2 h-2 rounded-full bg-gray-400 animate-bounce" style={{ animationDelay: '150ms' }}></div>
                    <div className="w-2 h-2 rounded-full bg-gray-400 animate-bounce" style={{ animationDelay: '300ms' }}></div>
                  </div>
                </div>
              </div>
            )}
            
            <div ref={messagesEndRef} />
          </div>
          
          {/* Input area */}
          <div className="p-4 border-t border-gray-200">
            <form onSubmit={handleSubmit} className="flex space-x-2">
              <input
                type="text"
                value={inputMessage}
                onChange={(e) => setInputMessage(e.target.value)}
                placeholder="Type your message..."
                className="flex-1 p-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                disabled={isProcessing}
                onCompositionStart={() => setIsComposing(true)}
                onCompositionEnd={() => setIsComposing(false)}
                onKeyDown={(e) => {
                  // Only handle Enter key press if not in IME composition mode
                  // and not using the form's submit handler
                  if (e.key === 'Enter' && !e.shiftKey && !isComposing) {
                    e.preventDefault();
                    e.stopPropagation(); // Prevent event bubbling
                    
                    // Only submit if there's content and not already processing
                    if (inputMessage.trim() && !isProcessing) {
                      // Use the form's submit method instead of calling handleSubmit directly
                      // This prevents double submission
                      e.target.form.dispatchEvent(new Event('submit', { cancelable: true, bubbles: true }));
                    }
                  }
                }}
              />
              <button
                type="submit"
                disabled={isProcessing || !inputMessage.trim()}
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-blue-300"
              >
                {isProcessing ? (
                  <svg className="animate-spin h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                ) : (
                  <span>Send</span>
                )}
              </button>
            </form>
            {error && (
              <div className="mt-2 p-2 bg-red-100 border border-red-300 rounded-md">
                <p className="text-sm text-red-600">{error}</p>
                {error.includes('Authentication') && (
                  <p className="text-sm text-red-600 mt-1">
                    Please try refreshing the page or logging in again.
                  </p>
                )}
              </div>
            )}
          </div>
        </div>
        
    {/* Right side - Network visualization */}
    <div className="w-3/4 bg-gray-50 p-4 flex flex-col">
          <div className="mb-4">
            <div className="flex justify-between items-center">
              <div>
                <h2 className="text-lg font-semibold text-gray-800">Network Visualization</h2>
                {layout && (
                  <p className="text-sm text-gray-600">
                    Current Layout: <span className="font-medium">{layout}</span>
                    {Object.keys(layoutParams).length > 0 && (
                      <span className="ml-2">
                        with parameters: {JSON.stringify(layoutParams)}
                      </span>
                    )}
                  </p>
                )}
              </div>
              
              {/* Control buttons */}
              <div className="flex space-x-2">
                {/* Layout selector */}
                <select
                  value={selectedLayout}
                  onChange={(e) => handleLayoutChange(e.target.value)}
                  className="px-2 py-1 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                  disabled={isLoading}
                >
                  {layoutOptions.map(option => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>
                
                {/* Compare layouts button */}
                <button
                  onClick={handleCompareLayouts}
                  className="px-3 py-1 bg-purple-600 text-white text-sm rounded-md hover:bg-purple-700 focus:outline-none focus:ring-2 focus:ring-purple-500"
                  disabled={isLoading}
                >
                  Compare Layouts
                </button>
                
                {/* Save network button */}
                <button
                  onClick={() => setShowSaveDialog(true)}
                  className="px-3 py-1 bg-green-600 text-white text-sm rounded-md hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-green-500"
                  disabled={isLoading}
                >
                  Save Network
                </button>
                
                {/* Load network button */}
                <button
                  onClick={() => setShowLoadDialog(true)}
                  className="px-3 py-1 bg-yellow-600 text-white text-sm rounded-md hover:bg-yellow-700 focus:outline-none focus:ring-2 focus:ring-yellow-500"
                  disabled={isLoading || savedNetworks.length === 0}
                >
                  Load Network
                </button>
                
                {/* File upload button */}
                <input
                  type="file"
                  ref={fileInputRef}
                  onChange={handleFileInputChange}
                  className="hidden"
                  accept=".graphml,.gexf,.gml,.json,.net,.edgelist,.adjlist"
                />
                <button
                  onClick={() => fileInputRef.current.click()}
                  className="px-3 py-1 bg-blue-600 text-white text-sm rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  disabled={isLoading}
                >
                  Upload File
                </button>
              </div>
            </div>
            
            {/* File upload error message */}
            {fileUploadError && (
              <div className="mt-2 p-2 bg-red-100 border border-red-300 rounded-md">
                <p className="text-sm text-red-600">{fileUploadError}</p>
              </div>
            )}
          </div>
          
          {/* File drop area */}
          <div 
            className={`flex-1 border-2 ${isDragging ? 'border-blue-500 bg-blue-50' : 'border-gray-200 bg-white'} rounded-lg overflow-hidden relative`}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleFileDrop}
          >
            {isLoading ? (
              <div className="h-full flex items-center justify-center">
                <div className="text-center">
                  <svg className="animate-spin h-8 w-8 text-blue-600 mx-auto" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  <p className="mt-2 text-sm text-gray-600">Loading network...</p>
                </div>
              </div>
            ) : graphData.nodes.length > 0 ? (
              <ForceGraph2D
                ref={graphRef}
                graphData={graphData}
                nodeLabel="label"
                nodeColor={node => node.color}
                nodeRelSize={node => node.size || 5}
                linkColor={link => link.color}
                linkWidth={link => link.width || 1}
                d3AlphaDecay={0}
                d3VelocityDecay={0.4}
                cooldownTime={2000}
                onEngineStop={() => {
                  if (graphRef.current) {
                    graphRef.current.d3Force('charge').strength(-120);
                    graphRef.current.d3Force('link').strength(0.8);
                    graphRef.current.d3Force('center', null);
                  }
                }}
              />
            ) : (
              <div className="h-full flex items-center justify-center">
                <div className="text-center">
                  <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 5a1 1 0 011-1h14a1 1 0 011 1v2a1 1 0 01-1 1H5a1 1 0 01-1-1V5zM4 13a1 1 0 011-1h6a1 1 0 011 1v6a1 1 0 01-1 1H5a1 1 0 01-1-1v-6zM16 13a1 1 0 011-1h2a1 1 0 011 1v6a1 1 0 01-1 1h-2a1 1 0 01-1-1v-6z" />
                  </svg>
                  <h3 className="mt-2 text-sm font-medium text-gray-900">No network data</h3>
                  <p className="mt-1 text-sm text-gray-500">
                    Upload a network file or start chatting to visualize a network.
                  </p>
                  <button
                    onClick={() => fileInputRef.current.click()}
                    className="mt-3 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    Upload Network File
                  </button>
                  <p className="mt-2 text-xs text-gray-500">
                    Supported formats: GraphML, GEXF, GML, JSON, Pajek, EdgeList, AdjList
                  </p>
                </div>
              </div>
            )}
          </div>
          
          {/* Save Network Dialog */}
          {showSaveDialog && (
            <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
              <div className="bg-white rounded-lg p-6 w-96">
                <h3 className="text-lg font-semibold mb-4">Save Network</h3>
                <div className="mb-4">
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Network Name
                  </label>
                  <input
                    type="text"
                    value={networkName}
                    onChange={(e) => setNetworkName(e.target.value)}
                    className="w-full p-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="Enter network name"
                  />
                </div>
                <div className="flex justify-end space-x-2">
                  <button
                    onClick={() => setShowSaveDialog(false)}
                    className="px-4 py-2 bg-gray-200 text-gray-800 rounded-md hover:bg-gray-300 focus:outline-none focus:ring-2 focus:ring-gray-500"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={handleSaveNetwork}
                    className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
                    disabled={!networkName.trim()}
                  >
                    Save
                  </button>
                </div>
              </div>
            </div>
          )}
          
          {/* Load Network Dialog */}
          {showLoadDialog && (
            <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
              <div className="bg-white rounded-lg p-6 w-96">
                <h3 className="text-lg font-semibold mb-4">Load Network</h3>
                {savedNetworks.length > 0 ? (
                  <div className="mb-4 max-h-60 overflow-y-auto">
                    <ul className="divide-y divide-gray-200">
                      {savedNetworks.map((name) => (
                        <li key={name} className="py-2">
                          <button
                            onClick={() => handleLoadNetwork(name)}
                            className="w-full text-left px-3 py-2 hover:bg-gray-100 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                          >
                            {name}
                          </button>
                        </li>
                      ))}
                    </ul>
                  </div>
                ) : (
                  <p className="text-gray-500 mb-4">No saved networks found.</p>
                )}
                <div className="flex justify-end">
                  <button
                    onClick={() => setShowLoadDialog(false)}
                    className="px-4 py-2 bg-gray-200 text-gray-800 rounded-md hover:bg-gray-300 focus:outline-none focus:ring-2 focus:ring-gray-500"
                  >
                    Cancel
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default NetworkChatPage;
