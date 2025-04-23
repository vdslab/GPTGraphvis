from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Optional, Any
import networkx as nx
import numpy as np

app = FastAPI()

class Node(BaseModel):
    id: str
    label: Optional[str] = None

class Edge(BaseModel):
    source: str
    target: str

class NetworkRequest(BaseModel):
    nodes: List[Node]
    edges: List[Edge]
    layout: str = "spring"  # spring, circular, random, spectral

class NodePosition(BaseModel):
    id: str
    x: float
    y: float
    label: Optional[str] = None

class NetworkResponse(BaseModel):
    nodes: List[NodePosition]
    edges: List[Edge]

def apply_layout(G: nx.Graph, layout_type: str) -> Dict[Any, np.ndarray]:
    if layout_type == "spring":
        return nx.spring_layout(G)
    elif layout_type == "circular":
        return nx.circular_layout(G)
    elif layout_type == "random":
        return nx.random_layout(G)
    elif layout_type == "spectral":
        return nx.spectral_layout(G)
    else:
        raise ValueError(f"Unsupported layout type: {layout_type}")

@app.post("/network/layout", response_model=NetworkResponse)
async def calculate_layout(request: NetworkRequest):
    try:
        # Create NetworkX graph
        G = nx.Graph()
        
        # Add nodes
        for node in request.nodes:
            G.add_node(node.id, label=node.label)
            
        # Add edges
        for edge in request.edges:
            G.add_edge(edge.source, edge.target)
            
        # Calculate layout
        pos = apply_layout(G, request.layout)
        
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
        
        return NetworkResponse(
            nodes=nodes_with_positions,
            edges=request.edges
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
async def root():
    return {"message": "Network Layout API is running"}
