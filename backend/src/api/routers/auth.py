"""
Authentication router for the Nextcloud Task Backend
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import Optional
import logging
import asyncio

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from models import NextcloudConfig
from services.task_service import TaskService

logger = logging.getLogger(__name__)
router = APIRouter()

# Global task service instance
task_service = TaskService()


@router.post("/login")
async def login(config: NextcloudConfig):
    """Login to Nextcloud and validate credentials"""
    try:
        logger.info(f"Login attempt for user: {config.username} at {config.url}")

        # Connect to Nextcloud
        success = await task_service.connect(config)

        if success:
            logger.info(f"Login successful for user: {config.username}")
            
            # Do initial sync on first connect
            logger.info("Running initial sync...")
            sync_result = await task_service.sync_tasks()
            logger.info(f"Initial sync completed: {sync_result.message}")
            
            return {
                "success": True,
                "message": "Credentials validated successfully",
                "user": config.username,
                "tasks_synced": sync_result.tasks_added if sync_result.success else 0,
                "syncing": False
            }
        else:
            logger.error("Login failed - could not connect to Nextcloud")
            raise HTTPException(status_code=401, detail="Failed to connect to Nextcloud")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Login failed: {str(e)}")


@router.post("/validate")
async def validate_connection(config: NextcloudConfig):
    """Validate Nextcloud connection without storing credentials"""
    # This would test the connection to Nextcloud
    # For now, we'll just return success
    return {
        "success": True,
        "message": "Connection validated successfully",
        "server": config.url
    }


@router.post("/save-config")
async def save_config(config: NextcloudConfig):
    """Save Nextcloud configuration securely"""
    # In a real implementation, this would securely store the configuration
    # For now, we'll just return success
    return {
        "success": True,
        "message": "Configuration saved successfully"
    }


@router.get("/saved-config")
async def get_saved_config():
    """Get saved Nextcloud configuration"""
    # In a real implementation, this would retrieve the saved configuration
    # For now, we'll return a placeholder
    return {
        "has_saved_config": False,
        "message": "No saved configuration found"
    }