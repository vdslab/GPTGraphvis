# NetworkX MCP Server

A FastAPI server for network visualization and analysis using NetworkX.

## Overview

This server provides a Model Context Protocol (MCP) interface for network visualization and analysis using NetworkX. It allows clients to:

- Upload network files
- Apply different layout algorithms
- Calculate centrality metrics
- Get network information
- Highlight nodes
- Change visual properties

## Dependencies

The server uses the following dependencies:

- fastapi
- uvicorn
- networkx
- numpy
- pydantic
- python-dotenv
- matplotlib
- scikit-learn
- python-louvain
- fastapi-mcp

## Installation

### Using pip

```bash
pip install -e .
```

### Using Docker

```bash
docker build -t networkx-mcp .
docker run -p 8001:8001 networkx-mcp
```

## Usage

### Running the server

```bash
uvicorn main:app --host 0.0.0.0 --port 8001
```

### API Endpoints

- `/get_sample_network`: Get a sample network (Zachary's Karate Club)
- `/upload_network_file`: Upload a network file and parse it into nodes and edges
- `/change_layout`: Change the layout algorithm for the network visualization
- `/calculate_centrality`: Calculate centrality metrics for nodes in the graph
- `/get_network_info`: Get information about the current network
- `/get_node_info`: Get information about specific nodes in the network
- `/highlight_nodes`: Highlight specific nodes in the network
- `/change_visual_properties`: Change visual properties of nodes or edges
- `/recommend_layout`: Recommend a layout algorithm based on user's question or network properties
- `/process_chat_message`: Process a chat message and execute network operations

### MCP Resources

- `/mcp/resources/network`: Get the current network as an MCP resource

## Package Structure

The package is organized into the following modules:

- `layouts`: Layout algorithms for network visualization
- `metrics`: Centrality metrics for network analysis
- `tools`: Utility functions for network operations

## Development

### Package Management

This package uses `pyproject.toml` for dependency management. To add a new dependency, add it to the `dependencies` list in the `pyproject.toml` file.

### Docker

The Dockerfile uses `uv` for package management. It installs the package in development mode using `uv pip install -e .`.
