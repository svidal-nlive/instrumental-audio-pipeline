from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import os
from pathlib import Path

from .api import router as api_router
from .api.endpoints import audio_services
from .core.config import settings
from .core.database import init_db
from .services.queue_manager import QueueManager
from .services.file_watcher import FileWatcher


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    await init_db()
    
    # Initialize queue manager
    queue_manager = QueueManager()
    app.state.queue_manager = queue_manager
    
    # Initialize file watcher
    file_watcher = FileWatcher(queue_manager)
    await file_watcher.start()
    app.state.file_watcher = file_watcher
    
    # Create data directories
    os.makedirs(settings.INPUT_DIR, exist_ok=True)
    os.makedirs(settings.OUTPUT_DIR, exist_ok=True)
    os.makedirs(settings.LOGS_DIR, exist_ok=True)
    
    yield
    
    # Shutdown
    if hasattr(app.state, 'file_watcher'):
        await app.state.file_watcher.stop()


# Create FastAPI app
app = FastAPI(
    title="Instrumental Maker API",
    description="API for managing audio processing pipeline",
    version="2.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(api_router, prefix="/api/v1")
app.include_router(audio_services.router, prefix="/api/v1/audio", tags=["Audio Services"])

# Serve static files (for file downloads)
if os.path.exists(settings.OUTPUT_DIR):
    app.mount("/files", StaticFiles(directory=settings.OUTPUT_DIR), name="files")


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Instrumental Maker API",
        "version": "2.0.0",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": "2025-01-21T22:00:00Z"
    }
