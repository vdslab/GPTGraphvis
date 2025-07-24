"""
Network tools for the NetworkX MCP server.
"""

import networkx as nx
import numpy as np
import base64
import io
from typing import Dict, Any, List, Optional, Tuple, Union

def parse_network_file(file_content: str, file_name: str, file_type: str = "") -> Dict[str, Any]:
    """
    Parse a network file and extract nodes and edges.
    
    Args:
        file_content: Base64 encoded content of the network file
        file_name: Name of the file being uploaded
        file_type: MIME type of the file
        
    Returns:
        Dictionary with parsed network data
    """
    try:
        # Decode base64 content
        content_bytes = base64.b64decode(file_content)
        content_io = io.BytesIO(content_bytes)
        
        # Determine file format from extension
        file_extension = file_name.split(".")[-1].lower()
        
        # Parse file based on format
        G = None
        
        if file_extension == "graphml":
            G = nx.read_graphml(content_io)
        elif file_extension == "gexf":
            G = nx.read_gexf(content_io)
        elif file_extension == "gml":
            G = nx.read_gml(content_io)
        elif file_extension == "edgelist":
            G = nx.read_edgelist(content_io)
        elif file_extension == "adjlist":
            G = nx.read_adjlist(content_io)
        elif file_extension == "pajek" or file_extension == "net":
            G = nx.read_pajek(content_io)
        elif file_extension == "json":
            import json
            data = json.loads(content_bytes.decode("utf-8"))
            G = nx.node_link_graph(data)
        else:
            # Try to guess format
            try:
                G = nx.read_graphml(content_io)
            except:
                content_io.seek(0)
                try:
                    G = nx.read_gexf(content_io)
                except:
                    content_io.seek(0)
                    try:
                        G = nx.read_edgelist(content_io)
                    except:
                        return {
                            "success": False,
                            "error": f"Unsupported file format: {file_extension}"
                        }
        
        if G is None:
            return {
                "success": False,
                "error": "Failed to parse network file"
            }
        
        # Extract nodes and edges
        nodes = []
        for node in G.nodes(data=True):
            node_id = str(node[0])
            node_data = {
                "id": node_id,
                "label": node[1].get("label", node_id) if node[1] else node_id
            }
            
            # Add any additional node attributes
            if node[1]:
                for key, value in node[1].items():
                    if key not in ["id", "label"]:
                        node_data[key] = value
            
            nodes.append(node_data)
        
        edges = []
        for edge in G.edges(data=True):
            source = str(edge[0])
            target = str(edge[1])
            edge_data = {
                "source": source,
                "target": target
            }
            
            # Add any additional edge attributes
            if edge[2]:
                for key, value in edge[2].items():
                    edge_data[key] = value
            
            edges.append(edge_data)
        
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

def get_network_info(G: nx.Graph) -> Dict[str, Any]:
    """
    Get information about the network.
    
    Args:
        G: NetworkX graph
        
    Returns:
        Dictionary with network information
    """
    try:
        # Basic network properties
        num_nodes = G.number_of_nodes()
        num_edges = G.number_of_edges()
        density = nx.density(G)
        
        # Connectivity
        is_connected = nx.is_connected(G) if not nx.is_directed(G) else nx.is_weakly_connected(G)
        num_components = nx.number_connected_components(G) if not nx.is_directed(G) else nx.number_weakly_connected_components(G)
        
        # Degree statistics
        degrees = [d for _, d in G.degree()]
        avg_degree = sum(degrees) / num_nodes if num_nodes > 0 else 0
        max_degree = max(degrees) if degrees else 0
        min_degree = min(degrees) if degrees else 0
        
        # Clustering
        clustering_coefficient = nx.average_clustering(G)
        
        # Diameter (only for connected graphs)
        diameter = -1
        if is_connected and num_nodes <= 1000:  # Limit to smaller graphs
            try:
                diameter = nx.diameter(G)
            except:
                diameter = -1
        
        return {
            "success": True,
            "network_info": {
                "num_nodes": num_nodes,
                "num_edges": num_edges,
                "density": density,
                "is_connected": is_connected,
                "num_components": num_components,
                "avg_degree": avg_degree,
                "max_degree": max_degree,
                "min_degree": min_degree,
                "clustering_coefficient": clustering_coefficient,
                "diameter": diameter,
                "is_directed": nx.is_directed(G),
                "is_multigraph": nx.is_multigraph(G)
            }
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Error getting network information: {str(e)}"
        }

