"""
LLM service for the API.
"""

import os
from typing import List, Dict, Any, Optional
import json
import httpx
import openai

from services.knowledge import get_network_visualization_knowledge

# Initialize OpenAI client
openai.api_key = os.getenv("OPENAI_API_KEY")

# NetworkX MCP server URL
NETWORKX_MCP_URL = "http://networkx-mcp:8001/mcp"

async def process_chat_message(messages: List[Dict[str, str]]) -> Dict[str, Any]:
    """
    Process a chat message using the OpenAI API.
    
    Args:
        messages: List of messages in the conversation
        
    Returns:
        Dictionary with the assistant's response
    """
    try:
        # Get the latest user message
        user_message = messages[-1]["content"] if messages and messages[-1]["role"] == "user" else ""
        
        # Check if the message is related to network visualization
        if is_network_visualization_related(user_message):
            # Try to process with NetworkX MCP server
            try:
                network_response = await process_with_networkx_mcp(user_message)
                if network_response and network_response.get("success"):
                    return {
                        "content": network_response.get("content", ""),
                        "metadata": {
                            "networkUpdate": network_response.get("networkUpdate", None)
                        }
                    }
            except Exception as e:
                print(f"Error processing with NetworkX MCP: {str(e)}")
                # Continue with OpenAI if NetworkX MCP fails
        
        # Get network visualization knowledge
        knowledge = get_network_visualization_knowledge()
        
        # Prepare system message
        system_message = {
            "role": "system",
            "content": f"""You are a helpful assistant specializing in network visualization and analysis.
You can help users understand and visualize network data using various layouts and metrics.

Here's what you know about network visualization:
{knowledge}

When users ask about network visualization, provide clear explanations and suggest appropriate visualization techniques.
If they want to perform specific operations like changing layouts or calculating centrality, explain how these operations work and their benefits.
"""
        }
        
        # Prepare messages for OpenAI
        openai_messages = [system_message] + messages
        
        # Call OpenAI API
        response = await openai.ChatCompletion.acreate(
            model="gpt-4o",
            messages=openai_messages,
            temperature=0.7,
            max_tokens=1000
        )
        
        # Extract response
        assistant_message = response.choices[0].message.content
        
        return {
            "content": assistant_message,
            "metadata": {}
        }
    except Exception as e:
        # Log error
        print(f"Error processing chat message: {str(e)}")
        
        # Return error message
        return {
            "content": "I'm sorry, I encountered an error processing your message. Please try again later.",
            "metadata": {"error": str(e)}
        }

def is_network_visualization_related(message: str) -> bool:
    """
    Check if a message is related to network visualization.
    
    Args:
        message: The message to check
        
    Returns:
        True if the message is related to network visualization, False otherwise
    """
    # Keywords related to network visualization
    keywords = [
        "network", "graph", "node", "edge", "layout", "centrality", "degree",
        "betweenness", "closeness", "eigenvector", "pagerank", "community",
        "cluster", "visualization", "visualize", "ネットワーク", "グラフ", "ノード",
        "エッジ", "レイアウト", "中心性", "次数", "媒介", "近接", "固有ベクトル",
        "コミュニティ", "クラスタ", "可視化"
    ]
    
    # Check if any keyword is in the message
    message_lower = message.lower()
    return any(keyword.lower() in message_lower for keyword in keywords)

async def process_with_networkx_mcp(message: str) -> Dict[str, Any]:
    """
    Process a message using the NetworkX MCP server.
    
    Args:
        message: The message to process
        
    Returns:
        Dictionary with the response from the NetworkX MCP server
    """
    try:
        # Call the process_chat_message tool on the NetworkX MCP server
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{NETWORKX_MCP_URL}/tools/process_chat_message",
                json={
                    "arguments": {
                        "message": message
                    }
                },
                timeout=30.0
            )
            
            # Check if the request was successful
            if response.status_code == 200:
                result = response.json()
                return result.get("result", {})
            else:
                # Return error
                return {
                    "success": False,
                    "content": f"Error processing message with NetworkX MCP server: {response.status_code}"
                }
    except Exception as e:
        # Return error
        return {
            "success": False,
            "content": f"Error connecting to NetworkX MCP server: {str(e)}"
        }
