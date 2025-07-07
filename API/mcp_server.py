"""
MCP (Model Context Protocol) server for network visualization.
This server provides tools for manipulating network graphs and visualization parameters.
"""

from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any, Union
import networkx as nx
import json
import os
from contextlib import asynccontextmanager

# Import local modules
import models
import auth
from database import get_db

# Define MCP models
class MCPToolRequest(BaseModel):
    arguments: Dict[str, Any]

class MCPToolResponse(BaseModel):
    result: Dict[str, Any]

class MCPError(BaseModel):
    error: str
    details: Optional[Dict[str, Any]] = None

# Network data models
class Node(BaseModel):
    id: str
    label: Optional[str] = None
    size: Optional[float] = None
    color: Optional[str] = None
    x: Optional[float] = None
    y: Optional[float] = None
    attributes: Optional[Dict[str, Any]] = None

class Edge(BaseModel):
    source: str
    target: str
    width: Optional[float] = None
    color: Optional[str] = None
    attributes: Optional[Dict[str, Any]] = None

class NetworkData(BaseModel):
    nodes: List[Node]
    edges: List[Edge]

# Global state for network data
# In a production environment, this would be stored in a database
network_state = {
    "graph": None,  # NetworkX graph object
    "layout": "spring",  # Current layout algorithm
    "layout_params": {},  # Parameters for the layout algorithm
    "positions": [],  # Node positions
    "centrality": None,  # Current centrality metric
    "centrality_values": {},  # Centrality values for nodes
    "visual_properties": {
        "node_size": 5,
        "node_color": "#1d4ed8",
        "edge_width": 1,
        "edge_color": "#94a3b8"
    }
}

# Initialize with a sample network
def initialize_sample_network():
    """Initialize the network state with a sample network (Zachary's Karate Club)."""
    G = nx.karate_club_graph()
    network_state["graph"] = G
    
    # Calculate initial positions
    pos = nx.spring_layout(G)
    
    # Convert to the expected format
    network_state["positions"] = [
        Node(
            id=str(node),
            label=f"Node {node}",
            x=float(pos[node][0]),
            y=float(pos[node][1]),
            size=5,
            color="#1d4ed8"
        )
        for node in G.nodes()
    ]
    
    # Store edges
    network_state["edges"] = [
        Edge(
            source=str(source),
            target=str(target),
            width=1,
            color="#94a3b8"
        )
        for source, target in G.edges()
    ]

# Initialize the network on startup
initialize_sample_network()

