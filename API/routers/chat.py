"""
Chat router for the API.
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
import json
import datetime
import httpx

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

@router.post("/conversations", response_model=schemas.Conversation)
async def create_conversation(
    conversation: schemas.ConversationCreate,
    current_user: models.User = Depends(auth.get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Create a new conversation.
    """
    db_conversation = models.Conversation(
        title=conversation.title,
        user_id=current_user.id
    )
    db.add(db_conversation)
    db.commit()
    db.refresh(db_conversation)
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

@router.get("/conversations/{conversation_id}", response_model=schemas.Conversation)
async def get_conversation(
    conversation_id: int,
    current_user: models.User = Depends(auth.get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get a specific conversation.
    """
    db_conversation = db.query(models.Conversation).filter(
        models.Conversation.id == conversation_id,
        models.Conversation.user_id == current_user.id
    ).first()
    
    if db_conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    return db_conversation

@router.delete("/conversations/{conversation_id}")
async def delete_conversation(
    conversation_id: int,
    current_user: models.User = Depends(auth.get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Delete a conversation.
    """
    db_conversation = db.query(models.Conversation).filter(
        models.Conversation.id == conversation_id,
        models.Conversation.user_id == current_user.id
    ).first()
    
    if db_conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    db.delete(db_conversation)
    db.commit()
    
    return {"message": "Conversation deleted"}

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
    
    # Get messages
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
    Create a new message in a conversation.
    """
    # Check if conversation exists and belongs to user
    db_conversation = db.query(models.Conversation).filter(
        models.Conversation.id == conversation_id,
        models.Conversation.user_id == current_user.id
    ).first()
    
    if db_conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    # Create user message
    db_message = models.ChatMessage(
        content=message.content,
        role=message.role,
        user_id=current_user.id,
        conversation_id=conversation_id
    )
    db.add(db_message)
    db.commit()
    db.refresh(db_message)
    
    # Process message in background and generate assistant response
    background_tasks.add_task(
        process_and_save_response,
        db=db,
        user_id=current_user.id,
        conversation_id=conversation_id,
        user_message=message.content
    )
    
    return db_message

async def process_and_save_response(
    db: Session,
    user_id: int,
    conversation_id: int,
    user_message: str
):
    """
    Process a user message and save the assistant's response.
    """
    try:
        # Get conversation history
        messages = db.query(models.ChatMessage).filter(
            models.ChatMessage.conversation_id == conversation_id
        ).order_by(models.ChatMessage.created_at).all()
        
        # Format messages for the LLM
        formatted_messages = [
            {"role": msg.role, "content": msg.content}
            for msg in messages
        ]
        
        # Process message with LLM
        response = await process_chat_message(formatted_messages)
        
        # Save assistant response with metadata (including any network updates)
        meta_data = response.get("metadata", {})
        
        # Add timestamp to metadata
        if "timestamp" not in meta_data:
            meta_data["timestamp"] = str(datetime.datetime.now())
        
        db_message = models.ChatMessage(
            content=response["content"],
            role="assistant",
            user_id=user_id,
            conversation_id=conversation_id,
            meta_data=json.dumps(meta_data)
        )
        db.add(db_message)
        db.commit()
    except Exception as e:
        # Log error
        print(f"Error processing message: {str(e)}")
        
        # Save error response
        error_message = "申し訳ありませんが、メッセージの処理中にエラーが発生しました。後でもう一度お試しください。"
        db_message = models.ChatMessage(
            content=error_message,
            role="assistant",
            user_id=user_id,
            conversation_id=conversation_id,
            meta_data=json.dumps({"error": str(e), "timestamp": str(datetime.datetime.now())})
        )
        db.add(db_message)
        db.commit()
