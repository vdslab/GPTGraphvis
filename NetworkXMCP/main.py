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

# Import custom modules
try:
    from tools.centrality_chat import process_chat_message as process_centrality_chat_message
    from tools.centrality_chat import recommend_centrality, get_centrality_info
except ImportError:
    # Fallback implementations if module not found
    def process_centrality_chat_message(message, G=None):
        return {
            "success": False,
            "content": "中心性チャットモジュールが見つかりません。"
        }
    
    def recommend_centrality(network_info, question=""):
        return {
            "recommended_centrality": "degree",
            "reason": "デフォルトの中心性指標です。"
        }
    
    def get_centrality_info(centrality_type):
        return {
            "name": "次数中心性 (Degree Centrality)",
            "description": "ノードの接続数に基づく中心性指標です。",
            "use_cases": "直接的な接続の重要性を測定するのに適しています。"
        }

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
        change_visual_properties,
        export_network_as_graphml,
        convert_to_standard_graphml,
        parse_graphml_string
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
    現在のネットワークをMCPリソースとして取得します。
    
    Returns:
        Dict: ネットワークリソース（ノード、エッジ、レイアウト、中心性、視覚属性）
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
class BaseGraphMLRequest(BaseModel):
    """
    GraphMLベースの基本リクエスト
    
    Attributes:
        graphml_content: GraphML形式のデータ文字列
    """
    graphml_content: str

class FileUploadRequest(BaseModel):
    """
    ファイルアップロードのリクエスト
    
    Attributes:
        file_content: Base64エンコードされたファイルコンテンツ
        file_name: ファイル名
        file_type: ファイルのMIMEタイプ (オプション)
    """
    file_content: str
    file_name: str
    file_type: str = ""

class GraphMLLayoutRequest(BaseGraphMLRequest):
    """
    GraphMLデータに対するレイアウト変更リクエスト
    
    Attributes:
        graphml_content: GraphML形式のデータ文字列
        layout_type: レイアウトアルゴリズムの種類 (spring, circular, spectral, kamada_kawai, fruchterman_reingoldなど)
        layout_params: レイアウトアルゴリズムのパラメータ (オプション)
    """
    layout_type: str
    layout_params: Dict[str, Any] = {}

class GraphMLCentralityRequest(BaseGraphMLRequest):
    """
    GraphMLデータに対する中心性計算リクエスト
    
    Attributes:
        graphml_content: GraphML形式のデータ文字列
        centrality_type: 中心性指標の種類 (degree, closeness, betweenness, eigenvector, pagerankなど)
    """
    centrality_type: str

class GraphMLNodeInfoRequest(BaseGraphMLRequest):
    """
    GraphMLデータに対するノード情報取得リクエスト
    
    Attributes:
        graphml_content: GraphML形式のデータ文字列
        node_ids: 情報を取得するノードIDのリスト
    """
    node_ids: List[str]

class GraphMLHighlightNodesRequest(BaseGraphMLRequest):
    """
    GraphMLデータに対するノードハイライトリクエスト
    
    Attributes:
        graphml_content: GraphML形式のデータ文字列
        node_ids: ハイライトするノードIDのリスト
        highlight_color: ハイライト色 (16進数カラーコード, デフォルト: "#ff0000")
    """
    node_ids: List[str]
    highlight_color: str = "#ff0000"

class GraphMLVisualPropertiesRequest(BaseGraphMLRequest):
    """
    GraphMLデータに対する視覚属性変更リクエスト
    
    Attributes:
        graphml_content: GraphML形式のデータ文字列
        property_type: 変更する属性のタイプ (node_size, node_color, edge_width, edge_colorなど)
        property_value: 設定する値
        property_mapping: ノード/エッジIDから値へのマッピング (オプション)
    """
    property_type: str
    property_value: Any
    property_mapping: Dict[str, Any] = {}

class GraphMLChatMessageRequest(BaseModel):
    """
    GraphMLデータを含むチャットメッセージリクエスト
    
    Attributes:
        message: 処理するチャットメッセージ
        graphml_content: GraphML形式のデータ文字列 (オプション)
    """
    message: str
    graphml_content: Optional[str] = None

class GraphMLQuestionRequest(BaseModel):
    """
    GraphMLデータを含む質問リクエスト
    
    Attributes:
        question: 処理する質問
        graphml_content: GraphML形式のデータ文字列 (オプション)
    """
    question: str
    graphml_content: Optional[str] = None

