"""
Task service for the Nextcloud Task Backend
Handles task synchronization, caching, and business logic
"""
import asyncio
import logging
import sys
import os
import hashlib
import aiosqlite
from typing import List, Optional
from datetime import datetime

# Add backend directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

import caldav
from caldav.elements import dav, cdav

from models import Task, Calendar, NextcloudConfig, SyncResult, TaskFilter
from utils.database import (
    save_tasks, get_tasks, get_task_by_id, save_calendars, get_calendars,
    get_sync_state, update_sync_state, clear_local_data, DATABASE_PATH
)

logger = logging.getLogger(__name__)


class TaskService:
    """Service class for handling task operations"""
    
    def __init__(self):
        self.client = None
        self.config = None
        self.is_connected = False
    
    def _generate_id(self, url: str) -> str:
        """Generate a consistent ID from URL using MD5 hash"""
        return hashlib.md5(url.encode()).hexdigest()

    async def connect(self, config: NextcloudConfig) -> bool:
        """Connect to Nextcloud using the provided configuration"""
        try:
            self.client = caldav.DAVClient(
                url=config.url,
                username=config.username,
                password=config.password
            )
            self.config = config

            # Test connection
            principal = self.client.principal()
            calendars = principal.calendars()

            # Update local calendar records
            local_calendars = []
            seen_urls = set()
            for cal in calendars:
                # Skip duplicates (same URL)
                cal_url = str(cal.url)
                if cal_url in seen_urls:
                    continue
                seen_urls.add(cal_url)
                
                # Check if it's a task calendar
                try:
                    supported_components = cal.get_supported_components()
                    if supported_components and 'VTODO' in str(supported_components):
                        calendar = Calendar(
                            id=self._generate_id(cal_url),
                            name=cal.name,
                            url=cal_url,
                            description=cal.description if hasattr(cal, 'description') else None
                        )
                        local_calendars.append(calendar)
                except:
                    # If we can't determine supported components, try to see if it contains tasks
                    try:
                        sample_tasks = cal.todos(include_completed=True)[:1]
                        if len(sample_tasks) > 0:
                            calendar = Calendar(
                                id=self._generate_id(cal_url),
                                name=cal.name,
                                url=cal_url,
                                description=cal.description if hasattr(cal, 'description') else None
                            )
                            local_calendars.append(calendar)
                    except:
                        continue

            # Clear existing calendars before saving (to avoid duplicates)
            async with aiosqlite.connect(DATABASE_PATH) as db:
                await db.execute("DELETE FROM calendars")
                await db.commit()

            # Save calendars to database
            await save_calendars(local_calendars)
            
            self.is_connected = True
            logger.info(f"Successfully connected to Nextcloud: {config.url}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to Nextcloud: {e}")
            self.is_connected = False
            return False
    
    async def get_calendars(self, enabled_only: bool = True) -> List[Calendar]:
        """Get calendars from local database"""
        return await get_calendars(enabled_only)
    
    async def get_tasks(self, filter_params: Optional[TaskFilter] = None) -> List[Task]:
        """Get tasks from local database with optional filtering"""
        if filter_params is None:
            filter_params = TaskFilter()
        
        return await get_tasks(
            calendar_ids=filter_params.calendar_ids,
            status=filter_params.status,
            due_before=filter_params.due_before,
            due_after=filter_params.due_after,
            completed=filter_params.completed,
            search_term=filter_params.search_term,
            limit=filter_params.limit,
            offset=filter_params.offset
        )
    
    async def get_task_by_id(self, task_id: str) -> Optional[Task]:
        """Get a specific task by ID"""
        return await get_task_by_id(task_id)
    
    async def sync_tasks(self) -> SyncResult:
        """Synchronize tasks with Nextcloud server"""
        if not self.is_connected or not self.client:
            return SyncResult(
                success=False,
                message="Not connected to Nextcloud"
            )

        try:
            logger.info("Starting task synchronization...")

            # Get current sync state
            sync_state = await get_sync_state()

            # Get principal and calendars - use the same calendars as stored during connect
            principal = self.client.principal()
            calendars = principal.calendars()

            # Build a map of calendar URL to calendar object for consistent ID generation
            calendar_map = {}
            for cal in calendars:
                cal_url = str(cal.url)
                calendar_id = self._generate_id(cal_url)
                calendar_map[cal_url] = {
                    'id': calendar_id,
                    'object': cal,
                    'name': cal.name
                }

            all_tasks = []
            tasks_added = 0
            tasks_updated = 0

            for cal_url, cal_info in calendar_map.items():
                calendar = cal_info['object']
                calendar_id = cal_info['id']
                calendar_name = cal_info['name']
                
                # Check if this calendar should be synced based on config
                if self.config.calendars and calendar_name not in self.config.calendars:
                    continue

                try:
                    # Get tasks from this calendar
                    calendar_tasks = calendar.todos()
                    
                    for task_obj in calendar_tasks:
                        # Extract task properties
                        summary = "No Summary"
                        status = "NEEDS-ACTION"
                        due_date = None
                        created = None
                        modified = None
                        priority = 0
                        description = None
                        
                        # Try to get properties using icalendar instance
                        if hasattr(task_obj, '_icalendar_instance') and task_obj._icalendar_instance:
                            vtodo_component = task_obj._icalendar_instance.walk('VTODO')[0] if task_obj._icalendar_instance.subcomponents else None
                            if vtodo_component:
                                # Extract summary
                                if hasattr(vtodo_component, 'get') and vtodo_component.get('SUMMARY'):
                                    summary = str(vtodo_component.get('SUMMARY'))

                                # Extract status
                                if hasattr(vtodo_component, 'get') and vtodo_component.get('STATUS'):
                                    status = str(vtodo_component.get('STATUS'))

                                # Extract due date
                                if hasattr(vtodo_component, 'get') and vtodo_component.get('DUE'):
                                    due_val = vtodo_component.get('DUE')
                                    if hasattr(due_val, 'to_ical'):
                                        due_date = due_val.to_ical().decode('utf-8') if isinstance(due_val.to_ical(), bytes) else str(due_val.to_ical())
                                    else:
                                        due_date = str(due_val)

                                # Extract creation date
                                if hasattr(vtodo_component, 'get') and vtodo_component.get('CREATED'):
                                    created_val = vtodo_component.get('CREATED')
                                    if hasattr(created_val, 'to_ical'):
                                        created_str = created_val.to_ical().decode('utf-8') if isinstance(created_val.to_ical(), bytes) else str(created_val.to_ical())
                                        try:
                                            created = datetime.fromisoformat(created_str.replace('Z', '+00:00'))
                                        except:
                                            pass

                                # Extract modification date
                                if hasattr(vtodo_component, 'get') and vtodo_component.get('LAST-MODIFIED'):
                                    mod_val = vtodo_component.get('LAST-MODIFIED')
                                    if hasattr(mod_val, 'to_ical'):
                                        mod_str = mod_val.to_ical().decode('utf-8') if isinstance(mod_val.to_ical(), bytes) else str(mod_val.to_ical())
                                        try:
                                            modified = datetime.fromisoformat(mod_str.replace('Z', '+00:00'))
                                        except:
                                            pass

                                # Extract priority
                                if hasattr(vtodo_component, 'get') and vtodo_component.get('PRIORITY'):
                                    try:
                                        priority = int(vtodo_component.get('PRIORITY'))
                                    except:
                                        priority = 0

                                # Extract description
                                if hasattr(vtodo_component, 'get') and vtodo_component.get('DESCRIPTION'):
                                    description = str(vtodo_component.get('DESCRIPTION'))

                        # Get unique identifier for the task using consistent hash
                        task_id = self._generate_id(str(task_obj.url)) if hasattr(task_obj, 'url') else str(id(task_obj))

                        # Create task model with consistent calendar_id from calendar_map
                        task = Task(
                            id=task_id,
                            summary=summary,
                            status=status,
                            due=due_date,
                            created=created,
                            modified=modified,
                            priority=priority,
                            description=description,
                            calendar_id=calendar_id,  # Use pre-computed ID from calendar_map
                            calendar_name=calendar_name,  # Use pre-computed name from calendar_map
                            etag=getattr(task_obj, 'etag', None)
                        )

                        all_tasks.append(task)
                
                except Exception as e:
                    logger.error(f"Error getting tasks from calendar {calendar.name}: {e}")
                    continue

            # Clear existing tasks before saving (to avoid duplicates)
            async with aiosqlite.connect(DATABASE_PATH) as db:
                await db.execute("DELETE FROM tasks")
                await db.commit()

            # Save all tasks to database
            await save_tasks(all_tasks)
            
            # Update sync state
            await update_sync_state(last_sync_time=datetime.utcnow())
            
            logger.info(f"Synchronization completed. Processed {len(all_tasks)} tasks.")
            
            return SyncResult(
                success=True,
                message=f"Successfully synchronized {len(all_tasks)} tasks",
                tasks_added=len(all_tasks),
                tasks_updated=0,  # For simplicity, counting all as added
                tasks_deleted=0,
                timestamp=datetime.utcnow()
            )
            
        except Exception as e:
            logger.error(f"Error during task synchronization: {e}")
            return SyncResult(
                success=False,
                message=f"Synchronization failed: {str(e)}"
            )
    
    async def search_tasks(self, search_term: str) -> List[Task]:
        """Search tasks by term in summary or description"""
        filter_params = TaskFilter(search_term=search_term)
        return await get_tasks(filter_params)
    
    async def get_today_tasks(self) -> List[Task]:
        """Get tasks that are due today or overdue"""
        from datetime import date
        today = date.today()

        # Due dates are stored as YYYYMMDD format, so use the same format for comparison
        today_str = today.strftime("%Y%m%d")

        # Create a filter for tasks due today or earlier
        # Note: We need to query directly since the due_before filter expects ISO format
        async with aiosqlite.connect(DATABASE_PATH) as db:
            db.row_factory = aiosqlite.Row
            query = """
                SELECT * FROM tasks 
                WHERE deleted = 0 
                AND due IS NOT NULL 
                AND due != ''
                AND due <= ?
                AND (completed IS NULL OR completed = '')
                ORDER BY CASE WHEN due IS NULL THEN 1 ELSE 0 END, due ASC
            """
            async with db.execute(query, (today_str,)) as cursor:
                rows = await cursor.fetchall()

        tasks = []
        for row in rows:
            task = Task(
                id=row['id'],
                summary=row['summary'],
                status=row['status'],
                due=row['due'],
                completed=datetime.fromisoformat(row['completed']) if row['completed'] else None,
                priority=row['priority'],
                created=datetime.fromisoformat(row['created']) if row['created'] else None,
                modified=datetime.fromisoformat(row['modified']) if row['modified'] else None,
                calendar_id=row['calendar_id'],
                calendar_name=row['calendar_name'],
                description=row['description'],
                parent_id=row['parent_id'],
                related_to=row['related_to'],
                etag=row['etag']
            )
            tasks.append(task)

        return tasks
    
    async def disconnect(self):
        """Disconnect from Nextcloud"""
        self.client = None
        self.config = None
        self.is_connected = False
        logger.info("Disconnected from Nextcloud")