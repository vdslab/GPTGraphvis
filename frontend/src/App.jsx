import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { useEffect, useState } from 'react';
import Navbar from './components/Navbar';
import ProtectedRoute from './components/ProtectedRoute';
import HomePage from './pages/HomePage';
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';
import NetworkVisualizationPage from './pages/NetworkVisualizationPage';
import LayoutRecommendationPage from './pages/LayoutRecommendationPage';
import NetworkChatPage from './pages/NetworkChatPage';
import useAuthStore from './services/authStore';

function App() {
  const { checkAuth, isLoading } = useAuthStore();
  const [authInitialized, setAuthInitialized] = useState(false);
  
  // Check authentication status on app load
  useEffect(() => {
    const initAuth = async () => {
      try {
        console.log("App: Initializing authentication check");
        await checkAuth();
        console.log("App: Authentication check completed");
      } catch (err) {
        console.error("App: Authentication check failed:", err);
      } finally {
        setAuthInitialized(true);
      }
    };
    
    initAuth();
  }, [checkAuth]);
  
  // Show loading spinner while checking authentication
  if (isLoading && !authInitialized) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
      </div>
    );
  }
  
  return (
    <Router>
      <div className="min-h-screen bg-gray-100">
        <Navbar />
        <main>
          <Routes>
            <Route path="/" element={<HomePage />} />
            <Route path="/login" element={<LoginPage />} />
            <Route path="/register" element={<RegisterPage />} />
            <Route 
              path="/network" 
              element={
                <ProtectedRoute>
                  <NetworkVisualizationPage />
                </ProtectedRoute>
              } 
            />
            <Route 
              path="/recommend" 
              element={
                <ProtectedRoute>
                  <LayoutRecommendationPage />
                </ProtectedRoute>
              } 
            />
            <Route 
              path="/chat" 
              element={
                <ProtectedRoute>
                  <NetworkChatPage />
                </ProtectedRoute>
              } 
            />
          </Routes>
        </main>
      </div>
    </Router>
  );
}

export default App;
