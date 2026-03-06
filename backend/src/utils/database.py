"""
Database utilities for the Nextcloud Task Backend
Uses SQLite for local caching and synchronization state
"""
import aiosqlite
import asyncio
import sys
import os
from typing import List, Optional
from datetime import datetime
import json
import logging

# Add backend directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from models import Task, Calendar

logger = logging.getLogger(__name__)

DATABASE_PATH = "nextcloud_tasks.db"

async def init_db():
    """Initialize the database with required tables"""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        # Create tasks table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id TEXT PRIMARY KEY,
                summary TEXT NOT NULL,
                status TEXT DEFAULT 'NEEDS-ACTION',
                due TEXT,
                completed TEXT,
                priority INTEGER DEFAULT 0,
                created TEXT,
                modified TEXT,
                calendar_id TEXT,
                calendar_name TEXT,
                description TEXT,
                parent_id TEXT,
                related_to TEXT,
                etag TEXT,
                last_sync TEXT,
                deleted BOOLEAN DEFAULT 0
            )
        """)
        
        # Create calendars table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS calendars (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                url TEXT NOT NULL,
                description TEXT,
                color TEXT,
                enabled BOOLEAN DEFAULT 1,
                task_count INTEGER DEFAULT 0,
                last_sync TEXT
            )
        """)
        
        # Create sync_state table to track synchronization state
        await db.execute("""
            CREATE TABLE IF NOT EXISTS sync_state (
                id TEXT PRIMARY KEY,
                last_sync_time TEXT,
                sync_token TEXT,
                config_hash TEXT
            )
        """)
        
        # Create indexes for better performance
        await db.execute("CREATE INDEX IF NOT EXISTS idx_tasks_calendar ON tasks(calendar_id)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_tasks_due ON tasks(due)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_tasks_modified ON tasks(modified)")
        
        await db.commit()
        logger.info("Database initialized successfully")


async def save_tasks(tasks: List[Task]):
    """Save tasks to the database"""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        for task in tasks:
            await db.execute("""
                INSERT OR REPLACE INTO tasks 
                (id, summary, status, due, completed, priority, created, modified, 
                 calendar_id, calendar_name, description, parent_id, related_to, etag, last_sync)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                task.id, task.summary, task.status, task.due, 
                task.completed.isoformat() if task.completed else None,
                task.priority, 
                task.created.isoformat() if task.created else None,
                task.modified.isoformat() if task.modified else None,
                task.calendar_id, task.calendar_name, task.description,
                task.parent_id, task.related_to, task.etag,
                datetime.utcnow().isoformat()
            ))
        await db.commit()


async def get_tasks(calendar_ids: Optional[List[str]] = None, 
                  status: Optional[str] = None,
                  due_before: Optional[datetime] = None,
                  due_after: Optional[datetime] = None,
                  completed: Optional[bool] = None,
                  search_term: Optional[str] = None,
                  limit: Optional[int] = None,
                  offset: Optional[int] = None) -> List[Task]:
    """Retrieve tasks from the database with optional filters"""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row  # Enable column access by name
        
        query = "SELECT * FROM tasks WHERE deleted = 0"
        params = []
        
        if calendar_ids:
            placeholders = ','.join(['?' for _ in calendar_ids])
            query += f" AND calendar_id IN ({placeholders})"
            params.extend(calendar_ids)
            
        if status:
            query += " AND status = ?"
            params.append(status)
            
        if due_before:
            query += " AND due <= ?"
            params.append(due_before.isoformat())
            
        if due_after:
            query += " AND due >= ?"
            params.append(due_after.isoformat())
            
        if completed is not None:
            if completed:
                query += " AND completed IS NOT NULL"
            else:
                query += " AND completed IS NULL"
                
        if search_term:
            query += " AND (summary LIKE ? OR description LIKE ?)"
            params.extend([f'%{search_term}%', f'%{search_term}%'])

        # SQLite doesn't support NULLS LAST, use CASE expression instead
        query += " ORDER BY CASE WHEN due IS NULL THEN 1 ELSE 0 END, due ASC"

        if limit:
            query += f" LIMIT {limit}"
            if offset:
                query += f" OFFSET {offset}"

        async with db.execute(query, params) as cursor:
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


async def get_task_by_id(task_id: str) -> Optional[Task]:
    """Retrieve a specific task by ID"""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM tasks WHERE id = ? AND deleted = 0", (task_id,)) as cursor:
            row = await cursor.fetchone()

        if not row:
            return None
            
        return Task(
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


async def save_calendars(calendars: List[Calendar]):
    """Save calendars to the database"""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        for calendar in calendars:
            await db.execute("""
                INSERT OR REPLACE INTO calendars
                (id, name, url, description, color, enabled, task_count, last_sync)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                calendar.id, calendar.name, calendar.url, calendar.description,
                calendar.color, calendar.enabled, calendar.task_count,
                datetime.utcnow().isoformat()
            ))
        await db.commit()


async def get_calendars(enabled_only: bool = True) -> List[Calendar]:
    """Retrieve calendars from the database"""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row

        query = "SELECT * FROM calendars"
        if enabled_only:
            query += " WHERE enabled = 1"
        query += " ORDER BY name"

        async with db.execute(query) as cursor:
            rows = await cursor.fetchall()

        calendars = []
        for row in rows:
            calendar = Calendar(
                id=row['id'],
                name=row['name'],
                url=row['url'],
                description=row['description'],
                color=row['color'],
                enabled=bool(row['enabled']),
                task_count=row['task_count']
            )
            calendars.append(calendar)
        
        return calendars


async def get_sync_state() -> dict:
    """Get the current synchronization state"""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM sync_state LIMIT 1") as cursor:
            row = await cursor.fetchone()

        if not row:
            return {
                'last_sync_time': None,
                'sync_token': None,
                'config_hash': None
            }
        
        return {
            'last_sync_time': datetime.fromisoformat(row['last_sync_time']) if row['last_sync_time'] else None,
            'sync_token': row['sync_token'],
            'config_hash': row['config_hash']
        }


async def update_sync_state(last_sync_time: Optional[datetime] = None, 
                          sync_token: Optional[str] = None,
                          config_hash: Optional[str] = None):
    """Update the synchronization state"""
    state = await get_sync_state()
    
    if last_sync_time is None:
        last_sync_time = state['last_sync_time'] or datetime.utcnow()
    if sync_token is None:
        sync_token = state['sync_token']
    if config_hash is None:
        config_hash = state['config_hash']
    
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("""
            INSERT OR REPLACE INTO sync_state
            (id, last_sync_time, sync_token, config_hash)
            VALUES (?, ?, ?, ?)
        """, ("default", last_sync_time.isoformat(), sync_token, config_hash))
        await db.commit()


async def clear_local_data():
    """Clear all local data (for testing/reset purposes)"""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("DELETE FROM tasks")
        await db.execute("DELETE FROM calendars")
        await db.execute("DELETE FROM sync_state")
        await db.commit()
        logger.info("Local data cleared")