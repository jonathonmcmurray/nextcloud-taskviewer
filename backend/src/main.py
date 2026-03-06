"""
Nextcloud Task Backend Service
REST API for managing Nextcloud tasks with caching and synchronization
"""
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import logging
from typing import List, Optional
from datetime import datetime

import sys
import os
# Add the backend directory to the path so imports work
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.api.routers import tasks, auth, sync
from src.services.task_service import TaskService
from src.utils.database import init_db

# Setup logging with file handler
BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
log_file = os.path.join(BACKEND_DIR, 'backend.log')

# Configure logging for both application and uvicorn access logs
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)

# Also configure uvicorn access logs
uvicorn_access_logger = logging.getLogger("uvicorn.access")
uvicorn_access_logger.setLevel(logging.INFO)
uvicorn_access_logger.handlers = [
    logging.FileHandler(log_file),
    logging.StreamHandler()
]

logger = logging.getLogger(__name__)

app = FastAPI(
    title="Nextcloud Task Backend",
    description="Backend service for synchronizing and managing Nextcloud tasks",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict this to your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
task_service = TaskService()

# Include routers
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(tasks.router, prefix="/tasks", tags=["Tasks"])
app.include_router(sync.router, prefix="/sync", tags=["Synchronization"])


async def periodic_sync():
    """Periodically sync tasks every 5 minutes"""
    while True:
        await asyncio.sleep(300)  # 5 minutes
        if task_service.is_connected and task_service.config:
            try:
                logger.info("Starting periodic background sync...")
                result = await task_service.sync_tasks()
                logger.info(f"Periodic sync completed: {result.message}")
            except Exception as e:
                logger.error(f"Periodic sync failed: {e}", exc_info=True)
        else:
            logger.debug("Skipping periodic sync - not connected")


@app.on_event("startup")
async def startup_event():
    """Initialize the database and services on startup"""
    logger.info("Initializing backend service...")
    await init_db()
    logger.info("Backend service initialized successfully")
    
    # Start periodic sync task
    asyncio.create_task(periodic_sync())
    logger.info("Periodic sync task started (every 5 minutes)")

@app.get("/")
async def root():
    """Root endpoint for health check"""
    return {"message": "Nextcloud Task Backend Service", "status": "running"}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "nextcloud-task-backend"
    }

@app.get("/api/v1/config")
async def get_config():
    """Get backend configuration"""
    return {
        "version": "1.0.0",
        "features": ["task_sync", "caching", "authentication"],
        "database_status": "connected"  # Placeholder
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)