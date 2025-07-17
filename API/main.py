import os
from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Optional, Any
import networkx as nx
import numpy as np
from dotenv import load_dotenv

from database import engine, Base
from routers import auth as auth_router
import auth
import models
from mcp_server import app as mcp_app

# Load environment variables
load_dotenv()

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Network Layout API with Authentication",
    description="API for network layout calculation with user authentication and ChatGPT integration",
    version="0.1.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # フロントエンドのオリジンを明示的に許可
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router.router)
# chatgpt, network_chat and network_layout routers have been removed as part of migration to MCP-based design

# Mount MCP server
# Make sure the MCP server is properly initialized
from mcp_server import initialize_sample_network, mcp_tools, app as mcp_app

# Initialize the sample network
initialize_sample_network()

# Register MCP routes directly
@app.post("/mcp/tools/{tool_name}")
async def execute_tool(
    tool_name: str,
    request: Request,
    current_user: models.User = Depends(auth.get_current_user)
):
    """
    Execute an MCP tool.
    """
    if tool_name not in mcp_tools:
        raise HTTPException(status_code=404, detail=f"Tool '{tool_name}' not found")
    
    try:
        # Parse request body
        body = await request.json()
        arguments = body.get("arguments", {})
        
        # Execute tool
        result = await mcp_tools[tool_name](arguments)
        return {"result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/mcp/resources/network")
async def get_network_resource(
    current_user: models.User = Depends(auth.get_current_user)
):
    """
    Get the current network as an MCP resource.
    """
    from mcp_server import network_state
    try:
        return {
            "nodes": [node.dict() for node in network_state["positions"]],
            "edges": [edge.dict() for edge in network_state["edges"]],
            "layout": network_state["layout"],
            "layout_params": network_state["layout_params"],
            "centrality": network_state["centrality"],
            "visual_properties": network_state["visual_properties"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/mcp/manifest")
async def get_manifest():
    """
    Get the MCP server manifest.
    """
    return {
        "name": "network-visualization-mcp",
        "version": "1.1.0",
        "description": "MCP server for network visualization with enhanced features",
        "tools": [
            {
                "name": "upload_network_file",
                "description": "Upload a network file and parse it into nodes and edges",
                "parameters": {
                    "file_content": {
                        "type": "string",
                        "description": "Base64 encoded content of the network file"
                    },
                    "file_name": {
                        "type": "string",
                        "description": "Name of the file being uploaded"
                    },
                    "file_type": {
                        "type": "string",
                        "description": "MIME type of the file"
                    }
                },
                "required": ["file_content", "file_name"]
            },
            {
                "name": "get_sample_network",
                "description": "Get a sample network (Zachary's Karate Club)",
                "parameters": {},
                "required": []
            },
            {
                "name": "recommend_layout",
                "description": "Recommend a layout algorithm based on user's question",
                "parameters": {
                    "question": {
                        "type": "string",
                        "description": "User's question about visualization"
                    }
                },
                "required": ["question"]
            },
            {
                "name": "change_layout",
                "description": "Change the layout algorithm for the network visualization",
                "parameters": {
                    "layout_type": {
                        "type": "string",
                        "description": "Type of layout algorithm"
                    },
                    "layout_params": {
                        "type": "object",
                        "description": "Parameters for the layout algorithm"
                    }
                },
                "required": ["layout_type"]
            },
            {
                "name": "process_chat_message",
                "description": "Process a chat message and execute network operations",
                "parameters": {
                    "message": {
                        "type": "string",
                        "description": "The chat message to process"
                    }
                },
                "required": ["message"]
            }
        ],
        "resources": [
            {
                "name": "network",
                "description": "Current network data including nodes and edges",
                "uri": "/mcp/resources/network"
            }
        ]
    }

class Node(BaseModel):
    id: str
    label: Optional[str] = None

class Edge(BaseModel):
    source: str
    target: str

# Network layout endpoints have been removed as part of migration to MCP-based design

@app.get("/")
async def root():
    return {"message": "Network Layout API is running"}
