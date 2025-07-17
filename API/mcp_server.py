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
import io
import re
from contextlib import asynccontextmanager

# Import local modules
import models
from database import get_db
import auth

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

# User network storage
# In a production environment, this would be stored in a database
user_networks = {}  # user_id -> {network_name -> network_data}

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

# Create FastAPI app
app = FastAPI()

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
async def update_network(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """
    Update the network data in the MCP server.
    
    Args:
        nodes: List of nodes
        edges: List of edges
        
    Returns:
        Success status
    """
    try:
        nodes = arguments.get("nodes", [])
        edges = arguments.get("edges", [])
        
        if not nodes or not edges:
            return {
                "success": False,
                "error": "No nodes or edges provided"
            }
        
        print(f"Updating network with {len(nodes)} nodes and {len(edges)} edges")
        
        # Create a new NetworkX graph
        G = nx.Graph()
        
        # Add nodes
        for node in nodes:
            G.add_node(node["id"], label=node.get("label", node["id"]))
        
        # Add edges
        for edge in edges:
            G.add_edge(edge["source"], edge["target"])
        
        # Update network state
        network_state["graph"] = G
        
        # Update positions and edges
        network_state["positions"] = [
            Node(
                id=node["id"],
                label=node.get("label", node["id"]),
                x=node.get("x", 0),
                y=node.get("y", 0),
                size=node.get("size", 5),
                color=node.get("color", "#1d4ed8")
            )
            for node in nodes
        ]
        
        network_state["edges"] = [
            Edge(
                source=edge["source"],
                target=edge["target"],
                width=edge.get("width", 1),
                color=edge.get("color", "#94a3b8")
            )
            for edge in edges
        ]
        
        # Apply default layout if positions are not provided
        if not all(node.get("x") is not None and node.get("y") is not None for node in nodes):
            print("Positions not provided, applying default layout")
            pos = nx.spring_layout(G)
            
            # Update positions
            for i, node in enumerate(network_state["positions"]):
                node_id = node.id
                if node_id in pos:
                    node.x = float(pos[node_id][0])
                    node.y = float(pos[node_id][1])
        
        return {
            "success": True,
            "nodes_count": len(nodes),
            "edges_count": len(edges)
        }
    except Exception as e:
        print(f"Error updating network: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            "success": False,
            "error": str(e)
        }

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

# Define MCP tools
mcp_tools = {
    "update_network": update_network,
    "change_layout": change_layout,
    "calculate_centrality": calculate_centrality,
    "highlight_nodes": highlight_nodes,
    "change_visual_properties": change_visual_properties,
    "get_network_info": get_network_info,
    "get_node_info": get_node_info,
    "save_network": save_network,
    "load_network": load_network,
    "list_user_networks": list_user_networks,
    "apply_community_layout": apply_community_layout,
    "compare_layouts": compare_layouts,
    "get_sample_network": get_sample_network,
    "recommend_layout": recommend_layout,
    "process_chat_message": process_chat_message
}

async def calculate_centrality(arguments: Dict[str, Any]) -> Dict[str, Any]:
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

async def save_network(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """
    Save the current network data for a user.
    
    Args:
        user_id: ID of the user
        network_name: Name to save the network as
        
    Returns:
        Success status and message
    """
    try:
        user_id = arguments.get("user_id")
        network_name = arguments.get("network_name", "default")
        
        if not user_id:
            return {
                "success": False,
                "error": "User ID is required"
            }
        
        # Create network data to save
        network_data = {
            "nodes": [node.dict() for node in network_state["positions"]],
            "edges": [edge.dict() for edge in network_state["edges"]],
            "layout": network_state["layout"],
            "layout_params": network_state["layout_params"],
            "centrality": network_state["centrality"],
            "visual_properties": network_state["visual_properties"]
        }
        
        # Initialize user's networks if not exists
        if user_id not in user_networks:
            user_networks[user_id] = {}
        
        # Save network data
        user_networks[user_id][network_name] = network_data
        
        return {
            "success": True,
            "message": f"Network saved as '{network_name}' for user {user_id}",
            "user_id": user_id,
            "network_name": network_name
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

async def load_network(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """
    Load a saved network for a user.
    
    Args:
        user_id: ID of the user
        network_name: Name of the network to load
        
    Returns:
        Loaded network data
    """
    try:
        user_id = arguments.get("user_id")
        network_name = arguments.get("network_name", "default")
        
        if not user_id:
            return {
                "success": False,
                "error": "User ID is required"
            }
        
        # Check if user has saved networks
        if user_id not in user_networks:
            return {
                "success": False,
                "error": f"No networks found for user {user_id}"
            }
        
        # Check if network exists
        if network_name not in user_networks[user_id]:
            return {
                "success": False,
                "error": f"Network '{network_name}' not found for user {user_id}"
            }
        
        # Get network data
        network_data = user_networks[user_id][network_name]
        
        # Update network state
        nodes_data = network_data["nodes"]
        edges_data = network_data["edges"]
        
        # Create a new NetworkX graph
        G = nx.Graph()
        
        # Add nodes
        for node in nodes_data:
            G.add_node(node["id"], label=node.get("label", node["id"]))
        
        # Add edges
        for edge in edges_data:
            G.add_edge(edge["source"], edge["target"])
        
        # Update network state
        network_state["graph"] = G
        network_state["positions"] = [
            Node(
                id=node["id"],
                label=node.get("label", node["id"]),
                x=node.get("x", 0),
                y=node.get("y", 0),
                size=node.get("size", 5),
                color=node.get("color", "#1d4ed8")
            )
            for node in nodes_data
        ]
        network_state["edges"] = [
            Edge(
                source=edge["source"],
                target=edge["target"],
                width=edge.get("width", 1),
                color=edge.get("color", "#94a3b8")
            )
            for edge in edges_data
        ]
        network_state["layout"] = network_data["layout"]
        network_state["layout_params"] = network_data["layout_params"]
        network_state["centrality"] = network_data["centrality"]
        network_state["visual_properties"] = network_data["visual_properties"]
        
        return {
            "success": True,
            "message": f"Network '{network_name}' loaded for user {user_id}",
            "network_data": network_data
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

async def list_user_networks(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """
    List all saved networks for a user.
    
    Args:
        user_id: ID of the user
        
    Returns:
        List of network names
    """
    try:
        user_id = arguments.get("user_id")
        
        if not user_id:
            return {
                "success": False,
                "error": "User ID is required"
            }
        
        # Check if user has saved networks
        if user_id not in user_networks:
            return {
                "success": True,
                "networks": []
            }
        
        # Get network names
        network_names = list(user_networks[user_id].keys())
        
        return {
            "success": True,
            "networks": network_names
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

async def apply_community_layout(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """
    Apply a layout algorithm based on community detection.
    
    Args:
        algorithm: Community detection algorithm to use
        layout_params: Parameters for the layout algorithm
        
    Returns:
        Updated network positions
    """
    try:
        algorithm = arguments.get("algorithm", "louvain")
        layout_params = arguments.get("layout_params", {})
        
        G = network_state["graph"]
        
        if not G:
            return {
                "success": False,
                "error": "No network data available"
            }
        
        # Detect communities
        communities = None
        if algorithm == "louvain":
            try:
                import community as community_louvain
                partition = community_louvain.best_partition(G)
                # Group nodes by community
                community_dict = {}
                for node, community_id in partition.items():
                    if community_id not in community_dict:
                        community_dict[community_id] = []
                    community_dict[community_id].append(node)
                communities = list(community_dict.values())
            except ImportError:
                # Fallback to networkx community detection
                communities = list(nx.community.greedy_modularity_communities(G))
        else:
            # Use networkx community detection
            communities = list(nx.community.greedy_modularity_communities(G))
        
        # Create a new graph with communities as nodes
        community_graph = nx.Graph()
        for i, community in enumerate(communities):
            community_graph.add_node(i, size=len(community))
        
        # Add edges between communities
        for i, comm1 in enumerate(communities):
            for j, comm2 in enumerate(communities):
                if i < j:  # Avoid duplicate edges
                    # Count edges between communities
                    edge_count = 0
                    for node1 in comm1:
                        for node2 in comm2:
                            if G.has_edge(node1, node2):
                                edge_count += 1
                    
                    if edge_count > 0:
                        community_graph.add_edge(i, j, weight=edge_count)
        
        # Apply layout to community graph
        scale = layout_params.get("scale", 1.0)
        community_pos = nx.spring_layout(community_graph, weight='weight', scale=scale)
        
        # Position nodes within their communities
        pos = {}
        for i, community in enumerate(communities):
            # Get the center of the community
            center = community_pos[i]
            
            # Create a subgraph for the community
            subgraph = G.subgraph(community)
            
            # Apply layout to the subgraph
            sub_pos = nx.spring_layout(subgraph, scale=0.3)
            
            # Adjust positions relative to community center
            for node, coords in sub_pos.items():
                pos[node] = (center[0] + coords[0], center[1] + coords[1])
        
        # Update positions
        for node in network_state["positions"]:
            node_id = node.id
            if node_id in pos:
                node.x = float(pos[node_id][0])
                node.y = float(pos[node_id][1])
        
        # Update network state
        network_state["layout"] = "community"
        network_state["layout_params"] = {
            "algorithm": algorithm,
            **layout_params
        }
        
        return {
            "success": True,
            "layout": "community",
            "layout_params": {
                "algorithm": algorithm,
                **layout_params
            },
            "communities": [list(c) for c in communities],
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

async def compare_layouts(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """
    Compare different layout algorithms for the current network.
    
    Args:
        layouts: List of layout algorithms to compare
        
    Returns:
        Positions for each layout algorithm
    """
    try:
        layouts = arguments.get("layouts", ["spring", "circular", "kamada_kawai"])
        
        G = network_state["graph"]
        
        if not G:
            return {
                "success": False,
                "error": "No network data available"
            }
        
        # Calculate positions for each layout
        layout_positions = {}
        for layout_type in layouts:
            try:
                pos = apply_layout(G, layout_type)
                layout_positions[layout_type] = {
                    node_id: [float(coords[0]), float(coords[1])]
                    for node_id, coords in pos.items()
                }
            except Exception as layout_error:
                print(f"Error calculating {layout_type} layout: {str(layout_error)}")
                layout_positions[layout_type] = {"error": str(layout_error)}
        
        return {
            "success": True,
            "layouts": layouts,
            "positions": layout_positions
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

# Process chat message
async def process_chat_message(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process a chat message and execute network operations.
    
    Args:
        message: The chat message to process
        
    Returns:
        Response with executed operation result
    """
    try:
        message = arguments.get("message", "")
        
        if not message:
            return {
                "success": False,
                "error": "No message provided"
            }
        
        # Convert message to lowercase for easier matching
        message_lower = message.lower()
        
        # Define patterns for different operations
        layout_patterns = {
            "spring": r'\b(spring|スプリング)\b',
            "circular": r'\b(circular|円形|サークル)\b',
            "random": r'\b(random|ランダム)\b',
            "spectral": r'\b(spectral|スペクトル)\b',
            "shell": r'\b(shell|シェル)\b',
            "kamada_kawai": r'\b(kamada|kawai|カマダ|カワイ)\b',
            "fruchterman_reingold": r'\b(fruchterman|reingold|フルクターマン|レインゴールド)\b'
        }
        
        centrality_patterns = {
            "degree": r'\b(degree|次数|ディグリー)\b',
            "closeness": r'\b(closeness|近接|クローズネス)\b',
            "betweenness": r'\b(betweenness|媒介|ビトウィーンネス)\b',
            "eigenvector": r'\b(eigenvector|固有ベクトル|アイゲンベクトル)\b',
            "pagerank": r'\b(pagerank|ページランク)\b'
        }
        
        color_patterns = {
            "red": r'\b(red|赤|レッド)\b',
            "blue": r'\b(blue|青|ブルー)\b',
            "green": r'\b(green|緑|グリーン)\b',
            "yellow": r'\b(yellow|黄|イエロー)\b',
            "purple": r'\b(purple|紫|パープル)\b',
            "orange": r'\b(orange|オレンジ)\b',
            "black": r'\b(black|黒|ブラック)\b',
            "white": r'\b(white|白|ホワイト)\b'
        }
        
        color_map = {
            "red": "#ff0000",
            "blue": "#0000ff",
            "green": "#00ff00",
            "yellow": "#ffff00",
            "purple": "#800080",
            "orange": "#ffa500",
            "black": "#000000",
            "white": "#ffffff"
        }
        
        # Check for layout change requests
        if "layout" in message_lower or "レイアウト" in message_lower:
            # Check for layout recommendation request
            if any(keyword in message_lower for keyword in ["recommend", "suggestion", "おすすめ", "提案"]):
                try:
                    result = await recommend_layout({"question": message})
                    if result and result.get("success"):
                        # Apply the recommended layout
                        layout_type = result.get("recommended_layout")
                        layout_params = result.get("recommended_parameters", {})
                        
                        # Apply the layout
                        layout_result = await change_layout({
                            "layout_type": layout_type,
                            "layout_params": layout_params
                        })
                        
                        if layout_result and layout_result.get("success"):
                            return {
                                "success": True,
                                "content": f"Based on your request, I recommend using the {layout_type} layout. {result.get('recommendation_reason')} I've applied this layout to the network.",
                                "networkUpdate": {
                                    "type": "layout",
                                    "layout": layout_type,
                                    "layoutParams": layout_params
                                }
                            }
                        else:
                            return {
                                "success": False,
                                "content": f"I recommend using the {layout_type} layout, but I couldn't apply it. Please try again later."
                            }
                    else:
                        return {
                            "success": False,
                            "content": "I couldn't recommend a layout based on your request. Please try again with more specific details about what you want to visualize."
                        }
                except Exception as e:
                    print(f"Error recommending layout: {str(e)}")
                    return {
                        "success": False,
                        "content": "I'm sorry, I encountered an error trying to recommend a layout. Please try again later."
                    }
            
            # Check for specific layout requests
            for layout_type, pattern in layout_patterns.items():
                if re.search(pattern, message_lower, re.IGNORECASE):
                    try:
                        result = await change_layout({
                            "layout_type": layout_type,
                            "layout_params": {}
                        })
                        
                        if result and result.get("success"):
                            return {
                                "success": True,
                                "content": f"I've changed the layout to {layout_type}. The network visualization has been updated.",
                                "networkUpdate": {
                                    "type": "layout",
                                    "layout": layout_type
                                }
                            }
                        else:
                            return {
                                "success": False,
                                "content": f"I couldn't apply the {layout_type} layout. Please try again later."
                            }
                    except Exception as e:
                        print(f"Error applying {layout_type} layout: {str(e)}")
                        return {
                            "success": False,
                            "content": f"I'm sorry, I encountered an error trying to apply the {layout_type} layout. Please try again later."
                        }
            
            # If no specific layout was mentioned but "layout" was
            return {
                "success": True,
                "content": "You can use the following layouts: Spring, Circular, Random, Spectral, Shell, Kamada-Kawai, and Fruchterman-Reingold. Just ask me to change to any of these layouts."
            }
        
        # Check for centrality requests
        if any(keyword in message_lower for keyword in ["centrality", "中心性", "センタリティ", "measure", "指標"]):
            for centrality_type, pattern in centrality_patterns.items():
                if re.search(pattern, message_lower, re.IGNORECASE):
                    try:
                        # Calculate centrality
                        centrality_result = await calculate_centrality({
                            "centrality_type": centrality_type
                        })
                        
                        if centrality_result and centrality_result.get("success"):
                            # Update node sizes and colors based on centrality
                            centrality_values = centrality_result.get("centrality_values", {})
                            
                            # Find max centrality value for normalization
                            max_value = max(centrality_values.values()) if centrality_values else 1.0
                            
                            # Create mapping of node IDs to sizes and colors
                            size_mapping = {}
                            color_mapping = {}
                            
                            for node_id, value in centrality_values.items():
                                # Scale size between 5 and 15
                                size_mapping[node_id] = 5 + (value / max_value) * 10
                                
                                # Generate color from blue (low) to red (high)
                                ratio = value / max_value
                                r = int(255 * ratio)
                                b = int(255 * (1 - ratio))
                                color_mapping[node_id] = f"rgb({r}, 70, {b})"
                            
                            # Apply size mapping
                            await change_visual_properties({
                                "property_type": "node_size",
                                "property_value": 5,  # Default size
                                "property_mapping": size_mapping
                            })
                            
                            # Apply color mapping
                            await change_visual_properties({
                                "property_type": "node_color",
                                "property_value": "#1d4ed8",  # Default color
                                "property_mapping": color_mapping
                            })
                            
                            return {
                                "success": True,
                                "content": f"I've applied {centrality_type} centrality to the network. Nodes are now sized and colored based on their {centrality_type} centrality values.",
                                "networkUpdate": {
                                    "type": "centrality",
                                    "centralityType": centrality_type
                                }
                            }
                        else:
                            return {
                                "success": False,
                                "content": f"I couldn't apply {centrality_type} centrality. Please try again later."
                            }
                    except Exception as e:
                        print(f"Error applying {centrality_type} centrality: {str(e)}")
                        return {
                            "success": False,
                            "content": f"I'm sorry, I encountered an error trying to apply {centrality_type} centrality. Please try again later."
                        }
            
            # If no specific centrality was mentioned but "centrality" was
            return {
                "success": True,
                "content": "You can apply the following centrality measures: Degree, Closeness, Betweenness, Eigenvector, and PageRank. Just ask me to apply any of these centrality measures."
            }
        
        # Check for color change requests
        if any(keyword in message_lower for keyword in ["color", "色", "カラー"]):
            # Check if it's for nodes or edges
            is_for_nodes = "node" in message_lower or "ノード" in message_lower or \
                          (not "edge" in message_lower and not "エッジ" in message_lower)
            
            target = "nodes" if is_for_nodes else "edges"
            property_type = "node_color" if is_for_nodes else "edge_color"
            
            # Check for specific colors
            for color_name, pattern in color_patterns.items():
                if re.search(pattern, message_lower, re.IGNORECASE):
                    try:
                        result = await change_visual_properties({
                            "property_type": property_type,
                            "property_value": color_map[color_name]
                        })
                        
                        if result and result.get("success"):
                            return {
                                "success": True,
                                "content": f"I've changed the color of the {target} to {color_name}.",
                                "networkUpdate": {
                                    "type": "visualProperty",
                                    "propertyType": property_type,
                                    "propertyValue": color_map[color_name]
                                }
                            }
                        else:
                            return {
                                "success": False,
                                "content": f"I couldn't change the color of the {target} to {color_name}. Please try again later."
                            }
                    except Exception as e:
                        print(f"Error changing {target} color to {color_name}: {str(e)}")
                        return {
                            "success": False,
                            "content": f"I'm sorry, I encountered an error trying to change the color of the {target} to {color_name}. Please try again later."
                        }
            
            # If no specific color was mentioned but "color" was
            return {
                "success": True,
                "content": f"You can change the color of {target} to: Red, Blue, Green, Yellow, Purple, Orange, Black, or White. Just ask me to change the color to any of these colors."
            }
        
        # Check for size change requests
        if any(keyword in message_lower for keyword in ["size", "サイズ", "大きさ", "太さ"]):
            # Check if it's for nodes or edges
            is_for_nodes = "node" in message_lower or "ノード" in message_lower or \
                          (not "edge" in message_lower and not "エッジ" in message_lower)
            
            target = "nodes" if is_for_nodes else "edges"
            property_type = "node_size" if is_for_nodes else "edge_width"
            
            # Check for increase or decrease
            is_increase = any(keyword in message_lower for keyword in ["increase", "larger", "bigger", "大きく", "太く"])
            is_decrease = any(keyword in message_lower for keyword in ["decrease", "smaller", "thinner", "小さく", "細く"])
            
            # Get current value
            current_value = network_state["visual_properties"][property_type]
            
            # Calculate new value
            new_value = current_value
            
            if is_increase:
                new_value = min(20 if is_for_nodes else 5, current_value * 1.5)
            elif is_decrease:
                new_value = max(2 if is_for_nodes else 0.5, current_value / 1.5)
            else:
                # Try to extract a specific size value
                size_match = re.search(r'\b(\d+(\.\d+)?)\b', message_lower)
                if size_match:
                    new_value = float(size_match.group(1))
                    # Ensure reasonable limits
                    if is_for_nodes:
                        new_value = max(2, min(20, new_value))
                    else:
                        new_value = max(0.5, min(5, new_value))
            
            # Only proceed if the value has changed
            if new_value != current_value:
                try:
                    result = await change_visual_properties({
                        "property_type": property_type,
                        "property_value": new_value
                    })
                    
                    if result and result.get("success"):
                        return {
                            "success": True,
                            "content": f"I've changed the size of the {target} to {new_value}.",
                            "networkUpdate": {
                                "type": "visualProperty",
                                "propertyType": property_type,
                                "propertyValue": new_value
                            }
                        }
                    else:
                        return {
                            "success": False,
                            "content": f"I couldn't change the size of the {target}. Please try again later."
                        }
                except Exception as e:
                    print(f"Error changing {target} size: {str(e)}")
                    return {
                        "success": False,
                        "content": f"I'm sorry, I encountered an error trying to change the size of the {target}. Please try again later."
                    }
            
            # If no specific size change was requested but "size" was mentioned
            return {
                "success": True,
                "content": f"You can ask me to increase or decrease the size of {target}, or specify a specific size value."
            }
        
        # Check for network information request
        if any(keyword in message_lower for keyword in ["info", "information", "statistics", "stats", "情報", "統計"]):
            try:
                result = await get_network_info({})
                
                if result and result.get("success"):
                    info = result.get("network_info", {})
                    return {
                        "success": True,
                        "content": f"""Network Information:
- Nodes: {info.get('num_nodes')}
- Edges: {info.get('num_edges')}
- Density: {info.get('density', 0):.4f}
- Connected: {'Yes' if info.get('is_connected') else 'No'}
- Components: {info.get('num_components')}
- Average Degree: {info.get('avg_degree', 0):.2f}
- Clustering Coefficient: {info.get('clustering_coefficient', 0):.4f}
- Current Layout: {info.get('current_layout')}
- Current Centrality: {info.get('current_centrality') or 'None'}"""
                    }
                else:
                    return {
                        "success": False,
                        "content": "I couldn't retrieve network information. Please try again later."
                    }
            except Exception as e:
                print(f"Error getting network information: {str(e)}")
                return {
                    "success": False,
                    "content": "I'm sorry, I encountered an error trying to retrieve network information. Please try again later."
                }
        
        # Check for help request
        if any(keyword in message_lower for keyword in ["help", "ヘルプ", "使い方", "how to"]):
            return {
                "success": True,
                "content": """Here are the operations you can perform via chat:

1. Change layout: "Use circular layout" or "Apply Fruchterman-Reingold layout"
2. Get layout recommendation: "Recommend a layout for community detection"
3. Apply centrality: "Show degree centrality" or "Apply betweenness centrality"
4. Change colors: "Make nodes red" or "Change edge color to blue"
5. Change sizes: "Increase node size" or "Make edges thinner"
6. Get network information: "Show network statistics" or "Display network info"

You can also upload network files using the "Upload Network File" button at the top of the visualization panel."""
            }
        
        # If no operation was recognized
        return {
            "success": False,
            "content": "I'm sorry, I don't understand that request. Type 'help' to see what operations I can perform."
        }
    except Exception as e:
        print(f"Error processing chat message: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            "success": False,
            "content": "I'm sorry, I encountered an error processing your message. Please try again later.",
            "error": str(e)
        }

# Get sample network
async def get_sample_network(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """
    Get a sample network (Zachary's Karate Club).
    
    Returns:
        Sample network data
    """
    try:
        # Initialize sample network if not already initialized
        if not network_state["graph"]:
            initialize_sample_network()
        
        return {
            "success": True,
            "nodes": [node.dict() for node in network_state["positions"]],
            "edges": [edge.dict() for edge in network_state["edges"]],
            "layout": network_state["layout"],
            "layout_params": network_state["layout_params"]
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

async def recommend_layout(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """
    Recommend a layout algorithm based on user's question or network properties.
    
    Args:
        question: User's question about visualization
        
    Returns:
        Recommended layout algorithm and parameters
    """
    try:
        question = arguments.get("question", "")
        
        if not question:
            return {
                "success": False,
                "error": "No question provided"
            }
        
        # Convert question to lowercase for easier matching
        question_lower = question.lower()
        
        # Define keywords for different layout types
        centrality_keywords = ["中心性", "centrality", "重要", "important", "中心", "center", "ハブ", "hub"]
        community_keywords = ["コミュニティ", "community", "グループ", "group", "クラスタ", "cluster", "モジュール", "module"]
        hierarchy_keywords = ["階層", "hierarchy", "ツリー", "tree", "親子", "parent-child", "レベル", "level"]
        overview_keywords = ["全体", "overview", "構造", "structure", "俯瞰", "bird's eye", "概観", "general"]
        dense_keywords = ["密", "dense", "混雑", "crowded", "複雑", "complex", "多い", "many"]
        sparse_keywords = ["疎", "sparse", "シンプル", "simple", "少ない", "few"]
        
        # Check network properties
        G = network_state["graph"]
        num_nodes = G.number_of_nodes()
        density = nx.density(G)
        is_connected = nx.is_connected(G)
        
        # Default recommendation
        recommended_layout = "spring"
        recommended_params = {}
        recommendation_reason = "Spring layout is a good general-purpose layout algorithm."
        
        # Check for centrality-related questions
        if any(keyword in question_lower for keyword in centrality_keywords):
            recommended_layout = "fruchterman_reingold"
            recommended_params = {"k": 0.5, "iterations": 50}
            recommendation_reason = "Fruchterman-Reingold layout is good for visualizing node centrality as it places more central nodes towards the center."
        
        # Check for community-related questions
        elif any(keyword in question_lower for keyword in community_keywords):
            recommended_layout = "community"
            recommended_params = {"algorithm": "louvain", "scale": 1.0}
            recommendation_reason = "Community layout is ideal for visualizing group structures in the network."
        
        # Check for hierarchy-related questions
        elif any(keyword in question_lower for keyword in hierarchy_keywords):
            if nx.is_directed(G):
                recommended_layout = "shell"
                recommendation_reason = "Shell layout is good for visualizing hierarchical structures in directed networks."
            else:
                recommended_layout = "spectral"
                recommendation_reason = "Spectral layout can reveal hierarchical patterns in the network structure."
        
        # Check for overview-related questions
        elif any(keyword in question_lower for keyword in overview_keywords):
            recommended_layout = "kamada_kawai"
            recommendation_reason = "Kamada-Kawai layout provides a good overview of the entire network structure."
        
        # Check network properties if no specific keywords matched
        else:
            if num_nodes > 100:
                if density > 0.1:
                    # Dense large network
                    recommended_layout = "spectral"
                    recommendation_reason = "Spectral layout works well for large, dense networks."
                else:
                    # Sparse large network
                    recommended_layout = "spring"
                    recommended_params = {"k": 0.3, "iterations": 100}
                    recommendation_reason = "Spring layout with adjusted parameters works well for large, sparse networks."
            else:
                if density > 0.2:
                    # Dense small network
                    recommended_layout = "kamada_kawai"
                    recommendation_reason = "Kamada-Kawai layout provides good visualization for small, dense networks."
                else:
                    # Sparse small network
                    recommended_layout = "fruchterman_reingold"
                    recommendation_reason = "Fruchterman-Reingold layout works well for small, sparse networks."
        
        return {
            "success": True,
            "recommended_layout": recommended_layout,
            "recommended_parameters": recommended_params,
            "recommendation_reason": recommendation_reason,
            "question": question
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }
