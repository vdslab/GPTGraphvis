"""
MCP (Model Context Protocol) server for network visualization.
This server provides tools for manipulating network graphs and visualization parameters.
"""

import os
import requests
import json
import logging
from fastapi import FastAPI, HTTPException, Depends, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any, Union
import asyncio
from datetime import datetime

# ロギングの設定
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("api_mcp_server")

# NetworkX MCPサーバーのURL
NETWORKX_MCP_URL = os.environ.get("NETWORKX_MCP_URL", "http://networkx-mcp:8001")

# WebSocket接続を管理するクラス
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
    
    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        self.active_connections[client_id] = websocket
        logger.info(f"Client {client_id} connected. Total connections: {len(self.active_connections)}")
    
    def disconnect(self, client_id: str):
        if client_id in self.active_connections:
            del self.active_connections[client_id]
            logger.info(f"Client {client_id} disconnected. Total connections: {len(self.active_connections)}")
    
    async def send_message(self, message: Dict[str, Any], client_id: str):
        if client_id in self.active_connections:
            await self.active_connections[client_id].send_json(message)
    
    async def broadcast(self, message: Dict[str, Any]):
        for connection in self.active_connections.values():
            await connection.send_json(message)

# 接続マネージャーのインスタンス
manager = ConnectionManager()

# FastAPIアプリケーションの作成
app = FastAPI(
    title="Network Visualization MCP Server",
    description="MCP server for network visualization",
    version="1.0.0",
)

# CORSミドルウェアの設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# リクエストモデル
class MCPToolRequest(BaseModel):
    arguments: Dict[str, Any]

class MCPToolResponse(BaseModel):
    result: Dict[str, Any]

