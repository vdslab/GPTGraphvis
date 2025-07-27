import time
import logging
from fastapi import FastAPI, APIRouter, HTTPException, Request, Depends, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Optional, Any
import sqlalchemy.exc
import json

from database import engine, Base
from routers import auth as auth_router
from routers import chat as chat_router
from routers import network as network_router
from routers import proxy as proxy_router
import auth

# WebSocket接続マネージャー
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
    
    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        self.active_connections[client_id] = websocket
        logging.info(f"Client {client_id} connected. Total: {len(self.active_connections)}")
    
    def disconnect(self, client_id: str):
        if client_id in self.active_connections:
            del self.active_connections[client_id]
            logging.info(f"Client {client_id} disconnected. Total: {len(self.active_connections)}")
    
    async def broadcast(self, message: Dict[str, Any]):
        for connection in self.active_connections.values():
            await connection.send_json(message)

# データベースの接続を待機
for i in range(10):
    try:
        with engine.connect():
            print(f"Database connection successful on attempt {i+1}")
            break
    except sqlalchemy.exc.OperationalError:
        if i < 9:
            time.sleep(3)
        else:
            print(f"Failed to connect to database after 10 attempts.")

# データベーステーブルの作成
try:
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully")
except Exception as e:
    print(f"Error creating database tables: {e}")

app = FastAPI(
    title="Network Visualization API",
    description="API for network visualization with user authentication, chat functionality, and NetworkX integration",
    version="1.1.0"
)

# CORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ルーターの登録
app.include_router(auth_router.router)
app.include_router(chat_router.router)
app.include_router(network_router.router)
app.include_router(proxy_router.router)

# WebSocket接続マネージャーをapp.stateに格納
app.state.ws_manager = ConnectionManager()

@app.get("/")
async def root():
    return {"message": "Network Visualization API is running"}

@app.get("/health")
async def health_check():
    try:
        with engine.connect():
            return {"status": "healthy", "database": "connected"}
    except Exception as e:
        return {"status": "unhealthy", "database": str(e)}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocketエンドポイント。
    認証済みクライアントからの接続を受け付け、接続を管理する。
    実際のイベント通知は他のルーターから `ws_manager` を介して行われる。
    """
    ws_manager = websocket.app.state.ws_manager
    token = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=1008, reason="Token is required")
        return
    
    try:
        user = auth.get_current_user_from_token(token)
        if not user:
            await websocket.close(code=1008, reason="Invalid token")
            return
        
        client_id = f"user_{user.id}_{time.time()}"
        await ws_manager.connect(websocket, client_id)
        
        try:
            # 接続を維持し、クライアントからの切断を待つ
            while True:
                await websocket.receive_text() # クライアントからのメッセージを待つが、何もしない
        except WebSocketDisconnect:
            ws_manager.disconnect(client_id)
    except Exception as e:
        logging.error(f"WebSocket error: {e}")
        if 'client_id' in locals():
            ws_manager.disconnect(client_id)
