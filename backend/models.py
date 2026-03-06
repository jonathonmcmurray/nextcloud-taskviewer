"""
Data models for the Nextcloud Task Backend
"""
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class Task(BaseModel):
    """Model representing a Nextcloud task"""
    id: str
    summary: str
    status: str = "NEEDS-ACTION"
    due: Optional[str] = None
    completed: Optional[datetime] = None
    priority: int = 0
    created: Optional[datetime] = None
    modified: Optional[datetime] = None
    calendar_id: str
    calendar_name: str
    description: Optional[str] = None
    parent_id: Optional[str] = None
    related_to: Optional[str] = None
    etag: Optional[str] = None


class Calendar(BaseModel):
    """Model representing a Nextcloud calendar"""
    id: str
    name: str
    url: str
    description: Optional[str] = None
    color: Optional[str] = None
    enabled: bool = True
    task_count: int = 0


class NextcloudConfig(BaseModel):
    """Configuration for Nextcloud connection"""
    url: str
    username: str
    password: str
    calendars: List[str] = []


class SyncResult(BaseModel):
    """Result of a synchronization operation"""
    success: bool
    message: str
    tasks_added: int = 0
    tasks_updated: int = 0
    tasks_deleted: int = 0
    timestamp: datetime = datetime.utcnow()


class TaskFilter(BaseModel):
    """Filter criteria for tasks"""
    calendar_ids: Optional[List[str]] = None
    status: Optional[str] = None
    due_before: Optional[datetime] = None
    due_after: Optional[datetime] = None
    completed: Optional[bool] = None
    search_term: Optional[str] = None
    limit: Optional[int] = None
    offset: Optional[int] = None