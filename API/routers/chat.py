"""
Chat router for the API.
Handles conversations, messages, and orchestrates interactions with the LLM and NetworkXMCP.
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Request
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
import json
import datetime
import httpx
import os
import networkx as nx
import io

import models
import schemas
import auth
from database import get_db
from services.llm import process_chat_message

router = APIRouter(
    prefix="/chat",
    tags=["chat"],
    responses={401: {"description": "Unauthorized"}},
)

NETWORKX_MCP_URL = os.environ.get("NETWORKX_MCP_URL", "http://networkx-mcp:8001")

def create_empty_graphml() -> str:
    """Creates an empty GraphML string."""
    G = nx.Graph()
    output = io.StringIO()
    nx.write_graphml(G, output)
    return output.getvalue()

@router.post("/conversations", response_model=schemas.Conversation)
async def create_conversation(
    conversation: schemas.ConversationCreate,
    current_user: models.User = Depends(auth.get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Create a new conversation and an associated empty network.
    """
    db_conversation = models.Conversation(
        title=conversation.title,
        user_id=current_user.id
    )
    db.add(db_conversation)
    db.commit()
    db.refresh(db_conversation)

    # Create an associated empty network
    db_network = models.Network(
        name="Initial Network",
        conversation_id=db_conversation.id,
        graphml_content=create_empty_graphml()
    )
    db.add(db_network)
    db.commit()
    db.refresh(db_conversation) # Refresh to load the network relationship

    return db_conversation

