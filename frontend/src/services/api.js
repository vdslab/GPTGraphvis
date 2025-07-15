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
      
      // Debug: Log the full token for debugging purposes
      console.log("Full token:", token);
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

// Network API
export const networkAPI = {
  calculateLayout: (nodes, edges, layout, layoutParams) =>
    axios.post(`${API_URL}/network/layout`, {
      nodes,
      edges,
      layout,
      layout_params: layoutParams,
    }),
  applyLayout: (nodes, edges, layout, layoutParams) =>
    axios.post(`${API_URL}/network-layout/apply`, {
      nodes,
      edges,
      layout,
      layout_params: layoutParams,
    }),
  recommendLayout: (description, purpose) =>
    axios.post(`${API_URL}/chatgpt/recommend-layout`, {
      description,
      purpose,
    }),
};

// ChatGPT API
export const chatgptAPI = {
  generateResponse: (prompt, maxTokens = 1000, temperature = 0.7) =>
    axios.post(`${API_URL}/chatgpt/generate`, {
      prompt,
      max_tokens: maxTokens,
      temperature,
    }),
};

// Network Chat API
export const networkChatAPI = {
  sendMessage: (message, history) => {
    console.log("Sending message to network chat API:", message);
    console.log("Current token:", localStorage.getItem("token"));
    
    // Ensure we have a token
    const token = localStorage.getItem("token");
    if (!token) {
      console.error("No token found when sending message");
      return Promise.reject(new Error("Authentication required"));
    }
    
    // Explicitly set the Authorization header for this request
    return axios.post(`${API_URL}/network-chat/chat`, {
      message,
      history
    }, {
      headers: {
        Authorization: `Bearer ${token}`
      }
    });
  },
  getSampleNetwork: () => {
    console.log("Getting sample network");
    console.log("Current token:", localStorage.getItem("token"));
    
    // Ensure we have a token
    const token = localStorage.getItem("token");
    if (!token) {
      console.error("No token found when getting sample network");
      return Promise.reject(new Error("Authentication required"));
    }
    
    // Explicitly set the Authorization header for this request
    return axios.post(`${API_URL}/network-chat/network`, {}, {
      headers: {
        Authorization: `Bearer ${token}`
      }
    });
  },
  uploadNetworkFile: (file) => {
    console.log("Uploading network file:", file.name);
    console.log("Current token:", localStorage.getItem("token"));
    
    // Ensure we have a token
    const token = localStorage.getItem("token");
    if (!token) {
      console.error("No token found when uploading network file");
      return Promise.reject(new Error("Authentication required"));
    }
    
    // Create form data
    const formData = new FormData();
    formData.append('file', file);
    
    // Explicitly set the Authorization header for this request
    return axios.post(`${API_URL}/network-chat/upload-network`, formData, {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'multipart/form-data'
      }
    });
  }
};
