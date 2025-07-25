import React, { useState, useEffect } from 'react';
import { useLocation } from 'react-router';
import { LoginForm } from '../components/auth/LoginForm';
import { RegisterForm } from '../components/auth/RegisterForm';

export default function AuthPage() {
  const location = useLocation();
  const [isLogin, setIsLogin] = useState(true);

  // URLパスに基づいてデフォルトフォームを決定
  useEffect(() => {
    if (location.pathname === '/register') {
      setIsLogin(false);
    } else {
      setIsLogin(true);
    }
  }, [location.pathname]);

  return (
    <>
      {isLogin ? (
        <LoginForm onSwitchToRegister={() => setIsLogin(false)} />
      ) : (
        <RegisterForm onSwitchToLogin={() => setIsLogin(true)} />
      )}
    </>
  );
}