# WebSocketエンドポイント
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    client_id = f"client_{datetime.now().timestamp()}"
    
    try:
        await manager.connect(websocket, client_id)
        
        # クライアントにウェルカムメッセージを送信
        await manager.send_message({
            "type": "connection_established",
            "message": "Connected to Network Visualization MCP Server"
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
                    await manager.broadcast({
                        "type": "network_update",
                        "data": message.get("data", {})
                    })
                elif message.get("type") == "chat_message":
                    # チャットメッセージを他のクライアントにブロードキャスト
                    await manager.broadcast({
                        "type": "chat_message",
                        "data": message.get("data", {})
                    })
                else:
                    # 不明なメッセージタイプ
                    await manager.send_message({
                        "type": "error",
                        "message": f"Unknown message type: {message.get('type')}"
                    }, client_id)
            except json.JSONDecodeError:
                # JSONデコードエラー
                await manager.send_message({
                    "type": "error",
                    "message": "Invalid JSON data"
                }, client_id)
            except Exception as e:
                # その他のエラー
                logger.error(f"Error processing message: {e}")
                await manager.send_message({
                    "type": "error",
                    "message": f"Error processing message: {str(e)}"
                }, client_id)
    
    except WebSocketDisconnect:
        # クライアントが切断した場合
        manager.disconnect(client_id)
    except Exception as e:
        # その他のエラー
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(client_id)

# NetworkX MCPサーバーにリクエストを送信する関数
async def forward_to_networkx_mcp(endpoint: str, data: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    NetworkX MCPサーバーにリクエストを転送する
    
    Args:
        endpoint: APIエンドポイント
        data: リクエストデータ
        
    Returns:
        レスポンスデータ
    """
    url = f"{NETWORKX_MCP_URL}/{endpoint}"
    
    try:
        if data:
            # POSTリクエスト
            response = requests.post(url, json=data)
        else:
            # GETリクエスト
            response = requests.get(url)
        
        # レスポンスのステータスコードをチェック
        response.raise_for_status()
        
        # JSONレスポンスを返す
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Error forwarding request to NetworkX MCP: {e}")
        raise HTTPException(status_code=500, detail=f"Error communicating with NetworkX MCP: {str(e)}")

# NetworkX MCPサーバーの情報を取得するエンドポイント
@app.get("/networkx/info")
async def get_networkx_info():
    """
    NetworkX MCPサーバーの情報を取得する
    """
    try:
        return await forward_to_networkx_mcp("info")
    except Exception as e:
        logger.error(f"Error getting NetworkX MCP info: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting NetworkX MCP info: {str(e)}")

# NetworkX MCPサーバーのヘルスチェックエンドポイント
@app.get("/networkx/health")
async def check_networkx_health():
    """
    NetworkX MCPサーバーのヘルスチェック
    """
    try:
        return await forward_to_networkx_mcp("health")
    except Exception as e:
        logger.error(f"Error checking NetworkX MCP health: {e}")
        raise HTTPException(status_code=500, detail=f"Error checking NetworkX MCP health: {str(e)}")

# サンプルネットワークを取得するエンドポイント
@app.get("/networkx/get_sample_network")
async def get_sample_network():
    """
    サンプルネットワークを取得する
    """
    try:
        result = await forward_to_networkx_mcp("get_sample_network")
        
        # WebSocketクライアントにネットワーク更新を通知
        if result.get("success"):
            await manager.broadcast({
                "type": "network_update",
                "data": {
                    "update_type": "full_update",
                    "nodes": result.get("nodes", []),
                    "edges": result.get("edges", [])
                }
            })
        
        return result
    except Exception as e:
        logger.error(f"Error getting sample network: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting sample network: {str(e)}")

# NetworkX MCPツールを使用するエンドポイント
@app.post("/networkx/tools/{tool_name}")
async def use_networkx_tool(tool_name: str, request: MCPToolRequest):
    """
    NetworkX MCPツールを使用する
    
    Args:
        tool_name: ツール名
        request: リクエストデータ
        
    Returns:
        ツールの実行結果
    """
    try:
        result = await forward_to_networkx_mcp(f"tools/{tool_name}", request.arguments)
        
        # WebSocketクライアントにネットワーク更新を通知
        if result.get("result", {}).get("success"):
            # ツールの種類に応じた更新通知
            if tool_name == "change_layout":
                # レイアウト変更
                await manager.broadcast({
                    "type": "network_update",
                    "data": {
                        "update_type": "layout",
                        "layout": result.get("result", {}).get("layout"),
                        "layout_params": result.get("result", {}).get("layout_params", {}),
                        "positions": result.get("result", {}).get("positions", [])
                    }
                })
            elif tool_name == "calculate_centrality":
                # 中心性計算
                await manager.broadcast({
                    "type": "network_update",
                    "data": {
                        "update_type": "centrality",
                        "centrality_type": result.get("result", {}).get("centrality_type"),
                        "centrality_values": result.get("result", {}).get("centrality_values", {})
                    }
                })
            elif tool_name == "import_graphml":
                # GraphMLインポート
                await manager.broadcast({
                    "type": "network_update",
                    "data": {
                        "update_type": "full_update",
                        "nodes": result.get("result", {}).get("nodes", []),
                        "edges": result.get("result", {}).get("edges", [])
                    }
                })
        
        return result
    except Exception as e:
        logger.error(f"Error using NetworkX MCP tool {tool_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Error using NetworkX MCP tool {tool_name}: {str(e)}")

# MCP情報エンドポイント
@app.get("/info")
async def get_mcp_info():
    """MCPサーバーの情報を返す"""
    return {
        "success": True,
        "name": "Network Visualization MCP Server",
        "version": "1.0.0",
        "description": "MCP server for network visualization",
        "tools": [
            {
                "name": "get_sample_network",
                "description": "Get a sample network"
            },
            {
                "name": "change_layout",
                "description": "Change the layout algorithm for the network"
            },
            {
                "name": "calculate_centrality",
                "description": "Calculate centrality metrics for the network"
            },
            {
                "name": "import_graphml",
                "description": "Import a network from GraphML"
            },
            {
                "name": "export_graphml",
                "description": "Export the current network as GraphML"
            },
        ]
    }