class GraphMLRequest(BaseGraphMLRequest):
    """
    GraphMLデータ入力のリクエスト
    
    Attributes:
        graphml_content: GraphML形式のデータ文字列
    """
    pass

class GraphMLConvertRequest(BaseGraphMLRequest):
    """
    GraphML変換のリクエスト
    
    Attributes:
        graphml_content: 変換する元のGraphML形式のデータ文字列
    """
    pass

class GraphMLResponse(BaseModel):
    """
    GraphMLデータを含む標準レスポンス
    
    Attributes:
        success: 操作が成功したかどうか
        graphml_content: GraphML形式のデータ文字列
        message: 操作に関するメッセージ (オプション)
        error: エラーメッセージ (操作が失敗した場合のみ)
    """
    success: bool
    graphml_content: Optional[str] = None
    message: Optional[str] = None
    error: Optional[str] = None

# 互換性のために既存のモデルも残す
class LayoutRequest(BaseModel):
    """
    レイアウト変更のリクエスト
    
    Attributes:
        layout_type: レイアウトアルゴリズムの種類 (spring, circular, spectral, kamada_kawai, fruchterman_reingoldなど)
        layout_params: レイアウトアルゴリズムのパラメータ (オプション)
    """
    layout_type: str
    layout_params: Dict[str, Any] = {}

class CentralityRequest(BaseModel):
    """
    中心性計算のリクエスト
    
    Attributes:
        centrality_type: 中心性指標の種類 (degree, closeness, betweenness, eigenvector, pagerankなど)
    """
    centrality_type: str

class NodeInfoRequest(BaseModel):
    """
    ノード情報取得のリクエスト
    
    Attributes:
        node_ids: 情報を取得するノードIDのリスト
    """
    node_ids: List[str]

class HighlightNodesRequest(BaseModel):
    """
    ノードハイライトのリクエスト
    
    Attributes:
        node_ids: ハイライトするノードIDのリスト
        highlight_color: ハイライト色 (16進数カラーコード, デフォルト: "#ff0000")
    """
    node_ids: List[str]
    highlight_color: str = "#ff0000"

class VisualPropertiesRequest(BaseModel):
    """
    視覚属性変更のリクエスト
    
    Attributes:
        property_type: 変更する属性のタイプ (node_size, node_color, edge_width, edge_colorなど)
        property_value: 設定する値
        property_mapping: ノード/エッジIDから値へのマッピング (オプション)
    """
    property_type: str
    property_value: Any
    property_mapping: Dict[str, Any] = {}

class ChatMessageRequest(BaseModel):
    """
    チャットメッセージのリクエスト
    
    Attributes:
        message: 処理するチャットメッセージ
    """
    message: str

class QuestionRequest(BaseModel):
    """
    質問のリクエスト
    
    Attributes:
        question: 処理する質問
    """
    question: str

# Define FastAPI routes for the operations
@app.get("/get_sample_network", tags=["Network Operations"])
async def get_sample_network():
    """
    サンプルネットワーク（Zachary's Karate Club）を取得します。
    
    Returns:
        Dict: サンプルネットワークデータ（成功した場合はsuccess=True、ノード、エッジ、レイアウト情報）
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
    ネットワークファイルをアップロードしてノードとエッジに解析します。
    
    GraphML、GEXF、GML、EdgeList、AdjList、Pajek、JSONフォーマットのファイルに対応しています。
    
    Parameters:
        request (FileUploadRequest): ファイルのコンテンツと名前を含むリクエストオブジェクト
    
    Returns:
        Dict: 解析結果（成功した場合はsuccess=True、ノード、エッジ、レイアウト情報）
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
    ネットワークビジュアライゼーションのレイアウトアルゴリズムを変更します。
    
    利用可能なレイアウト：spring, circular, random, spectral, shell, kamada_kawai, fruchterman_reingold
    
    Parameters:
        request (LayoutRequest): レイアウトタイプとパラメータを含むリクエストオブジェクト
    
    Returns:
        Dict: 変更結果（成功した場合はsuccess=True、レイアウト情報、ノード位置）
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
    グラフ内のノードの中心性指標を計算します。
    
    利用可能な中心性指標：degree, closeness, betweenness, eigenvector, pagerank
    
    Parameters:
        request (CentralityRequest): 中心性タイプを含むリクエストオブジェクト
    
    Returns:
        Dict: 計算結果（成功した場合はsuccess=True、中心性値）
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
    現在のネットワークに関する情報を取得します。
    
    Returns:
        Dict: ネットワーク情報（ノード数、エッジ数、密度、連結性、コンポーネント数、平均次数など）
    """
    try:
        G = network_state["graph"]
        if not G:
            # ネットワークがない場合は特別なレスポンスを返す
            return {
                "success": True,
                "network_info": {
                    "has_network": False,
                    "current_layout": network_state["layout"],
                    "current_centrality": network_state["centrality"]
                }
            }
        
        result = get_network_info(G)
        
        # Add current layout and centrality and has_network flag
        result["network_info"]["has_network"] = True
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
    ネットワーク内の特定のノードに関する情報を取得します。
    
    Parameters:
        request (NodeInfoRequest): 情報を取得するノードIDのリストを含むリクエストオブジェクト
    
    Returns:
        Dict: ノード情報（次数、隣接ノード、属性、中心性値（計算されている場合））
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
    ネットワーク内の特定のノードをハイライトします。
    
    Parameters:
        request (HighlightNodesRequest): ハイライトするノードIDとハイライト色を含むリクエストオブジェクト
    
    Returns:
        Dict: ハイライト結果（成功した場合はsuccess=True、ハイライトされたノード）
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
    ノードまたはエッジの視覚属性を変更します。
    
    Parameters:
        request (VisualPropertiesRequest): プロパティタイプと値を含むリクエストオブジェクト
    
    Returns:
        Dict: 変更結果（成功した場合はsuccess=True、変更された視覚属性）
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
    ユーザーの質問やネットワークプロパティに基づいてレイアウトアルゴリズムを推奨します。
    
    Parameters:
        request (QuestionRequest): ユーザーの質問を含むリクエストオブジェクト
    
    Returns:
        Dict: 推奨結果（成功した場合はsuccess=True、推奨レイアウト、推奨理由）
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

