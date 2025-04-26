import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { useEffect } from 'react';
import Navbar from './components/Navbar';
import ProtectedRoute from './components/ProtectedRoute';
import HomePage from './pages/HomePage';
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';
import DashboardPage from './pages/DashboardPage';
import NetworkVisualizationPage from './pages/NetworkVisualizationPage';
import LayoutRecommendationPage from './pages/LayoutRecommendationPage';
import useAuthStore from './services/authStore';

function App() {
  const { checkAuth } = useAuthStore();
  
  // Check authentication status on app load
  useEffect(() => {
    checkAuth();
  }, [checkAuth]);
  
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
              path="/dashboard" 
              element={
                <ProtectedRoute>
                  <DashboardPage />
                </ProtectedRoute>
              } 
            />
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
          </Routes>
        </main>
      </div>
    </Router>
  );
}

export default App;
