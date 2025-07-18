import os
from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Optional, Any
import networkx as nx
import numpy as np
from dotenv import load_dotenv

from database import engine, Base
from routers import auth as auth_router
from routers import chat as chat_router
from routers import proxy as proxy_router
import auth
import models

# Load environment variables
load_dotenv()

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Network Visualization API",
    description="API for network visualization with user authentication, chat functionality, and NetworkX integration",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Allow frontend origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router.router)
app.include_router(chat_router.router)
app.include_router(proxy_router.router)

@app.get("/")
async def root():
    return {
        "message": "Network Visualization API is running",
        "version": "1.0.0",
        "documentation": "/docs"
    }
