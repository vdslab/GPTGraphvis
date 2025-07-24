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

def export_network_as_graphml(G: nx.Graph, include_positions: bool = True, include_visual_properties: bool = True) -> Dict[str, Any]:
    """
    Export the network as GraphML format.
    
    Args:
        G: NetworkX graph
        include_positions: Whether to include node positions in the GraphML
        include_visual_properties: Whether to include visual properties in the GraphML
        
    Returns:
        Dictionary with GraphML content
    """
    try:
        # Create a copy of the graph to avoid modifying the original
        export_G = G.copy()
        
        # Add positions and visual properties if requested
        if include_positions:
            # Add positions from network_state
            pass
        
        if include_visual_properties:
            # Add visual properties from network_state
            pass
        
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
