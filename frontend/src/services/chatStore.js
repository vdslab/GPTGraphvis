import { create } from 'zustand';

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
    
    // First add the user message to the state directly
    // This is a more direct approach to ensure the message is added
    const currentMessages = [...messages];
    const updatedMessagesWithUser = [...currentMessages, userMessage];
    
    console.log("Setting messages directly:", updatedMessagesWithUser);
    set({ 
      messages: updatedMessagesWithUser,
      isProcessing: true,
      error: null
    });
    
    console.log("After direct set, messages:", get().messages);
    
    try {
      console.log("Preparing to send message to API:", message);
      console.log("Message history length:", messages.length);
      
      // Simulate a response since we're not using an API
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      console.log("Generating simulated response for message:", message);
      
      // Create a simple response based on the message content
      let responseContent = "I'm sorry, I don't understand that request. You can ask me about network visualization or uploading network files.";
      let networkUpdate = null;
      let visualizationUpdate = null;
      
      // Simple keyword-based responses
      if (message.toLowerCase().includes('upload') || message.toLowerCase().includes('file')) {
        responseContent = "You can upload a network file by clicking the 'Upload Network File' button at the top of the visualization panel. Supported formats include GraphML, GEXF, GML, JSON, and others.";
      } else if (message.toLowerCase().includes('layout') || message.toLowerCase().includes('visualize')) {
        responseContent = "You can change the network layout using the dropdown menu at the top of the visualization panel. Available layouts include Spring, Circular, Random, Spectral, and others.";
      } else if (message.toLowerCase().includes('centrality') || message.toLowerCase().includes('measure')) {
        responseContent = "You can apply centrality measures to the network using the 'Apply Centrality' dropdown. Available measures include Degree, Closeness, Betweenness, Eigenvector, and PageRank.";
      }
      
      // Add assistant response to the chat with timestamp
      const assistantMessage = { 
        role: 'assistant', 
        content: responseContent,
        networkUpdate: networkUpdate,
        visualizationUpdate: visualizationUpdate,
        timestamp: new Date().toISOString()
      };
      
      console.log("Generated assistant message:", assistantMessage);
      
      console.log("Created assistant message:", assistantMessage);
      
      // Add the message to the state
      set(state => {
        console.log("Updating state with assistant message");
        const updatedMessages = [...state.messages, assistantMessage];
        console.log("Updated messages array:", updatedMessages);
        return { 
          messages: updatedMessages,
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
    
    console.log("Adding message directly:", message);
    console.log("Current messages before adding:", get().messages);
    
    // Create a new message object to avoid reference issues
    const newMessage = { ...message };
    
    // Force a completely new array to avoid reference issues
    const currentMessages = [...get().messages];
    const updatedMessages = [...currentMessages, newMessage];
    
    console.log("Updated messages array after direct add:", updatedMessages);
    console.log("Message count after adding:", updatedMessages.length);
    
    // Set the state with the updated messages
    set(() => {
      console.log("Setting state with messages:", updatedMessages);
      return { messages: updatedMessages };
    });
    
    // Add a small delay and then verify the message was added
    setTimeout(() => {
      console.log("Messages after state update (delayed check):", get().messages);
      console.log("Message count after delay:", get().messages.length);
    }, 100);
    
    return newMessage; // Return the added message for chaining
  },
  
  // Debug function to check the current state of messages
  debugMessages: () => {
    const currentMessages = get().messages;
    console.log("DEBUG - Current messages:", currentMessages);
    console.log("DEBUG - Message count:", currentMessages.length);
    return currentMessages;
  }
}));

export default useChatStore;
