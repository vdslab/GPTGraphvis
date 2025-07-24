"""
LLM service for processing chat messages.
"""

import json
import httpx
from typing import List, Dict, Any

async def process_chat_message(messages: List[Dict[str, str]]) -> Dict[str, Any]:
    """
    Process chat messages and generate a response using an LLM.
    
    Args:
        messages: A list of message dictionaries with 'role' and 'content' keys
        
    Returns:
        A dictionary containing the assistant's response with 'content' and optional 'metadata'
    """
    try:
        # For now, this is a simple implementation that returns a fixed response
        # In a real application, this would call an LLM API like OpenAI or a local model
        
        # Get the latest user message for context
        user_message = next((msg["content"] for msg in reversed(messages) 
                            if msg["role"] == "user"), "")
        
        # Simple response logic
        response = {
            "content": f"あなたのメッセージを受け取りました: {user_message}",
            "metadata": {
                "processed": True,
                "model": "placeholder-model",
            }
        }
        
        return response
        
    except Exception as e:
        # Log error and return a generic response
        print(f"Error in process_chat_message: {str(e)}")
        return {
            "content": "申し訳ありませんが、メッセージの処理中にエラーが発生しました。",
            "metadata": {
                "error": str(e)
            }
        }
