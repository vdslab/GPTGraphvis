"""
Proxy router for forwarding requests to the NetworkX MCP server.
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
import httpx
from typing import Dict, Any, Optional
import os

import models
import auth

# NetworkX MCP server URL
NETWORKX_MCP_URL = "http://networkx-mcp:8001"

router = APIRouter(
    prefix="/proxy/networkx",
    tags=["proxy"],
    responses={401: {"description": "Unauthorized"}},
)

@router.post("/tools/{tool_name}")
async def proxy_tool(
    tool_name: str,
    request: Request,
    current_user: models.User = Depends(auth.get_current_active_user)
):
    """
    Proxy a tool request to the NetworkX MCP server.
    """
    try:
        # Get request body
        body = await request.json()
        
        # Format request for the NetworkX MCP server
        mcp_request = body.get("arguments", {})
        
        # Forward request to NetworkX MCP server
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{NETWORKX_MCP_URL}/tools/{tool_name}",
                json=mcp_request,
                timeout=30.0
            )
            
            # Return response from NetworkX MCP server
            return JSONResponse(
                content=response.json(),
                status_code=response.status_code
            )
    except httpx.RequestError as e:
        raise HTTPException(
            status_code=503,
            detail=f"Error connecting to NetworkX MCP server: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error proxying request: {str(e)}"
        )

@router.get("/resources/{resource_name}")
async def proxy_resource(
    resource_name: str,
    request: Request,
    current_user: models.User = Depends(auth.get_current_active_user)
):
    """
    Proxy a resource request to the NetworkX MCP server.
    """
    try:
        # Forward request to NetworkX MCP server
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{NETWORKX_MCP_URL}/resources/{resource_name}",
                params=request.query_params,
                timeout=30.0
            )
            
            # Return response from NetworkX MCP server
            return JSONResponse(
                content=response.json(),
                status_code=response.status_code
            )
    except httpx.RequestError as e:
        raise HTTPException(
            status_code=503,
            detail=f"Error connecting to NetworkX MCP server: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error proxying request: {str(e)}"
        )

@router.get("/manifest")
async def proxy_manifest(
    current_user: models.User = Depends(auth.get_current_active_user)
):
    """
    Proxy a manifest request to the NetworkX MCP server.
    """
    try:
        # Forward request to NetworkX MCP server
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{NETWORKX_MCP_URL}/manifest",
                timeout=30.0
            )
            
            # Return response from NetworkX MCP server
            return JSONResponse(
                content=response.json(),
                status_code=response.status_code
            )
    except httpx.RequestError as e:
        raise HTTPException(
            status_code=503,
            detail=f"Error connecting to NetworkX MCP server: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error proxying request: {str(e)}"
        )
