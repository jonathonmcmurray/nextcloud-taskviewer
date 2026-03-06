"""
API routers for the Nextcloud Task Backend
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional
from datetime import datetime

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from models import Task, Calendar, NextcloudConfig, SyncResult, TaskFilter
from services.task_service import TaskService

router = APIRouter()

# Global task service instance (in a real app, you'd use dependency injection)
task_service = TaskService()


@router.post("/connect")
async def connect(config: NextcloudConfig):
    """Connect to Nextcloud"""
    success = await task_service.connect(config)
    if not success:
        raise HTTPException(status_code=400, detail="Failed to connect to Nextcloud")
    return {"success": True, "message": "Connected to Nextcloud successfully"}


@router.get("/calendars", response_model=List[Calendar])
async def get_calendars(enabled_only: bool = True):
    """Get calendars"""
    return await task_service.get_calendars(enabled_only)


@router.get("/tasks", response_model=List[Task])
async def get_tasks(
    calendar_ids: List[str] = Query(None),
    status: Optional[str] = Query(None),
    due_before: Optional[datetime] = Query(None),
    due_after: Optional[datetime] = Query(None),
    completed: Optional[bool] = Query(None),
    search_term: Optional[str] = Query(None),
    limit: Optional[int] = Query(None),
    offset: Optional[int] = Query(None)
):
    """Get tasks with optional filters"""
    filter_params = TaskFilter(
        calendar_ids=calendar_ids,
        status=status,
        due_before=due_before,
        due_after=due_after,
        completed=completed,
        search_term=search_term,
        limit=limit,
        offset=offset
    )
    return await task_service.get_tasks(filter_params)


@router.get("/tasks/today", response_model=List[Task])
async def get_today_tasks():
    """Get tasks due today or overdue"""
    return await task_service.get_today_tasks()


@router.get("/tasks/{task_id}", response_model=Task)
async def get_task(task_id: str):
    """Get a specific task by ID"""
    task = await task_service.get_task_by_id(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.post("/sync", response_model=SyncResult)
async def sync_tasks():
    """Synchronize tasks with Nextcloud"""
    result = await task_service.sync_tasks()
    if not result.success:
        raise HTTPException(status_code=400, detail=result.message)
    return result


@router.get("/search", response_model=List[Task])
async def search_tasks(query: str):
    """Search tasks by query term"""
    if not query:
        raise HTTPException(status_code=400, detail="Query parameter is required")
    return await task_service.search_tasks(query)


@router.post("/disconnect")
async def disconnect():
    """Disconnect from Nextcloud"""
    await task_service.disconnect()
    return {"success": True, "message": "Disconnected from Nextcloud"}