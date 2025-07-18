from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from datetime import datetime

# User schemas
class UserBase(BaseModel):
    username: str

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = {
        "from_attributes": True
    }

# Token schemas
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

# Conversation schemas
class ConversationBase(BaseModel):
    title: str = "New Conversation"

class ConversationCreate(ConversationBase):
    pass

class Conversation(ConversationBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = {
        "from_attributes": True
    }

# Chat message schemas
class ChatMessageBase(BaseModel):
    content: str
    role: str = "user"

class ChatMessageCreate(ChatMessageBase):
    conversation_id: int

class ChatMessage(ChatMessageBase):
    id: int
    user_id: int
    conversation_id: int
    meta_data: Optional[str] = "{}"
    created_at: datetime

    model_config = {
        "from_attributes": True
    }

    def get_metadata(self) -> Dict[str, Any]:
        """Get metadata as a dictionary."""
        try:
            import json
            return json.loads(self.meta_data)
        except:
            return {}

# Network operation schemas
class NetworkOperationRequest(BaseModel):
    message: str

class NetworkOperationResponse(BaseModel):
    success: bool
    content: str
    networkUpdate: Optional[Dict[str, Any]] = None