@app.post("/graphml_layout", tags=["GraphML Operations"])
async def graphml_layout(request: GraphMLLayoutRequest):
    """
    GraphML形式のネットワークデータにレイアウトアルゴリズムを適用します。
    
    Parameters:
        request (GraphMLLayoutRequest): GraphMLデータとレイアウト情報を含むリクエストオブジェクト
        
    Returns:
        GraphMLResponse: 更新されたGraphMLデータを含むレスポンス
    """
    try:
        if not request.graphml_content:
            return GraphMLResponse(
                success=False,
                error="GraphML content is required"
            )
        
        # Import network tools functions
        try:
            from tools.network_tools import apply_layout_to_graphml
        except ImportError:
            return GraphMLResponse(
                success=False,
                error="Failed to import required module: apply_layout_to_graphml"
            )
        
        # Apply layout to GraphML data
        result = apply_layout_to_graphml(
            request.graphml_content,
            request.layout_type,
            request.layout_params
        )
        
        if result["success"]:
            return GraphMLResponse(
                success=True,
                graphml_content=result["graphml_content"],
                message=f"Successfully applied {request.layout_type} layout to the network"
            )
        else:
            return GraphMLResponse(
                success=False,
                error=result.get("error", "Unknown error applying layout")
            )
    except Exception as e:
        return GraphMLResponse(
            success=False,
            error=f"Error applying layout: {str(e)}"
        )

@app.post("/graphml_centrality", tags=["GraphML Operations"])
async def graphml_centrality(request: GraphMLCentralityRequest):
    """
    GraphML形式のネットワークデータに中心性指標を計算します。
    
    Parameters:
        request (GraphMLCentralityRequest): GraphMLデータと中心性タイプを含むリクエストオブジェクト
        
    Returns:
        GraphMLResponse: 中心性値を含む更新されたGraphMLデータを含むレスポンス
    """
    try:
        if not request.graphml_content:
            return GraphMLResponse(
                success=False,
                error="GraphML content is required"
            )
        
        # Import network tools functions
        try:
            from tools.network_tools import calculate_centrality_for_graphml
        except ImportError:
            return GraphMLResponse(
                success=False,
                error="Failed to import required module: calculate_centrality_for_graphml"
            )
        
        # Calculate centrality for GraphML data
        result = calculate_centrality_for_graphml(
            request.graphml_content,
            request.centrality_type
        )
        
        if result["success"]:
            return GraphMLResponse(
                success=True,
                graphml_content=result["graphml_content"],
                message=f"Successfully calculated {request.centrality_type} centrality"
            )
        else:
            return GraphMLResponse(
                success=False,
                error=result.get("error", "Unknown error calculating centrality")
            )
    except Exception as e:
        return GraphMLResponse(
            success=False,
            error=f"Error calculating centrality: {str(e)}"
        )

