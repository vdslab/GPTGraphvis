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

# Network schemas
class NetworkBase(BaseModel):
    name: str = "Untitled Network"

class NetworkCreate(NetworkBase):
    nodes_data: str = "[]"
    edges_data: str = "[]"
    layout_data: str = "{}"
    meta_data: str = "{}"

class NetworkUpdate(BaseModel):
    name: Optional[str] = None
    nodes_data: Optional[str] = None
    edges_data: Optional[str] = None
    layout_data: Optional[str] = None
    meta_data: Optional[str] = None

class Network(NetworkBase):
    id: int
    user_id: int
    nodes_data: str
    edges_data: str
    layout_data: str
    meta_data: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = {
        "from_attributes": True
    }

    def get_nodes(self) -> List[Dict[str, Any]]:
        """Get nodes as a list of dictionaries."""
        try:
            import json
            return json.loads(self.nodes_data)
        except:
            return []

    def get_edges(self) -> List[Dict[str, Any]]:
        """Get edges as a list of dictionaries."""
        try:
            import json
            return json.loads(self.edges_data)
        except:
            return []

    def get_layout(self) -> Dict[str, Any]:
        """Get layout data as a dictionary."""
        try:
            import json
            return json.loads(self.layout_data)
        except:
            return {}

    def get_metadata(self) -> Dict[str, Any]:
        """Get metadata as a dictionary."""
        try:
            import json
            return json.loads(self.meta_data)
        except:
            return {}
