from fastapi import APIRouter

router = APIRouter(
    prefix="/network-chat",
    tags=["network-chat"],
    responses={401: {"description": "Unauthorized"}},
)

# All endpoints have been removed as part of migration to MCP-based design