@app.post("/graphml_node_info", tags=["GraphML Operations"])
async def graphml_node_info(request: GraphMLNodeInfoRequest):
    """
    GraphML形式のネットワークデータから特定のノードの情報を取得します。
    
    Parameters:
        request (GraphMLNodeInfoRequest): GraphMLデータとノードIDリストを含むリクエストオブジェクト
        
    Returns:
        Dict: ノード情報と更新されたGraphMLデータを含むレスポンス
    """
    try:
        if not request.graphml_content:
            return {
                "success": False,
                "error": "GraphML content is required"
            }
        
        # Import network tools functions
        try:
            from tools.network_tools import get_node_info_from_graphml
        except ImportError:
            return {
                "success": False,
                "error": "Failed to import required module: get_node_info_from_graphml"
            }
        
        # Get node info from GraphML data
        result = get_node_info_from_graphml(
            request.graphml_content,
            request.node_ids
        )
        
        if result["success"]:
            return {
                "success": True,
                "node_info": result["node_info"],
                "graphml_content": result["graphml_content"]
            }
        else:
            return {
                "success": False,
                "error": result.get("error", "Unknown error getting node info")
            }
    except Exception as e:
        return {
            "success": False,
            "error": f"Error getting node info: {str(e)}"
        }

@app.post("/graphml_highlight_nodes", tags=["GraphML Operations"])
async def graphml_highlight_nodes(request: GraphMLHighlightNodesRequest):
    """
    GraphML形式のネットワークデータ内の特定のノードをハイライトします。
    
    Parameters:
        request (GraphMLHighlightNodesRequest): GraphMLデータとハイライト情報を含むリクエストオブジェクト
        
    Returns:
        GraphMLResponse: ハイライトされたノードを含む更新されたGraphMLデータを含むレスポンス
    """
    try:
        if not request.graphml_content:
            return GraphMLResponse(
                success=False,
                error="GraphML content is required"
            )
        
        # Import network tools functions
        try:
            from tools.network_tools import highlight_nodes_in_graphml
        except ImportError:
            return GraphMLResponse(
                success=False,
                error="Failed to import required module: highlight_nodes_in_graphml"
            )
        
        # Highlight nodes in GraphML data
        result = highlight_nodes_in_graphml(
            request.graphml_content,
            request.node_ids,
            request.highlight_color
        )
        
        if result["success"]:
            return GraphMLResponse(
                success=True,
                graphml_content=result["graphml_content"],
                message=f"Successfully highlighted {len(request.node_ids)} nodes"
            )
        else:
            return GraphMLResponse(
                success=False,
                error=result.get("error", "Unknown error highlighting nodes")
            )
    except Exception as e:
        return GraphMLResponse(
            success=False,
            error=f"Error highlighting nodes: {str(e)}"
        )

@app.post("/graphml_visual_properties", tags=["GraphML Operations"])
async def graphml_visual_properties(request: GraphMLVisualPropertiesRequest):
    """
    GraphML形式のネットワークデータの視覚属性を変更します。
    
    Parameters:
        request (GraphMLVisualPropertiesRequest): GraphMLデータと視覚属性情報を含むリクエストオブジェクト
        
    Returns:
        GraphMLResponse: 更新された視覚属性を含むGraphMLデータを含むレスポンス
    """
    try:
        if not request.graphml_content:
            return GraphMLResponse(
                success=False,
                error="GraphML content is required"
            )
        
        # Import network tools functions
        try:
            from tools.network_tools import change_visual_properties_in_graphml
        except ImportError:
            return GraphMLResponse(
                success=False,
                error="Failed to import required module: change_visual_properties_in_graphml"
            )
        
        # Change visual properties in GraphML data
        result = change_visual_properties_in_graphml(
            request.graphml_content,
            request.property_type,
            request.property_value,
            request.property_mapping
        )
        
        if result["success"]:
            return GraphMLResponse(
                success=True,
                graphml_content=result["graphml_content"],
                message=f"Successfully changed {request.property_type} to {request.property_value}"
            )
        else:
            return GraphMLResponse(
                success=False,
                error=result.get("error", "Unknown error changing visual properties")
            )
    except Exception as e:
        return GraphMLResponse(
            success=False,
            error=f"Error changing visual properties: {str(e)}"
        )

