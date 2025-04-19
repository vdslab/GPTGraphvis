FROM python:3.12-slim

# uvのインストール（公式ドキュメント推奨方法）
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/

# アプリケーションをコンテナにコピー
COPY . /app

# 作業ディレクトリの設定
WORKDIR /app

# 依存関係をシステムレベルでインストール（仮想環境ではなく）
RUN uv pip install --system -e .

# アプリケーションの実行
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "80"]