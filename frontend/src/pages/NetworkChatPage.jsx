import { useState, useEffect, useRef } from 'react';
import ForceGraph2D from 'react-force-graph-2d';
import useNetworkStore from '../services/networkStore';
import useChatStore from '../services/chatStore';

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
    applyCentrality
  } = useNetworkStore();
  
  const {
    messages,
    sendMessage,
    isProcessing
  } = useChatStore();
  
  const [inputMessage, setInputMessage] = useState('');
  const [graphData, setGraphData] = useState({ nodes: [], links: [] });
  const graphRef = useRef();
  const messagesEndRef = useRef();
  
  // Load sample network on component mount
  useEffect(() => {
    loadSampleNetwork();
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
    if (!inputMessage.trim() || isProcessing) return;
    
    await sendMessage(inputMessage);
    setInputMessage('');
  };
  
  // Handle network updates from chat responses
  useEffect(() => {
    const lastMessage = messages[messages.length - 1];
    if (lastMessage && lastMessage.role === 'assistant' && lastMessage.networkUpdate) {
      const update = lastMessage.networkUpdate;
      
      if (update.type === 'layout') {
        setLayout(update.layout);
        setLayoutParams(update.layoutParams || {});
        calculateLayout();
      } else if (update.type === 'centrality') {
        applyCentrality(update.centralityType);
      }
      // Handle other update types as needed
    }
    
    // Handle visualization updates
    if (lastMessage && lastMessage.role === 'assistant' && lastMessage.visualizationUpdate) {
      const update = lastMessage.visualizationUpdate;
      
      if (update.type === 'highlight' && graphRef.current) {
        // Implementation for highlighting nodes would go here
        // This would typically involve updating the node colors in the graph data
      } else if (update.type === 'visual_properties' && graphRef.current) {
        // Implementation for changing visual properties would go here
      }
    }
  }, [messages, setLayout, setLayoutParams, calculateLayout, applyCentrality]);
  
  return (
    <div className="h-screen flex flex-col">
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
            {messages.map((message, index) => (
              <div 
                key={index} 
                className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div 
                  className={`max-w-3/4 p-3 rounded-lg ${
                    message.role === 'user' 
                      ? 'bg-blue-100 text-blue-900' 
                      : 'bg-gray-100 text-gray-900'
                  }`}
                >
                  <p className="text-sm">{message.content}</p>
                </div>
              </div>
            ))}
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
              />
              <button
                type="submit"
                disabled={isProcessing || !inputMessage.trim()}
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-blue-300"
              >
                {isProcessing ? 'Sending...' : 'Send'}
              </button>
            </form>
            {error && (
              <p className="mt-2 text-sm text-red-600">{error}</p>
            )}
          </div>
        </div>
        
        {/* Right side - Network visualization */}
        <div className="w-2/3 bg-gray-50 p-4 flex flex-col">
          <div className="mb-4">
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
          
          <div className="flex-1 border border-gray-200 rounded-lg bg-white overflow-hidden">
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
                    Start chatting to visualize a network.
                  </p>
                </div>
              </div>
            )}
          </div>
          
          <div className="mt-4 text-sm text-gray-600">
            <p>
              Try asking the assistant to:
            </p>
            <ul className="list-disc pl-5 mt-1 space-y-1">
              <li>Change the layout to circular</li>
              <li>Calculate degree centrality</li>
              <li>Highlight important nodes</li>
              <li>Change node colors based on centrality</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
};

export default NetworkChatPage;
