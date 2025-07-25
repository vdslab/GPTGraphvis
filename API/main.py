import time
import logging
from fastapi import FastAPI, APIRouter, HTTPException, Request, Depends, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Optional, Any
import networkx as nx
import numpy as np
from dotenv import load_dotenv
import sqlalchemy.exc
import json

from database import engine, Base
from routers import auth as auth_router
from routers import chat as chat_router
from routers import proxy as proxy_router
from routers import network as network_router
import auth

# Load environment variables
load_dotenv()

# データベースの接続を待機する
max_retries = 10
retry_interval = 3  # 秒
for i in range(max_retries):
    try:
        # 接続テスト
        with engine.connect() as conn:
            print(f"Database connection successful on attempt {i+1}")
            break
    except sqlalchemy.exc.OperationalError as e:
        if i < max_retries - 1:
            print(f"Database connection attempt {i+1} failed. Retrying in {retry_interval} seconds...")
            time.sleep(retry_interval)
        else:
            print(f"Failed to connect to database after {max_retries} attempts: {e}")
            # エラーを発生させずに続行（コンテナ再起動ループを避けるため）

# Create database tables
try:
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully")
except Exception as e:
    print(f"Error creating database tables: {e}")

app = FastAPI(
    title="Network Visualization API",
    description="API for network visualization with user authentication, chat functionality, and NetworkX integration",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Allow frontend origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router.router)
app.include_router(chat_router.router)
app.include_router(proxy_router.router)
app.include_router(network_router.router)

# Create a simple MCP router instead of including the full app
mcp_router = APIRouter()

@mcp_router.get("/health")
async def mcp_health():
    return {"status": "ok", "service": "mcp"}

# Include the MCP router
app.include_router(mcp_router, prefix="/mcp")

# WebSocketマネージャーの作成
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
    
    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        self.active_connections[client_id] = websocket
        logging.info(f"Client {client_id} connected. Total connections: {len(self.active_connections)}")
    
    def disconnect(self, client_id: str):
        if client_id in self.active_connections:
            del self.active_connections[client_id]
            logging.info(f"Client {client_id} disconnected. Total connections: {len(self.active_connections)}")
    
    async def send_message(self, message: Dict[str, Any], client_id: str):
        if client_id in self.active_connections:
            await self.active_connections[client_id].send_json(message)
    
    async def broadcast(self, message: Dict[str, Any]):
        for connection in self.active_connections.values():
            await connection.send_json(message)

# WebSocketマネージャーのインスタンス
ws_manager = ConnectionManager()

@app.get("/")
async def root():
    return {
        "message": "Network Visualization API is running",
        "version": "1.0.0",
        "documentation": "/docs"
    }

@app.get("/health")
async def health_check():
    """
    Health check endpoint for Docker healthcheck.
    """
    try:
        # 接続テスト
        with engine.connect() as conn:
            return {"status": "healthy", "database": "connected"}
    except Exception as e:
        return {"status": "unhealthy", "database": str(e)}

# WebSocketエンドポイント
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocketエンドポイント
    クライアントからの接続を受け付け、メッセージの送受信を行う
    """
    # トークンの検証
    token = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=1008, reason="Token is required")
        return
    
    try:
        # トークンの検証
        user = auth.get_current_user_from_token(token)
        if not user:
            await websocket.close(code=1008, reason="Invalid token")
            return
        
        # クライアントIDの生成
        client_id = f"user_{user.id}_{time.time()}"
        
        # WebSocket接続の確立
        await ws_manager.connect(websocket, client_id)
        
        # クライアントにウェルカムメッセージを送信
        await ws_manager.send_message({
            "type": "connection_established",
            "message": f"Connected to Network Visualization API as {user.username}"
        }, client_id)
        
        # メッセージの受信ループ
        while True:
            # メッセージを受信
            data = await websocket.receive_text()
            
            try:
                # JSONデータをパース
                message = json.loads(data)
                
                # メッセージタイプに基づいて処理
                if message.get("type") == "network_update":
                    # ネットワーク更新メッセージを他のクライアントにブロードキャスト
                    await ws_manager.broadcast({
                        "type": "network_update",
                        "data": message.get("data", {})
                    })
                elif message.get("type") == "chat_message":
                    # チャットメッセージを他のクライアントにブロードキャスト
                    await ws_manager.broadcast({
                        "type": "chat_message",
                        "data": message.get("data", {})
                    })
                else:
                    # 不明なメッセージタイプ
                    await ws_manager.send_message({
                        "type": "error",
                        "message": f"Unknown message type: {message.get('type')}"
                    }, client_id)
            except json.JSONDecodeError:
                # JSONデコードエラー
                await ws_manager.send_message({
                    "type": "error",
                    "message": "Invalid JSON data"
                }, client_id)
            except Exception as e:
                # その他のエラー
                logging.error(f"Error processing message: {e}")
                await ws_manager.send_message({
                    "type": "error",
                    "message": f"Error processing message: {str(e)}"
                }, client_id)
    
    except WebSocketDisconnect:
        # クライアントが切断した場合
        if 'client_id' in locals():
            ws_manager.disconnect(client_id)
    except Exception as e:
        # その他のエラー
        logging.error(f"WebSocket error: {e}")
        if 'client_id' in locals():
            ws_manager.disconnect(client_id)
