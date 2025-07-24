import os
import time
from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Optional, Any
import networkx as nx
import numpy as np
from dotenv import load_dotenv
import sqlalchemy.exc

from database import engine, Base
from routers import auth as auth_router
from routers import chat as chat_router
from routers import proxy as proxy_router
import auth
import models

# Load environment variables
load_dotenv()

# データベースの接続を待機する
max_retries = 10
retry_interval = 3  # 秒
for i in range(max_retries):
    try:
        # 接続テスト
        with engine.connect() as conn:
            print(f"Database connection successful on attempt {i+1}")
            break
    except sqlalchemy.exc.OperationalError as e:
        if i < max_retries - 1:
            print(f"Database connection attempt {i+1} failed. Retrying in {retry_interval} seconds...")
            time.sleep(retry_interval)
        else:
            print(f"Failed to connect to database after {max_retries} attempts: {e}")
            # エラーを発生させずに続行（コンテナ再起動ループを避けるため）

# Create database tables
try:
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully")
except Exception as e:
    print(f"Error creating database tables: {e}")

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

@app.get("/health")
async def health_check():
    """
    Health check endpoint for Docker healthcheck.
    """
    try:
        # 接続テスト
        with engine.connect() as conn:
            return {"status": "healthy", "database": "connected"}
    except Exception as e:
        return {"status": "unhealthy", "database": str(e)}
