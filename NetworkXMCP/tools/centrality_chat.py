"""
Centrality Chat Tool
====================

This module provides tools to facilitate a dialogue with the user about which centrality measure is most appropriate for their analysis goals.
"""

import logging
from typing import Dict, Any, List

logger = logging.getLogger("networkx_mcp.tools.centrality_chat")

# --- Centrality Definitions ---
CENTRALITY_DEFINITIONS = {
    "degree": {
        "name": "Degree Centrality (次数中心性)",
        "description": "Measures the number of direct connections a node has. Good for identifying simple popularity or direct influence.",
        "keywords": ["connections", "links", "degree", "popularity", "connected", "次数", "つながり", "接続数"],
    },
    "closeness": {
        "name": "Closeness Centrality (近接中心性)",
        "description": "Measures how close a node is to all other nodes in the network. Good for identifying nodes that can spread information efficiently.",
        "keywords": ["close", "reach", "spread", "efficient", "near", "近接", "近い", "効率"],
    },
    "betweenness": {
        "name": "Betweenness Centrality (媒介中心性)",
        "description": "Measures how often a node lies on the shortest path between other nodes. Good for identifying bridges, bottlenecks, or brokers of information.",
        "keywords": ["between", "bridge", "bottleneck", "broker", "control", "flow", "媒介", "橋渡し", "ボトルネック"],
    },
    "eigenvector": {
        "name": "Eigenvector Centrality (固有ベクトル中心性)",
        "description": "Measures a node's influence based on the importance of its neighbors. Good for identifying influence in connected networks (like being friends with popular people).",
        "keywords": ["influence", "important neighbors", "eigenvector", "influential", "固有ベクトル", "影響力"],
    },
    "pagerank": {
        "name": "PageRank",
        "description": "Originally for ranking web pages, it measures a node's importance based on the number and quality of links pointing to it. Similar to Eigenvector but for directed networks.",
        "keywords": ["pagerank", "rank", "web page", "ページランク"],
    }
}

def suggest_centrality_from_query(user_query: str) -> Dict[str, Any]:
    """
    Analyzes a user's query and suggests relevant centrality measures.

    Args:
        user_query: The user's natural language query about node importance.

    Returns:
        A dictionary containing a list of suggested centralities with explanations.
    """
    try:
        suggestions = []
        query_lower = user_query.lower()

        for key, data in CENTRALITY_DEFINITIONS.items():
            # Score based on keyword matches
            score = sum(1 for keyword in data["keywords"] if keyword in query_lower)
            if score > 0:
                suggestions.append({
                    "centrality_type": key,
                    "name": data["name"],
                    "reason": f"Your query contained keywords related to '{data['name']}'.",
                    "description": data["description"],
                    "score": score
                })

        # Sort suggestions by score
        suggestions.sort(key=lambda x: x["score"], reverse=True)

        if not suggestions:
            # If no keywords match, return a general suggestion to clarify
            return {
                "success": True,
                "suggestion_type": "clarification_needed",
                "message": "To help you choose the right analysis, could you tell me more about what 'importance' means for your network? For example, are you interested in the number of connections, how central a node is, or its role as a bridge?",
                "options": list(CENTRALITY_DEFINITIONS.keys())
            }

        return {
            "success": True,
            "suggestion_type": "recommendation",
            "suggestions": suggestions
        }

    except Exception as e:
        logger.error(f"Error in suggest_centrality_from_query: {e}")
        return {
            "success": False,
            "error": str(e)
        }
