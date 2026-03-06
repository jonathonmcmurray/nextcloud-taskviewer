"""
Module for handling caching of tasks, calendars, and ETags.
"""
import json
import os
import pickle
from datetime import datetime
import logging


class CacheManager:
    """Handles caching of tasks, calendars, and ETags to local files."""
    
    def __init__(self, cache_file='tasks_cache.pkl', etag_cache_file='etag_cache.json', 
                 calendar_cache_file='calendars_cache.pkl'):
        self.cache_file = cache_file
        self.etag_cache_file = etag_cache_file
        self.calendar_cache_file = calendar_cache_file
        self.logger = logging.getLogger(__name__)

    def save_tasks_to_cache(self, tasks, etags=None):
        """Save tasks to local cache with ETags - expects already processed tasks"""
        try:
            # Tasks are already processed with the correct structure, just save them
            # But make sure to extract ETags if available from the task objects
            processed_tasks = []
            for task_dict in tasks:
                # Copy the existing task dictionary
                processed_task = task_dict.copy()

                # Extract ETag from the raw task object if available
                raw_task_obj = task_dict.get('task_obj')
                if raw_task_obj:
                    etag = getattr(raw_task_obj, 'etag', None)
                    processed_task['etag'] = etag
                else:
                    processed_task['etag'] = None

                processed_tasks.append(processed_task)

            # Save tasks with timestamp
            cache_data = {
                'timestamp': datetime.now(),
                'tasks': processed_tasks
            }
            with open(self.cache_file, 'wb') as f:
                pickle.dump(cache_data, f)

            # Save ETags if provided
            if etags:
                with open(self.etag_cache_file, 'w') as f:
                    json.dump(etags, f)
        except Exception as e:
            self.logger.error(f"Error saving cache: {e}", exc_info=True)

    def load_tasks_from_cache(self):
        """Load tasks from local cache"""
        try:
            if os.path.exists(self.cache_file):
                with open(self.cache_file, 'rb') as f:
                    cache_data = pickle.load(f)
                    return cache_data.get('tasks', []), cache_data.get('timestamp', None)
        except Exception as e:
            self.logger.error(f"Error loading cache: {e}", exc_info=True)
        return [], None

    def save_calendars_to_cache(self, calendars):
        """Save calendars to local cache"""
        try:
            # Prepare calendar data for caching
            calendar_data = []
            for calendar in calendars:
                # Get task count with error handling for problematic calendars
                tasks_count = 0
                if hasattr(calendar, 'todos'):
                    try:
                        tasks_count = len(calendar.todos())
                    except (OSError, ValueError, TypeError) as e:
                        # Handle datetime/OS errors that occur on some systems (especially Windows)
                        self.logger.warning(f"Could not get task count for calendar {calendar.name}: {e}")
                        # Try alternative method to get task count
                        try:
                            tasks_count = len(calendar.todos(include_completed=True))
                        except:
                            # If all methods fail, default to 0
                            tasks_count = 0
                calendar_info = {
                    'name': calendar.name,
                    'url': str(calendar.url),
                    'tasks_count': tasks_count
                }
                calendar_data.append(calendar_info)

            cache_data = {
                'timestamp': datetime.now(),
                'calendars': calendar_data
            }
            with open(self.calendar_cache_file, 'wb') as f:
                pickle.dump(cache_data, f)
        except Exception as e:
            self.logger.error(f"Error saving calendar cache: {e}", exc_info=True)

    def load_calendars_from_cache(self):
        """Load calendars from local cache"""
        try:
            if os.path.exists(self.calendar_cache_file):
                with open(self.calendar_cache_file, 'rb') as f:
                    cache_data = pickle.load(f)
                    return cache_data.get('calendars', []), cache_data.get('timestamp', None)
        except Exception as e:
            self.logger.error(f"Error loading calendar cache: {e}", exc_info=True)
        return [], None

    def load_etags_from_cache(self):
        """Load ETags from cache"""
        try:
            if os.path.exists(self.etag_cache_file):
                with open(self.etag_cache_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            self.logger.error(f"Error loading ETag cache: {e}", exc_info=True)
        return {}

    def get_updated_tasks(self, calendar, cached_tasks):
        """Compare cached tasks with server to get updated tasks using ETags"""
        try:
            # Get all tasks from server
            server_tasks = calendar.todos()

            # Create a map of cached tasks by URL for comparison
            cached_task_map = {task['task_obj'].url: task for task in cached_tasks}

            # Find new or updated tasks
            updated_tasks = []
            new_tasks = []

            for task in server_tasks:
                task_url = task.url

                if task_url in cached_task_map:
                    # Task exists in cache, check if it's been updated
                    cached_task = cached_task_map[task_url]

                    # Get ETag from server task (if available)
                    server_etag = getattr(task, 'etag', None)
                    cached_etag = cached_task.get('etag', None)

                    # Compare ETags to see if task has been updated
                    if server_etag and cached_etag and server_etag != cached_etag:
                        # Task has been updated
                        updated_tasks.append(task)
                    elif not server_etag and not cached_etag:
                        # No ETag comparison possible, check if content has changed
                        # For now, we'll consider it updated to be safe
                        updated_tasks.append(task)
                    # If ETag matches, task hasn't changed, so we don't add it
                else:
                    # New task
                    new_tasks.append(task)

            # Return both new and updated tasks
            return new_tasks + updated_tasks
        except Exception as e:
            self.logger.error(f"Error getting updated tasks: {e}", exc_info=True)
            # If ETag comparison fails, return all server tasks to be safe
            return calendar.todos()