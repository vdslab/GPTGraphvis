"""
Layout functions for the NetworkX MCP server.
"""

import networkx as nx
import numpy as np
from typing import Dict, Any, Optional, List, Tuple

def get_available_layouts() -> List[str]:
    """
    Get a list of available layout algorithms.
    
    Returns:
        List of layout algorithm names
    """
    return [
        "spring",
        "circular",
        "random",
        "spectral",
        "shell",
        "spiral",
        "kamada_kawai",
        "fruchterman_reingold",
        "bipartite",
        "multipartite",
        "planar"
    ]

def apply_layout(G: nx.Graph, layout_type: str, **kwargs) -> Dict[Any, Tuple[float, float]]:
    """
    Apply a layout algorithm to a graph.
    
    Args:
        G: NetworkX graph
        layout_type: Type of layout algorithm
        **kwargs: Additional parameters for the layout algorithm
        
    Returns:
        Dictionary mapping node IDs to (x, y) coordinates
    """
    # Define layout functions
    layout_functions = {
        "spring": nx.spring_layout,
        "circular": nx.circular_layout,
        "random": nx.random_layout,
        "spectral": nx.spectral_layout,
        "shell": nx.shell_layout,
        "kamada_kawai": nx.kamada_kawai_layout,
        "fruchterman_reingold": nx.fruchterman_reingold_layout
    }
    
    # Add special layouts
    if layout_type == "spiral":
        return spiral_layout(G, **kwargs)
    elif layout_type == "bipartite" and nx.is_bipartite(G):
        return bipartite_layout(G, **kwargs)
    elif layout_type == "multipartite":
        return multipartite_layout(G, **kwargs)
    elif layout_type == "planar" and nx.is_planar(G):
        return planar_layout(G, **kwargs)
    
    # Use standard NetworkX layouts
    if layout_type in layout_functions:
        return layout_functions[layout_type](G, **kwargs)
    else:
        # Default to spring layout
        return nx.spring_layout(G, **kwargs)

def spiral_layout(G: nx.Graph, **kwargs) -> Dict[Any, Tuple[float, float]]:
    """
    Create a spiral layout for a graph.
    
    Args:
        G: NetworkX graph
        **kwargs: Additional parameters
        
    Returns:
        Dictionary mapping node IDs to (x, y) coordinates
    """
    nodes = list(G.nodes())
    n = len(nodes)
    pos = {}
    
    # Parameters
    radius_step = kwargs.get("radius_step", 0.1)
    angle_step = kwargs.get("angle_step", 0.5)
    
    # Create spiral
    radius = 0.0
    angle = 0.0
    for i, node in enumerate(nodes):
        x = radius * np.cos(angle)
        y = radius * np.sin(angle)
        pos[node] = (x, y)
        
        # Update radius and angle
        radius += radius_step / (i + 1)
        angle += angle_step
    
    return pos

def bipartite_layout(G: nx.Graph, **kwargs) -> Dict[Any, Tuple[float, float]]:
    """
    Create a bipartite layout for a graph.
    
    Args:
        G: NetworkX graph (must be bipartite)
        **kwargs: Additional parameters
        
    Returns:
        Dictionary mapping node IDs to (x, y) coordinates
    """
    # Get bipartite sets
    try:
        top, bottom = nx.bipartite.sets(G)
    except:
        # Fallback to spring layout if not bipartite
        return nx.spring_layout(G, **kwargs)
    
    top = list(top)
    bottom = list(bottom)
    
    # Parameters
    height = kwargs.get("height", 1.0)
    width = kwargs.get("width", 1.0)
    
    # Create positions
    pos = {}
    
    # Position nodes in top set
    for i, node in enumerate(top):
        pos[node] = (width * i / max(1, len(top) - 1), height)
    
    # Position nodes in bottom set
    for i, node in enumerate(bottom):
        pos[node] = (width * i / max(1, len(bottom) - 1), 0.0)
    
    return pos

def multipartite_layout(G: nx.Graph, **kwargs) -> Dict[Any, Tuple[float, float]]:
    """
    Create a multipartite layout for a graph.
    
    Args:
        G: NetworkX graph
        **kwargs: Additional parameters
        
    Returns:
        Dictionary mapping node IDs to (x, y) coordinates
    """
    # Parameters
    partition = kwargs.get("partition", None)
    
    if partition is None:
        # Try to detect communities
        try:
            import community as community_louvain
            partition = community_louvain.best_partition(G)
        except:
            # Fallback to spring layout
            return nx.spring_layout(G, **kwargs)
    
    # Get unique partition values
    partitions = set(partition.values())
    num_partitions = len(partitions)
    
    # Create positions
    pos = {}
    
    # Group nodes by partition
    partition_nodes = {}
    for node, part in partition.items():
        if part not in partition_nodes:
            partition_nodes[part] = []
        partition_nodes[part].append(node)
    
    # Position nodes in each partition
    for part, nodes in partition_nodes.items():
        # Calculate y-coordinate for this partition
        y = 1.0 - (part / max(1, num_partitions - 1))
        
        # Position nodes horizontally
        for i, node in enumerate(nodes):
            x = i / max(1, len(nodes) - 1)
            pos[node] = (x, y)
    
    return pos

def planar_layout(G: nx.Graph, **kwargs) -> Dict[Any, Tuple[float, float]]:
    """
    Create a planar layout for a graph.
    
    Args:
        G: NetworkX graph (must be planar)
        **kwargs: Additional parameters
        
    Returns:
        Dictionary mapping node IDs to (x, y) coordinates
    """
    try:
        # Use NetworkX's planar layout
        return nx.planar_layout(G, **kwargs)
    except:
        # Fallback to spring layout
        return nx.spring_layout(G, **kwargs)
