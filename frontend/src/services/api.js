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
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error),
);

// Auth API
export const authAPI = {
  login: (username, password) =>
    axios.post(
      `${API_URL}/auth/token`,
      `username=${username}&password=${password}`,
      {
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
      },
    ),
  register: (username, password) =>
    axios.post(`${API_URL}/auth/register`, { username, password }),
  getCurrentUser: () => axios.get(`${API_URL}/auth/users/me`),
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
