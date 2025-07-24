"""
Centrality functions for the NetworkX MCP server.
"""

import networkx as nx
import numpy as np
from typing import Dict, Any, List

def get_available_centrality_metrics() -> List[str]:
    """
    Get a list of available centrality metrics.
    
    Returns:
        List of centrality metric names
    """
    return [
        "degree",
        "closeness",
        "betweenness",
        "eigenvector",
        "pagerank",
        "katz",
        "load",
        "harmonic",
        "subgraph",
        "clustering"
    ]

def calculate_centrality(G: nx.Graph, centrality_type: str, **kwargs) -> Dict[Any, float]:
    """
    Calculate centrality metrics for nodes in the graph.
    
    Args:
        G: NetworkX graph
        centrality_type: Type of centrality to calculate
        **kwargs: Additional parameters for the centrality calculation
        
    Returns:
        Dictionary mapping node IDs to centrality values
    """
    # Define centrality functions
    centrality_functions = {
        "degree": nx.degree_centrality,
        "closeness": nx.closeness_centrality,
        "betweenness": nx.betweenness_centrality,
        "eigenvector": nx.eigenvector_centrality_numpy,
        "pagerank": nx.pagerank,
        "katz": nx.katz_centrality_numpy,
        "load": nx.load_centrality,
        "harmonic": nx.harmonic_centrality,
        "subgraph": nx.subgraph_centrality,
        "clustering": nx.clustering
    }
    
    # Use the specified centrality function
    if centrality_type in centrality_functions:
        try:
            # グラフが有効かチェック
            if G is None or G.number_of_nodes() == 0:
                print("Warning: Empty graph or no graph provided for centrality calculation")
                return {}
                
            # 特定の中心性指標のための前処理と特別処理
            if centrality_type == "closeness" and not nx.is_connected(G):
                # 非連結グラフの場合、各連結成分ごとに計算
                print("Graph is not connected, calculating closeness centrality for each component")
                centrality = {}
                for component in nx.connected_components(G):
                    subgraph = G.subgraph(component)
                    comp_centrality = nx.closeness_centrality(subgraph, **kwargs)
                    centrality.update(comp_centrality)
                return centrality
            
            elif centrality_type == "eigenvector":
                try:
                    # まず標準のeigenvector_centralityを試す（より高速）
                    return nx.eigenvector_centrality(G, max_iter=1000, **kwargs)
                except (nx.PowerIterationFailedConvergence, ValueError) as e:
                    # 収束しない場合はNumPy版を使用（より安定）
                    print(f"Standard eigenvector centrality failed: {e}. Using NumPy implementation.")
                    return nx.eigenvector_centrality_numpy(G, **kwargs)
            
            # 通常の中心性計算
            return centrality_functions[centrality_type](G, **kwargs)
        
        except Exception as e:
            # エラーのタイプを詳細に出力
            print(f"Error calculating {centrality_type} centrality: {type(e).__name__}: {str(e)}")
            
            # 次数中心性にフォールバック
            try:
                print(f"Falling back to degree centrality")
                return nx.degree_centrality(G)
            except Exception as fallback_error:
                # すべての中心性計算が失敗した場合は空の辞書を返す
                print(f"Fallback to degree centrality also failed: {str(fallback_error)}")
                return {node: 0.0 for node in G.nodes()}
    else:
        # サポートされていない中心性タイプの場合は次数中心性を使用
        print(f"Unsupported centrality type: {centrality_type}, using degree centrality instead")
        return nx.degree_centrality(G)

def normalize_centrality_values(centrality_values: Dict[Any, float]) -> Dict[Any, float]:
    """
    Normalize centrality values to the range [0, 1].
    
    Args:
        centrality_values: Dictionary mapping node IDs to centrality values
        
    Returns:
        Dictionary mapping node IDs to normalized centrality values
    """
    if not centrality_values:
        return {}
    
    # Find min and max values
    min_value = min(centrality_values.values())
    max_value = max(centrality_values.values())
    
    # Avoid division by zero
    if max_value == min_value:
        return {node: 1.0 for node in centrality_values}
    
    # Normalize values
    return {
        node: (value - min_value) / (max_value - min_value)
        for node, value in centrality_values.items()
    }

def get_top_nodes_by_centrality(centrality_values: Dict[Any, float], top_n: int = 5) -> List[Any]:
    """
    Get the top N nodes by centrality value.
    
    Args:
        centrality_values: Dictionary mapping node IDs to centrality values
        top_n: Number of top nodes to return
        
    Returns:
        List of node IDs with the highest centrality values
    """
    if not centrality_values:
        return []
    
    # Sort nodes by centrality value (descending)
    sorted_nodes = sorted(centrality_values.items(), key=lambda x: x[1], reverse=True)
    
    # Return top N nodes
    return [node for node, _ in sorted_nodes[:top_n]]

def get_centrality_distribution(centrality_values: Dict[Any, float], num_bins: int = 10) -> Dict[str, List[float]]:
    """
    Get the distribution of centrality values.
    
    Args:
        centrality_values: Dictionary mapping node IDs to centrality values
        num_bins: Number of bins for the histogram
        
    Returns:
        Dictionary with histogram data
    """
    if not centrality_values:
        return {"bins": [], "counts": []}
    
    # Get centrality values
    values = list(centrality_values.values())
    
    # Create histogram
    counts, bin_edges = np.histogram(values, bins=num_bins)
    
    # Convert to lists for JSON serialization
    return {
        "bins": [float(edge) for edge in bin_edges[:-1]],
        "counts": [int(count) for count in counts]
    }
