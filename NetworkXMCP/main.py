"""
NetworkX MCP Server (Stateless)
=================================

FastAPI Model Context Protocol (MCP) サーバー
ネットワーク分析と可視化のためのステートレスなAPIを提供します。
GraphML形式のデータをサポートし、NetworkXを使用したグラフ分析を行います。
"""

import os
import logging
import networkx as nx
import numpy as np
from typing import Dict, Any, List, Optional, Union
from fastapi import FastAPI, Depends, HTTPException, Body, Request, Header
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import random
import json
import base64
import io
from datetime import datetime

# ロギングの設定
log_level = os.environ.get("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=getattr(logging, log_level),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("networkx_mcp")

# FastAPIアプリケーションの作成
app = FastAPI(
    title="NetworkX MCP (Stateless)",
    description="Stateless MCP server for network analysis and visualization using NetworkX",
    version="0.2.0",
)

# CORSミドルウェアの設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Pydanticモデル定義 ---

class GraphData(BaseModel):
    graphml_content: str = Field(..., description="GraphML content representing the network.")

class LayoutParams(GraphData):
    layout_type: str = Field("spring", description="The layout algorithm to apply.")
    layout_params: Dict[str, Any] = Field({}, description="Parameters for the layout algorithm.")

class CentralityParams(GraphData):
    centrality_type: str = Field("degree", description="The type of centrality to calculate.")
    centrality_params: Dict[str, Any] = Field({}, description="Parameters for the centrality calculation.")

# --- ヘルパー関数 ---

def parse_graphml_string(graphml_content: str) -> nx.Graph:
    """GraphML文字列をパースしてNetworkXグラフを返す"""
    try:
        content_io = io.BytesIO(graphml_content.encode('utf-8'))
        G = nx.read_graphml(content_io)
        return G
    except Exception as e:
        logger.error(f"Error parsing GraphML string: {e}")
        raise HTTPException(status_code=400, detail=f"Invalid GraphML content: {str(e)}")

def graph_to_cytoscape(G: nx.Graph, positions: Optional[Dict] = None) -> Dict[str, Any]:
    """NetworkXグラフをCytoscape.jsが期待するJSON形式に変換する"""
    nodes = []
    for node, attrs in G.nodes(data=True):
        node_data = {"data": {"id": str(node), "label": attrs.get("name", str(node)), **attrs}}
        if positions and str(node) in positions:
            node_data["position"] = positions[str(node)]
        nodes.append(node_data)

    edges = [
        {"data": {"source": str(u), "target": str(v), **attrs}}
        for u, v, attrs in G.edges(data=True)
    ]
    return {"nodes": nodes, "edges": edges}

def apply_layout(G: nx.Graph, layout_type: str, **kwargs) -> Dict:
    """レイアウトアルゴリズムを適用し、ノードの位置を返す"""
    layout_functions = {
        "spring": nx.spring_layout,
        "circular": nx.circular_layout,
        "random": nx.random_layout,
        "spectral": nx.spectral_layout,
        "shell": nx.shell_layout,
        "kamada_kawai": nx.kamada_kawai_layout,
        "fruchterman_reingold": nx.fruchterman_reingold_layout
    }
    layout_func = layout_functions.get(layout_type, nx.spring_layout)
    positions = layout_func(G, **kwargs)
    # JSONシリアライズ可能な形式に変換
    return {str(k): {"x": float(v[0]), "y": float(v[1])} for k, v in positions.items()}

def calculate_centrality(G: nx.Graph, centrality_type: str, **kwargs) -> Dict:
    """中心性指標を計算する"""
    centrality_functions = {
        "degree": nx.degree_centrality,
        "closeness": nx.closeness_centrality,
        "betweenness": nx.betweenness_centrality,
        "eigenvector": nx.eigenvector_centrality_numpy,
        "pagerank": nx.pagerank
    }
    centrality_func = centrality_functions.get(centrality_type, nx.degree_centrality)
    values = centrality_func(G, **kwargs)
    return {str(k): float(v) for k, v in values.items()}


# --- APIエンドポイント ---

@app.get("/health")
async def health_check():
    return {"status": "ok", "timestamp": datetime.now().isoformat()}

@app.get("/info")
async def get_mcp_info():
    """MCPサーバーの情報を返す"""
    return {
        "success": True,
        "name": "NetworkX MCP (Stateless)",
        "version": "0.2.0",
        "description": "Stateless NetworkX graph analysis and visualization MCP server",
        "tools": [
            {"name": "get_sample_network", "description": "Get a sample network in GraphML format"},
            {"name": "change_layout", "description": "Change the layout algorithm for a given network"},
            {"name": "calculate_centrality", "description": "Calculate centrality metrics for a given network"}
        ]
    }

@app.get("/get_sample_network", response_model=Dict[str, Any])
async def get_sample_network():
    """サンプルネットワークを生成し、GraphML形式で返す"""
    try:
        num_nodes = random.randint(18, 25)
        edge_probability = random.uniform(0.15, 0.25)
        G = nx.gnp_random_graph(num_nodes, edge_probability)
        
        if not nx.is_connected(G):
            components = list(nx.connected_components(G))
            largest_component = max(components, key=len)
            for component in components:
                if component != largest_component:
                    node_from = random.choice(list(component))
                    node_to = random.choice(list(largest_component))
                    G.add_edge(node_from, node_to)

        # GraphMLとして出力
        output = io.BytesIO()
        nx.write_graphml(G, output)
        output.seek(0)
        graphml_content = output.read().decode("utf-8")
        
        return {
            "success": True,
            "graphml_content": graphml_content
        }
    except Exception as e:
        logger.error(f"Error creating sample network: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/tools/change_layout", response_model=Dict[str, Any])
async def api_change_layout(params: LayoutParams):
    """
    与えられたネットワークのレイアウトを計算し、ノードの位置を返す
    """
    try:
        G = parse_graphml_string(params.graphml_content)
        positions = apply_layout(G, params.layout_type, **params.layout_params)
        return {
            "result": {
                "success": True,
                "layout": params.layout_type,
                "positions": positions
            }
        }
    except Exception as e:
        logger.error(f"Error changing layout: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/tools/calculate_centrality", response_model=Dict[str, Any])
async def api_calculate_centrality(params: CentralityParams):
    """
    与えられたネットワークの中心性を計算し、各ノードの値を返す
    """
    try:
        G = parse_graphml_string(params.graphml_content)
        centrality_values = calculate_centrality(G, params.centrality_type, **params.centrality_params)
        return {
            "result": {
                "success": True,
                "centrality_type": params.centrality_type,
                "centrality_values": centrality_values
            }
        }
    except Exception as e:
        logger.error(f"Error calculating centrality: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
