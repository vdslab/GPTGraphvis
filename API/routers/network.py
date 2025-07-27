"""
Network router for the API.
Handles network data operations like import, export, and formatting for visualization.
"""

from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, Response
from sqlalchemy.orm import Session
from typing import Dict, Any
import networkx as nx
import io
import json

import models
import schemas
import auth
from database import get_db
from . import proxy

router = APIRouter(
    prefix="/network",
    tags=["network"],
    dependencies=[Depends(auth.get_current_active_user)],
    responses={404: {"description": "Not found"}},
)

def get_network_for_user(db: Session, network_id: int, user_id: int) -> models.Network:
    """Helper to get a network and verify ownership."""
    db_network = db.query(models.Network).filter(
        models.Network.id == network_id
    ).first()

    if not db_network:
        raise HTTPException(status_code=404, detail="Network not found")

    # Check if the network's conversation belongs to the current user
    if db_network.conversation.user_id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized to access this network")
        
    return db_network

@router.get("/{network_id}/cytoscape", response_model=Dict[str, Any])
async def get_network_cytoscape_format(
    network_id: int,
    current_user: models.User = Depends(auth.get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get network data in Cytoscape.js JSON format.
    """
    db_network = get_network_for_user(db, network_id, current_user.id)
    
    try:
        G = nx.read_graphml(io.StringIO(db_network.graphml_content))
        
        # 位置情報もCytoscape形式に含める
        nodes = []
        for n, data in G.nodes(data=True):
            node_data = {"data": {"id": str(n), **data}}
            if 'x' in data and 'y' in data:
                node_data["position"] = {"x": data['x'], "y": data['y']}
            nodes.append(node_data)
            
        edges = [{"data": {"source": str(u), "target": str(v), **d}} for u, v, d in G.edges(data=True)]
        
        return {"elements": {"nodes": nodes, "edges": edges}}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing GraphML: {str(e)}")

@router.get("/{network_id}/export")
async def export_network_graphml(
    network_id: int,
    current_user: models.User = Depends(auth.get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Export the network as a GraphML file.
    """
    db_network = get_network_for_user(db, network_id, current_user.id)
    return Response(
        content=db_network.graphml_content,
        media_type="application/xml",
        headers={"Content-Disposition": f"attachment; filename=network_{network_id}.graphml"}
    )

@router.post("/upload", response_model=Dict[str, int])
async def upload_new_network(
    file: UploadFile = File(...),
    current_user: models.User = Depends(auth.get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Upload a GraphML file to create a new conversation and network.
    The file is first sent to NetworkXMCP for normalization.
    """
    if not file.filename.endswith(".graphml"):
        raise HTTPException(status_code=400, detail="Invalid file type. Please upload a .graphml file.")
    
    try:
        graphml_content_bytes = await file.read()
        graphml_content_str = graphml_content_bytes.decode("utf-8")

        # Call NetworkXMCP to convert/normalize the GraphML
        normalized_graphml_str = await proxy.convert_graphml_through_proxy(graphml_content_str)

        # Create a new conversation
        db_conversation = models.Conversation(
            title=f"Conversation for {file.filename}",
            user_id=current_user.id
        )
        db.add(db_conversation)
        db.commit()
        db.refresh(db_conversation)

        # Create the associated network with the normalized content
        db_network = models.Network(
            name=file.filename,
            conversation_id=db_conversation.id,
            graphml_content=normalized_graphml_str
        )
        db.add(db_network)
        db.commit()
        db.refresh(db_network)

        return {"conversation_id": db_conversation.id, "network_id": db_network.id}

    except HTTPException as e:
        # Re-raise HTTPException to preserve status code and detail
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")


@router.post("/{conversation_id}/upload", response_model=schemas.Network)
async def upload_and_overwrite_network(
    conversation_id: int,
    file: UploadFile = File(...),
    current_user: models.User = Depends(auth.get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Upload a GraphML file to overwrite an existing network associated with a conversation.
    """
    if not file.filename.endswith(".graphml"):
        raise HTTPException(status_code=400, detail="Invalid file type. Please upload a .graphml file.")
    
    # Find the conversation and verify ownership
    db_conversation = db.query(models.Conversation).filter(
        models.Conversation.id == conversation_id,
        models.Conversation.user_id == current_user.id
    ).first()

    if not db_conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    db_network = db_conversation.network
    if not db_network:
        raise HTTPException(status_code=404, detail="Network not found for this conversation")

    try:
        graphml_content_bytes = await file.read()
        graphml_content_str = graphml_content_bytes.decode("utf-8")

        # Call NetworkXMCP to convert/normalize the GraphML
        normalized_graphml_str = await proxy.convert_graphml_through_proxy(graphml_content_str)

        # Update the network content
        db_network.graphml_content = normalized_graphml_str
        db_network.name = file.filename
        db.commit()
        db.refresh(db_network)
        
        return db_network
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")
