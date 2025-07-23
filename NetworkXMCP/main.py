"""
NetworkX MCP Server
A FastAPI server for network visualization and analysis using NetworkX.
"""

import os
import re
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
from fastapi_mcp import FastApiMCP

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

# Create MCP server
mcp = FastApiMCP(app)

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

# Define a route for the network resource
@app.get("/mcp/resources/network", tags=["MCP Resources"])
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

# Define Pydantic models for request bodies
class FileUploadRequest(BaseModel):
    file_content: str
    file_name: str
    file_type: str = ""

class LayoutRequest(BaseModel):
    layout_type: str
    layout_params: Dict[str, Any] = {}

class CentralityRequest(BaseModel):
    centrality_type: str

class NodeInfoRequest(BaseModel):
    node_ids: List[str]

class HighlightNodesRequest(BaseModel):
    node_ids: List[str]
    highlight_color: str = "#ff0000"

class VisualPropertiesRequest(BaseModel):
    property_type: str
    property_value: Any
    property_mapping: Dict[str, Any] = {}

class ChatMessageRequest(BaseModel):
    message: str

class QuestionRequest(BaseModel):
    question: str

# Define FastAPI routes for the operations
@app.get("/get_sample_network", tags=["Network Operations"])
async def get_sample_network():
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

@app.post("/upload_network_file", tags=["Network Operations"])
async def upload_network_file(request: FileUploadRequest):
    """
    Upload a network file and parse it into nodes and edges.
    """
    try:
        if not request.file_content or not request.file_name:
            return {
                "success": False,
                "error": "File content and name are required"
            }
        
        # Parse the network file
        result = parse_network_file(request.file_content, request.file_name, request.file_type)
        
        if result["success"]:
            # Update network state
            network_state["graph"] = result["graph"]
            network_state["positions"] = result["nodes"]
            network_state["edges"] = result["edges"]
            
            # Apply default layout
            layout_result = await change_layout(LayoutRequest(layout_type="spring"))
            
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

@app.post("/change_layout", tags=["Network Operations"])
async def change_layout(request: LayoutRequest):
    """
    Change the layout algorithm for the network visualization.
    """
    try:
        # Update network state
        network_state["layout"] = request.layout_type
        network_state["layout_params"] = request.layout_params
        
        # Apply layout
        G = network_state["graph"]
        if not G:
            return {
                "success": False,
                "error": "No network data available"
            }
        
        pos = apply_layout(G, request.layout_type, **request.layout_params)
        
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
            "layout": request.layout_type,
            "layout_params": request.layout_params,
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

@app.post("/calculate_centrality", tags=["Network Operations"])
async def calculate_centrality_tool(request: CentralityRequest):
    """
    Calculate centrality metrics for nodes in the graph.
    """
    try:
        # Update network state
        network_state["centrality"] = request.centrality_type
        
        # Calculate centrality
        G = network_state["graph"]
        if not G:
            return {
                "success": False,
                "error": "No network data available"
            }
        
        centrality_values = calculate_centrality(G, request.centrality_type)
        
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
            "centrality_type": request.centrality_type,
            "centrality_values": centrality_values
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