def get_node_info(G: nx.Graph, node_ids: List[str], centrality_type: Optional[str] = None, centrality_values: Optional[Dict[str, float]] = None) -> Dict[str, Any]:
    """
    Get information about specific nodes in the network.
    
    Args:
        G: NetworkX graph
        node_ids: List of node IDs to get information for
        centrality_type: Type of centrality (optional)
        centrality_values: Centrality values (optional)
        
    Returns:
        Dictionary with node information
    """
    try:
        node_info = {}
        
        for node_id in node_ids:
            # Convert string node ID to the appropriate type if needed
            node = node_id
            if node_id.isdigit() and int(node_id) in G:
                node = int(node_id)
            elif node_id not in G and node not in G:
                continue
            
            # Get node attributes
            attrs = dict(G.nodes[node]) if node in G.nodes else {}
            
            # Get node degree
            degree = G.degree(node)
            
            # Get neighbors
            neighbors = [str(n) for n in G.neighbors(node)]
            
            # Get centrality value if available
            centrality = None
            if centrality_values and str(node) in centrality_values:
                centrality = centrality_values[str(node)]
            
            # Combine information
            node_info[str(node)] = {
                "attributes": attrs,
                "degree": degree,
                "neighbors": neighbors,
                "num_neighbors": len(neighbors)
            }
            
            if centrality is not None:
                node_info[str(node)]["centrality"] = {
                    "type": centrality_type,
                    "value": centrality
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

def highlight_nodes(network_state: Dict[str, Any], node_ids: List[str], highlight_color: str = "#ff0000") -> Dict[str, Any]:
    """
    Highlight specific nodes in the network.
    
    Args:
        network_state: Current network state
        node_ids: List of node IDs to highlight
        highlight_color: Color to use for highlighting
        
    Returns:
        Dictionary with updated node colors
    """
    try:
        # Get default node color
        default_color = network_state["visual_properties"]["node_color"]
        
        # Update node colors
        for node in network_state["positions"]:
            if node["id"] in node_ids:
                node["color"] = highlight_color
            else:
                node["color"] = default_color
        
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

def change_visual_properties(network_state: Dict[str, Any], property_type: str, property_value: Union[str, float], property_mapping: Dict[str, Union[str, float]] = {}) -> Dict[str, Any]:
    """
    Change visual properties of nodes or edges.
    
    Args:
        network_state: Current network state
        property_type: Type of property to change (node_size, node_color, edge_width, edge_color)
        property_value: Value to set for the property
        property_mapping: Optional mapping of node/edge IDs to property values
        
    Returns:
        Dictionary with updated visual properties
    """
    try:
        # Update global visual property
        network_state["visual_properties"][property_type] = property_value
        
        # Update individual elements
        if property_type.startswith("node_"):
            # Node property
            attribute = property_type.split("_")[1]
            for node in network_state["positions"]:
                if node["id"] in property_mapping:
                    node[attribute] = property_mapping[node["id"]]
                else:
                    node[attribute] = property_value
        elif property_type.startswith("edge_"):
            # Edge property
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

def export_network_as_graphml(G: nx.Graph, positions: List[Dict[str, Any]] = None, visual_properties: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Export the network as GraphML format.
    
    Args:
        G: NetworkX graph
        positions: Node positions from network_state
        visual_properties: Visual properties from network_state
        
    Returns:
        Dictionary with GraphML content
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
        return {
            "success": False,
            "error": f"Error exporting network as GraphML: {str(e)}"
        }

def convert_to_standard_graphml(graphml_content: str) -> Dict[str, Any]:
    """
    あらゆるGraphMLデータを標準形式に変換します。
    
    標準化されたGraphML形式では、ノードには以下の属性が含まれます：
    - name: ノードの名前 (表示ラベルとして使用)
    - color: ノードの色 (16進数カラーコードまたはRGB値)
    - size: ノードのサイズ (float値)
    - description: ノードの説明 (詳細情報として使用)
    
    これらの属性がない場合は自動的に追加されます。
    
    Args:
        graphml_content: GraphML形式の文字列
        
    Returns:
        Dictionary with standardized GraphML content and parsed graph
    """
    print("--- Entering convert_to_standard_graphml ---")
    try:
        print("Attempting to parse GraphML content...")
        # Parse the GraphML content
        content_io = io.BytesIO(graphml_content.encode('utf-8'))
        G = nx.read_graphml(content_io)
        print("Successfully parsed GraphML content into a NetworkX graph.")
        
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
        print(f"--- ERROR in convert_to_standard_graphml ---")
        print(f"Error details: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            "success": False,
            "error": f"Error converting GraphML: {str(e)}"
        }

def parse_graphml_string(graphml_content: str) -> Dict[str, Any]:
    """
    Parse GraphML string into a NetworkX graph and extract nodes and edges.
    
    Args:
        graphml_content: GraphML content as string
        
    Returns:
        Dictionary with parsed network data
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
        return {
            "success": False,
            "error": f"Error parsing GraphML string: {str(e)}"
        }

def apply_layout_to_graphml(graphml_content: str, layout_type: str, layout_params: Dict[str, Any] = {}) -> Dict[str, Any]:
    """
    Apply a layout algorithm to a network in GraphML format.
    
    Args:
        graphml_content: GraphML format string
        layout_type: Type of layout algorithm to apply
        layout_params: Parameters for the layout algorithm
        
    Returns:
        Dictionary with updated GraphML content including node positions
    """
    try:
        # Parse the GraphML content
        content_io = io.BytesIO(graphml_content.encode('utf-8'))
        G = nx.read_graphml(content_io)
        
        # Import layout functions dynamically
        try:
            from layouts.layout_functions import apply_layout
        except ImportError:
            # Fallback implementation
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
        
        # Apply the layout algorithm
        pos = apply_layout(G, layout_type, **layout_params)
        
        # Update node positions in the graph
        for node, position in pos.items():
            G.nodes[node]['x'] = str(float(position[0]))
            G.nodes[node]['y'] = str(float(position[1]))
        
        # Export to GraphML
        output = io.BytesIO()
        nx.write_graphml(G, output)
        output.seek(0)
        updated_graphml = output.read().decode("utf-8")
        
        return {
            "success": True,
            "layout_type": layout_type,
            "layout_params": layout_params,
            "graphml_content": updated_graphml,
            "graph": G
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Error applying layout to GraphML: {str(e)}"
        }

def calculate_centrality_for_graphml(graphml_content: str, centrality_type: str, **kwargs) -> Dict[str, Any]:
    """
    Calculate centrality metrics for a network in GraphML format.
    
    Args:
        graphml_content: GraphML format string
        centrality_type: Type of centrality to calculate
        **kwargs: Additional parameters for the centrality calculation
        
    Returns:
        Dictionary with updated GraphML content including centrality values
    """
    try:
        # Parse the GraphML content
        content_io = io.BytesIO(graphml_content.encode('utf-8'))
        G = nx.read_graphml(content_io)
        
        # Import centrality functions dynamically
        try:
            from metrics.centrality_functions import calculate_centrality
        except ImportError:
            # Fallback implementation
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
        
        # Calculate centrality
        centrality_values = calculate_centrality(G, centrality_type, **kwargs)
        
        # Find max centrality value for normalization
        max_value = max(centrality_values.values()) if centrality_values else 1.0
        
        # Update node attributes in the graph with centrality values and visual properties
        for node, value in centrality_values.items():
            # Add centrality value as node attribute
            G.nodes[node]['centrality_value'] = str(value)
            G.nodes[node]['centrality_type'] = centrality_type
            
            # Update node size based on centrality (scale between 5 and 15)
            G.nodes[node]['size'] = str(5 + (value / max_value) * 10)
            
            # Update node color based on centrality (blue to red gradient)
            ratio = value / max_value
            r = int(255 * ratio)
            b = int(255 * (1 - ratio))
            G.nodes[node]['color'] = f"rgb({r}, 70, {b})"
        
        # Add graph-level attributes
        G.graph['centrality_type'] = centrality_type
        
        # Export to GraphML
        output = io.BytesIO()
        nx.write_graphml(G, output)
        output.seek(0)
        updated_graphml = output.read().decode("utf-8")
        
        return {
            "success": True,
            "centrality_type": centrality_type,
            "graphml_content": updated_graphml,
            "graph": G,
            "centrality_values": {str(node): value for node, value in centrality_values.items()}
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Error calculating centrality for GraphML: {str(e)}"
        }

def highlight_nodes_in_graphml(graphml_content: str, node_ids: List[str], highlight_color: str = "#ff0000") -> Dict[str, Any]:
    """
    Highlight specific nodes in a network in GraphML format.
    
    Args:
        graphml_content: GraphML format string
        node_ids: List of node IDs to highlight
        highlight_color: Color to use for highlighting
        
    Returns:
        Dictionary with updated GraphML content including highlighted nodes
    """
    try:
        # Parse the GraphML content
        content_io = io.BytesIO(graphml_content.encode('utf-8'))
        G = nx.read_graphml(content_io)
        
        # Store original colors for non-highlighted nodes
        default_color = G.graph.get('node_default_color', "#1d4ed8")
        
        # Update node colors in the graph
        for node in G.nodes():
            node_str = str(node)
            if node_str in node_ids:
                G.nodes[node]['color'] = highlight_color
                G.nodes[node]['highlighted'] = "true"
            else:
                G.nodes[node]['color'] = default_color
                G.nodes[node]['highlighted'] = "false"
        
        # Export to GraphML
        output = io.BytesIO()
        nx.write_graphml(G, output)
        output.seek(0)
        updated_graphml = output.read().decode("utf-8")
        
        return {
            "success": True,
            "highlighted_nodes": node_ids,
            "highlight_color": highlight_color,
            "graphml_content": updated_graphml,
            "graph": G
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Error highlighting nodes in GraphML: {str(e)}"
        }

def change_visual_properties_in_graphml(graphml_content: str, property_type: str, property_value: Any, property_mapping: Dict[str, Any] = {}) -> Dict[str, Any]:
    """
    Change visual properties of nodes or edges in a network in GraphML format.
    
    Args:
        graphml_content: GraphML format string
        property_type: Type of property to change (node_size, node_color, edge_width, edge_color)
        property_value: Value to set for the property
        property_mapping: Optional mapping of node/edge IDs to property values
        
    Returns:
        Dictionary with updated GraphML content including changed visual properties
    """
    try:
        # Parse the GraphML content
        content_io = io.BytesIO(graphml_content.encode('utf-8'))
        G = nx.read_graphml(content_io)
        
        # Update graph-level visual properties
        if property_type.startswith("node_"):
            property_name = property_type.split("_")[1]
            G.graph[f'node_default_{property_name}'] = str(property_value) if not isinstance(property_value, str) else property_value
        elif property_type.startswith("edge_"):
            property_name = property_type.split("_")[1]
            G.graph[f'edge_default_{property_name}'] = str(property_value) if not isinstance(property_value, str) else property_value
        
        # Update individual elements
        if property_type == "node_size":
            for node in G.nodes():
                node_str = str(node)
                if node_str in property_mapping:
                    G.nodes[node]['size'] = str(property_mapping[node_str])
                else:
                    G.nodes[node]['size'] = str(property_value)
        elif property_type == "node_color":
            for node in G.nodes():
                node_str = str(node)
                if node_str in property_mapping:
                    G.nodes[node]['color'] = property_mapping[node_str]
                else:
                    G.nodes[node]['color'] = property_value
        elif property_type == "edge_width":
            for u, v, data in G.edges(data=True):
                edge_key = f"{u}-{v}"
                if edge_key in property_mapping:
                    G[u][v]['width'] = str(property_mapping[edge_key])
                else:
                    G[u][v]['width'] = str(property_value)
        elif property_type == "edge_color":
            for u, v, data in G.edges(data=True):
                edge_key = f"{u}-{v}"
                if edge_key in property_mapping:
                    G[u][v]['color'] = property_mapping[edge_key]
                else:
                    G[u][v]['color'] = property_value
        
        # Export to GraphML
        output = io.BytesIO()
        nx.write_graphml(G, output)
        output.seek(0)
        updated_graphml = output.read().decode("utf-8")
        
        return {
            "success": True,
            "property_type": property_type,
            "property_value": property_value,
            "property_mapping": property_mapping,
            "graphml_content": updated_graphml,
            "graph": G
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Error changing visual properties in GraphML: {str(e)}"
        }

def get_network_info_from_graphml(graphml_content: str) -> Dict[str, Any]:
    """
    Extract network information from a network in GraphML format.
    
    Args:
        graphml_content: GraphML format string
        
    Returns:
        Dictionary with network information and updated GraphML content including network info as attributes
    """
    try:
        # Parse the GraphML content
        content_io = io.BytesIO(graphml_content.encode('utf-8'))
        G = nx.read_graphml(content_io)
        
        # Calculate network metrics
        num_nodes = G.number_of_nodes()
        num_edges = G.number_of_edges()
        density = nx.density(G)
        
        # Connectivity
        is_connected = nx.is_connected(G) if not nx.is_directed(G) else nx.is_weakly_connected(G)
        num_components = nx.number_connected_components(G) if not nx.is_directed(G) else nx.number_weakly_connected_components(G)
        
        # Degree statistics
        degrees = [d for _, d in G.degree()]
        avg_degree = sum(degrees) / num_nodes if num_nodes > 0 else 0
        max_degree = max(degrees) if degrees else 0
        min_degree = min(degrees) if degrees else 0
        
        # Clustering
        clustering_coefficient = nx.average_clustering(G)
        
        # Diameter (only for connected graphs)
        diameter = -1
        if is_connected and num_nodes <= 1000:  # Limit to smaller graphs
            try:
                diameter = nx.diameter(G)
            except:
                diameter = -1
        
        # Add network info as graph attributes
        G.graph['num_nodes'] = str(num_nodes)
        G.graph['num_edges'] = str(num_edges)
        G.graph['density'] = str(density)
        G.graph['is_connected'] = str(is_connected).lower()
        G.graph['num_components'] = str(num_components)
        G.graph['avg_degree'] = str(avg_degree)
        G.graph['clustering_coefficient'] = str(clustering_coefficient)
        G.graph['diameter'] = str(diameter)
        G.graph['is_directed'] = str(nx.is_directed(G)).lower()
        G.graph['is_multigraph'] = str(nx.is_multigraph(G)).lower()
        
        # Export to GraphML
        output = io.BytesIO()
        nx.write_graphml(G, output)
        output.seek(0)
        updated_graphml = output.read().decode("utf-8")
        
        # Create network info dictionary
        network_info = {
            "num_nodes": num_nodes,
            "num_edges": num_edges,
            "density": density,
            "is_connected": is_connected,
            "num_components": num_components,
            "avg_degree": avg_degree,
            "max_degree": max_degree,
            "min_degree": min_degree,
            "clustering_coefficient": clustering_coefficient,
            "diameter": diameter,
            "is_directed": nx.is_directed(G),
            "is_multigraph": nx.is_multigraph(G),
            "current_layout": G.graph.get('layout', 'unknown'),
            "current_centrality": G.graph.get('centrality_type', None)
        }
        
        return {
            "success": True,
            "network_info": network_info,
            "graphml_content": updated_graphml,
            "graph": G
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Error getting network info from GraphML: {str(e)}"
        }

def get_node_info_from_graphml(graphml_content: str, node_ids: List[str]) -> Dict[str, Any]:
    """
    Extract information about specific nodes from a network in GraphML format.
    
    Args:
        graphml_content: GraphML format string
        node_ids: List of node IDs to get information for
        
    Returns:
        Dictionary with node information and updated GraphML content
    """
    try:
        # Parse the GraphML content
        content_io = io.BytesIO(graphml_content.encode('utf-8'))
        G = nx.read_graphml(content_io)
        
        node_info = {}
        
        for node_id in node_ids:
            # Handle numeric node IDs
            node = node_id
            if node_id.isdigit():
                try:
                    int_id = int(node_id)
                    if int_id in G.nodes():
                        node = int_id
                except:
                    pass
            
            # Skip if node not in graph
            if node not in G.nodes():
                continue
            
            # Get node attributes
            attrs = dict(G.nodes[node])
            
            # Get node degree
            degree = G.degree(node)
            
            # Get neighbors
            neighbors = [str(n) for n in G.neighbors(node)]
            
            # Get centrality value if available
            centrality = None
            if 'centrality_value' in G.nodes[node] and 'centrality_type' in G.nodes[node]:
                centrality = {
                    "type": G.nodes[node]['centrality_type'],
                    "value": float(G.nodes[node]['centrality_value'])
                }
            
            # Combine information
            node_info[str(node)] = {
                "attributes": attrs,
                "degree": degree,
                "neighbors": neighbors,
                "num_neighbors": len(neighbors)
            }
            
            if centrality is not None:
                node_info[str(node)]["centrality"] = centrality
        
        # Export to GraphML
        output = io.BytesIO()
        nx.write_graphml(G, output)
        output.seek(0)
        updated_graphml = output.read().decode("utf-8")
        
        return {
            "success": True,
            "node_info": node_info,
            "graphml_content": updated_graphml,
            "graph": G
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Error getting node info from GraphML: {str(e)}"
        }

def detect_communities_in_graphml(graphml_content: str, algorithm: str = "louvain") -> Dict[str, Any]:
    """
    Detect communities in a network in GraphML format.
    
    Args:
        graphml_content: GraphML format string
        algorithm: Community detection algorithm to use
        
    Returns:
        Dictionary with community assignments and updated GraphML content
    """
    try:
        # Parse the GraphML content
        content_io = io.BytesIO(graphml_content.encode('utf-8'))
        G = nx.read_graphml(content_io)
        
        # Ensure graph is undirected for community detection
        if nx.is_directed(G):
            G = G.to_undirected()
        
        communities = {}
        
        if algorithm == "louvain":
            try:
                import community as community_louvain
                partition = community_louvain.best_partition(G)
                communities = partition
            except ImportError:
                # Fallback to Girvan-Newman
                algorithm = "girvan_newman"
        
        if algorithm == "girvan_newman":
            try:
                comp = nx.community.girvan_newman(G)
                # Take the first level of communities
                communities_list = tuple(sorted(c) for c in next(comp))
                communities = {str(node): i for i, comm in enumerate(communities_list) for node in comm}
            except:
                # Fallback to greedy modularity
                algorithm = "greedy_modularity"
        
        if algorithm == "greedy_modularity":
            try:
                communities_list = list(nx.community.greedy_modularity_communities(G))
                communities = {str(node): i for i, comm in enumerate(communities_list) for node in comm}
            except:
                return {
                    "success": False,
                    "error": "Failed to detect communities with any algorithm"
                }
        
        # Count communities
        num_communities = len(set(communities.values()))
        
        # Add community assignments as node attributes
        for node, community_id in communities.items():
            try:
                # Handle different node types
                node_key = node
                if isinstance(node, str) and node.isdigit():
                    int_node = int(node)
                    if int_node in G.nodes():
                        node_key = int_node
                
                if node_key in G.nodes():
                    G.nodes[node_key]['community'] = str(community_id)
            except:
                pass
        
        # Add graph-level attributes
        G.graph['community_algorithm'] = algorithm
        G.graph['num_communities'] = str(num_communities)
        
        # Export to GraphML
        output = io.BytesIO()
        nx.write_graphml(G, output)
        output.seek(0)
        updated_graphml = output.read().decode("utf-8")
        
        return {
            "success": True,
            "algorithm": algorithm,
            "communities": {str(node): comm for node, comm in communities.items()},
            "num_communities": num_communities,
            "graphml_content": updated_graphml,
            "graph": G
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Error detecting communities in GraphML: {str(e)}"
        }

def detect_communities(G: nx.Graph, algorithm: str = "louvain") -> Dict[str, Any]:
    """
    Detect communities in the network.
    
    Args:
        G: NetworkX graph
        algorithm: Community detection algorithm to use
        
    Returns:
        Dictionary with community assignments
    """
    try:
        communities = {}
        
        if algorithm == "louvain":
            try:
                import community as community_louvain
                partition = community_louvain.best_partition(G)
                communities = partition
            except ImportError:
                # Fallback to Girvan-Newman
                algorithm = "girvan_newman"
        
        if algorithm == "girvan_newman":
            try:
                comp = nx.community.girvan_newman(G)
                # Take the first level of communities
                communities_list = tuple(sorted(c) for c in next(comp))
                communities = {str(node): i for i, comm in enumerate(communities_list) for node in comm}
            except:
                # Fallback to greedy modularity
                algorithm = "greedy_modularity"
        
        if algorithm == "greedy_modularity":
            try:
                communities_list = list(nx.community.greedy_modularity_communities(G))
                communities = {str(node): i for i, comm in enumerate(communities_list) for node in comm}
            except:
                return {
                    "success": False,
                    "error": "Failed to detect communities with any algorithm"
                }
        
        # Count communities
        num_communities = len(set(communities.values()))
        
        return {
            "success": True,
            "algorithm": algorithm,
            "communities": communities,
            "num_communities": num_communities
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Error detecting communities: {str(e)}"
        }
