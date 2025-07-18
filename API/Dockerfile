FROM python:3.12-slim

# uvのインストール（公式ドキュメント推奨方法）
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/

# 作業ディレクトリの設定
WORKDIR /app

# アプリケーションをコンテナにコピー
COPY . .

# 依存関係をシステムレベルでインストール
RUN uv pip install --system fastapi uvicorn networkx openai python-dotenv python-jose passlib sqlalchemy psycopg2-binary alembic numpy scipy httpx python-multipart

# アプリケーションの実行
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "80"]
