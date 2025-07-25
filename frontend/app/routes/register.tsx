import React from 'react';
import { RegisterForm } from '../components/auth/RegisterForm';

export default function RegisterPage() {
  return <RegisterForm onSwitchToLogin={() => window.location.href = '/login'} />;
}
