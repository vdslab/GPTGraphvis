import { create } from 'zustand';
import { networkChatAPI } from './api';

const useChatStore = create((set, get) => ({
  messages: [],
  isProcessing: false,
  error: null,

  // Send a message to the chat API
  sendMessage: async (message) => {
    const { messages } = get();
    
    // Add user message to the chat
    const userMessage = { role: 'user', content: message };
    set(state => ({ 
      messages: [...state.messages, userMessage],
      isProcessing: true,
      error: null
    }));
    
    try {
      // Send message to API
      const response = await networkChatAPI.sendMessage(
        message, 
        messages // Send current message history
      );
      
      // Add assistant response to the chat
      const assistantMessage = { 
        role: 'assistant', 
        content: response.data.response,
        networkUpdate: response.data.network_update,
        visualizationUpdate: response.data.visualization_update
      };
      
      set(state => ({ 
        messages: [...state.messages, assistantMessage],
        isProcessing: false
      }));
      
      return assistantMessage;
    } catch (error) {
      set({ 
        isProcessing: false, 
        error: error.response?.data?.detail || 'Failed to send message'
      });
      return null;
    }
  },

  // Clear all messages
  clearMessages: () => {
    set({ messages: [], error: null });
  }
}));

export default useChatStore;