@app.get("/get_network_info", tags=["Network Operations"])
async def get_network_info_tool():
    """
    Get information about the current network.
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

@app.post("/get_node_info", tags=["Network Operations"])
async def get_node_info_tool(request: NodeInfoRequest):
    """
    Get information about specific nodes in the network.
    """
    try:
        G = network_state["graph"]
        if not G:
            return {
                "success": False,
                "error": "No network data available"
            }
        
        return get_node_info(G, request.node_ids, network_state["centrality"], network_state["centrality_values"])
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

@app.post("/highlight_nodes", tags=["Network Operations"])
async def highlight_nodes_tool(request: HighlightNodesRequest):
    """
    Highlight specific nodes in the network.
    """
    try:
        return highlight_nodes(network_state, request.node_ids, request.highlight_color)
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

@app.post("/change_visual_properties", tags=["Network Operations"])
async def change_visual_properties_tool(request: VisualPropertiesRequest):
    """
    Change visual properties of nodes or edges.
    """
    try:
        return change_visual_properties(network_state, request.property_type, request.property_value, request.property_mapping)
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

@app.post("/recommend_layout", tags=["Network Operations"])
async def recommend_layout(request: QuestionRequest):
    """
    Recommend a layout algorithm based on user's question or network properties.
    """
    try:
        if not request.question:
            return {
                "success": False,
                "error": "No question provided"
            }
        
        # Convert question to lowercase for easier matching
        question_lower = request.question.lower()
        
        # Define keywords for different layout types
        centrality_keywords = ["中心性", "centrality", "重要", "important", "中心", "center", "ハブ", "hub"]
        community_keywords = ["コミュニティ", "community", "グループ", "group", "クラスタ", "cluster", "モジュール", "module"]
        hierarchy_keywords = ["階層", "hierarchy", "ツリー", "tree", "親子", "parent-child", "レベル", "level"]
        overview_keywords = ["全体", "overview", "構造", "structure", "俯瞰", "bird's eye", "概観", "general"]
        
        # Check network properties
        G = network_state["graph"]
        if not G:
            return {
                "success": False,
                "error": "No network data available"
            }
        
        num_nodes = G.number_of_nodes()
        density = nx.density(G)
        
        # Default recommendation
        recommended_layout = "spring"
        recommended_params = {}
        recommendation_reason = "Spring layout is a good general-purpose layout algorithm."
        
        # Check for centrality-related questions
        if any(keyword in question_lower for keyword in centrality_keywords):
            recommended_layout = "fruchterman_reingold"
            recommended_params = {"k": 0.5, "iterations": 50}
            recommendation_reason = "Fruchterman-Reingold layout is good for visualizing node centrality."
        
        # Check for community-related questions
        elif any(keyword in question_lower for keyword in community_keywords):
            recommended_layout = "spring"
            recommended_params = {"k": 0.3}
            recommendation_reason = "Spring layout with adjusted parameters is good for visualizing communities."
        
        # Check for hierarchy-related questions
        elif any(keyword in question_lower for keyword in hierarchy_keywords):
            recommended_layout = "spectral"
            recommendation_reason = "Spectral layout can reveal hierarchical patterns in the network structure."
        
        # Check for overview-related questions
        elif any(keyword in question_lower for keyword in overview_keywords):
            recommended_layout = "kamada_kawai"
            recommendation_reason = "Kamada-Kawai layout provides a good overview of the entire network structure."
        
        return {
            "success": True,
            "recommended_layout": recommended_layout,
            "recommended_parameters": recommended_params,
            "recommendation_reason": recommendation_reason,
            "question": request.question
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

@app.post("/process_chat_message", tags=["Network Operations"])
async def process_chat_message(request: ChatMessageRequest):
    """
    Process a chat message and execute network operations.
    """
    try:
        if not request.message:
            return {
                "success": False,
                "error": "No message provided"
            }
        
        # Convert message to lowercase for easier matching
        message_lower = request.message.lower()
        
        # Check for layout change requests
        if "layout" in message_lower:
            # Check for layout recommendation request
            if "recommend" in message_lower or "suggestion" in message_lower:
                result = await recommend_layout(QuestionRequest(question=request.message))
                if result and result.get("success"):
                    # Apply the recommended layout
                    layout_type = result.get("recommended_layout")
                    layout_params = result.get("recommended_parameters", {})
                    
                    # Apply the layout
                    layout_result = await change_layout(
                        LayoutRequest(
                            layout_type=layout_type,
                            layout_params=layout_params
                        )
                    )
                    
                    if layout_result and layout_result.get("success"):
                        return {
                            "success": True,
                            "content": f"Based on your request, I recommend using the {layout_type} layout. {result.get('recommendation_reason')} I've applied this layout to the network."
                        }
                    else:
                        return {
                            "success": False,
                            "content": f"I recommend using the {layout_type} layout, but I couldn't apply it."
                        }
                else:
                    return {
                        "success": False,
                        "content": "I couldn't recommend a layout based on your request."
                    }
            
            # Check for specific layout requests
            layout_types = ["spring", "circular", "random", "spectral", "shell", "kamada_kawai", "fruchterman_reingold"]
            for layout_type in layout_types:
                if layout_type in message_lower:
                    result = await change_layout(
                        LayoutRequest(
                            layout_type=layout_type,
                            layout_params={}
                        )
                    )
                    
                    if result and result.get("success"):
                        return {
                            "success": True,
                            "content": f"I've changed the layout to {layout_type}. The network visualization has been updated."
                        }
                    else:
                        return {
                            "success": False,
                            "content": f"I couldn't apply the {layout_type} layout. Please try again later."
                        }
            
            # If no specific layout was mentioned but "layout" was
            return {
                "success": True,
                "content": "You can use the following layouts: Spring, Circular, Random, Spectral, Shell, Kamada-Kawai, and Fruchterman-Reingold."
            }
        
        # Check for centrality requests
        if "centrality" in message_lower or "measure" in message_lower:
            centrality_types = ["degree", "closeness", "betweenness", "eigenvector", "pagerank"]
            for centrality_type in centrality_types:
                if centrality_type in message_lower:
                    # Calculate centrality
                    centrality_result = await calculate_centrality_tool(
                        CentralityRequest(centrality_type=centrality_type)
                    )
                    
                    if centrality_result and centrality_result.get("success"):
                        return {
                            "success": True,
                            "content": f"I've applied {centrality_type} centrality to the network. Nodes are now sized and colored based on their {centrality_type} centrality values."
                        }
                    else:
                        return {
                            "success": False,
                            "content": f"I couldn't apply {centrality_type} centrality. Please try again later."
                        }
            
            # If no specific centrality was mentioned but "centrality" was
            return {
                "success": True,
                "content": "You can apply the following centrality measures: Degree, Closeness, Betweenness, Eigenvector, and PageRank."
            }
        
        # Check for network information request
        if "info" in message_lower or "information" in message_lower or "statistics" in message_lower:
            result = await get_network_info_tool()
            
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
- Current Layout: {info.get('current_layout')}
- Current Centrality: {info.get('current_centrality') or 'None'}"""
                }
            else:
                return {
                    "success": False,
                    "content": "I couldn't retrieve network information. Please try again later."
                }
        
        # Check for help request
        if "help" in message_lower:
            return {
                "success": True,
                "content": """Here are the operations you can perform via chat:

1. Change layout: "Use circular layout" or "Apply Fruchterman-Reingold layout"
2. Get layout recommendation: "Recommend a layout for community detection"
3. Apply centrality: "Show degree centrality" or "Apply betweenness centrality"
4. Get network information: "Show network statistics" or "Display network info"

You can also upload network files using the "Upload Network File" button."""
            }
        
        # If no operation was recognized
        return {
            "success": False,
            "content": "I'm sorry, I don't understand that request. Type 'help' to see what operations I can perform."
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

# Add MCP routes manually
@app.post("/mcp/tools/get_sample_network")
async def mcp_get_sample_network(request: Request):
    """
    Get a sample network (Zachary's Karate Club).
    """
    try:
        # Get request body
        body = await request.json()
        
        # Call the handler function
        result = await get_sample_network()
        
        # Return response
        return result
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

@app.post("/mcp/tools/upload_network_file")
async def mcp_upload_network_file(request: Request):
    """
    Upload a network file and parse it into nodes and edges.
    """
    try:
        # Get request body
        body = await request.json()
        
        # Call the handler function
        result = await upload_network_file(body.get("arguments", {}))
        
        # Return response
        return result
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

@app.post("/mcp/tools/change_layout")
async def mcp_change_layout(request: Request):
    """
    Change the layout algorithm for the network visualization.
    """
    try:
        # Get request body
        body = await request.json()
        
        # Call the handler function
        result = await change_layout(body.get("arguments", {}))
        
        # Return response
        return result
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

@app.post("/mcp/tools/calculate_centrality")
async def mcp_calculate_centrality(request: Request):
    """
    Calculate centrality metrics for nodes in the graph.
    """
    try:
        # Get request body
        body = await request.json()
        
        # Call the handler function
        result = await calculate_centrality_tool(body.get("arguments", {}))
        
        # Return response
        return result
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

@app.post("/mcp/tools/get_network_info")
async def mcp_get_network_info(request: Request):
    """
    Get information about the current network.
    """
    try:
        # Get request body
        body = await request.json()
        
        # Call the handler function
        result = await get_network_info_tool()
        
        # Return response
        return result
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

@app.post("/mcp/tools/get_node_info")
async def mcp_get_node_info(request: Request):
    """
    Get information about specific nodes in the network.
    """
    try:
        # Get request body
        body = await request.json()
        
        # Call the handler function
        result = await get_node_info_tool(body.get("arguments", {}))
        
        # Return response
        return result
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

@app.post("/mcp/tools/highlight_nodes")
async def mcp_highlight_nodes(request: Request):
    """
    Highlight specific nodes in the network.
    """
    try:
        # Get request body
        body = await request.json()
        
        # Call the handler function
        result = await highlight_nodes_tool(body.get("arguments", {}))
        
        # Return response
        return result
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

@app.post("/mcp/tools/change_visual_properties")
async def mcp_change_visual_properties(request: Request):
    """
    Change visual properties of nodes or edges.
    """
    try:
        # Get request body
        body = await request.json()
        
        # Call the handler function
        result = await change_visual_properties_tool(body.get("arguments", {}))
        
        # Return response
        return result
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

@app.post("/mcp/tools/recommend_layout")
async def mcp_recommend_layout(request: Request):
    """
    Recommend a layout algorithm based on user's question or network properties.
    """
    try:
        # Get request body
        body = await request.json()
        
        # Call the handler function
        result = await recommend_layout(body.get("arguments", {}))
        
        # Return response
        return result
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

@app.post("/mcp/tools/process_chat_message")
async def mcp_process_chat_message(request: Request):
    """
    Process a chat message and execute network operations.
    """
    try:
        # Get request body
        body = await request.json()
        
        # Call the handler function
        result = await process_chat_message(body.get("arguments", {}))
        
        # Return response
        return result
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

@app.get("/mcp/resources/network")
async def mcp_get_network_resource():
    """
    Get the current network as an MCP resource.
    """
    try:
        # Call the handler function
        result = await get_network_resource()
        
        # Return response
        return result
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

@app.get("/mcp/manifest")
async def mcp_manifest():
    """
    Get the MCP server manifest.
    """
    try:
        # Return the manifest
        return {
            "name": "network-visualization-mcp",
            "description": "MCP server for network visualization with enhanced features",
            "tools": [
                {
                    "name": "get_sample_network",
                    "description": "Get a sample network (Zachary's Karate Club)",
                    "parameters": {}
                },
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
                    }
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
                    }
                },
                {
                    "name": "calculate_centrality",
                    "description": "Calculate centrality metrics for nodes in the graph",
                    "parameters": {
                        "centrality_type": {
                            "type": "string",
                            "description": "Type of centrality to calculate"
                        }
                    }
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
                            "description": "List of node IDs to get information for"
                        }
                    }
                },
                {
                    "name": "highlight_nodes",
                    "description": "Highlight specific nodes in the network",
                    "parameters": {
                        "node_ids": {
                            "type": "array",
                            "description": "List of node IDs to highlight"
                        },
                        "highlight_color": {
                            "type": "string",
                            "description": "Color to use for highlighting"
                        }
                    }
                },
                {
                    "name": "change_visual_properties",
                    "description": "Change visual properties of nodes or edges",
                    "parameters": {
                        "property_type": {
                            "type": "string",
                            "description": "Type of property to change"
                        },
                        "property_value": {
                            "type": "string",
                            "description": "Value to set for the property"
                        },
                        "property_mapping": {
                            "type": "object",
                            "description": "Optional mapping of node/edge IDs to property values"
                        }
                    }
                },
                {
                    "name": "recommend_layout",
                    "description": "Recommend a layout algorithm based on user's question or network properties",
                    "parameters": {
                        "question": {
                            "type": "string",
                            "description": "User's question about visualization"
                        }
                    }
                },
                {
                    "name": "process_chat_message",
                    "description": "Process a chat message and execute network operations",
                    "parameters": {
                        "message": {
                            "type": "string",
                            "description": "The chat message to process"
                        }
                    }
                }
            ],
            "resources": [
                {
                    "name": "network",
                    "description": "Current network data including nodes and edges",
                    "uri": "/resources/network"
                }
            ]
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

# Health check endpoint
@app.get("/health", tags=["Health"])
async def health_check():
    """
    Health check endpoint for Docker healthcheck.
    """
    return {"status": "healthy"}

# Mount the MCP server
mcp.mount()
