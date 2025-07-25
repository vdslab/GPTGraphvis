"""
ネットワーク操作ツールモジュール
===================

NetworkXを使用したグラフの操作ツールを提供します。
"""

import networkx as nx
import numpy as np
import logging
import io
import random
from typing import Dict, List, Any, Optional, Union

# ロギングの設定
logger = logging.getLogger("networkx_mcp.tools.network")

def create_random_network(num_nodes=20, edge_probability=0.2, seed=None):
    """
    ランダムネットワークを作成する
    
    Args:
        num_nodes (int, optional): ノード数
        edge_probability (float, optional): エッジ確率
        seed (int, optional): 乱数シード
        
    Returns:
        tuple: (NetworkXグラフ, ノードリスト, エッジリスト)
    """
    try:
        # 乱数シードの設定
        if seed is not None:
            random.seed(seed)
            np.random.seed(seed)
        
        # ランダムグラフを生成
        G = nx.gnp_random_graph(num_nodes, edge_probability, seed=seed)
        
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
        
        return G, nodes, edges
    except Exception as e:
        logger.error(f"Error creating random network: {e}")
        return None, [], []

def parse_graphml_string(graphml_content):
    """
    GraphML文字列をパースしてNetworkXグラフとノード・エッジ情報を抽出する
    
    Args:
        graphml_content (str): GraphML文字列
        
    Returns:
        dict: 処理結果を含む辞書
    """
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

def convert_to_standard_graphml(graphml_content):
    """
    あらゆるGraphMLデータを標準形式に変換する
    
    Args:
        graphml_content (str): GraphML文字列
        
    Returns:
        dict: 処理結果を含む辞書
    """
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

def export_network_as_graphml(G, positions=None, visual_properties=None):
    """
    ネットワークをGraphML形式でエクスポートする
    
    Args:
        G (nx.Graph): NetworkXグラフ
        positions (list, optional): ノードの位置情報
        visual_properties (dict, optional): ビジュアルプロパティ
        
    Returns:
        dict: 処理結果を含む辞書
    """
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

def get_network_info(G):
    """
    ネットワークの基本情報を取得する
    
    Args:
        G (nx.Graph): NetworkXグラフ
        
    Returns:
        dict: ネットワーク情報
    """
    try:
        # 基本的なネットワーク指標を計算
        num_nodes = G.number_of_nodes()
        num_edges = G.number_of_edges()
        density = nx.density(G)
        
        # 連結成分の計算
        is_connected = nx.is_connected(G)
        num_components = nx.number_connected_components(G) if not is_connected else 1
        
        # 次数の計算
        degrees = [d for _, d in G.degree()]
        avg_degree = sum(degrees) / len(degrees) if degrees else 0
        
        # クラスタリング係数の計算
        clustering = nx.average_clustering(G)
        
        return {
            "num_nodes": num_nodes,
            "num_edges": num_edges,
            "density": density,
            "is_connected": is_connected,
            "num_components": num_components,
            "avg_degree": avg_degree,
            "clustering_coefficient": clustering
        }
    except Exception as e:
        logger.error(f"Error getting network info: {e}")
        return {
            "error": f"Error getting network info: {str(e)}"
        }

def detect_communities(G, algorithm="louvain"):
    """
    コミュニティ検出を行う
    
    Args:
        G (nx.Graph): NetworkXグラフ
        algorithm (str, optional): コミュニティ検出アルゴリズム
        
    Returns:
        dict: コミュニティ検出結果
    """
    try:
        communities = None
        
        if algorithm == "louvain":
            try:
                import community as community_louvain
                partition = community_louvain.best_partition(G)
                # コミュニティごとにノードをグループ化
                community_dict = {}
                for node, community_id in partition.items():
                    if community_id not in community_dict:
                        community_dict[community_id] = []
                    community_dict[community_id].append(node)
                communities = list(community_dict.values())
            except ImportError:
                # フォールバック: NetworkXのコミュニティ検出
                communities = list(nx.community.greedy_modularity_communities(G))
        elif algorithm == "girvan_newman":
            # Girvan-Newmanアルゴリズム
            communities = list(nx.community.girvan_newman(G))
            # 最初の分割のみを使用
            if communities:
                communities = list(communities[0])
        elif algorithm == "label_propagation":
            # ラベル伝播アルゴリズム
            communities = list(nx.community.label_propagation_communities(G))
        else:
            # デフォルト: モジュラリティベースのコミュニティ検出
            communities = list(nx.community.greedy_modularity_communities(G))
        
        # コミュニティ情報を整形
        community_info = []
        for i, community in enumerate(communities):
            community_info.append({
                "id": i,
                "nodes": list(community),
                "size": len(community)
            })
        
        return {
            "success": True,
            "algorithm": algorithm,
            "num_communities": len(communities),
            "communities": community_info
        }
    except Exception as e:
        logger.error(f"Error detecting communities: {e}")
        return {
            "success": False,
            "error": f"Error detecting communities: {str(e)}"
        }
