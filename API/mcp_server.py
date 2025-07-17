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
            
            # Also recommend calculating centrality
            recommended_centrality = "degree"
            if "closeness" in question_lower or "近接" in question_lower:
                recommended_centrality = "closeness"
            elif "betweenness" in question_lower or "媒介" in question_lower:
                recommended_centrality = "betweenness"
            elif "eigenvector" in question_lower or "固有ベクトル" in question_lower:
                recommended_centrality = "eigenvector"
            elif "pagerank" in question_lower:
                recommended_centrality = "pagerank"
        
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

async def export_network_as_graphml(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """
    Export the current network as GraphML format.
    
    Args:
        include_positions: Whether to include node positions in the GraphML
        include_visual_properties: Whether to include visual properties in the GraphML
        
    Returns:
        GraphML string representation of the network
    """
    try:
        include_positions = arguments.get("include_positions", True)
        include_visual_properties = arguments.get("include_visual_properties", True)
        
        G = network_state["graph"]
        
        if not G:
            return {
                "success": False,
                "error": "No network data available"
            }
        
        # Create a copy of the graph to add attributes
        export_graph = nx.Graph()
        
        # Add nodes with attributes
        for node in network_state["positions"]:
            node_attrs = {}
            
            # Add label
            if node.label:
                node_attrs["label"] = node.label
            
            # Add positions if requested
            if include_positions:
                node_attrs["x"] = float(node.x)
                node_attrs["y"] = float(node.y)
            
            # Add visual properties if requested
            if include_visual_properties:
                node_attrs["size"] = float(node.size) if node.size is not None else 5.0
                node_attrs["color"] = node.color if node.color else "#1d4ed8"
            
            # Add centrality values if available
            if network_state["centrality_values"] and node.id in network_state["centrality_values"]:
                node_attrs["centrality"] = float(network_state["centrality_values"][node.id])
                node_attrs["centrality_type"] = network_state["centrality"]
            
            # Add node to export graph
            export_graph.add_node(node.id, **node_attrs)
        
        # Add edges with attributes
        for edge in network_state["edges"]:
            edge_attrs = {}
            
            # Add visual properties if requested
            if include_visual_properties:
                edge_attrs["width"] = float(edge.width) if edge.width is not None else 1.0
                edge_attrs["color"] = edge.color if edge.color else "#94a3b8"
            
            # Add edge to export graph
            export_graph.add_edge(edge.source, edge.target, **edge_attrs)
        
        # Export as GraphML
        graphml_output = io.StringIO()
        nx.write_graphml(export_graph, graphml_output)
        graphml_string = graphml_output.getvalue()
        
        return {
            "success": True,
            "graphml": graphml_string,
            "nodes_count": export_graph.number_of_nodes(),
            "edges_count": export_graph.number_of_edges(),
            "layout": network_state["layout"],
            "layout_params": network_state["layout_params"]
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

# Upload network file
async def upload_network_file(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """
    Upload a network file and parse it into nodes and edges.
    
    Args:
        file_content: Base64 encoded content of the network file
        file_name: Name of the file being uploaded
        file_type: MIME type of the file
        
    Returns:
        Parsed network data
    """
    try:
        file_content = arguments.get("file_content", "")
        file_name = arguments.get("file_name", "")
        file_type = arguments.get("file_type", "")
        
        if not file_content or not file_name:
            return {
                "success": False,
                "error": "File content and name are required"
            }
        
        # Get file extension
        file_extension = file_name.split('.')[-1].lower()
        
        # Check if file extension is supported
        supported_formats = ['graphml', 'gexf', 'gml', 'json', 'net', 'edgelist', 'adjlist']
        if file_extension not in supported_formats:
            return {
                "success": False,
                "error": f"Unsupported file format: {file_extension}. Supported formats: {', '.join(supported_formats)}"
            }
        
        # Decode base64 content
        import base64
        try:
            decoded_content = base64.b64decode(file_content)
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to decode file content: {str(e)}"
            }
        
        # Create a temporary file
        import tempfile
        import os
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=f'.{file_extension}') as temp_file:
            temp_file.write(decoded_content)
            temp_file_path = temp_file.name
        
        try:
            # Parse the file based on its extension
            G = None
            
            if file_extension == 'graphml':
                G = nx.read_graphml(temp_file_path)
            elif file_extension == 'gexf':
                G = nx.read_gexf(temp_file_path)
            elif file_extension == 'gml':
                G = nx.read_gml(temp_file_path)
            elif file_extension == 'json':
                # Try different JSON formats
                try:
                    G = nx.node_link_graph(json.load(open(temp_file_path)))
                except:
                    try:
                        G = nx.jit_graph(json.load(open(temp_file_path)))
                    except:
                        return {
                            "success": False,
                            "error": "Failed to parse JSON file. Supported JSON formats: node-link and JIT"
                        }
            elif file_extension == 'net':
                G = nx.read_pajek(temp_file_path)
            elif file_extension == 'edgelist':
                G = nx.read_edgelist(temp_file_path)
            elif file_extension == 'adjlist':
                G = nx.read_adjlist(temp_file_path)
            
            # Clean up temporary file
            os.unlink(temp_file_path)
            
            if not G:
                return {
                    "success": False,
                    "error": "Failed to parse network file"
                }
            
            # Update network state
            network_state["graph"] = G
            
            # Calculate initial positions
            pos = nx.spring_layout(G)
            
            # Convert to the expected format
            network_state["positions"] = [
                Node(
                    id=str(node),
                    label=G.nodes[node].get('label', f"Node {node}") if isinstance(G.nodes[node], dict) else f"Node {node}",
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
            
            return {
                "success": True,
                "nodes": [node.dict() for node in network_state["positions"]],
                "edges": [edge.dict() for edge in network_state["edges"]],
                "layout": "spring",
                "layout_params": {},
                "nodes_count": G.number_of_nodes(),
                "edges_count": G.number_of_edges(),
                "file_name": file_name
            }
        except Exception as e:
            # Clean up temporary file
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
            
            return {
                "success": False,
                "error": f"Failed to parse network file: {str(e)}"
            }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

# Map of tool names to their implementations
mcp_tools = {
    "update_network": update_network,
    "upload_network_file": upload_network_file,
    "change_layout": change_layout,
    "calculate_centrality": calculate_node_centrality,
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
    "export_network_as_graphml": export_network_as_graphml
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
        "version": "1.1.0",
        "description": "MCP server for network visualization with enhanced features",
        "tools": [
            {
                "name": "upload_network_file",
                "description": "Upload a network file and parse it into nodes and edges",
                "parameters": {
                    "file_content": {
                        "type": "string",
                        "description": "Base64 encoded content of the network file"
                    },
                    "file_name": {
                        "type": "string",
                        "description": "Name of the file being uploaded"
                    },
                    "file_type": {
                        "type": "string",
                        "description": "MIME type of the file"
                    }
                },
                "required": ["file_content", "file_name"]
            },
            {
                "name": "update_network",
                "description": "Update the network data in the MCP server",
                "parameters": {
                    "nodes": {
                        "type": "array",
                        "description": "List of nodes",
                        "items": {
                            "type": "object",
                            "properties": {
                                "id": {
                                    "type": "string",
                                    "description": "Node ID"
                                },
                                "label": {
                                    "type": "string",
                                    "description": "Node label"
                                },
                                "x": {
                                    "type": "number",
                                    "description": "X coordinate"
                                },
                                "y": {
                                    "type": "number",
                                    "description": "Y coordinate"
                                },
                                "size": {
                                    "type": "number",
                                    "description": "Node size"
                                },
                                "color": {
                                    "type": "string",
                                    "description": "Node color"
                                }
                            },
                            "required": ["id"]
                        }
                    },
                    "edges": {
                        "type": "array",
                        "description": "List of edges",
                        "items": {
                            "type": "object",
                            "properties": {
                                "source": {
                                    "type": "string",
                                    "description": "Source node ID"
                                },
                                "target": {
                                    "type": "string",
                                    "description": "Target node ID"
                                },
                                "width": {
                                    "type": "number",
                                    "description": "Edge width"
                                },
                                "color": {
                                    "type": "string",
                                    "description": "Edge color"
                                }
                            },
                            "required": ["source", "target"]
                        }
                    }
                },
                "required": ["nodes", "edges"]
            },
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
            },
            {
                "name": "save_network",
                "description": "Save the current network data for a user",
                "parameters": {
                    "user_id": {
                        "type": "string",
                        "description": "ID of the user"
                    },
                    "network_name": {
                        "type": "string",
                        "description": "Name to save the network as"
                    }
                },
                "required": ["user_id"]
            },
            {
                "name": "load_network",
                "description": "Load a saved network for a user",
                "parameters": {
                    "user_id": {
                        "type": "string",
                        "description": "ID of the user"
                    },
                    "network_name": {
                        "type": "string",
                        "description": "Name of the network to load"
                    }
                },
                "required": ["user_id"]
            },
            {
                "name": "list_user_networks",
                "description": "List all saved networks for a user",
                "parameters": {
                    "user_id": {
                        "type": "string",
                        "description": "ID of the user"
                    }
                },
                "required": ["user_id"]
            },
            {
                "name": "apply_community_layout",
                "description": "Apply a layout algorithm based on community detection",
                "parameters": {
                    "algorithm": {
                        "type": "string",
                        "description": "Community detection algorithm to use",
                        "enum": ["louvain", "greedy_modularity"]
                    },
                    "layout_params": {
                        "type": "object",
                        "description": "Parameters for the layout algorithm"
                    }
                },
                "required": []
            },
            {
                "name": "compare_layouts",
                "description": "Compare different layout algorithms for the current network",
                "parameters": {
                    "layouts": {
                        "type": "array",
                        "description": "List of layout algorithms to compare",
                        "items": {
                            "type": "string",
                            "enum": [
                                "spring", "circular", "random", "spectral", "shell", 
                                "spiral", "kamada_kawai", "fruchterman_reingold", 
                                "bipartite", "multipartite", "planar", "community"
                            ]
                        }
                    }
                },
                "required": []
            },
            {
                "name": "get_sample_network",
                "description": "Get a sample network (Zachary's Karate Club)",
                "parameters": {},
                "required": []
            },
            {
                "name": "recommend_layout",
                "description": "Recommend a layout algorithm based on user's question or network properties",
                "parameters": {
                    "question": {
                        "type": "string",
                        "description": "User's question about visualization"
                    }
                },
                "required": ["question"]
            },
            {
                "name": "export_network_as_graphml",
                "description": "Export the current network as GraphML format",
                "parameters": {
                    "include_positions": {
                        "type": "boolean",
                        "description": "Whether to include node positions in the GraphML"
                    },
                    "include_visual_properties": {
                        "type": "boolean",
                        "description": "Whether to include visual properties in the GraphML"
                    }
                },
                "required": []
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