# Layout functions
def apply_layout(G: nx.Graph, layout_type: str, **kwargs) -> Dict[Any, tuple]:
    """
    Apply a layout algorithm to the graph.
    
    Args:
        G: NetworkX graph
        layout_type: Type of layout algorithm
        **kwargs: Additional parameters for the layout algorithm
        
    Returns:
        Dictionary mapping node IDs to positions
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
    
    # Planar layout only available for planar graphs
    if layout_type == "planar" and nx.is_planar(G):
        return nx.planar_layout(G, **kwargs)
    
    if layout_type in layout_functions:
        return layout_functions[layout_type](G, **kwargs)
    else:
        raise ValueError(f"Unsupported layout type: {layout_type}. Supported types: {', '.join(layout_functions.keys())}")

# Centrality functions
def calculate_centrality(G: nx.Graph, centrality_type: str) -> Dict[str, float]:
    """
    Calculate centrality metrics for nodes in the graph.
    
    Args:
        G: NetworkX graph
        centrality_type: Type of centrality to calculate
        
    Returns:
        Dictionary mapping node IDs to centrality values
    """
    centrality_functions = {
        "degree": nx.degree_centrality,
        "closeness": nx.closeness_centrality,
        "betweenness": nx.betweenness_centrality,
        "eigenvector": nx.eigenvector_centrality,
        "pagerank": nx.pagerank
    }
    
    if centrality_type in centrality_functions:
        return centrality_functions[centrality_type](G)
    else:
        raise ValueError(f"Unsupported centrality type: {centrality_type}. Supported types: {', '.join(centrality_functions.keys())}")

# MCP Tool implementations
async def change_layout(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """
    Change the layout algorithm for the network visualization.
    
    Args:
        layout_type: Type of layout algorithm
        layout_params: Parameters for the layout algorithm
        
    Returns:
        Updated network positions
    """
    try:
        layout_type = arguments.get("layout_type", "spring")
        layout_params = arguments.get("layout_params", {})
        
        # Update network state
        network_state["layout"] = layout_type
        network_state["layout_params"] = layout_params
        
        # Apply layout
        G = network_state["graph"]
        pos = apply_layout(G, layout_type, **layout_params)
        
        # Update positions
        for node in network_state["positions"]:
            node_id = int(node.id)
            if node_id in pos:
                node.x = float(pos[node_id][0])
                node.y = float(pos[node_id][1])
        
        return {
            "success": True,
            "layout": layout_type,
            "layout_params": layout_params,
            "positions": [
                {
                    "id": node.id,
                    "x": node.x,
                    "y": node.y
                }
                for node in network_state["positions"]
            ]
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

async def calculate_node_centrality(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculate centrality metrics for nodes in the graph.
    
    Args:
        centrality_type: Type of centrality to calculate
        
    Returns:
        Centrality values for nodes
    """
    try:
        centrality_type = arguments.get("centrality_type", "degree")
        
        # Update network state
        network_state["centrality"] = centrality_type
        
        # Calculate centrality
        G = network_state["graph"]
        centrality_values = calculate_centrality(G, centrality_type)
        
        # Convert node IDs to strings
        centrality_values = {str(node): value for node, value in centrality_values.items()}
        
        # Store centrality values
        network_state["centrality_values"] = centrality_values
        
        return {
            "success": True,
            "centrality_type": centrality_type,
            "centrality_values": centrality_values
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

async def highlight_nodes(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """
    Highlight specific nodes in the network.
    
    Args:
        node_ids: List of node IDs to highlight
        highlight_color: Color to use for highlighting
        
    Returns:
        Updated node colors
    """
    try:
        node_ids = arguments.get("node_ids", [])
        highlight_color = arguments.get("highlight_color", "#ff0000")
        
        # Convert node IDs to strings
        node_ids = [str(node_id) for node_id in node_ids]
        
        # Update node colors
        for node in network_state["positions"]:
            if node.id in node_ids:
                node.color = highlight_color
            else:
                node.color = network_state["visual_properties"]["node_color"]
        
        return {
            "success": True,
            "highlighted_nodes": node_ids,
            "highlight_color": highlight_color
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

async def change_visual_properties(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """
    Change visual properties of nodes or edges.
    
    Args:
        property_type: Type of property to change (node_size, node_color, edge_width, edge_color)
        property_value: Value to set for the property
        property_mapping: Optional mapping of node/edge IDs to property values
        
    Returns:
        Updated visual properties
    """
    try:
        property_type = arguments.get("property_type", "")
        property_value = arguments.get("property_value", "")
        property_mapping = arguments.get("property_mapping", {})
        
        if not property_type or property_type not in ["node_size", "node_color", "edge_width", "edge_color"]:
            return {
                "success": False,
                "error": f"Invalid property type: {property_type}"
            }
        
        # Update global property
        network_state["visual_properties"][property_type] = property_value
        
        # Apply property to nodes or edges
        if property_type.startswith("node_"):
            attribute = property_type.split("_")[1]  # "size" or "color"
            for node in network_state["positions"]:
                if node.id in property_mapping:
                    setattr(node, attribute, property_mapping[node.id])
                else:
                    setattr(node, attribute, property_value)
        else:  # edge property
            attribute = property_type.split("_")[1]  # "width" or "color"
            for edge in network_state["edges"]:
                edge_key = f"{edge.source}-{edge.target}"
                if edge_key in property_mapping:
                    setattr(edge, attribute, property_mapping[edge_key])
                else:
                    setattr(edge, attribute, property_value)
        
        return {
            "success": True,
            "property_type": property_type,
            "property_value": property_value,
            "property_mapping": property_mapping
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

async def get_network_info(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """
    Get information about the current network.
    
    Returns:
        Network information including number of nodes, edges, density, etc.
    """
    try:
        G = network_state["graph"]
        
        # Calculate basic network metrics
        num_nodes = G.number_of_nodes()
        num_edges = G.number_of_edges()
        density = nx.density(G)
        
        # Calculate connected components
        is_connected = nx.is_connected(G)
        num_components = nx.number_connected_components(G) if not is_connected else 1
        
        # Calculate average degree
        degrees = [d for _, d in G.degree()]
        avg_degree = sum(degrees) / len(degrees) if degrees else 0
        
        # Calculate clustering coefficient
        clustering = nx.average_clustering(G)
        
        return {
            "success": True,
            "network_info": {
                "num_nodes": num_nodes,
                "num_edges": num_edges,
                "density": density,
                "is_connected": is_connected,
                "num_components": num_components,
                "avg_degree": avg_degree,
                "clustering_coefficient": clustering,
                "current_layout": network_state["layout"],
                "current_centrality": network_state["centrality"]
            }
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

async def get_node_info(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """
    Get information about specific nodes in the network.
    
    Args:
        node_ids: List of node IDs to get information for
        
    Returns:
        Node information including degree, centrality, etc.
    """
    try:
        node_ids = arguments.get("node_ids", [])
        
        # Convert node IDs to integers for NetworkX
        node_ids_int = [int(node_id) for node_id in node_ids]
        
        G = network_state["graph"]
        
        # Get node information
        node_info = {}
        for node_id in node_ids_int:
            if node_id in G:
                # Get degree
                degree = G.degree(node_id)
                
                # Get neighbors
                neighbors = list(G.neighbors(node_id))
                
                # Get centrality values if available
                centrality_value = None
                if network_state["centrality_values"] and str(node_id) in network_state["centrality_values"]:
                    centrality_value = network_state["centrality_values"][str(node_id)]
                
                node_info[str(node_id)] = {
                    "degree": degree,
                    "neighbors": [str(n) for n in neighbors],
                    "centrality": {
                        "type": network_state["centrality"],
                        "value": centrality_value
                    } if centrality_value is not None else None
                }
        
        return {
            "success": True,
            "node_info": node_info
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

# Map of tool names to their implementations
mcp_tools = {
    "change_layout": change_layout,
    "calculate_centrality": calculate_node_centrality,
    "highlight_nodes": highlight_nodes,
    "change_visual_properties": change_visual_properties,
    "get_network_info": get_network_info,
    "get_node_info": get_node_info
}

# MCP server FastAPI app
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize the network
    initialize_sample_network()
    yield
    # Shutdown: Clean up resources if needed
    pass

app = FastAPI(lifespan=lifespan)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict this to your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/mcp/tools/{tool_name}")
async def execute_tool(
    tool_name: str,
    request: MCPToolRequest,
    current_user: models.User = Depends(auth.get_current_active_user)
):
    """
    Execute an MCP tool.
    
    Args:
        tool_name: Name of the tool to execute
        request: Tool request with arguments
        
    Returns:
        Tool response with result
    """
    if tool_name not in mcp_tools:
        raise HTTPException(status_code=404, detail=f"Tool '{tool_name}' not found")
    
    try:
        result = await mcp_tools[tool_name](request.arguments)
        return MCPToolResponse(result=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/mcp/resources/network")
async def get_network_resource(
    current_user: models.User = Depends(auth.get_current_active_user)
):
    """
    Get the current network as an MCP resource.
    
    Returns:
        Network data including nodes and edges
    """
    try:
        return {
            "nodes": [node.dict() for node in network_state["positions"]],
            "edges": [edge.dict() for edge in network_state["edges"]],
            "layout": network_state["layout"],
            "layout_params": network_state["layout_params"],
            "centrality": network_state["centrality"],
            "visual_properties": network_state["visual_properties"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/mcp/manifest")
async def get_manifest():
    """
    Get the MCP server manifest.
    
    Returns:
        MCP server manifest with available tools and resources
    """
    return {
        "name": "network-visualization-mcp",
        "version": "1.0.0",
        "description": "MCP server for network visualization",
        "tools": [
            {
                "name": "change_layout",
                "description": "Change the layout algorithm for the network visualization",
                "parameters": {
                    "layout_type": {
                        "type": "string",
                        "description": "Type of layout algorithm",
                        "enum": [
                            "spring", "circular", "random", "spectral", "shell", 
                            "spiral", "kamada_kawai", "fruchterman_reingold", 
                            "bipartite", "multipartite", "planar"
                        ]
                    },
                    "layout_params": {
                        "type": "object",
                        "description": "Parameters for the layout algorithm"
                    }
                },
                "required": ["layout_type"]
            },
            {
                "name": "calculate_centrality",
                "description": "Calculate centrality metrics for nodes in the graph",
                "parameters": {
                    "centrality_type": {
                        "type": "string",
                        "description": "Type of centrality to calculate",
                        "enum": ["degree", "closeness", "betweenness", "eigenvector", "pagerank"]
                    }
                },
                "required": ["centrality_type"]
            },
            {
                "name": "highlight_nodes",
                "description": "Highlight specific nodes in the network",
                "parameters": {
                    "node_ids": {
                        "type": "array",
                        "description": "List of node IDs to highlight",
                        "items": {
                            "type": "string"
                        }
                    },
                    "highlight_color": {
                        "type": "string",
                        "description": "Color to use for highlighting"
                    }
                },
                "required": ["node_ids"]
            },
            {
                "name": "change_visual_properties",
                "description": "Change visual properties of nodes or edges",
                "parameters": {
                    "property_type": {
                        "type": "string",
                        "description": "Type of property to change",
                        "enum": ["node_size", "node_color", "edge_width", "edge_color"]
                    },
                    "property_value": {
                        "type": "string",
                        "description": "Value to set for the property"
                    },
                    "property_mapping": {
                        "type": "object",
                        "description": "Optional mapping of node/edge IDs to property values"
                    }
                },
                "required": ["property_type", "property_value"]
            },
            {
                "name": "get_network_info",
                "description": "Get information about the current network",
                "parameters": {}
            },
            {
                "name": "get_node_info",
                "description": "Get information about specific nodes in the network",
                "parameters": {
                    "node_ids": {
                        "type": "array",
                        "description": "List of node IDs to get information for",
                        "items": {
                            "type": "string"
                        }
                    }
                },
                "required": ["node_ids"]
            }
        ],
        "resources": [
            {
                "name": "network",
                "description": "Current network data including nodes and edges",
                "uri": "/mcp/resources/network"
            }
        ]
    }
