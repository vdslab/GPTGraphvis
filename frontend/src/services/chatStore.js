import { create } from 'zustand';
import { networkChatAPI } from './api';

const useChatStore = create((set, get) => ({
  messages: [],
  isProcessing: false,
  error: null,
  typingTimeout: null,

  // Send a message to the chat API
  sendMessage: async (message) => {
    console.log("chatStore.sendMessage called with:", message);
    const { messages } = get();
    console.log("Current messages in store:", messages);
    
    // Add user message to the chat with timestamp
    const userMessage = { 
      role: 'user', 
      content: message,
      timestamp: new Date().toISOString()
    };
    console.log("Adding user message to chat:", userMessage);
    
    set(state => {
      console.log("Updating state with user message");
      return { 
        messages: [...state.messages, userMessage],
        isProcessing: true,
        error: null
      };
    });
    
    try {
      console.log("Preparing to send message to API:", message);
      console.log("Message history length:", messages.length);
      
      // Send message to API
      console.log("Calling networkChatAPI.sendMessage");
      const response = await networkChatAPI.sendMessage(
        message, 
        messages // Send current message history
      );
      
      console.log("Received response from API:", response);
      console.log("Response data:", response.data);
      
      // Add assistant response to the chat with timestamp
      const assistantMessage = { 
        role: 'assistant', 
        content: response.data.response,
        networkUpdate: response.data.network_update,
        visualizationUpdate: response.data.visualization_update,
        timestamp: new Date().toISOString()
      };
      
      console.log("Created assistant message:", assistantMessage);
      
      set(state => {
        console.log("Updating state with assistant message");
        return { 
          messages: [...state.messages, assistantMessage],
          isProcessing: false
        };
      });
      
      console.log("State updated, returning assistant message");
      return assistantMessage;
    } catch (error) {
      console.error("Error sending message:", error);
      console.error("Error type:", error.constructor.name);
      console.error("Error message:", error.message);
      console.error("Error stack:", error.stack);
      
      // Check if it's an authentication error
      if (error.response?.status === 401) {
        console.error("Authentication error when sending message");
        set({ 
          isProcessing: false, 
          error: "Authentication failed. Please log in again."
        });
      } else {
        console.error("Other error type:", error.name);
        console.error("Error response:", error.response);
        
        set({ 
          isProcessing: false, 
          error: error.response?.data?.detail || 'Failed to send message'
        });
      }
      
      console.log("Returning null due to error");
      return null;
    }
  },

  // Clear all messages
  clearMessages: () => {
    set({ messages: [], error: null });
  },
  
  // Set typing indicator
  setTypingIndicator: (isTyping) => {
    const { typingTimeout } = get();
    
    // Clear any existing timeout
    if (typingTimeout) {
      clearTimeout(typingTimeout);
    }
    
    if (isTyping) {
      // Set typing indicator and clear it after 30 seconds (failsafe)
      const timeout = setTimeout(() => {
        set({ isProcessing: false });
      }, 30000);
      
      set({ isProcessing: true, typingTimeout: timeout });
    } else {
      set({ isProcessing: false, typingTimeout: null });
    }
  },
  
  // Add a message directly (useful for system messages or local updates)
  addMessage: (message) => {
    if (!message.role || !message.content) {
      console.error("Invalid message format:", message);
      return;
    }
    
    // Add timestamp if not provided
    if (!message.timestamp) {
      message.timestamp = new Date().toISOString();
    }
    
    set(state => ({
      messages: [...state.messages, message]
    }));
  }
}));

export default useChatStore;
