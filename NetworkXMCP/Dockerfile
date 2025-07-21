FROM python:3.12-slim

# uvのインストール（公式ドキュメント推奨方法）
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/

# 作業ディレクトリの設定
WORKDIR /app

# アプリケーションをコンテナにコピー
COPY . .

# 依存関係のインストール
RUN uv pip install -e . --no-deps && uv pip install -r requirements.txt

# アプリケーションの実行
CMD ["uv", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]
