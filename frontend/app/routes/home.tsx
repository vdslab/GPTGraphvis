import React, { useEffect } from 'react';
import type { Route } from "./+types/home";
import { Navigate } from 'react-router';
import { useAuthStore } from '../store/authStore';
import { Welcome } from "../welcome/welcome";

export function meta({}: Route.MetaArgs) {
  return [
    { title: "ネットワーク可視化システム" },
    { name: "description", content: "ChatGPT連携ネットワーク可視化システム" },
  ];
}

export default function Home() {
  const { user, token, getCurrentUser } = useAuthStore();

  // トークンがある場合は現在のユーザー情報を取得
  useEffect(() => {
    if (token && !user) {
      getCurrentUser();
    }
  }, [token, user, getCurrentUser]);

  // 認証状態に基づいてリダイレクト
  if (token) {
    // 認証済みの場合はダッシュボードにリダイレクト
    return <Navigate to="/dashboard" replace />;
  }

  // 未認証の場合は認証ページにリダイレクト
  return <Navigate to="/auth" replace />;
}
