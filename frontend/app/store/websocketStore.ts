import { create } from 'zustand';
import type { WebSocketStore, WebSocketMessage } from '../lib/types';

export const useWebSocketStore = create<WebSocketStore>((set, get) => ({
  socket: null,
  isConnected: false,

  connect: (token: string) => {
    const { socket } = get();
    
    // Close existing connection if any
    if (socket) {
      socket.close();
    }

    try {
      const wsUrl = `ws://localhost:8000/ws?token=${encodeURIComponent(token)}`;
      const newSocket = new WebSocket(wsUrl);

      newSocket.onopen = () => {
        console.log('WebSocket connected');
        set({ isConnected: true });
      };

      newSocket.onmessage = (event) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data);
          console.log('WebSocket message received:', message);
          
          // Handle different message types
          switch (message.type) {
            case 'network_update':
              // Trigger network data refresh
              window.dispatchEvent(new CustomEvent('network-updated', { 
                detail: message.data 
              }));
              break;
            case 'chat_message':
              // Trigger chat message refresh
              window.dispatchEvent(new CustomEvent('chat-message-received', { 
                detail: message.data 
              }));
              break;
            case 'connection_established':
              console.log('WebSocket connection established:', message.message);
              break;
            case 'error':
              console.error('WebSocket error:', message.message);
              break;
            default:
              console.log('Unknown WebSocket message type:', message.type);
          }
        } catch (error) {
          console.error('Error parsing WebSocket message:', error);
        }
      };

      newSocket.onclose = (event) => {
        console.log('WebSocket disconnected:', event.code, event.reason);
        set({ isConnected: false, socket: null });
        
        // Attempt to reconnect after a delay if not a clean close
        if (event.code !== 1000 && event.code !== 1001) {
          setTimeout(() => {
            const currentToken = localStorage.getItem('token');
            if (currentToken) {
              get().connect(currentToken);
            }
          }, 3000);
        }
      };

      newSocket.onerror = (error) => {
        console.error('WebSocket error:', error);
        set({ isConnected: false });
      };

      set({ socket: newSocket });
    } catch (error) {
      console.error('Failed to create WebSocket connection:', error);
    }
  },

  disconnect: () => {
    const { socket } = get();
    if (socket) {
      socket.close(1000, 'Client disconnect');
      set({ socket: null, isConnected: false });
    }
  },

  sendMessage: (message: any) => {
    const { socket, isConnected } = get();
    if (socket && isConnected) {
      try {
        socket.send(JSON.stringify(message));
      } catch (error) {
        console.error('Failed to send WebSocket message:', error);
      }
    } else {
      console.warn('WebSocket is not connected, cannot send message');
    }
  },
}));