@app.post("/graphml_network_info", tags=["GraphML Operations"])
async def graphml_network_info(request: GraphMLRequest):
    """
    GraphML形式のネットワークデータから情報を取得します。
    
    Parameters:
        request (GraphMLRequest): GraphMLデータを含むリクエストオブジェクト
        
    Returns:
        Dict: ネットワーク情報と更新されたGraphMLデータを含むレスポンス
    """
    try:
        if not request.graphml_content:
            return {
                "success": False,
                "error": "GraphML content is required"
            }
        
        # Import network tools functions
        try:
            from tools.network_tools import get_network_info_from_graphml
        except ImportError:
            return {
                "success": False,
                "error": "Failed to import required module: get_network_info_from_graphml"
            }
        
        # Get network info from GraphML data
        result = get_network_info_from_graphml(request.graphml_content)
        
        if result["success"]:
            return {
                "success": True,
                "network_info": result["network_info"],
                "graphml_content": result["graphml_content"]
            }
        else:
            return {
                "success": False,
                "error": result.get("error", "Unknown error getting network info")
            }
    except Exception as e:
        return {
            "success": False,
            "error": f"Error getting network info: {str(e)}"
        }

@app.post("/graphml_chat", tags=["GraphML Operations"])
async def graphml_chat(request: GraphMLChatMessageRequest):
    """
    GraphMLデータを含むチャットメッセージを処理します。
    
    Parameters:
        request (GraphMLChatMessageRequest): チャットメッセージとGraphMLデータを含むリクエストオブジェクト
        
    Returns:
        Dict: 処理結果と更新されたGraphMLデータを含むレスポンス
    """
    try:
        if not request.message:
            return {
                "success": False,
                "error": "Message is required"
            }
        
        # If GraphML content is not provided, use default message processing
        if not request.graphml_content:
            return await process_chat_message(ChatMessageRequest(message=request.message))
        
        # Parse the GraphML string to get a NetworkX graph
        try:
            from tools.network_tools import parse_graphml_string
        except ImportError:
            return {
                "success": False,
                "error": "Failed to import required module: parse_graphml_string"
            }
        
        result = parse_graphml_string(request.graphml_content)
        
        if not result["success"]:
            return {
                "success": False,
                "error": f"Error parsing GraphML data: {result.get('error', 'Unknown error')}"
            }
        
        # Temporarily update network state with the GraphML data
        temp_network_state = network_state.copy()
        network_state["graph"] = result["graph"]
        network_state["positions"] = result["nodes"]
        network_state["edges"] = result["edges"]
        
        # Process chat message
        chat_result = await process_chat_message(ChatMessageRequest(message=request.message))
        
        # Export updated network to GraphML
        try:
            from tools.network_tools import export_network_as_graphml
        except ImportError:
            # Restore original network state
            network_state.update(temp_network_state)
            return {
                "success": False,
                "error": "Failed to import required module: export_network_as_graphml"
            }
        
        export_result = export_network_as_graphml(
            network_state["graph"],
            positions=network_state["positions"],
            visual_properties=network_state["visual_properties"]
        )
        
        # Restore original network state
        network_state.update(temp_network_state)
        
        if not export_result["success"]:
            return {
                "success": False,
                "error": f"Error exporting updated network to GraphML: {export_result.get('error', 'Unknown error')}"
            }
        
        # Return chat result with updated GraphML
        if chat_result["success"]:
            return {
                "success": True,
                "content": chat_result.get("content", ""),
                "graphml_content": export_result["content"],
                "networkUpdate": chat_result.get("networkUpdate")
            }
        else:
            return {
                "success": False,
                "content": chat_result.get("content", ""),
                "error": chat_result.get("error", "Unknown error processing chat message")
            }
    except Exception as e:
        return {
            "success": False,
            "error": f"Error processing chat message: {str(e)}"
        }

@app.post("/import_graphml", tags=["Network Operations"])
async def import_graphml(request: GraphMLRequest):
    """
    GraphML形式の文字列からネットワークをインポートします。
    
    Parameters:
        request (GraphMLRequest): GraphML形式のデータを含むリクエストオブジェクト
    
    Returns:
        Dict: インポート結果（成功した場合はsuccess=True、ノード、エッジ情報）
    """
    try:
        if not request.graphml_content:
            return {
                "success": False,
                "error": "GraphML content is required"
            }
        
        # Parse the GraphML string
        result = parse_graphml_string(request.graphml_content)
        
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

@app.get("/export_graphml", tags=["Network Operations"])
async def export_graphml():
    """
    現在のネットワークをGraphML形式でエクスポートします。
    
    標準化されたGraphML形式で、ノードには名前（name）、色（color）、サイズ(size)、説明（description）の属性が含まれます。
    
    Returns:
        Dict: エクスポート結果（成功した場合はsuccess=True、GraphML形式のコンテンツ）
    """
    try:
        G = network_state["graph"]
        if not G:
            return {
                "success": False,
                "error": "No network data available"
            }
        
        # Export the network as GraphML
        result = export_network_as_graphml(
            G, 
            positions=network_state["positions"],
            visual_properties=network_state["visual_properties"]
        )
        
        return result
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