@router.get("/conversations", response_model=List[schemas.Conversation])
async def get_conversations(
    current_user: models.User = Depends(auth.get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get all conversations for the current user.
    """
    return db.query(models.Conversation).filter(models.Conversation.user_id == current_user.id).all()

@router.get("/conversations/{conversation_id}/messages", response_model=List[schemas.ChatMessage])
async def get_messages(
    conversation_id: int,
    current_user: models.User = Depends(auth.get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get all messages for a conversation.
    """
    # Check if conversation exists and belongs to user
    db_conversation = db.query(models.Conversation).filter(
        models.Conversation.id == conversation_id,
        models.Conversation.user_id == current_user.id
    ).first()
    
    if db_conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    return db.query(models.ChatMessage).filter(
        models.ChatMessage.conversation_id == conversation_id
    ).order_by(models.ChatMessage.created_at).all()

@router.post("/conversations/{conversation_id}/messages", response_model=schemas.ChatMessage)
async def create_message(
    conversation_id: int,
    message: schemas.ChatMessageCreate,
    background_tasks: BackgroundTasks,
    current_user: models.User = Depends(auth.get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Create a new message, process it with the LLM, and potentially trigger network operations.
    """
    db_conversation = db.query(models.Conversation).filter(
        models.Conversation.id == conversation_id,
        models.Conversation.user_id == current_user.id
    ).first()
    
    if db_conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    # Save user message
    db_message = models.ChatMessage(
        content=message.content,
        role="user",
        user_id=current_user.id,
        conversation_id=conversation_id
    )
    db.add(db_message)
    db.commit()
    db.refresh(db_message)
    
    # Process message in the background
    background_tasks.add_task(
        process_and_respond,
        db=db,
        conversation_id=conversation_id,
        user_message_content=message.content
    )
    
    return db_message

async def process_and_respond(db: Session, conversation_id: int, user_message_content: str):
    """
    Process user message, interact with LLM and NetworkXMCP, and save the response.
    """
    db_conversation = db.query(models.Conversation).get(conversation_id)
    if not db_conversation or not db_conversation.network:
        # Log error and exit
        return

    try:
        # 1. Get conversation history
        history = db.query(models.ChatMessage).filter(
            models.ChatMessage.conversation_id == conversation_id
        ).order_by(models.ChatMessage.created_at).all()
        formatted_history = [{"role": msg.role, "content": msg.content} for msg in history]

        # 2. Call LLM
        llm_response = await process_chat_message(formatted_history) # This needs to be adapted to potentially return tool calls

        # 3. Check for tool calls
        tool_calls = llm_response.get("tool_calls")
        if tool_calls:
            # For now, assume one tool call per message for simplicity
            tool_call = tool_calls[0]
            tool_name = tool_call["function"]["name"]
            tool_args = json.loads(tool_call["function"]["arguments"])

            # Prepare data for NetworkXMCP
            mcp_payload = {
                "graphml_content": db_conversation.network.graphml_content,
                **tool_args
            }

            # 4. Call NetworkXMCP
            async with httpx.AsyncClient() as client:
                response = await client.post(f"{NETWORKX_MCP_URL}/tools/{tool_name}", json=mcp_payload, timeout=30.0)
                response.raise_for_status()
                mcp_result = response.json().get("result", {})

            # 5. Update network based on result
            if mcp_result.get("success"):
                # This part needs to be more robust based on the tool's output
                # For example, 'change_layout' returns 'positions'
                if 'positions' in mcp_result:
                    # Read, update, and write back the GraphML
                    G = nx.read_graphml(io.StringIO(db_conversation.network.graphml_content))
                    for node_id, pos in mcp_result['positions'].items():
                        if G.has_node(node_id):
                            G.nodes[node_id]['x'] = pos['x']
                            G.nodes[node_id]['y'] = pos['y']
                    
                    output = io.StringIO()
                    nx.write_graphml(G, output)
                    db_conversation.network.graphml_content = output.getvalue()
                    db.commit()
                    
                    # WebSocket通知を送信
                    try:
                        # FastAPIアプリケーションのインスタンスを取得
                        from fastapi import FastAPI
                        from fastapi.concurrency import run_in_threadpool
                        
                        app = FastAPI.get_current()
                        
                        # WebSocket接続マネージャーを取得
                        ws_manager = app.state.ws_manager
                        
                        # 通知を送信
                        print(f"Sending WebSocket notification for network update: network_id={db_conversation.network.id}")
                        await ws_manager.broadcast({
                            "event": "graph_updated",
                            "network_id": db_conversation.network.id,
                            "timestamp": datetime.datetime.now().isoformat()
                        })
                    except Exception as ws_error:
                        print(f"Error sending WebSocket notification: {ws_error}")

            # Save assistant response about tool use
            assistant_content = f"I have performed the operation: {tool_name}."
        else:
            assistant_content = llm_response.get("content", "I am not sure how to respond to that.")

        # 6. Save assistant's final response
        db_response = models.ChatMessage(
            content=assistant_content,
            role="assistant",
            user_id=db_conversation.user_id,
            conversation_id=conversation_id,
            meta_data=json.dumps(llm_response)
        )
        db.add(db_response)
        db.commit()

        # WebSocket通知は削除（循環参照を避けるため）

    except Exception as e:
        # Log and save error message
        error_content = f"An error occurred: {str(e)}"
        db_error = models.ChatMessage(
            content=error_content,
            role="assistant",
            user_id=db_conversation.user_id,
            conversation_id=conversation_id,
            meta_data=json.dumps({"error": True})
        )
        db.add(db_error)
        db.commit()

@router.post("/process")
async def process_chat(
    request: Request,
    background_tasks: BackgroundTasks,
    current_user: models.User = Depends(auth.get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Process a chat message without a specific conversation.
    This endpoint is used by the frontend to process chat messages that are not tied to a specific conversation.
    It forwards the message to the LLM and NetworkXMCP, and returns the response.
    """
    try:
        # Get request body
        body = await request.json()
        message = body.get("message", "")
        
        if not message:
            raise HTTPException(status_code=400, detail="Message is required")
        
        # Get the user's active conversation or create a new one
        db_conversation = db.query(models.Conversation).filter(
            models.Conversation.user_id == current_user.id
        ).order_by(models.Conversation.created_at.desc()).first()
        
        if not db_conversation:
            # Create a new conversation
            db_conversation = models.Conversation(
                title="New Conversation",
                user_id=current_user.id
            )
            db.add(db_conversation)
            db.commit()
            db.refresh(db_conversation)
            
            # Create an associated empty network
            db_network = models.Network(
                name="Initial Network",
                conversation_id=db_conversation.id,
                graphml_content=create_empty_graphml()
            )
            db.add(db_network)
            db.commit()
            db.refresh(db_conversation)
        
        # Save user message
        db_message = models.ChatMessage(
            content=message,
            role="user",
            user_id=current_user.id,
            conversation_id=db_conversation.id
        )
        db.add(db_message)
        db.commit()
        db.refresh(db_message)
        
        # Get conversation history
        history = db.query(models.ChatMessage).filter(
            models.ChatMessage.conversation_id == db_conversation.id
        ).order_by(models.ChatMessage.created_at).all()
        formatted_history = [{"role": msg.role, "content": msg.content} for msg in history]
        
        # Call LLM
        llm_response = await process_chat_message(formatted_history)
        
        # Check for tool calls
        tool_calls = llm_response.get("tool_calls")
        result = {"success": True}
        
        if tool_calls:
            # For now, assume one tool call per message for simplicity
            tool_call = tool_calls[0]
            tool_name = tool_call["function"]["name"]
            tool_args = json.loads(tool_call["function"]["arguments"])
            
            # Prepare data for NetworkXMCP
            mcp_payload = {
                "graphml_content": db_conversation.network.graphml_content,
                **tool_args
            }
            
            # Call NetworkXMCP
            async with httpx.AsyncClient() as client:
                response = await client.post(f"{NETWORKX_MCP_URL}/tools/{tool_name}", json=mcp_payload, timeout=30.0)
                response.raise_for_status()
                mcp_result = response.json().get("result", {})
            
            # Update network based on result
            if mcp_result.get("success"):
                # This part needs to be more robust based on the tool's output
                if 'positions' in mcp_result:
                    # Read, update, and write back the GraphML
                    G = nx.read_graphml(io.StringIO(db_conversation.network.graphml_content))
                    for node_id, pos in mcp_result['positions'].items():
                        if G.has_node(node_id):
                            G.nodes[node_id]['x'] = pos['x']
                            G.nodes[node_id]['y'] = pos['y']
                    
                    output = io.StringIO()
                    nx.write_graphml(G, output)
                    db_conversation.network.graphml_content = output.getvalue()
                    db.commit()
                    
                    # WebSocket通知を送信
                    try:
                        # FastAPIアプリケーションのインスタンスを取得
                        from fastapi import FastAPI
                        from fastapi.concurrency import run_in_threadpool
                        
                        app = FastAPI.get_current()
                        
                        # WebSocket接続マネージャーを取得
                        ws_manager = app.state.ws_manager
                        
                        # 通知を送信
                        print(f"Sending WebSocket notification for network update: network_id={db_conversation.network.id}")
                        await ws_manager.broadcast({
                            "event": "graph_updated",
                            "network_id": db_conversation.network.id,
                            "timestamp": datetime.datetime.now().isoformat()
                        })
                    except Exception as ws_error:
                        print(f"Error sending WebSocket notification: {ws_error}")
                
                # Add network update info to result
                result["networkUpdate"] = {
                    "type": tool_name,
                    **mcp_result
                }
            
            # Set assistant response about tool use
            assistant_content = f"I have performed the operation: {tool_name}."
        else:
            assistant_content = llm_response.get("content", "I am not sure how to respond to that.")
        
        # Save assistant's response
        db_response = models.ChatMessage(
            content=assistant_content,
            role="assistant",
            user_id=current_user.id,
            conversation_id=db_conversation.id,
            meta_data=json.dumps(llm_response)
        )
        db.add(db_response)
        db.commit()
        
        # Return the result
        result["content"] = assistant_content
        return result
        
    except Exception as e:
        # Log the error
        print(f"Error processing chat message: {type(e).__name__}: {e}")
        
        # Return error response
        try:
            # バイト型のエラーメッセージを適切に処理
            if isinstance(e, UnicodeDecodeError) or isinstance(e.__str__(), bytes):
                error_message = "Unicode decode error occurred"
            else:
                error_message = str(e)
                
            return {
                "success": False,
                "content": f"An error occurred: {error_message}"
            }
        except Exception as decode_error:
            # 最終的なフォールバック
            return {
                "success": False,
                "content": "An unexpected error occurred while processing your message"
            }
