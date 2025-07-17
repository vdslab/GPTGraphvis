"""
MCP (Model Context Protocol) server for network visualization.
This server provides tools for manipulating network graphs and visualization parameters.
"""

from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any, Union
import json
import os
import io
import re
from contextlib import asynccontextmanager

# Import local modules
import models
from database import get_db
import auth

# Define MCP models
class MCPToolRequest(BaseModel):
    arguments: Dict[str, Any]

class MCPToolResponse(BaseModel):
    result: Dict[str, Any]

class MCPError(BaseModel):
    error: str
    details: Optional[Dict[str, Any]] = None

# Create FastAPI app
app = FastAPI()

# Define MCP tools
mcp_tools = {}

# Note: All network visualization and analysis functionality has been removed
# as it is now provided by the NetworkX MCP server at http://localhost:8765
