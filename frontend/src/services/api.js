import axios from "axios";

// Direct connection to API server
// Using localhost:8000 to connect directly to the API server
const DIRECT_API_URL = "http://localhost:8000";
const API_URL = DIRECT_API_URL;

console.log("Using API URL:", API_URL);

// Add auth token to requests
axios.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem("token");
    if (token) {
      // Ensure the Authorization header is set correctly
      config.headers = {
        ...config.headers,
        Authorization: `Bearer ${token}`
      };
      console.log("Adding token to request:", config.url, "Token:", token.substring(0, 10) + "...");
      console.log("Full headers:", JSON.stringify(config.headers));
    } else {
      console.log("No token found for request:", config.url);
      
      // Check if we're on a protected route and redirect to login if needed
      if (window.location.pathname !== '/' && 
          window.location.pathname !== '/login' && 
          window.location.pathname !== '/register') {
        console.log("Protected route detected without token, redirecting to login");
        // We'll handle this in the response interceptor
      }
    }
    return config;
  },
  (error) => Promise.reject(error),
);

// Add response interceptor for debugging
axios.interceptors.response.use(
  (response) => {
    console.log("Response from:", response.config.url, "Status:", response.status);
    return response;
  },
  (error) => {
    console.error("Error response:", error.config?.url, "Status:", error.response?.status);
    console.error("Error details:", error.response?.data);
    
    // Handle 401 errors globally
    if (error.response?.status === 401) {
      console.error("Authentication error detected, clearing token and redirecting to login");
      localStorage.removeItem('token');
      
      // Only redirect if we're not already on the login page
      if (window.location.pathname !== '/login' && window.location.pathname !== '/register') {
        window.location.href = '/login';
      }
    }
    
    return Promise.reject(error);
  }
);

// Auth API
export const authAPI = {
  login: (username, password) => {
    console.log("Login request with username:", username);
    return axios.post(
      `${API_URL}/auth/token`,
      `username=${username}&password=${password}`,
      {
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
      },
    );
  },
  register: (username, password) => {
    console.log("Register request with username:", username);
    return axios.post(`${API_URL}/auth/register`, { username, password });
  },
  getCurrentUser: () => {
    console.log("Getting current user");
    return axios.get(`${API_URL}/auth/users/me`);
  },
};

// Network API endpoints
export const networkAPI = {
  getNetworks: () => {
    console.log("Getting all networks");
    return axios.get(`${API_URL}/network/`);
  },
  getNetwork: (networkId) => {
    console.log("Getting network:", networkId);
    return axios.get(`${API_URL}/network/${networkId}`);
  },
  createNetwork: (networkData) => {
    console.log("Creating network with data:", networkData);
    return axios.post(`${API_URL}/network/`, networkData);
  },
  updateNetwork: (networkId, networkData) => {
    console.log("Updating network:", networkId);
    return axios.put(`${API_URL}/network/${networkId}`, networkData);
  },
  deleteNetwork: (networkId) => {
    console.log("Deleting network:", networkId);
    return axios.delete(`${API_URL}/network/${networkId}`);
  },
  getNetworkCytoscape: (networkId) => {
    console.log("Getting network in Cytoscape format:", networkId);
    return axios.get(`${API_URL}/network/${networkId}/cytoscape`);
  },
  // NetworkXMCP関連のプロキシAPI
  getSampleNetwork: () => {
    console.log("Getting sample network via API proxy");
    return axios.get(`${API_URL}/proxy/networkx/get_sample_network`);
  },
  changeLayout: (layoutType, layoutParams = {}) => {
    console.log("Changing layout via API proxy:", layoutType, layoutParams);
    return axios.post(`${API_URL}/proxy/networkx/tools/change_layout`, {
      arguments: { layout_type: layoutType, layout_params: layoutParams }
    });
  },
  calculateCentrality: (centralityType) => {
    console.log("Calculating centrality via API proxy:", centralityType);
    return axios.post(`${API_URL}/proxy/networkx/tools/calculate_centrality`, {
      arguments: { centrality_type: centralityType }
    });
  },
  exportNetworkAsGraphML: () => {
    console.log("Exporting network as GraphML via API proxy");
    return axios.post(`${API_URL}/proxy/networkx/tools/export_graphml`, {
      arguments: {}
    });
  },
  importGraphML: (graphmlContent) => {
    console.log("Importing GraphML via API proxy");
    return axios.post(`${API_URL}/proxy/networkx/tools/import_graphml`, {
      arguments: { graphml_content: graphmlContent }
    });
  },
  convertGraphML: (graphmlContent) => {
    console.log("Converting GraphML via API proxy");
    return axios.post(`${API_URL}/proxy/networkx/tools/convert_graphml`, {
      arguments: { graphml_content: graphmlContent }
    });
  },
  graphmlLayout: (graphmlContent, layoutType, layoutParams = {}) => {
    console.log("Applying layout to GraphML via API proxy:", layoutType);
    return axios.post(`${API_URL}/proxy/networkx/tools/graphml_layout`, {
      arguments: {
        graphml_content: graphmlContent,
        layout_type: layoutType,
        layout_params: layoutParams
      }
    });
  },
  graphmlCentrality: (graphmlContent, centralityType) => {
    console.log("Calculating centrality for GraphML via API proxy:", centralityType);
    return axios.post(`${API_URL}/proxy/networkx/tools/graphml_centrality`, {
      arguments: {
        graphml_content: graphmlContent,
        centrality_type: centralityType
      }
    });
  },
  graphmlVisualProperties: (graphmlContent, propertyType, propertyValue, propertyMapping = {}) => {
    console.log("Changing visual properties for GraphML via API proxy:", propertyType, propertyValue);
    return axios.post(`${API_URL}/proxy/networkx/tools/graphml_visual_properties`, {
      arguments: {
        graphml_content: graphmlContent,
        property_type: propertyType,
        property_value: propertyValue,
        property_mapping: propertyMapping
      }
    });
  },
  getNetworkInfo: () => {
    console.log("Getting network info via API proxy");
    return axios.post(`${API_URL}/proxy/networkx/tools/get_network_info`, {
      arguments: {}
    });
  },
  useTool: (toolName, args = {}) => {
    console.log(`Using tool via API proxy: ${toolName}`, args);
    return axios.post(`${API_URL}/proxy/networkx/tools/${toolName}`, {
      arguments: args
    });
  }
};

// Network Chat API endpoints
export const networkChatAPI = {
  getConversations: () => {
    console.log("Getting all conversations");
    return axios.get(`${API_URL}/chat/conversations`);
  },
  getMessages: (conversationId) => {
    console.log("Getting messages for conversation:", conversationId);
    return axios.get(`${API_URL}/chat/conversations/${conversationId}/messages`);
  },
  sendMessage: (conversationId, message) => {
    console.log("Sending message to conversation:", conversationId, message);
    return axios.post(`${API_URL}/chat/conversations/${conversationId}/messages`, {
      content: message,
      role: "user"
    });
  },
  createConversation: (title = "New Conversation") => {
    console.log("Creating new conversation with title:", title);
    return axios.post(`${API_URL}/chat/conversations`, { title });
  },
  deleteConversation: (conversationId) => {
    console.log("Deleting conversation:", conversationId);
    return axios.delete(`${API_URL}/chat/conversations/${conversationId}`);
  },
  processChatMessage: (message) => {
    console.log("Processing chat message via API:", message);
    // APIサーバーを経由してチャットメッセージを処理
    return axios.post(`${API_URL}/chat/process`, { message });
  }
};
