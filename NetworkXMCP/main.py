"""
NetworkX MCP Server
A FastAPI server for network visualization and analysis using NetworkX.
"""

import os
from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, List, Optional, Any, Union
import networkx as nx
import numpy as np
import json
import base64
from io import BytesIO
from dotenv import load_dotenv
from pydantic import BaseModel

# Load environment variables
load_dotenv()

# Create FastAPI app
app = FastAPI(
    title="NetworkX MCP Server",
    description="MCP server for network visualization and analysis using NetworkX",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Define request models
class ToolRequest(BaseModel):
    arguments: Dict[str, Any] = {}

# Add manifest endpoint
@app.get("/mcp/manifest")
async def get_manifest():
    """
    Get the MCP server manifest.
    """
    return {
        "name": "network-visualization-mcp",
        "version": "1.0.0",
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
                "name": "get_sample_network",
                "description": "Get a sample network (Zachary's Karate Club)",
                "parameters": {},
                "required": []
            },
            {
                "name": "recommend_layout",
                "description": "Recommend a layout algorithm based on user's question",
                "parameters": {
                    "question": {
                        "type": "string",
                        "description": "User's question about visualization"
                    }
                },
                "required": ["question"]
            },
            {
                "name": "change_layout",
                "description": "Change the layout algorithm for the network visualization",
                "parameters": {
                    "layout_type": {
                        "type": "string",
                        "description": "Type of layout algorithm"
                    },
                    "layout_params": {
                        "type": "object",
                        "description": "Parameters for the layout algorithm"
                    }
                },
                "required": ["layout_type"]
            },
            {
                "name": "process_chat_message",
                "description": "Process a chat message and execute network operations",
                "parameters": {
                    "message": {
                        "type": "string",
                        "description": "The chat message to process"
                    }
                },
                "required": ["message"]
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

# Add resource endpoint
@app.get("/mcp/resources/network")
async def get_network_resource():
    """
    Get the current network as an MCP resource.
    """
    try:
        return {
            "nodes": network_state["positions"],
            "edges": network_state["edges"],
            "layout": network_state["layout"],
            "layout_params": network_state["layout_params"],
            "centrality": network_state["centrality"],
            "visual_properties": network_state["visual_properties"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

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
        {
            "id": str(node),
            "label": f"Node {node}",
            "x": float(pos[node][0]),
            "y": float(pos[node][1]),
            "size": 5,
            "color": "#1d4ed8"
        }
        for node in G.nodes()
    ]
    
    # Store edges
    network_state["edges"] = [
        {
            "source": str(source),
            "target": str(target),
            "width": 1,
            "color": "#94a3b8"
        }
        for source, target in G.edges()
    ]

# Initialize the network on startup
initialize_sample_network()

# Create empty directories for modules if they don't exist
import os
os.makedirs('layouts', exist_ok=True)
os.makedirs('metrics', exist_ok=True)
os.makedirs('tools', exist_ok=True)

# Import layout functions
try:
    from layouts.layout_functions import apply_layout, get_available_layouts
except ImportError:
    # Fallback implementations
    def get_available_layouts():
        return ["spring", "circular", "random", "spectral", "shell", "kamada_kawai", "fruchterman_reingold"]
    
    def apply_layout(G, layout_type, **kwargs):
        layout_functions = {
            "spring": nx.spring_layout,
            "circular": nx.circular_layout,
            "random": nx.random_layout,
            "spectral": nx.spectral_layout,
            "shell": nx.shell_layout,
            "kamada_kawai": nx.kamada_kawai_layout,
            "fruchterman_reingold": nx.fruchterman_reingold_layout
        }
        
        if layout_type in layout_functions:
            return layout_functions[layout_type](G, **kwargs)
        else:
            return nx.spring_layout(G)

# Import centrality functions
try:
    from metrics.centrality_functions import calculate_centrality, get_available_centrality_metrics
except ImportError:
    # Fallback implementations
    def get_available_centrality_metrics():
        return ["degree", "closeness", "betweenness", "eigenvector", "pagerank"]
    
    def calculate_centrality(G, centrality_type, **kwargs):
        centrality_functions = {
            "degree": nx.degree_centrality,
            "closeness": nx.closeness_centrality,
            "betweenness": nx.betweenness_centrality,
            "eigenvector": nx.eigenvector_centrality_numpy,
            "pagerank": nx.pagerank
        }
        
        if centrality_type in centrality_functions:
            return centrality_functions[centrality_type](G, **kwargs)
        else:
            return nx.degree_centrality(G)

# Import tools
try:
    from tools.network_tools import (
        parse_network_file,
        get_network_info,
        get_node_info,
        highlight_nodes,
        change_visual_properties
    )
except ImportError:
    # Fallback implementations
    def parse_network_file(file_content, file_name, file_type=""):
        try:
            # Simple implementation for GraphML files
            import base64
            import io
            
            content_bytes = base64.b64decode(file_content)
            content_io = io.BytesIO(content_bytes)
            
            G = nx.read_graphml(content_io)
            
            # Extract nodes and edges
            nodes = [{"id": str(node), "label": str(node)} for node in G.nodes()]
            edges = [{"source": str(source), "target": str(target)} for source, target in G.edges()]
            
            return {
                "success": True,
                "graph": G,
                "nodes": nodes,
                "edges": edges
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Error parsing network file: {str(e)}"
            }
    
    def get_network_info(G):
        try:
            return {
                "success": True,
                "network_info": {
                    "num_nodes": G.number_of_nodes(),
                    "num_edges": G.number_of_edges(),
                    "density": nx.density(G),
                    "is_connected": nx.is_connected(G),
                    "num_components": nx.number_connected_components(G) if not nx.is_connected(G) else 1,
                    "avg_degree": sum(d for _, d in G.degree()) / G.number_of_nodes() if G.number_of_nodes() > 0 else 0,
                    "clustering_coefficient": nx.average_clustering(G)
                }
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Error getting network information: {str(e)}"
            }
    
    def get_node_info(G, node_ids, centrality_type=None, centrality_values=None):
        try:
            node_info = {}
            for node_id in node_ids:
                if node_id in G:
                    node_info[str(node_id)] = {
                        "degree": G.degree(node_id),
                        "neighbors": [str(n) for n in G.neighbors(node_id)]
                    }
            
            return {
                "success": True,
                "node_info": node_info
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Error getting node information: {str(e)}"
            }
    
    def highlight_nodes(network_state, node_ids, highlight_color="#ff0000"):
        try:
            for node in network_state["positions"]:
                if node["id"] in node_ids:
                    node["color"] = highlight_color
                else:
                    node["color"] = network_state["visual_properties"]["node_color"]
            
            return {
                "success": True,
                "highlighted_nodes": node_ids,
                "highlight_color": highlight_color
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Error highlighting nodes: {str(e)}"
            }
    
    def change_visual_properties(network_state, property_type, property_value, property_mapping={}):
        try:
            network_state["visual_properties"][property_type] = property_value
            
            if property_type.startswith("node_"):
                attribute = property_type.split("_")[1]
                for node in network_state["positions"]:
                    if node["id"] in property_mapping:
                        node[attribute] = property_mapping[node["id"]]
                    else:
                        node[attribute] = property_value
            else:
                attribute = property_type.split("_")[1]
                for edge in network_state["edges"]:
                    edge_key = f"{edge['source']}-{edge['target']}"
                    if edge_key in property_mapping:
                        edge[attribute] = property_mapping[edge_key]
                    else:
                        edge[attribute] = property_value
            
            return {
                "success": True,
                "property_type": property_type,
                "property_value": property_value,
                "property_mapping": property_mapping
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Error changing visual properties: {str(e)}"
            }

# Define API routes

@app.post("/mcp/tools/get_sample_network")
async def get_sample_network(request: ToolRequest) -> Dict[str, Any]:
    arguments = request.arguments
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
            "nodes": network_state["positions"],
            "edges": network_state["edges"],
            "layout": network_state["layout"],
            "layout_params": network_state["layout_params"]
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

@app.post("/mcp/tools/upload_network_file")
async def upload_network_file(request: ToolRequest) -> Dict[str, Any]:
    arguments = request.arguments
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
        
        # Parse the network file
        result = parse_network_file(file_content, file_name, file_type)
        
        if result["success"]:
            # Update network state
            network_state["graph"] = result["graph"]
            network_state["positions"] = result["nodes"]
            network_state["edges"] = result["edges"]
            
            # Apply default layout
            layout_result = await change_layout({"layout_type": "spring"})
            
            return {
                "success": True,
                "nodes": network_state["positions"],
                "edges": network_state["edges"],
                "layout": network_state["layout"],
                "layout_params": network_state["layout_params"]
            }
        else:
            return result
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

@app.post("/mcp/tools/change_layout")
async def change_layout(request: ToolRequest) -> Dict[str, Any]:
    arguments = request.arguments
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
        if not G:
            return {
                "success": False,
                "error": "No network data available"
            }
        
        pos = apply_layout(G, layout_type, **layout_params)
        
        # Update positions
        updated_positions = []
        for node in network_state["positions"]:
            node_id = node["id"]
            node_id_int = int(node_id) if node_id.isdigit() else node_id
            
            if node_id_int in pos:
                node["x"] = float(pos[node_id_int][0])
                node["y"] = float(pos[node_id_int][1])
            
            updated_positions.append(node)
        
        network_state["positions"] = updated_positions
        
        return {
            "success": True,
            "layout": layout_type,
            "layout_params": layout_params,
            "positions": [
                {
                    "id": node["id"],
                    "x": node["x"],
                    "y": node["y"]
                }
                for node in network_state["positions"]
            ]
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

@app.post("/mcp/tools/calculate_centrality")
async def calculate_centrality_tool(request: ToolRequest) -> Dict[str, Any]:
    arguments = request.arguments
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
        if not G:
            return {
                "success": False,
                "error": "No network data available"
            }
        
        centrality_values = calculate_centrality(G, centrality_type)
        
        # Convert node IDs to strings
        centrality_values = {str(node): value for node, value in centrality_values.items()}
        
        # Store centrality values
        network_state["centrality_values"] = centrality_values
        
        # Find max centrality value for normalization
        max_value = max(centrality_values.values()) if centrality_values else 1.0
        
        # Update node sizes and colors based on centrality
        for node in network_state["positions"]:
            node_id = node["id"]
            if node_id in centrality_values:
                value = centrality_values[node_id]
                # Scale size between 5 and 15
                node["size"] = 5 + (value / max_value) * 10
                
                # Generate color from blue (low) to red (high)
                ratio = value / max_value
                r = int(255 * ratio)
                b = int(255 * (1 - ratio))
                node["color"] = f"rgb({r}, 70, {b})"
        
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

@app.post("/mcp/tools/get_network_info")
async def get_network_info_tool(request: ToolRequest) -> Dict[str, Any]:
    arguments = request.arguments
    """
    Get information about the current network.
    
    Returns:
        Network information including number of nodes, edges, density, etc.
    """
    try:
        G = network_state["graph"]
        if not G:
            return {
                "success": False,
                "error": "No network data available"
            }
        
        result = get_network_info(G)
        
        # Add current layout and centrality
        result["network_info"]["current_layout"] = network_state["layout"]
        result["network_info"]["current_centrality"] = network_state["centrality"]
        
        return result
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

@app.post("/mcp/tools/get_node_info")
async def get_node_info_tool(request: ToolRequest) -> Dict[str, Any]:
    arguments = request.arguments
    """
    Get information about specific nodes in the network.
    
    Args:
        node_ids: List of node IDs to get information for
        
    Returns:
        Node information including degree, centrality, etc.
    """
    try:
        node_ids = arguments.get("node_ids", [])
        
        G = network_state["graph"]
        if not G:
            return {
                "success": False,
                "error": "No network data available"
            }
        
        return get_node_info(G, node_ids, network_state["centrality"], network_state["centrality_values"])
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

@app.post("/mcp/tools/highlight_nodes")
async def highlight_nodes_tool(request: ToolRequest) -> Dict[str, Any]:
    arguments = request.arguments
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
        
        return highlight_nodes(network_state, node_ids, highlight_color)
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

@app.post("/mcp/tools/change_visual_properties")
async def change_visual_properties_tool(request: ToolRequest) -> Dict[str, Any]:
    arguments = request.arguments
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
        
        return change_visual_properties(network_state, property_type, property_value, property_mapping)
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

@app.post("/mcp/tools/recommend_layout")
async def recommend_layout(request: ToolRequest) -> Dict[str, Any]:
    arguments = request.arguments
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
        if not G:
            return {
                "success": False,
                "error": "No network data available"
            }
        
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

@app.post("/mcp/tools/process_chat_message")
async def process_chat_message(request: ToolRequest) -> Dict[str, Any]:
    arguments = request.arguments
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
                    return {
                        "success": False,
                        "content": f"I'm sorry, I encountered an error trying to recommend a layout: {str(e)}"
                    }
            
            # Check for specific layout requests
            import re
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
                        return {
                            "success": False,
                            "content": f"I'm sorry, I encountered an error trying to apply the {layout_type} layout: {str(e)}"
                        }
            
            # If no specific layout was mentioned but "layout" was
            return {
                "success": True,
                "content": "You can use the following layouts: Spring, Circular, Random, Spectral, Shell, Kamada-Kawai, and Fruchterman-Reingold. Just ask me to change to any of these layouts."
            }
        
        # Check for centrality requests
        if any(keyword in message_lower for keyword in ["centrality", "中心性", "センタリティ", "measure", "指標"]):
            import re
            for centrality_type, pattern in centrality_patterns.items():
                if re.search(pattern, message_lower, re.IGNORECASE):
                    try:
                        # Calculate centrality
                        centrality_result = await calculate_centrality_tool({
                            "centrality_type": centrality_type
                        })
                        
                        if centrality_result and centrality_result.get("success"):
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
                        return {
                            "success": False,
                            "content": f"I'm sorry, I encountered an error trying to apply {centrality_type} centrality: {str(e)}"
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
            import re
            for color_name, pattern in color_patterns.items():
                if re.search(pattern, message_lower, re.IGNORECASE):
                    try:
                        result = await change_visual_properties_tool({
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
                        return {
                            "success": False,
                            "content": f"I'm sorry, I encountered an error trying to change the color of the {target} to {color_name}: {str(e)}"
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
                import re
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
                    result = await change_visual_properties_tool({
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
                    return {
                        "success": False,
                        "content": f"I'm sorry, I encountered an error trying to change the size of the {target}: {str(e)}"
                    }
            
            # If no specific size change was requested but "size" was mentioned
            return {
                "success": True,
                "content": f"You can ask me to increase or decrease the size of {target}, or specify a specific size value."
            }
        
        # Check for network information request
        if any(keyword in message_lower for keyword in ["info", "information", "statistics", "stats", "情報", "統計"]):
            try:
                result = await get_network_info_tool({})
                
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
                return {
                    "success": False,
                    "content": f"I'm sorry, I encountered an error trying to retrieve network information: {str(e)}"
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
        return {
            "success": False,
            "content": f"I'm sorry, I encountered an error processing your message: {str(e)}"
        }
