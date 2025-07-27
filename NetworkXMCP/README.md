# NetworkX MCP Server

NetworkX Model Context Protocol (MCP) サーバーは、ネットワーク分析と可視化のためのAPIを提供します。GraphML形式のデータをサポートし、NetworkXを使用したグラフ分析を行います。

## 機能

- GraphMLファイルのインポート/エクスポート
- ネットワークレイアウトの計算と適用
- 中心性指標の計算
- チャットインターフェースによるネットワーク操作

## 使用方法

### サーバーの起動

```bash
uvicorn main:app --host 0.0.0.0 --port 8001 --reload
```

### Dockerでの実行

```bash
docker build -t networkx-mcp .
docker run -p 8001:8001 networkx-mcp
```

### Docker Composeでの実行

```bash
docker-compose up
```

## APIエンドポイント

- `GET /health`: ヘルスチェック
- `GET /info`: サーバー情報
- `GET /get_sample_network`: サンプルネットワークの取得
- `POST /tools/export_graphml`: GraphML形式でのエクスポート
- `POST /tools/import_graphml`: GraphML形式からのインポート
- `POST /tools/convert_graphml`: GraphMLの標準形式への変換
- `POST /tools/process_chat_message`: チャットメッセージの処理
- `POST /tools/graphml_chat`: GraphMLチャット
- `POST /tools/change_layout`: レイアウトの変更
- `POST /tools/calculate_centrality`: 中心性の計算

## 依存関係

- FastAPI
- Uvicorn
- NetworkX
- NumPy
- Matplotlib
- Pydantic
