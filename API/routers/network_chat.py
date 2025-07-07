from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Optional, Any
import networkx as nx
import json
import os
from openai import OpenAI
from pydantic import BaseModel, Field

import models, auth
from database import get_db

router = APIRouter(
    prefix="/network-chat",
    tags=["network-chat"],
    responses={401: {"description": "Unauthorized"}},
)

# Pydantic models for request and response
from pydantic import BaseModel

class ChatMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str

class ChatRequest(BaseModel):
    message: str
    history: Optional[List[ChatMessage]] = []

class ChatResponse(BaseModel):
    response: str
    network_update: Optional[Dict[str, Any]] = None
    visualization_update: Optional[Dict[str, Any]] = None

class Node(BaseModel):
    id: str
    label: Optional[str] = None

class Edge(BaseModel):
    source: str
    target: str

class NetworkData(BaseModel):
    nodes: List[Node]
    edges: List[Edge]

# Initialize OpenAI client
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("OPENAI_API_KEY environment variable is not set")
client = OpenAI(api_key=api_key)

def calculate_centrality(G: nx.Graph, centrality_type: str) -> Dict[str, float]:
    """
    Calculate centrality metrics for nodes in the graph.
    
    Args:
        G: NetworkX graph
        centrality_type: Type of centrality to calculate
        
    Returns:
        Dictionary mapping node IDs to centrality values
    """
    centrality_functions = {
        "degree": nx.degree_centrality,
        "closeness": nx.closeness_centrality,
        "betweenness": nx.betweenness_centrality,
        "eigenvector": nx.eigenvector_centrality,
        "pagerank": nx.pagerank
    }
    
    if centrality_type in centrality_functions:
        return centrality_functions[centrality_type](G)
    else:
        raise ValueError(f"Unsupported centrality type: {centrality_type}. Supported types: {', '.join(centrality_functions.keys())}")

def apply_layout(G: nx.Graph, layout_type: str, **kwargs) -> Dict[Any, tuple]:
    """
    Apply a layout algorithm to the graph.
    
    Args:
        G: NetworkX graph
        layout_type: Type of layout algorithm
        **kwargs: Additional parameters for the layout algorithm
        
    Returns:
        Dictionary mapping node IDs to positions
    """
    layout_functions = {
        "spring": nx.spring_layout,
        "circular": nx.circular_layout,
        "random": nx.random_layout,
        "spectral": nx.spectral_layout,
        "shell": nx.shell_layout,
        "spiral": nx.spiral_layout,
        "kamada_kawai": nx.kamada_kawai_layout,
        "fruchterman_reingold": nx.fruchterman_reingold_layout,
        "bipartite": nx.bipartite_layout,
        "multipartite": nx.multipartite_layout
    }
    
    # 平面グラフの場合のみ使用可能
    if layout_type == "planar" and nx.is_planar(G):
        return nx.planar_layout(G, **kwargs)
    
    if layout_type in layout_functions:
        return layout_functions[layout_type](G, **kwargs)
    else:
        raise ValueError(f"Unsupported layout type: {layout_type}. Supported types: {', '.join(layout_functions.keys())}")

