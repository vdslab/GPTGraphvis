import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Optional, Any
import networkx as nx
import numpy as np
from dotenv import load_dotenv

from database import engine, Base
from routers import auth
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
app.include_router(auth.router)
# chatgpt, network_chat and network_layout routers have been removed as part of migration to MCP-based design

# Mount MCP server
# Make sure the MCP server is properly initialized
from mcp_server import initialize_sample_network
initialize_sample_network()
app.mount("/mcp", mcp_app)

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
