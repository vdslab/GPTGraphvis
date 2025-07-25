import React from 'react';
import { ProtectedRoute } from '../components/auth/ProtectedRoute';
import { MainLayout } from '../components/layout/MainLayout';

export default function Dashboard() {
  return (
    <ProtectedRoute>
      <MainLayout />
    </ProtectedRoute>
  );
}