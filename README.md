# Network Layout Application with Authentication

グラフのレイアウト計算とユーザー認証機能を備えたWebアプリケーション

## プロジェクト構成

このプロジェクトは以下のコンポーネントで構成されています：

- **frontend**: Reactフロントエンド
- **API**: FastAPIバックエンド（認証、ChatGPT連携）
- **NetworkXMCP**: NetworkXを使用したグラフ計算とMCPサーバー
- **db**: PostgreSQLデータベース（ユーザー認証用）

## 機能

- グラフのレイアウト計算（spring, circular, random, spectral）
- ユーザー認証（OAuth2 + JWT + PostgreSQL）
- ChatGPT連携（認証保護）
- Reactフロントエンド

## 始め方

1. `.env`ファイルを編集して、必要な環境変数を設定します：

```
# データベース設定
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres  # 本番環境ではより強固なパスワードに変更してください
POSTGRES_DB=graphvis
DATABASE_URL=postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@db:5432/${POSTGRES_DB}

# セキュリティ
SECRET_KEY=09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7  # 本番環境では変更してください

# OpenAI API Key
OPENAI_API_KEY=your_openai_api_key_here  # 実際のAPIキーに置き換えてください
```

2. アプリケーションを起動します：

```zsh
# 開発環境（ホットリロード有効）
docker compose up --build

# 本番環境
docker compose -f docker-compose.prod.yml up --build
```

3. アプリケーションにアクセスする：
   - フロントエンド: http://localhost:3000
   - バックエンドAPI: http://localhost:8000

## 認証の使い方

### 1. ユーザー登録

```bash
curl -X POST "http://localhost:8000/auth/register" \
  -H "Content-Type: application/json" \
  -d '{"username": "testuser", "password": "password123"}'
```

### 2. トークン取得

```bash
curl -X POST "http://localhost:8000/auth/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=testuser&password=password123"
```

レスポンス：

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

### 3. 保護されたエンドポイントへのアクセス

```bash
curl -X POST "http://localhost:8000/chatgpt/generate" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Hello, ChatGPT!"}'
```

## API エンドポイント

- `POST /auth/register` - 新規ユーザー登録
- `POST /auth/token` - アクセストークン取得
- `GET /auth/users/me` - 現在のユーザー情報取得
- `POST /chatgpt/generate` - ChatGPT応答生成（認証必須）
- `POST /chatgpt/recommend-layout` - ネットワーク特性に基づいた最適なレイアウトアルゴリズムの推薦（認証必須）
- `POST /network/layout` - グラフレイアウト計算

## NetworkXMCP

NetworkXMCPは、NetworkXを使用したグラフ計算とMCPサーバーを提供するコンポーネントです。依存関係は`pyproject.toml`で管理されています。詳細は[NetworkXMCP/README.md](NetworkXMCP/README.md)を参照してください。

## サポートされているレイアウトアルゴリズム

NetworkXの以下のレイアウトアルゴリズムをサポートしています：

1. **spring** - バネモデルに基づくレイアウト
2. **circular** - 円形配置
3. **random** - ランダム配置
4. **spectral** - スペクトル分解に基づくレイアウト
5. **shell** - 同心円状配置
6. **spiral** - 螺旋状配置
7. **planar** - 平面グラフ用レイアウト
8. **kamada_kawai** - Kamada-Kawaiアルゴリズム
9. **fruchterman_reingold** - Fruchterman-Reingoldアルゴリズム
10. **bipartite** - 二部グラフ用レイアウト
11. **multipartite** - 多部グラフ用レイアウト

## レイアウト推薦機能の使用例

```bash
curl -X POST "http://localhost:8000/chatgpt/recommend-layout" \
  -H "Authorization: Bearer {取得したトークン}" \
  -H "Content-Type: application/json" \
  -d '{
    "description": "ソーシャルネットワークで、約500ノードと2000エッジがあります。コミュニティ構造が存在します。",
    "purpose": "コミュニティ構造を視覚化したいです。"
  }'
```

レスポンス例：

```json
{
  "recommended_layout": "fruchterman_reingold",
  "explanation": "Fruchterman-Reingoldアルゴリズムは、大規模なネットワークのコミュニティ構造を視覚化するのに適しています。このアルゴリズムは力学モデルを使用し、ノードの分布を均等にしながらクラスター構造を保持します。",
  "recommended_parameters": {
    "k": 0.5,
    "iterations": 50
  }
}
```
