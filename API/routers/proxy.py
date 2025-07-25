"""
プロキシルーター
=============

NetworkX MCPサーバーへのリクエストをプロキシするルーター
"""

import os
import requests
import json
import logging
from fastapi import APIRouter, HTTPException, Depends, Request, Body
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Dict, List, Optional, Any, Union
import auth

# ロギングの設定
logger = logging.getLogger("api.routers.proxy")

# ルーターの作成
router = APIRouter(
    prefix="/proxy",
    tags=["proxy"],
    dependencies=[Depends(auth.get_current_user)],
    responses={404: {"description": "Not found"}},
)

# NetworkX MCPサーバーのURL
NETWORKX_MCP_URL = os.environ.get("NETWORKX_MCP_URL", "http://networkx-mcp:8001")

# リクエストモデル
class ProxyRequest(BaseModel):
    arguments: Dict[str, Any]

# NetworkX MCPサーバーにリクエストを転送する関数
def forward_to_networkx_mcp(endpoint: str, data: Dict[str, Any] = None) -> Dict[str, Any]:
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
@router.get("/networkx/info")
async def get_networkx_info():
    """
    NetworkX MCPサーバーの情報を取得する
    """
    try:
        return forward_to_networkx_mcp("info")
    except Exception as e:
        logger.error(f"Error getting NetworkX MCP info: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting NetworkX MCP info: {str(e)}")

# NetworkX MCPサーバーのヘルスチェックエンドポイント
@router.get("/networkx/health")
async def check_networkx_health():
    """
    NetworkX MCPサーバーのヘルスチェック
    """
    try:
        return forward_to_networkx_mcp("health")
    except Exception as e:
        logger.error(f"Error checking NetworkX MCP health: {e}")
        raise HTTPException(status_code=500, detail=f"Error checking NetworkX MCP health: {str(e)}")

# サンプルネットワークを取得するエンドポイント
@router.get("/networkx/get_sample_network")
async def get_sample_network():
    """
    サンプルネットワークを取得する
    """
    try:
        return forward_to_networkx_mcp("get_sample_network")
    except Exception as e:
        logger.error(f"Error getting sample network: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting sample network: {str(e)}")

# NetworkX MCPツールを使用するエンドポイント
@router.post("/networkx/tools/{tool_name}")
async def use_networkx_tool(tool_name: str, request: ProxyRequest):
    """
    NetworkX MCPツールを使用する
    
    Args:
        tool_name: ツール名
        request: リクエストデータ
        
    Returns:
        ツールの実行結果
    """
    try:
        return forward_to_networkx_mcp(f"tools/{tool_name}", request.arguments)
    except Exception as e:
        logger.error(f"Error using NetworkX MCP tool {tool_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Error using NetworkX MCP tool {tool_name}: {str(e)}")
