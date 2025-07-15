from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any
import os
from openai import OpenAI

import models, auth
from database import get_db

router = APIRouter(
    prefix="/chatgpt",
    tags=["chatgpt"],
    responses={401: {"description": "Unauthorized"}},
)

# Pydantic models for request and response
from pydantic import BaseModel
import json

class ChatGPTRequest(BaseModel):
    prompt: str
    max_tokens: Optional[int] = 1000
    temperature: Optional[float] = 0.7

class ChatGPTResponse(BaseModel):
    response: str


# Initialize OpenAI client
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("OPENAI_API_KEY environment variable is not set")
client = OpenAI(api_key=api_key)

@router.post("/generate", response_model=ChatGPTResponse)
async def generate_response(
    request: ChatGPTRequest,
    current_user: models.User = Depends(auth.get_current_active_user),
    db: Session = Depends(get_db)
):
    """Generate a response from ChatGPT."""
    try:
        # Call OpenAI API
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": request.prompt}
            ],
            max_tokens=request.max_tokens,
            temperature=request.temperature
        )
        
        # Extract response text
        response_text = response.choices[0].message.content
        
        return {"response": response_text}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error generating response: {str(e)}"
        )
