"""
Synchronization router for the Nextcloud Task Backend
"""
from fastapi import APIRouter, HTTPException
from typing import Dict, Any

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from services.task_service import TaskService
from models import SyncResult

router = APIRouter()
task_service = TaskService()


@router.post("/sync-now", response_model=SyncResult)
async def sync_now():
    """Force immediate synchronization with Nextcloud"""
    if not task_service.is_connected:
        raise HTTPException(status_code=400, detail="Not connected to Nextcloud")
    
    result = await task_service.sync_tasks()
    if not result.success:
        raise HTTPException(status_code=400, detail=result.message)
    return result


@router.get("/sync-status")
async def get_sync_status():
    """Get current synchronization status"""
    from utils.database import get_sync_state

    sync_state = await get_sync_state()
    
    return {
        "is_connected": task_service.is_connected,
        "last_sync": sync_state['last_sync_time'],
        "sync_token": sync_state['sync_token'],
        "status": "idle" if not task_service.is_connected else "ready"
    }


@router.get("/stats")
async def get_sync_stats():
    """Get synchronization statistics"""
    from utils.database import get_tasks, get_calendars

    # Get task count
    all_tasks = await get_tasks()
    completed_tasks = await get_tasks()
    # Note: In a real implementation, we'd filter for completed tasks
    
    # Get calendar count
    calendars = await get_calendars()
    
    return {
        "total_tasks": len(all_tasks),
        "completed_tasks": len([t for t in all_tasks if t.completed is not None]),
        "pending_tasks": len([t for t in all_tasks if t.completed is None]),
        "total_calendars": len(calendars),
        "last_sync": (await get_sync_state())['last_sync_time']
    }


@router.post("/clear-cache")
async def clear_cache():
    """Clear local cache (for troubleshooting)"""
    from utils.database import clear_local_data

    await clear_local_data()
    return {
        "success": True,
        "message": "Local cache cleared successfully"
    }


@router.get("/capabilities")
async def get_capabilities():
    """Get backend capabilities"""
    return {
        "sync": True,
        "caching": True,
        "offline_access": True,
        "search": True,
        "filtering": True,
        "multiple_calendars": True,
        "task_relationships": True
    }