"""
NetworkX MCP Server
===================

FastAPI Model Context Protocol (MCP) サーバー
ネットワーク分析と可視化のためのAPIを提供します。
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

# グローバルステート
class State:
    graph = None
    positions = []
    edges = []
    visual_properties = {
        "node_size": 5,
        "node_color": "#1d4ed8",
        "edge_width": 1,
        "edge_color": "#94a3b8"
    }
    layout = "spring"
    layout_params = {}
    centrality_type = None
    centrality_values = {}

# グローバルステートの初期化
state = State()

# FastAPIアプリケーションの作成
app = FastAPI(
    title="NetworkX MCP",
    description="Model Context Protocol server for network analysis and visualization using NetworkX",
    version="0.1.0",
)

# CORSミドルウェアの設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# リクエストモデル
class ExportGraphMLParams(BaseModel):
    format: str = Field("graphml", description="Format to export the network as")

class ImportGraphMLParams(BaseModel):
    graphml_content: str = Field(..., description="GraphML content to import")

# 基本的なヘルパー関数

def apply_layout(G, layout_type, **kwargs):
    """レイアウトアルゴリズムを適用する"""
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

def calculate_centrality(G, centrality_type, **kwargs):
    """中心性指標を計算する"""
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

def export_network_as_graphml(G, positions=None, visual_properties=None):
    """ネットワークをGraphML形式でエクスポートする"""
    try:
        # Create a copy of the graph to avoid modifying the original
        export_G = G.copy()
        
        # Add standard node attributes (name, color, size, description) if not present
        for node in export_G.nodes():
            node_str = str(node)
            
            # Set default attributes if not present
            if 'name' not in export_G.nodes[node]:
                export_G.nodes[node]['name'] = node_str
                
            if 'size' not in export_G.nodes[node]:
                export_G.nodes[node]['size'] = "5.0"  # Default size
                
            if 'color' not in export_G.nodes[node]:
                export_G.nodes[node]['color'] = "#1d4ed8"  # Default color
                
            if 'description' not in export_G.nodes[node]:
                export_G.nodes[node]['description'] = f"Node {node_str}"
        
        # Add positions if provided
        if positions:
            pos_dict = {}
            for node_pos in positions:
                node_id = node_pos["id"]
                if node_id.isdigit():
                    try:
                        node_id = int(node_id)
                    except:
                        pass
                
                if node_id in export_G.nodes():
                    # Add position attributes
                    export_G.nodes[node_id]['x'] = str(node_pos.get('x', 0.0))
                    export_G.nodes[node_id]['y'] = str(node_pos.get('y', 0.0))
                    
                    # Add other visual attributes if present
                    if 'size' in node_pos:
                        export_G.nodes[node_id]['size'] = str(node_pos['size'])
                    if 'color' in node_pos:
                        export_G.nodes[node_id]['color'] = node_pos['color']
                    if 'label' in node_pos:
                        export_G.nodes[node_id]['name'] = node_pos['label']
        
        # Add global visual properties if provided
        if visual_properties:
            # Add graph-level attributes
            export_G.graph['node_default_size'] = str(visual_properties.get('node_size', 5))
            export_G.graph['node_default_color'] = visual_properties.get('node_color', '#1d4ed8')
            export_G.graph['edge_default_width'] = str(visual_properties.get('edge_width', 1))
            export_G.graph['edge_default_color'] = visual_properties.get('edge_color', '#94a3b8')
        
        # Export to GraphML
        output = io.BytesIO()
        nx.write_graphml(export_G, output)
        output.seek(0)
        graphml_content = output.read().decode("utf-8")
        
        return {
            "success": True,
            "format": "graphml",
            "content": graphml_content
        }
    except Exception as e:
        logger.error(f"Error exporting network as GraphML: {e}")
        return {
            "success": False,
            "error": f"Error exporting network as GraphML: {str(e)}"
        }

def convert_to_standard_graphml(graphml_content):
    """あらゆるGraphMLデータを標準形式に変換する"""
    try:
        # Parse the GraphML content
        content_io = io.BytesIO(graphml_content.encode('utf-8'))
        G = nx.read_graphml(content_io)
        
        # 既存の属性を確認し、標準属性名へのマッピングを検出
        attribute_mapping = {
            'name': ['name', 'label', 'id', 'title', 'node_name', 'node_label'],
            'color': ['color', 'colour', 'node_color', 'fill_color', 'fill', 'rgb', 'hex'],
            'size': ['size', 'node_size', 'width', 'radius', 'scale'],
            'description': ['description', 'desc', 'note', 'info', 'detail', 'tooltip']
        }
        
        # 各ノードに標準属性を追加
        for node in G.nodes():
            node_str = str(node)
            node_attrs = G.nodes[node]
            
            # 名前属性の処理
            if 'name' not in node_attrs:
                # 代替属性を探す
                for alt_attr in attribute_mapping['name']:
                    if alt_attr in node_attrs and alt_attr != 'name':
                        node_attrs['name'] = str(node_attrs[alt_attr])
                        break
                else:
                    # 代替属性が見つからない場合はノードIDを使用
                    node_attrs['name'] = node_str
            
            # 色属性の処理
            if 'color' not in node_attrs:
                # 代替属性を探す
                for alt_attr in attribute_mapping['color']:
                    if alt_attr in node_attrs and alt_attr != 'color':
                        node_attrs['color'] = str(node_attrs[alt_attr])
                        break
                else:
                    # 代替属性が見つからない場合はデフォルト色を使用
                    node_attrs['color'] = "#1d4ed8"  # Default color
            
            # サイズ属性の処理
            if 'size' not in node_attrs:
                # 代替属性を探す
                for alt_attr in attribute_mapping['size']:
                    if alt_attr in node_attrs and alt_attr != 'size':
                        node_attrs['size'] = str(node_attrs[alt_attr])
                        break
                else:
                    # 代替属性が見つからない場合はデフォルトサイズを使用
                    node_attrs['size'] = "5.0"  # Default size
            
            # 説明属性の処理
            if 'description' not in node_attrs:
                # 代替属性を探す
                for alt_attr in attribute_mapping['description']:
                    if alt_attr in node_attrs and alt_attr != 'description':
                        node_attrs['description'] = str(node_attrs[alt_attr])
                        break
                else:
                    # 代替属性が見つからない場合はデフォルト説明を使用
                    node_attrs['description'] = f"Node {node_str}"
        
        # グラフレベルの属性を追加
        G.graph['node_default_size'] = "5.0"
        G.graph['node_default_color'] = "#1d4ed8"
        G.graph['edge_default_width'] = "1.0"
        G.graph['edge_default_color'] = "#94a3b8"
        G.graph['graph_format_version'] = "1.0"
        G.graph['graph_format_type'] = "standardized_graphml"
        
        # エッジにも標準的な属性を追加
        for u, v, data in G.edges(data=True):
            if 'width' not in data:
                data['width'] = "1.0"
            if 'color' not in data:
                data['color'] = "#94a3b8"
        
        # 標準化されたGraphMLにエクスポート
        output = io.BytesIO()
        nx.write_graphml(G, output)
        output.seek(0)
        standardized_graphml = output.read().decode("utf-8")
        
        return {
            "success": True,
            "graph": G,
            "graphml_content": standardized_graphml
        }
    except Exception as e:
        logger.error(f"Error converting GraphML: {e}")
        return {
            "success": False,
            "error": f"Error converting GraphML: {str(e)}"
        }

def parse_graphml_string(graphml_content):
    """GraphML文字列をパースしてNetworkXグラフとノード・エッジ情報を抽出する"""
    try:
        # Parse the GraphML content
        content_io = io.BytesIO(graphml_content.encode('utf-8'))
        G = nx.read_graphml(content_io)
        
        # Extract nodes and edges
        nodes = []
        for node in G.nodes(data=True):
            node_id = str(node[0])
            attrs = node[1]
            
            node_data = {
                "id": node_id,
                "label": attrs.get("name", node_id)
            }
            
            # Add position if available
            if 'x' in attrs and 'y' in attrs:
                try:
                    node_data['x'] = float(attrs['x'])
                    node_data['y'] = float(attrs['y'])
                except (ValueError, TypeError):
                    pass
            
            # Add size if available
            if 'size' in attrs:
                try:
                    node_data['size'] = float(attrs['size'])
                except (ValueError, TypeError):
                    node_data['size'] = 5.0
            
            # Add color if available
            if 'color' in attrs:
                node_data['color'] = attrs['color']
            
            # Add any additional node attributes
            for key, value in attrs.items():
                if key not in ["id", "label", "x", "y", "size", "color"]:
                    node_data[key] = value
            
            nodes.append(node_data)
        
        edges = []
        for edge in G.edges(data=True):
            source = str(edge[0])
            target = str(edge[1])
            attrs = edge[2]
            
            edge_data = {
                "source": source,
                "target": target
            }
            
            # Add width if available
            if 'width' in attrs:
                try:
                    edge_data['width'] = float(attrs['width'])
                except (ValueError, TypeError):
                    pass
            
            # Add color if available
            if 'color' in attrs:
                edge_data['color'] = attrs['color']
            
            # Add any additional edge attributes
            for key, value in attrs.items():
                if key not in ["source", "target", "width", "color"]:
                    edge_data[key] = value
            
            edges.append(edge_data)
        
        return {
            "success": True,
            "graph": G,
            "nodes": nodes,
            "edges": edges
        }
    except Exception as e:
        logger.error(f"Error parsing GraphML string: {e}")
        return {
            "success": False,
            "error": f"Error parsing GraphML string: {str(e)}"
        }


# ヘルスチェックエンドポイント
@app.get("/health")
async def health_check():
    return {"status": "ok", "timestamp": datetime.now().isoformat()}

# サンプルネットワークの作成
def create_sample_network():
    try:
        logger.info("ネットワークが存在しません。サンプルネットワークを生成します。")
        
        # ノード数とエッジ確率をランダムに設定
        num_nodes = random.randint(18, 25)  # 18〜25のランダムなノード数
        edge_probability = random.uniform(0.15, 0.25)  # 15%〜25%のランダムな確率
        
        # ランダムグラフを生成
        G = nx.gnp_random_graph(num_nodes, edge_probability)
        
        # 連結グラフを確保（孤立ノードがないようにする）
        if not nx.is_connected(G):
            # 連結成分を取得
            components = list(nx.connected_components(G))
            # 最大の連結成分以外の各成分から、最大成分へエッジを追加
            largest_component = max(components, key=len)
            for component in components:
                if component != largest_component:
                    # 各成分から最大成分へのエッジを追加
                    node_from = random.choice(list(component))
                    node_to = random.choice(list(largest_component))
                    G.add_edge(node_from, node_to)
        
        # ノードとエッジの情報を抽出
        nodes = []
        for node in G.nodes():
            # ノードごとに少し異なるサイズと色の変化をつける
            size_variation = random.uniform(4.5, 5.5)
            color_variation = random.randint(-15, 15)
            base_color = [29, 78, 216]  # #1d4ed8のRGB値
            
            # 色の変化を適用（範囲内に収める）
            r = max(0, min(255, base_color[0] + color_variation))
            g = max(0, min(255, base_color[1] + color_variation))
            b = max(0, min(255, base_color[2] + color_variation))
            
            nodes.append({
                "id": str(node),
                "label": f"Node {node}",
                "size": size_variation,
                "color": f"rgb({r}, {g}, {b})"
            })
        
        edges = []
        for edge in G.edges():
            edges.append({
                "source": str(edge[0]),
                "target": str(edge[1]),
                "width": 1,
                "color": "#94a3b8"
            })
        
        # スプリングレイアウトを適用
        pos = nx.spring_layout(G)
        
        # ノードの位置情報を追加
        for node in nodes:
            node_id = int(node["id"])
            if node_id in pos:
                node["x"] = float(pos[node_id][0])
                node["y"] = float(pos[node_id][1])
        
        # グローバルステートを更新
        state.graph = G
        state.positions = nodes
        state.edges = edges
        state.layout = "spring"
        state.layout_params = {}
        
        return {
            "success": True,
            "nodes": nodes,
            "edges": edges,
            "layout": "spring",
            "layout_params": {}
        }
    except Exception as e:
        logger.error(f"Error creating sample network: {e}")
        return {
            "success": False,
            "error": f"Error creating sample network: {str(e)}"
        }

# サンプルネットワーク取得エンドポイント
@app.get("/get_sample_network")
async def get_sample_network():
    if state.graph is None:
        return create_sample_network()
    else:
        return {
            "success": True,
            "nodes": state.positions,
            "edges": state.edges,
            "layout": state.layout,
            "layout_params": state.layout_params
        }

# GraphML形式のエクスポートエンドポイント
@app.post("/tools/export_graphml")
async def api_export_graphml(params: ExportGraphMLParams = Body(ExportGraphMLParams())):
    try:
        if state.graph is None:
            return {"result": {"success": False, "error": "No network loaded"}}
        
        result = export_network_as_graphml(state.graph, state.positions, state.visual_properties)
        return {"result": result}
    except Exception as e:
        logger.error(f"Error exporting network as GraphML: {e}")
        return {"result": {"success": False, "error": f"Error exporting network as GraphML: {str(e)}"}}

# GraphML形式のインポートエンドポイント
@app.post("/tools/import_graphml")
async def api_import_graphml(params: ImportGraphMLParams):
    try:
        # 標準化されたGraphMLに変換
        conversion_result = convert_to_standard_graphml(params.graphml_content)
        if not conversion_result["success"]:
            return {"result": conversion_result}
        
        # 変換されたGraphMLをパース
        result = parse_graphml_string(conversion_result["graphml_content"])
        
        if result["success"]:
            # グローバルステートを更新
            state.graph = result["graph"]
            state.positions = result["nodes"]
            state.edges = result["edges"]
            del result["graph"]
        
        return {"result": result}
    except Exception as e:
        logger.error(f"Error importing GraphML: {e}")
        return {"result": {"success": False, "error": f"Error importing GraphML: {str(e)}"}}


# レイアウト変更エンドポイント
@app.post("/tools/change_layout")
async def api_change_layout(params: dict = Body(...)):
    try:
        if state.graph is None:
            return {"result": {"success": False, "error": "No network loaded"}}
        
        layout_type = params.get("layout_type", "spring")
        layout_params = params.get("layout_params", {})
        
        # レイアウトの適用
        pos = apply_layout(state.graph, layout_type, **layout_params)
        
        # ノードの位置情報を更新
        for node in state.positions:
            node_id = node["id"]
            if node_id.isdigit():
                node_id = int(node_id)
            
            if node_id in pos:
                node["x"] = float(pos[node_id][0])
                node["y"] = float(pos[node_id][1])
        
        # グローバルステートを更新
        state.layout = layout_type
        state.layout_params = layout_params
        
        return {"result": {
            "success": True,
            "layout": layout_type,
            "layout_params": layout_params,
            "positions": state.positions
        }}
    except Exception as e:
        logger.error(f"Error changing layout: {e}")
        return {"result": {"success": False, "error": f"Error changing layout: {str(e)}"}}

# 中心性計算エンドポイント
@app.post("/tools/calculate_centrality")
async def api_calculate_centrality(params: dict = Body(...)):
    try:
        if state.graph is None:
            return {"result": {"success": False, "error": "No network loaded"}}
        
        centrality_type = params.get("centrality_type", "degree")
        calc_params = params.get("params", {})
        
        # 中心性の計算
        centrality_values = calculate_centrality(state.graph, centrality_type, **calc_params)
        
        # 値の正規化
        max_value = max(centrality_values.values()) if centrality_values else 1.0
        
        # ノードのサイズと色を中心性に基づいて更新
        for node in state.positions:
            node_id = node["id"]
            if node_id in centrality_values:
                value = centrality_values[node_id]
                # サイズの更新 (スケール: 5-15)
                node["size"] = 5 + (value / max_value) * 10
                # 色の更新 (青から赤へのグラデーション)
                r = int(255 * (value / max_value))
                b = int(255 * (1 - (value / max_value)))
                node["color"] = f"rgb({r}, 70, {b})"
        
        # グローバルステートを更新
        state.centrality_type = centrality_type
        state.centrality_values = {str(k): v for k, v in centrality_values.items()}
        
        return {"result": {
            "success": True,
            "centrality_type": centrality_type,
            "centrality_values": state.centrality_values
        }}
    except Exception as e:
        logger.error(f"Error calculating centrality: {e}")
        return {"result": {"success": False, "error": f"Error calculating centrality: {str(e)}"}}

# MCP情報エンドポイント
@app.get("/info")
async def get_mcp_info():
    """MCPサーバーの情報を返す"""
    return {
        "success": True,
        "name": "NetworkX MCP",
        "version": "0.1.0",
        "description": "NetworkX graph analysis and visualization MCP server",
        "tools": [
            {
                "name": "get_sample_network",
                "description": "Get a sample network"
            },
            {
                "name": "export_graphml",
                "description": "Export the current network as GraphML"
            },
            {
                "name": "import_graphml",
                "description": "Import a network from GraphML"
            },
            {
                "name": "change_layout",
                "description": "Change the layout algorithm for the network"
            },
            {
                "name": "calculate_centrality",
                "description": "Calculate centrality metrics for the network"
            }
        ]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
