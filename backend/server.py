"""
Aether Trader - FastAPI Server
REST API for the AI Quantitative Trading Research Platform.
"""

import asyncio
import logging
import os
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Dict, List, Optional

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel

from .api.routes import router as api_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    logger.info("Aether Trader starting up...")
    yield
    logger.info("Aether Trader shutting down...")


app = FastAPI(
    title="Aether Trader",
    description="AI Quantitative Trading Research Platform",
    version="2.0.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(api_router, prefix="/api/v1")


@app.get("/health")
def health():
    """Health check endpoint."""
    return {"status": "running", "timestamp": datetime.utcnow().isoformat()}


@app.get("/")
def root():
    """Root endpoint."""
    return {
        "name": "Aether Trader",
        "version": "2.0.0",
        "description": "AI Quantitative Trading Research Platform",
        "docs": "/docs",
        "health": "/health",
        "api": "/api/v1",
    }


# ============================================================
# Runnable entry point
# ============================================================

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "backend.server:app",
        host=os.getenv("AETHER_HOST", "0.0.0.0"),
        port=int(os.getenv("AETHER_PORT", "8000")),
        reload=os.getenv("AETHER_DEBUG", "false").lower() == "true",
        log_level="info",
    )
