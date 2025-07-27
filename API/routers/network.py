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
        
        nodes = [{"data": {"id": str(n), **G.nodes[n]}} for n in G.nodes()]
        edges = [{"data": {"source": str(u), "target": str(v), **d}} for u, v, d in G.edges(data=True)]
        
        return {"elements": nodes + edges}
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

@router.post("/upload", response_model=schemas.Conversation)
async def upload_new_network(
    file: UploadFile = File(...),
    current_user: models.User = Depends(auth.get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Upload a GraphML file to create a new conversation and network.
    """
    if not file.filename.endswith(".graphml"):
        raise HTTPException(status_code=400, detail="Invalid file type. Please upload a .graphml file.")
    
    try:
        graphml_content = await file.read()
        
        # Validate GraphML content
        try:
            G = nx.read_graphml(io.StringIO(graphml_content.decode("utf-8")))
            print(f"Successfully validated GraphML: Nodes: {G.number_of_nodes()}, Edges: {G.number_of_edges()}")
        except Exception as validate_error:
            print(f"Error validating GraphML: {str(validate_error)}")
            raise HTTPException(status_code=400, detail=f"Invalid GraphML content: {str(validate_error)}")
        
        # Create a new conversation
        try:
            db_conversation = models.Conversation(
                title=f"Conversation for {file.filename}",
                user_id=current_user.id
            )
            db.add(db_conversation)
            db.commit()
            db.refresh(db_conversation)
            print(f"Created conversation with ID: {db_conversation.id}")
        except Exception as db_error:
            print(f"Error creating conversation: {str(db_error)}")
            raise HTTPException(status_code=500, detail=f"Error creating conversation: {str(db_error)}")
        
        # Create the associated network
        try:
            db_network = models.Network(
                name=file.filename,
                conversation_id=db_conversation.id,
                graphml_content=graphml_content.decode("utf-8")
            )
            db.add(db_network)
            db.commit()
            db.refresh(db_conversation) # Refresh to get the network relationship loaded
            print(f"Created network for conversation ID: {db_conversation.id}")
        except Exception as network_error:
            print(f"Error creating network: {str(network_error)}")
            # Rollback conversation if network creation fails
            db.delete(db_conversation)
            db.commit()
            raise HTTPException(status_code=500, detail=f"Error creating network: {str(network_error)}")
        
        return db_conversation
    except HTTPException:
        raise
    except Exception as e:
        print(f"Unexpected error in upload_new_network: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

@router.post("/{network_id}/upload", response_model=schemas.Network)
async def upload_and_overwrite_network(
    network_id: int,
    file: UploadFile = File(...),
    current_user: models.User = Depends(auth.get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Upload a GraphML file to overwrite an existing network.
    """
    if not file.filename.endswith(".graphml"):
        raise HTTPException(status_code=400, detail="Invalid file type. Please upload a .graphml file.")
        
    db_network = get_network_for_user(db, network_id, current_user.id)
    
    graphml_content = await file.read()
    db_network.graphml_content = graphml_content.decode("utf-8")
    db_network.name = file.filename
    db.commit()
    db.refresh(db_network)
    
    return db_network
