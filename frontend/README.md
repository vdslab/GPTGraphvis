# ネットワーク可視化システム - フロントエンド

このプロジェクトは、React Router v7とTypeScriptを使用したネットワーク可視化システムのフロントエンドです。

## 機能

- **認証システム**: ログイン・ユーザー登録機能
- **ネットワーク可視化**: Cytoscape.jsを使用したインタラクティブなグラフ表示
- **チャットインターフェース**: LLMとの自然言語による対話
- **リアルタイム更新**: WebSocketによるリアルタイムデータ同期
- **状態管理**: Zustandによる効率的な状態管理

## アーキテクチャ

### コンポーネント構成

```
app/
├── components/
│   ├── auth/              # 認証関連コンポーネント
│   │   ├── LoginForm.tsx
│   │   ├── RegisterForm.tsx
│   │   └── ProtectedRoute.tsx
│   ├── chat/              # チャット機能
│   │   └── ChatInterface.tsx
│   ├── layout/            # レイアウト
│   │   └── MainLayout.tsx
│   └── network/           # ネットワーク可視化
│       └── NetworkVisualization.tsx
├── lib/                   # ユーティリティ
│   ├── api.ts            # API通信
│   └── types.ts          # 型定義
├── routes/               # ページコンポーネント
│   ├── auth.tsx
│   └── dashboard.tsx
└── store/                # 状態管理
    ├── authStore.ts
    ├── networkStore.ts
    └── websocketStore.ts
```

### 状態管理

- **AuthStore**: 認証状態とユーザー情報
- **NetworkStore**: ネットワークデータとCRUD操作
- **WebSocketStore**: リアルタイム通信管理

## セットアップ

### 前提条件

- Node.js 18以上
- APIサーバーが起動していること（http://localhost:8000）

### インストール

```bash
npm install
```

### 開発サーバー起動

```bash
npm run dev
```

アプリケーションは http://localhost:3000 で利用できます。

### ビルド

```bash
npm run build
```

### 本番サーバー起動

```bash
npm start
```

## API通信

### エンドポイント

- **認証**: 
  - `POST /auth/token` - ログイン
  - `POST /auth/register` - ユーザー登録
  - `GET /auth/users/me` - 現在のユーザー情報

- **ネットワーク**:
  - `GET /network` - ネットワーク一覧
  - `POST /network` - ネットワーク作成
  - `GET /network/:id/cytoscape` - Cytoscape.js形式でデータ取得

- **チャット**:
  - `GET /chat/conversations` - 会話一覧
  - `POST /chat/conversations/:id/messages` - メッセージ送信

### WebSocket

- **接続**: `ws://localhost:8000/ws?token=<JWT_TOKEN>`
- **メッセージ形式**:
  ```typescript
  {
    type: 'network_update' | 'chat_message' | 'error',
    data?: any,
    message?: string
  }
  ```

## 依存関係

### 主要ライブラリ

- **React Router v7**: ルーティング
- **Zustand**: 状態管理
- **Axios**: HTTP通信
- **Cytoscape.js**: グラフ可視化
- **Tailwind CSS**: スタイリング

### 型安全性

TypeScriptを使用して完全な型安全性を提供：

- APIレスポンスの型定義
- Zustandストアの型安全性
- Cytoscape.jsデータ形式の型定義

## 開発時の注意点

### エラーハンドリング

- API通信エラーは自動的にログアウト処理
- WebSocket接続エラーは自動再接続
- ネットワーク可視化の依存関係エラーは適切なメッセージ表示

### パフォーマンス

- 依存関係の動的インポート
- メッセージの自動スクロール最適化
- ネットワークデータの効率的な更新

## トラブルシューティング

### よくある問題

1. **Cytoscape.jsが読み込まれない**
   ```bash
   npm install cytoscape cytoscape-cose @types/cytoscape
   ```

2. **WebSocket接続エラー**
   - APIサーバーが起動していることを確認
   - JWTトークンが有効であることを確認

3. **型エラー**
   - `npm run typecheck` で型チェック実行
   - 必要に応じて型定義を更新

### デバッグ

- ブラウザの開発者ツールでコンソールログを確認
- ネットワークタブでAPI通信を監視
- WebSocketの接続状態を確認

## 今後の改善点

- [ ] ネットワークレイアウトの追加オプション
- [ ] チャット履歴の永続化
- [ ] ファイルエクスポート機能
- [ ] ユーザー設定画面
- [ ] ダークモード対応
