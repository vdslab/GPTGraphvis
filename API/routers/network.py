"""
Network router for the API.
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
import json
import datetime

import models
import schemas
import auth
from database import get_db

router = APIRouter(
    prefix="/network",
    tags=["network"],
    responses={401: {"description": "Unauthorized"}},
)

@router.post("/", response_model=schemas.Network)
async def create_network(
    network: schemas.NetworkCreate,
    current_user: models.User = Depends(auth.get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Create a new network.
    """
    db_network = models.Network(
        name=network.name,
        user_id=current_user.id,
        nodes_data=network.nodes_data,
        edges_data=network.edges_data,
        layout_data=network.layout_data,
        meta_data=network.meta_data
    )
    db.add(db_network)
    db.commit()
    db.refresh(db_network)
    return db_network

@router.get("/", response_model=List[schemas.Network])
async def get_networks(
    current_user: models.User = Depends(auth.get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get all networks for the current user.
    """
    return db.query(models.Network).filter(models.Network.user_id == current_user.id).all()

@router.get("/{network_id}", response_model=schemas.Network)
async def get_network(
    network_id: int,
    current_user: models.User = Depends(auth.get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get a specific network.
    """
    db_network = db.query(models.Network).filter(
        models.Network.id == network_id,
        models.Network.user_id == current_user.id
    ).first()
    
    if db_network is None:
        raise HTTPException(status_code=404, detail="Network not found")
    
    return db_network

@router.put("/{network_id}", response_model=schemas.Network)
async def update_network(
    network_id: int,
    network_update: schemas.NetworkUpdate,
    current_user: models.User = Depends(auth.get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Update a network.
    """
    db_network = db.query(models.Network).filter(
        models.Network.id == network_id,
        models.Network.user_id == current_user.id
    ).first()
    
    if db_network is None:
        raise HTTPException(status_code=404, detail="Network not found")
    
    # Update fields that are provided
    if network_update.name is not None:
        db_network.name = network_update.name
    if network_update.nodes_data is not None:
        db_network.nodes_data = network_update.nodes_data
    if network_update.edges_data is not None:
        db_network.edges_data = network_update.edges_data
    if network_update.layout_data is not None:
        db_network.layout_data = network_update.layout_data
    if network_update.meta_data is not None:
        db_network.meta_data = network_update.meta_data
    
    db.commit()
    db.refresh(db_network)
    return db_network

@router.delete("/{network_id}")
async def delete_network(
    network_id: int,
    current_user: models.User = Depends(auth.get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Delete a network.
    """
    db_network = db.query(models.Network).filter(
        models.Network.id == network_id,
        models.Network.user_id == current_user.id
    ).first()
    
    if db_network is None:
        raise HTTPException(status_code=404, detail="Network not found")
    
    db.delete(db_network)
    db.commit()
    
    return {"message": "Network deleted"}

@router.get("/{network_id}/cytoscape", response_model=Dict[str, Any])
async def get_network_cytoscape_format(
    network_id: int,
    current_user: models.User = Depends(auth.get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get network data in Cytoscape.js format.
    """
    db_network = db.query(models.Network).filter(
        models.Network.id == network_id,
        models.Network.user_id == current_user.id
    ).first()
    
    if db_network is None:
        raise HTTPException(status_code=404, detail="Network not found")
    
    try:
        nodes = json.loads(db_network.nodes_data)
        edges = json.loads(db_network.edges_data)
        layout = json.loads(db_network.layout_data)
        
        # Convert to Cytoscape.js format
        cytoscape_elements = []
        
        # Add nodes
        for node in nodes:
            element = {
                "data": {
                    "id": str(node.get("id", "")),
                    "label": node.get("label", str(node.get("id", ""))),
                    **{k: v for k, v in node.items() if k not in ["id", "label", "x", "y"]}
                }
            }
            
            # Add position if available
            if "x" in node and "y" in node:
                element["position"] = {"x": node["x"], "y": node["y"]}
            elif str(node.get("id", "")) in layout:
                pos = layout[str(node.get("id", ""))]
                element["position"] = {"x": pos.get("x", 0), "y": pos.get("y", 0)}
            
            cytoscape_elements.append(element)
        
        # Add edges
        for edge in edges:
            element = {
                "data": {
                    "id": edge.get("id", f"{edge.get('source', '')}-{edge.get('target', '')}"),
                    "source": str(edge.get("source", "")),
                    "target": str(edge.get("target", "")),
                    **{k: v for k, v in edge.items() if k not in ["id", "source", "target"]}
                }
            }
            cytoscape_elements.append(element)
        
        return {
            "elements": cytoscape_elements,
            "metadata": json.loads(db_network.meta_data)
        }
    
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=500, detail=f"Invalid network data format: {str(e)}")

@router.post("/{network_id}/update_from_networkx")
async def update_network_from_networkx(
    network_id: int,
    networkx_data: Dict[str, Any],
    current_user: models.User = Depends(auth.get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Update network data from NetworkX computation results.
    """
    db_network = db.query(models.Network).filter(
        models.Network.id == network_id,
        models.Network.user_id == current_user.id
    ).first()
    
    if db_network is None:
        raise HTTPException(status_code=404, detail="Network not found")
    
    try:
        # Update network data based on NetworkX results
        if "nodes" in networkx_data:
            db_network.nodes_data = json.dumps(networkx_data["nodes"])
        if "edges" in networkx_data:
            db_network.edges_data = json.dumps(networkx_data["edges"])
        if "layout" in networkx_data:
            db_network.layout_data = json.dumps(networkx_data["layout"])
        if "metadata" in networkx_data:
            current_metadata = json.loads(db_network.meta_data)
            current_metadata.update(networkx_data["metadata"])
            db_network.meta_data = json.dumps(current_metadata)
        
        db.commit()
        db.refresh(db_network)
        
        return {"message": "Network updated successfully", "network": db_network}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating network: {str(e)}")