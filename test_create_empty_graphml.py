"""
create_empty_graphml関数のテスト
"""

import networkx as nx
import io

def create_empty_graphml() -> str:
    """Creates an empty GraphML string."""
    G = nx.Graph()
    output = io.BytesIO()
    nx.write_graphml(G, output)
    return output.getvalue().decode('utf-8')

def test_create_empty_graphml():
    """create_empty_graphml関数のテスト"""
    graphml = create_empty_graphml()
    print("Generated GraphML:")
    print(graphml)
    
    # GraphMLの形式が正しいか確認
    try:
        G = nx.read_graphml(io.StringIO(graphml))
        print("GraphML is valid")
        print(f"Number of nodes: {len(G.nodes)}")
        print(f"Number of edges: {len(G.edges)}")
    except Exception as e:
        print(f"Error parsing GraphML: {e}")

if __name__ == "__main__":
    test_create_empty_graphml()