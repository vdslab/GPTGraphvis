import React, { useEffect, useState } from 'react';
import { useAuthStore } from '../../store/authStore';
import { useNetworkStore } from '../../store/networkStore';
import { useWebSocketStore } from '../../store/websocketStore';
import { NetworkVisualization } from '../network/NetworkVisualization';
import { ChatInterface } from '../chat/ChatInterface';
import { networkAPI } from '../../lib/api';
import type { CytoscapeElement, Network } from '../../lib/types';

export const MainLayout: React.FC = () => {
  const { user, logout } = useAuthStore();
  const { networks, currentNetwork, fetchNetworks, createNetwork, setCurrentNetwork } = useNetworkStore();
  const { connect, disconnect, isConnected } = useWebSocketStore();
  
  const [networkData, setNetworkData] = useState<CytoscapeElement | null>(null);
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);
  const [isLoadingNetwork, setIsLoadingNetwork] = useState(false);

  useEffect(() => {
    if (user) {
      fetchNetworks();
      
      // Connect to WebSocket
      const token = localStorage.getItem('token');
      if (token) {
        connect(token);
      }
    }

    return () => {
      disconnect();
    };
  }, [user]);

  useEffect(() => {
    // Listen for network updates from WebSocket
    const handleNetworkUpdate = (event: CustomEvent) => {
      console.log('Network update received:', event.detail);
      if (currentNetwork) {
        fetchNetworkData(currentNetwork.id);
      }
    };

    // チャットメッセージの更新も処理
    const handleChatMessage = (event: CustomEvent) => {
      console.log('Chat message received:', event.detail);
      // 必要に応じてUIの更新処理をここに追加
    };

    window.addEventListener('network-updated', handleNetworkUpdate as EventListener);
    window.addEventListener('chat-message-received', handleChatMessage as EventListener);
    
    return () => {
      window.removeEventListener('network-updated', handleNetworkUpdate as EventListener);
      window.removeEventListener('chat-message-received', handleChatMessage as EventListener);
    };
  }, [currentNetwork]);

  const fetchNetworkData = async (networkId: number) => {
    setIsLoadingNetwork(true);
    try {
      const response = await networkAPI.getNetworkCytoscape(networkId);
      const data: CytoscapeElement = response.data;
      setNetworkData(data);
    } catch (error) {
      console.error('Failed to fetch network data:', error);
    } finally {
      setIsLoadingNetwork(false);
    }
  };

  const handleNetworkSelect = async (network: Network) => {
    setCurrentNetwork(network);
    await fetchNetworkData(network.id);
  };

  const handleCreateNetwork = async () => {
    try {
      await createNetwork({
        name: '新しいネットワーク',
        nodes_data: JSON.stringify([
          { id: 'n1', label: 'ノード1', x: 100, y: 100 },
          { id: 'n2', label: 'ノード2', x: 200, y: 200 },
        ]),
        edges_data: JSON.stringify([
          { id: 'e1', source: 'n1', target: 'n2' },
        ]),
      });
    } catch (error) {
      console.error('Failed to create network:', error);
    }
  };

  const handleNodeSelect = (nodeId: string) => {
    setSelectedNodeId(nodeId);
    console.log('Node selected:', nodeId);
  };

  const handleEdgeSelect = (edgeId: string) => {
    console.log('Edge selected:', edgeId);
  };

  return (
    <div className="h-screen flex flex-col bg-gray-100">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="px-4 py-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <h1 className="text-xl font-semibold text-gray-900">
                ネットワーク可視化システム
              </h1>
              
              {/* Network Selector */}
              <div className="flex items-center space-x-2">
                <select
                  value={currentNetwork?.id || ''}
                  onChange={(e) => {
                    const network = networks.find(n => n.id === parseInt(e.target.value));
                    if (network) handleNetworkSelect(network);
                  }}
                  className="px-3 py-1 text-sm border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-indigo-500"
                >
                  <option value="">ネットワークを選択</option>
                  {networks.map(network => (
                    <option key={network.id} value={network.id}>
                      {network.name}
                    </option>
                  ))}
                </select>
                
                <button
                  onClick={handleCreateNetwork}
                  className="px-3 py-1 text-sm bg-indigo-600 text-white rounded hover:bg-indigo-700 transition-colors"
                >
                  新規作成
                </button>
              </div>
              
              {/* Connection Status */}
              <div className="flex items-center space-x-2">
                <div className={`w-2 h-2 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'}`}></div>
                <span className="text-xs text-gray-600">
                  {isConnected ? '接続中' : '切断'}
                </span>
              </div>
            </div>
            
            <div className="flex items-center space-x-4">
              <span className="text-sm text-gray-600">{user?.username}</span>
              <button
                onClick={logout}
                className="px-3 py-1 text-sm text-gray-600 hover:text-gray-800 transition-colors"
              >
                ログアウト
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <div className="flex-1 flex overflow-hidden">
        {/* Network Visualization */}
        <div className="flex-1 flex flex-col">
          <div className="bg-white border-b border-gray-200 px-4 py-2">
            <div className="flex items-center justify-between">
              <h2 className="font-medium text-gray-900">
                {currentNetwork ? currentNetwork.name : 'ネットワーク'}
              </h2>
              {selectedNodeId && (
                <span className="text-sm text-gray-600">
                  選択中: {selectedNodeId}
                </span>
              )}
            </div>
          </div>
          
          <div className="flex-1 relative">
            {isLoadingNetwork ? (
              <div className="absolute inset-0 flex items-center justify-center bg-gray-50">
                <div className="text-center">
                  <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mx-auto mb-4"></div>
                  <p className="text-gray-600">ネットワークデータを読み込み中...</p>
                </div>
              </div>
            ) : (
              <NetworkVisualization
                data={networkData}
                onNodeSelect={handleNodeSelect}
                onEdgeSelect={handleEdgeSelect}
                className="w-full h-full"
              />
            )}
          </div>
        </div>

        {/* Chat Panel */}
        <div className="w-80 border-l border-gray-200 bg-white">
          <ChatInterface
            className="h-full"
            onNetworkUpdate={(data) => {
              console.log('Network update from chat:', data);
              if (currentNetwork) {
                fetchNetworkData(currentNetwork.id);
              }
            }}
          />
        </div>
      </div>
    </div>
  );
};