def parse_network_command(message: str, history: List[ChatMessage]) -> Dict[str, Any]:
    """
    Parse a user message to extract network-related commands.
    
    Args:
        message: User message
        history: Chat history
        
    Returns:
        Dictionary with command type and parameters
    """
    try:
        print(f"Parsing network command from message: {message}")
        print(f"History length: {len(history)}")
        
        # Define the function for OpenAI to use
        network_command_function = {
            "name": "extract_network_command",
            "description": "Extract network visualization commands from user messages",
            "parameters": {
                "type": "object",
                "properties": {
                    "command_type": {
                        "type": "string",
                        "enum": [
                            "change_layout", 
                            "calculate_centrality", 
                            "filter_nodes", 
                            "highlight_nodes",
                            "change_visual_properties",
                            "none"
                        ],
                        "description": "The type of network command to execute"
                    },
                    "parameters": {
                        "type": "object",
                        "description": "Parameters for the command"
                    },
                    "explanation": {
                        "type": "string",
                        "description": "Explanation of what the command will do"
                    }
                },
                "required": ["command_type", "explanation"]
            }
        }
        
        # Create messages for OpenAI
        messages = [
            {
                "role": "system", 
                "content": """
                You are a network visualization assistant that helps users visualize and analyze network data.
                Extract network-related commands from user messages. The commands can be:
                
                1. change_layout: Change the layout algorithm or its parameters
                   - Parameters: layout_type (string), layout_params (object)
                
                2. calculate_centrality: Calculate node centrality metrics
                   - Parameters: centrality_type (string: degree, closeness, betweenness, eigenvector, pagerank)
                
                3. filter_nodes: Filter nodes based on criteria
                   - Parameters: filter_criteria (object)
                
                4. highlight_nodes: Highlight specific nodes
                   - Parameters: node_ids (array), highlight_color (string)
                
                5. change_visual_properties: Change visual properties of nodes or edges
                   - Parameters: property_type (string: node_size, node_color, edge_width, edge_color), 
                                property_value (any), 
                                property_mapping (object, optional)
                
                6. none: No network command detected
                   - No parameters needed
                
                If the user's message doesn't contain a network command, return command_type as "none".
                """
            }
        ]
        
        # Add history messages
        for msg in history:
            messages.append({"role": msg.role, "content": msg.content})
        
        # Add current message
        messages.append({"role": "user", "content": message})
        
        print(f"Calling OpenAI API with {len(messages)} messages")
        
        # Call OpenAI API
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
            functions=[network_command_function],
            function_call={"name": "extract_network_command"}
        )
        
        # Extract function call result
        function_call = response.choices[0].message.function_call
        if function_call:
            result = json.loads(function_call.arguments)
            print(f"Parsed command: {result}")
            
            # Ensure parameters is a dictionary
            if "parameters" not in result:
                result["parameters"] = {}
            
            # For 'change_layout' command, if layout_type is not specified but the command is about circular layout,
            # set layout_type to 'circular'
            if result["command_type"] == "change_layout":
                if "layout_type" not in result["parameters"] and "circular" in message.lower():
                    print("Setting layout_type to 'circular' based on message content")
                    result["parameters"]["layout_type"] = "circular"
            
            # For 'calculate_centrality' command, if centrality_type is not specified but the command mentions a specific type,
            # set centrality_type accordingly
            if result["command_type"] == "calculate_centrality":
                message_lower = message.lower()
                if "centrality_type" not in result["parameters"]:
                    if "degree" in message_lower:
                        result["parameters"]["centrality_type"] = "degree"
                    elif "closeness" in message_lower:
                        result["parameters"]["centrality_type"] = "closeness"
                    elif "betweenness" in message_lower:
                        result["parameters"]["centrality_type"] = "betweenness"
                    elif "eigenvector" in message_lower:
                        result["parameters"]["centrality_type"] = "eigenvector"
                    elif "pagerank" in message_lower:
                        result["parameters"]["centrality_type"] = "pagerank"
            
            return result
        else:
            print("No function call in response, returning 'none' command")
            return {"command_type": "none", "explanation": "No network command detected", "parameters": {}}
    except Exception as e:
        print(f"Error parsing network command: {str(e)}")
        import traceback
        traceback.print_exc()
        # Return a default response in case of error
        return {
            "command_type": "none", 
            "explanation": f"Error parsing command: {str(e)}", 
            "parameters": {}
        }