@app.post("/convert_graphml", tags=["Network Operations"])
async def convert_graphml(request: GraphMLConvertRequest):
    """
    任意のGraphMLデータを標準形式に変換します。
    
    標準化されたGraphML形式では、ノードには名前（name）、色（color）、サイズ(size)、説明（description）の属性が含まれます。
    
    Parameters:
        request (GraphMLConvertRequest): 変換する元のGraphMLデータを含むリクエストオブジェクト
    
    Returns:
        Dict: 変換結果（成功した場合はsuccess=True、標準化されたGraphML形式のコンテンツ）
    """
    try:
        if not request.graphml_content:
            return {
                "success": False,
                "error": "GraphML content is required"
            }
        
        # Convert the GraphML to standard format
        result = convert_to_standard_graphml(request.graphml_content)
        
        return result
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

@app.post("/process_chat_message", tags=["Network Operations"])
async def process_chat_message(request: ChatMessageRequest):
    """
    チャットメッセージを処理し、ネットワーク操作を実行します。
    
    Parameters:
        request (ChatMessageRequest): 処理するチャットメッセージを含むリクエストオブジェクト
    
    Returns:
        Dict: 処理結果（成功した場合はsuccess=True、応答内容、ネットワーク更新情報（ある場合））
    """
    try:
        if not request.message:
            return {
                "success": False,
                "error": "No message provided"
            }
        
        # 現在のグラフを取得
        G = network_state["graph"]
        
        # Convert message to lowercase for easier matching
        message_lower = request.message.lower()
        
        # まずは中心性に関する質問かどうかを確認
        importance_keywords = [
            "重要", "中心性", "重要度", "中心", "重要なノード", "important", "centrality", 
            "significance", "central", "ノードの大きさ", "中心的", "影響力"
        ]
        
        if any(keyword in message_lower for keyword in importance_keywords):
            # 中心性チャット処理関数を呼び出す
            # ネットワーク情報を取得
            network_info_result = await get_network_info_tool()
            network_info = network_info_result.get("network_info", {}) if network_info_result and network_info_result.get("success") else {}
            
            # 中心性チャット処理を実行
            result = process_centrality_chat_message(request.message, network_info)
            
            if result and result.get("success"):
                # レスポンスの取得
                content = result.get("content", "")
                
                # 推奨された中心性があれば適用
                recommended_centrality = result.get("recommended_centrality")
                if recommended_centrality:
                    centrality_type = recommended_centrality
                    
                    # Apply centrality if mentioned in query
                    apply_keywords = ["適用", "apply", "使用", "使って", "表示", "可視化", "show"]
                    if any(keyword in message_lower for keyword in apply_keywords):
                        try:
                            # Calculate centrality
                            centrality_result = await calculate_centrality_tool(
                                CentralityRequest(centrality_type=centrality_type)
                            )
                            
                            if centrality_result and centrality_result.get("success"):
                                # 中心性を適用した旨を返答に追加
                                return {
                                    "success": True,
                                    "content": f"{content}\n\n{centrality_type}中心性をネットワークに適用しました。ノードのサイズと色は中心性の値に基づいて変更されています。",
                                    "networkUpdate": {
                                        "type": "centrality",
                                        "centralityType": centrality_type
                                    }
                                }
                        except Exception as e:
                            print(f"Error applying centrality: {str(e)}")
                
                # 中心性を適用しない場合は単純に応答を返す
                return {
                    "success": True,
                    "content": content
                }
            else:
                return {
                    "success": False,
                    "content": result.get("content", "中心性に関する質問の処理中にエラーが発生しました。")
                }
        
        # 以下、既存の処理を続行
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
                "content": """ネットワークチャットでは以下の操作が可能です：

1. レイアウトの変更: 「円形レイアウトを使用」または「Fruchterman-Reingoldレイアウトを適用」
2. レイアウトの推奨: 「コミュニティ検出に適したレイアウトを推奨」
3. 中心性の適用: 「次数中心性を表示」または「媒介中心性を適用」
4. ネットワーク情報の表示: 「ネットワーク統計を表示」
5. ノードの重要度に関する質問: 「重要なノードを大きく表示したい」「このネットワークではどの中心性が適していますか？」

「アップロードネットワークファイル」ボタンを使用してネットワークファイルをアップロードすることもできます。"""
            }
        
        # If no operation was recognized
        return {
            "success": False,
            "content": "申し訳ありませんが、その要求を理解できません。「help」と入力すると、実行可能な操作が表示されます。"
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
        
        # レスポンスが正しい形式かどうか検証
        if result and result.get("success") and "network_info" not in result:
            # レスポンスにnetwork_infoキーがない場合、適切な形式で返す
            if result.get("error"):
                # エラーがある場合
                return {
                    "result": {
                        "success": False,
                        "error": result.get("error")
                    }
                }
            else:
                # エラーがない場合（この状況は通常発生しない）
                return {
                    "result": {
                        "success": True,
                        "network_info": {
                            "has_network": False,
                            "current_layout": network_state["layout"],
                            "current_centrality": network_state["centrality"]
                        }
                    }
                }
        
        # 通常のレスポンス
        return {
            "result": result
        }
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

@app.post("/mcp/tools/graphml_layout")
async def mcp_graphml_layout(request: Request):
    """
    Apply a layout algorithm to a network in GraphML format.
    
    Parameters:
        request (Request): FastAPI request with GraphML content and layout info
    
    Returns:
        Dict: Updated GraphML content with node positions
    """
    try:
        # Get request body
        body = await request.json()
        arguments = body.get("arguments", {})
        
        # Call the handler function
        result = await graphml_layout(GraphMLLayoutRequest(**arguments))
        
        # Return response
        return result
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

@app.post("/mcp/tools/graphml_centrality")
async def mcp_graphml_centrality(request: Request):
    """
    Calculate centrality metrics for a network in GraphML format.
    
    Parameters:
        request (Request): FastAPI request with GraphML content and centrality type
    
    Returns:
        Dict: Updated GraphML content with centrality values
    """
    try:
        # Get request body
        body = await request.json()
        arguments = body.get("arguments", {})
        
        # Call the handler function
        result = await graphml_centrality(GraphMLCentralityRequest(**arguments))
        
        # Return response
        return result
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

@app.post("/mcp/tools/graphml_node_info")
async def mcp_graphml_node_info(request: Request):
    """
    Get information about specific nodes in a network in GraphML format.
    
    Parameters:
        request (Request): FastAPI request with GraphML content and node IDs
    
    Returns:
        Dict: Node information and updated GraphML content
    """
    try:
        # Get request body
        body = await request.json()
        arguments = body.get("arguments", {})
        
        # Call the handler function
        result = await graphml_node_info(GraphMLNodeInfoRequest(**arguments))
        
        # Return response
        return result
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

@app.post("/mcp/tools/graphml_highlight_nodes")
async def mcp_graphml_highlight_nodes(request: Request):
    """
    Highlight specific nodes in a network in GraphML format.
    
    Parameters:
        request (Request): FastAPI request with GraphML content and highlight info
    
    Returns:
        Dict: Updated GraphML content with highlighted nodes
    """
    try:
        # Get request body
        body = await request.json()
        arguments = body.get("arguments", {})
        
        # Call the handler function
        result = await graphml_highlight_nodes(GraphMLHighlightNodesRequest(**arguments))
        
        # Return response
        return result
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

@app.post("/mcp/tools/graphml_visual_properties")
async def mcp_graphml_visual_properties(request: Request):
    """
    Change visual properties of nodes or edges in a network in GraphML format.
    
    Parameters:
        request (Request): FastAPI request with GraphML content and visual property info
    
    Returns:
        Dict: Updated GraphML content with changed visual properties
    """
    try:
        # Get request body
        body = await request.json()
        arguments = body.get("arguments", {})
        
        # Call the handler function
        result = await graphml_visual_properties(GraphMLVisualPropertiesRequest(**arguments))
        
        # Return response
        return result
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

@app.post("/mcp/tools/graphml_network_info")
async def mcp_graphml_network_info(request: Request):
    """
    Get information about a network in GraphML format.
    
    Parameters:
        request (Request): FastAPI request with GraphML content
    
    Returns:
        Dict: Network information and updated GraphML content
    """
    try:
        # Get request body
        body = await request.json()
        arguments = body.get("arguments", {})
        
        # Call the handler function
        result = await graphml_network_info(GraphMLRequest(**arguments))
        
        # Return response
        return result
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

@app.post("/mcp/tools/graphml_chat")
async def mcp_graphml_chat(request: Request):
    """
    Process a chat message with GraphML data.
    
    Parameters:
        request (Request): FastAPI request with chat message and GraphML content
    
    Returns:
        Dict: Processing result and updated GraphML content
    """
    try:
        # Get request body
        body = await request.json()
        arguments = body.get("arguments", {})
        
        # Call the handler function
        result = await graphml_chat(GraphMLChatMessageRequest(**arguments))
        
        # Return response
        return result
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

@app.post("/mcp/tools/import_graphml")
async def mcp_import_graphml(request: Request):
    """
    Import a network from GraphML format string.
    
    Parameters:
        request (Request): FastAPI request with GraphML content
    
    Returns:
        Dict: Import result with network data
    """
    try:
        # Get request body
        body = await request.json()
        arguments = body.get("arguments", {})
        
        # Call the handler function
        result = await import_graphml(GraphMLRequest(**arguments))
        
        # Return response
        return result
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

@app.post("/mcp/tools/export_graphml")
async def mcp_export_graphml(request: Request):
    """
    Export the current network as GraphML format.
    
    Returns:
        Dict: Export result with GraphML content
    """
    try:
        # Call the handler function
        result = await export_graphml()
        
        # Return response
        return result
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

@app.post("/mcp/tools/convert_graphml")
async def mcp_convert_graphml(request: Request):
    """
    Convert any GraphML data to the standard format.
    
    Parameters:
        request (Request): FastAPI request with GraphML content to convert
    
    Returns:
        Dict: Conversion result with standardized GraphML content
    """
    try:
        # Get request body
        body = await request.json()
        arguments = body.get("arguments", {})
        
        # Call the handler function
        result = await convert_graphml(GraphMLConvertRequest(**arguments))
        
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
        
        # Return response with network update if available
        if result and result.get("success") and "networkUpdate" in result:
            return {
                "result": {
                    "success": result.get("success"),
                    "content": result.get("content"),
                    "networkUpdate": result.get("networkUpdate")
                }
            }
        else:
            # Return standard response
            return {
                "result": result
            }
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
                    "name": "import_graphml",
                    "description": "Import a network from GraphML format string",
                    "parameters": {
                        "graphml_content": {
                            "type": "string",
                            "description": "GraphML format string"
                        }
                    }
                },
                {
                    "name": "export_graphml",
                    "description": "Export the current network as GraphML format",
                    "parameters": {}
                },
                {
                    "name": "convert_graphml",
                    "description": "Convert any GraphML data to the standard format with name, color, size, and description attributes",
                    "parameters": {
                        "graphml_content": {
                            "type": "string",
                            "description": "GraphML content to convert"
                        }
                    }
                },
                {
                    "name": "graphml_layout",
                    "description": "Apply a layout algorithm to a network in GraphML format",
                    "parameters": {
                        "graphml_content": {
                            "type": "string",
                            "description": "GraphML format string"
                        },
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
                    "name": "graphml_centrality",
                    "description": "Calculate centrality metrics for a network in GraphML format",
                    "parameters": {
                        "graphml_content": {
                            "type": "string",
                            "description": "GraphML format string"
                        },
                        "centrality_type": {
                            "type": "string",
                            "description": "Type of centrality to calculate"
                        }
                    }
                },
                {
                    "name": "graphml_node_info",
                    "description": "Get information about specific nodes in a network in GraphML format",
                    "parameters": {
                        "graphml_content": {
                            "type": "string",
                            "description": "GraphML format string"
                        },
                        "node_ids": {
                            "type": "array",
                            "description": "List of node IDs to get information for"
                        }
                    }
                },
                {
                    "name": "graphml_highlight_nodes",
                    "description": "Highlight specific nodes in a network in GraphML format",
                    "parameters": {
                        "graphml_content": {
                            "type": "string",
                            "description": "GraphML format string"
                        },
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
                    "name": "graphml_visual_properties",
                    "description": "Change visual properties of nodes or edges in a network in GraphML format",
                    "parameters": {
                        "graphml_content": {
                            "type": "string",
                            "description": "GraphML format string"
                        },
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
                    "name": "graphml_network_info",
                    "description": "Get information about a network in GraphML format",
                    "parameters": {
                        "graphml_content": {
                            "type": "string",
                            "description": "GraphML format string"
                        }
                    }
                },
                {
                    "name": "graphml_chat",
                    "description": "Process a chat message with GraphML data",
                    "parameters": {
                        "message": {
                            "type": "string",
                            "description": "The chat message to process"
                        },
                        "graphml_content": {
                            "type": "string",
                            "description": "GraphML format string (optional)"
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
