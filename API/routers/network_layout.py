from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List, Dict, Optional, Any
import networkx as nx
import numpy as np
from pydantic import BaseModel

import models, auth
from database import get_db

router = APIRouter(
    prefix="/network-layout",
    tags=["network-layout"],
    responses={401: {"description": "Unauthorized"}},
)

# Pydantic models for request and response
class Node(BaseModel):
    id: str
    label: Optional[str] = None

class Edge(BaseModel):
    source: str
    target: str

class LayoutRequest(BaseModel):
    nodes: List[Node]
    edges: List[Edge]
    layout: str = "spring"  # デフォルトのレイアウトアルゴリズム
    layout_params: Optional[Dict[str, Any]] = None  # レイアウトアルゴリズムのパラメータ

class NodePosition(BaseModel):
    id: str
    x: float
    y: float
    label: Optional[str] = None

class LayoutResponse(BaseModel):
    nodes: List[NodePosition]
    edges: List[Edge]

def apply_layout(G: nx.Graph, layout_type: str, **kwargs) -> Dict[Any, np.ndarray]:
    """
    指定されたレイアウトアルゴリズムを適用してノードの位置を計算します。
    
    Args:
        G: NetworkXグラフ
        layout_type: レイアウトアルゴリズムの名前
        **kwargs: レイアウトアルゴリズムに渡す追加パラメータ
        
    Returns:
        ノードIDをキー、位置座標を値とする辞書
    """
    layout_functions = {
        "spring": nx.spring_layout,
        "circular": nx.circular_layout,
        "random": nx.random_layout,
        "spectral": nx.spectral_layout,
        "shell": nx.shell_layout,
        "spiral": nx.spiral_layout,
        "kamada_kawai": nx.kamada_kawai_layout,
        "fruchterman_reingold": nx.fruchterman_reingold_layout,
        "bipartite": nx.bipartite_layout,
        "multipartite": nx.multipartite_layout
    }
    
    # 平面グラフの場合のみ使用可能
    if layout_type == "planar" and nx.is_planar(G):
        return nx.planar_layout(G, **kwargs)
    
    if layout_type in layout_functions:
        return layout_functions[layout_type](G, **kwargs)
    else:
        raise ValueError(f"Unsupported layout type: {layout_type}. Supported types: {', '.join(layout_functions.keys())}")

@router.post("/apply", response_model=LayoutResponse)
async def calculate_layout(
    request: LayoutRequest,
    current_user: models.User = Depends(auth.get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    ネットワークデータにレイアウトアルゴリズムを適用し、ノードの位置を計算します。
    
    Args:
        request: ノード、エッジ、レイアウトタイプ、レイアウトパラメータを含むリクエスト
        
    Returns:
        位置情報が追加されたノードとエッジを含むレスポンス
    """
    try:
        # Create NetworkX graph
        G = nx.Graph()
        
        # Add nodes
        for node in request.nodes:
            G.add_node(node.id, label=node.label)
            
        # Add edges
        for edge in request.edges:
            G.add_edge(edge.source, edge.target)
            
        # Calculate layout with parameters if provided
        layout_params = request.layout_params or {}
        pos = apply_layout(G, request.layout, **layout_params)
        
        # Prepare response
        nodes_with_positions = [
            NodePosition(
                id=node_id,
                x=float(coords[0]),  # Convert numpy float to Python float
                y=float(coords[1]),
                label=G.nodes[node_id].get("label")
            )
            for node_id, coords in pos.items()
        ]
        
        return LayoutResponse(
            nodes=nodes_with_positions,
            edges=request.edges
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