@router.post("/chat", response_model=ChatResponse)
async def process_chat_message(
    request: ChatRequest,
    current_user: models.User = Depends(auth.get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Process a chat message and return a response with optional network updates.
    """
    try:
        # Log the request for debugging
        print(f"Processing chat message from user {current_user.username}: {request.message}")
        
        # Ensure history is a list
        if request.history is None:
            request.history = []
        
        # Convert history items to ChatMessage objects if they're dictionaries
        validated_history = []
        for msg in request.history:
            if isinstance(msg, dict):
                try:
                    validated_history.append(ChatMessage(**msg))
                except Exception as e:
                    print(f"Error converting history item to ChatMessage: {e}")
                    # Skip invalid messages
                    continue
            else:
                validated_history.append(msg)
        
        request.history = validated_history
        print(f"Message history length: {len(request.history)}")
        
        # Parse the message for network commands
        try:
            command_info = parse_network_command(request.message, request.history)
            print(f"Command info: {command_info}")
        except Exception as parse_error:
            print(f"Error parsing network command: {str(parse_error)}")
            # Default to no command if parsing fails
            command_info = {"command_type": "none", "explanation": "No network command detected"}
        
        # Prepare response data
        response_data = {
            "response": "",
            "network_update": None,
            "visualization_update": None
        }
        
        # Handle different command types
        if command_info["command_type"] == "none":
            # If no network command, just generate a regular chat response
            try:
                chat_response = await generate_chat_response(request.message, request.history)
                response_data["response"] = chat_response
                print(f"Generated chat response: {chat_response[:100]}...")
            except Exception as chat_error:
                print(f"Error generating chat response: {str(chat_error)}")
                response_data["response"] = "I'm sorry, I encountered an error processing your request. Please try again."
        else:
            # If there's a network command, include the explanation in the response
            response_data["response"] = command_info["explanation"]
            print(f"Using command explanation as response: {command_info['explanation'][:100]}...")
            
            # Add command-specific updates
            if command_info["command_type"] == "change_layout":
                # Check if parameters exists in command_info
                if "parameters" not in command_info or not command_info["parameters"]:
                    print("No parameters found in command_info, using defaults")
                    command_info["parameters"] = {}
                
                # For 'change_layout' command, if layout_type is not specified but the command is about circular layout,
                # set layout_type to 'circular'
                if "layout_type" not in command_info["parameters"] and "circular" in request.message.lower():
                    print("Setting layout_type to 'circular' based on message content")
                    command_info["parameters"]["layout_type"] = "circular"
                
                layout_type = command_info["parameters"].get("layout_type", "spring")
                layout_params = command_info["parameters"].get("layout_params", {})
                
                print(f"Changing layout to {layout_type} with params {layout_params}")
                
                # Try to use MCP server if available
                try:
                    # This would be implemented if we had direct access to the MCP server
                    # For now, we'll just return the update to the frontend
                    pass
                except Exception as mcp_error:
                    print(f"Error using MCP for layout change: {str(mcp_error)}")
                
                response_data["network_update"] = {
                    "type": "layout",
                    "layout": layout_type,
                    "layout_params": layout_params
                }
            
            elif command_info["command_type"] == "calculate_centrality":
                # Check if parameters exists in command_info
                if "parameters" not in command_info or not command_info["parameters"]:
                    print("No parameters found in command_info for centrality, using defaults")
                    command_info["parameters"] = {}
                
                # For 'calculate_centrality' command, if centrality_type is not specified but the command mentions a specific type,
                # set centrality_type accordingly
                message_lower = request.message.lower()
                if "centrality_type" not in command_info["parameters"]:
                    if "degree" in message_lower:
                        command_info["parameters"]["centrality_type"] = "degree"
                    elif "closeness" in message_lower:
                        command_info["parameters"]["centrality_type"] = "closeness"
                    elif "betweenness" in message_lower:
                        command_info["parameters"]["centrality_type"] = "betweenness"
                    elif "eigenvector" in message_lower:
                        command_info["parameters"]["centrality_type"] = "eigenvector"
                    elif "pagerank" in message_lower:
                        command_info["parameters"]["centrality_type"] = "pagerank"
                
                centrality_type = command_info["parameters"].get("centrality_type", "degree")
                print(f"Calculating {centrality_type} centrality")
                
                response_data["network_update"] = {
                    "type": "centrality",
                    "centrality_type": centrality_type
                }
                
            elif command_info["command_type"] == "filter_nodes":
                filter_criteria = command_info["parameters"].get("filter_criteria", {})
                print(f"Filtering nodes with criteria: {filter_criteria}")
                
                response_data["network_update"] = {
                    "type": "filter",
                    "filter_criteria": filter_criteria
                }
                
            elif command_info["command_type"] == "highlight_nodes":
                # Check if parameters exists in command_info
                if "parameters" not in command_info or not command_info["parameters"]:
                    print("No parameters found in command_info for highlighting, using defaults")
                    command_info["parameters"] = {}
                
                node_ids = command_info["parameters"].get("node_ids", [])
                highlight_color = command_info["parameters"].get("highlight_color", "#ff0000")
                print(f"Highlighting nodes {node_ids} with color {highlight_color}")
                
                response_data["visualization_update"] = {
                    "type": "highlight",
                    "node_ids": node_ids,
                    "highlight_color": highlight_color
                }
                
            elif command_info["command_type"] == "change_visual_properties":
                # Check if parameters exists in command_info
                if "parameters" not in command_info or not command_info["parameters"]:
                    print("No parameters found in command_info for visual properties, using defaults")
                    command_info["parameters"] = {}
                
                property_type = command_info["parameters"].get("property_type", "node_color")
                property_value = command_info["parameters"].get("property_value", "#1d4ed8")
                property_mapping = command_info["parameters"].get("property_mapping", {})
                print(f"Changing visual property {property_type} to {property_value}")
                
                response_data["visualization_update"] = {
                    "type": "visual_properties",
                    "property_type": property_type,
                    "property_value": property_value,
                    "property_mapping": property_mapping
                }
        
        print(f"Returning response data: {str(response_data)[:200]}...")
        return response_data
        
    except Exception as e:
        print(f"Error processing chat message: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Error processing chat message: {str(e)}"
        )

async def generate_chat_response(message: str, history: List[ChatMessage]) -> str:
    """
    Generate a response to a chat message using OpenAI.
    """
    try:
        print(f"Generating chat response for message: {message}")
        print(f"History length: {len(history)}")
        
        # Create messages for OpenAI
        messages = [
            {
                "role": "system", 
                "content": """
                You are a friendly and helpful network visualization assistant that helps users visualize and analyze network data.
                
                Provide conversational and informative responses about:
                - Network visualization techniques and best practices
                - Graph theory concepts and applications
                - Network analysis methods and metrics
                - Data visualization principles
                
                You can explain complex concepts in simple terms and provide examples when appropriate.
                Feel free to ask clarifying questions if the user's request is ambiguous.
                
                You can use markdown formatting in your responses to improve readability.
                """
            }
        ]
        
        # Add history messages
        for msg in history:
            try:
                messages.append({"role": msg.role, "content": msg.content})
            except Exception as history_error:
                print(f"Error adding history message: {str(history_error)}")
                # Skip invalid messages
                continue
        
        # Add current message
        messages.append({"role": "user", "content": message})
        
        print(f"Calling OpenAI API with {len(messages)} messages")
        
        # Call OpenAI API
        try:
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=messages,
                temperature=0.7,
                max_tokens=1000
            )
            
            # Extract response text
            content = response.choices[0].message.content
            print(f"Generated response: {content[:100]}...")
            return content
        except Exception as api_error:
            print(f"Error calling OpenAI API: {str(api_error)}")
            return "I'm sorry, I encountered an error generating a response. Please try again."
        
    except Exception as e:
        print(f"Error in generate_chat_response: {str(e)}")
        import traceback
        traceback.print_exc()
        # Return a default response instead of raising an exception
        return "I apologize, but I'm having trouble processing your request right now. Please try again later."

@router.post("/network", response_model=NetworkData)
async def create_sample_network(
    current_user: models.User = Depends(auth.get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Create a sample network for demonstration.
    """
    try:
        # Create a sample network (Zachary's Karate Club)
        G = nx.karate_club_graph()
        
        # Convert to the expected format
        nodes = [
            Node(id=str(node), label=f"Node {node}")
            for node in G.nodes()
        ]
        
        edges = [
            Edge(source=str(source), target=str(target))
            for source, target in G.edges()
        ]
        
        return NetworkData(nodes=nodes, edges=edges)
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error creating sample network: {str(e)}"
        )
