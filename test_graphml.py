import networkx as nx
import sys

def test_graphml(file_path):
    try:
        G = nx.read_graphml(file_path)
        print(f"Successfully read GraphML file: {file_path}")
        print(f"Nodes: {G.number_of_nodes()}, Edges: {G.number_of_edges()}")
        return True
    except Exception as e:
        print(f"Error reading GraphML file: {file_path}")
        print(f"Error: {str(e)}")
        return False

if __name__ == "__main__":
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
        test_graphml(file_path)
    else:
        print("Please provide a GraphML file path")
        sys.exit(1)
