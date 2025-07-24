import networkx as nx
import numpy as np
from routers.network_layout import apply_layout

# Create a sample graph
G = nx.Graph()
G.add_nodes_from([
    (1, {"label": "Node 1"}),
    (2, {"label": "Node 2"}),
    (3, {"label": "Node 3"}),
    (4, {"label": "Node 4"}),
    (5, {"label": "Node 5"})
])
G.add_edges_from([
    (1, 2), (1, 3), (2, 3), (3, 4), (4, 5), (5, 1)
])

# Test different layout algorithms
layout_types = [
    "spring", "circular", "random", "spectral", "shell", 
    "spiral", "kamada_kawai", "fruchterman_reingold"
]

for layout_type in layout_types:
    print(f"\nTesting {layout_type} layout:")
    try:
        pos = apply_layout(G, layout_type)
        print(f"  Success! Generated positions for {len(pos)} nodes")
        # Print first node position as example
        first_node = list(pos.keys())[0]
        print(f"  Example - Node {first_node}: {pos[first_node]}")
    except Exception as e:
        print(f"  Error: {str(e)}")

print("\nAll tests completed!")
