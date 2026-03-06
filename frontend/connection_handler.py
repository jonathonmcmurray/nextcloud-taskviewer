"""
Module for handling connections to Nextcloud and managing calendars/tasks.
"""
import caldav
from caldav.elements import dav, cdav
import threading
import time
import logging
import json
import os
import tkinter as tk
from datetime import datetime, date


class ConnectionHandler:
    """Handles all connection logic to Nextcloud and calendar/task operations."""
    
    def __init__(self, app_instance):
        self.app = app_instance  # Reference to main app for callbacks
        self.logger = logging.getLogger(__name__)
        self.calendars = []
        self.tasks = []
        self.original_tasks = []  # Store original tasks for filtering
        self.current_view = "all"  # Track current view: "all" or "today"

    def show_today_view(self):
        """Display only tasks that are due today or overdue"""
        try:
            today = date.today()
            
            # Store original tasks if not already stored
            if not self.original_tasks:
                self.original_tasks = self.tasks[:]
            
            # Filter tasks to show only those due today or overdue
            today_tasks = []
            for task in self.tasks:
                due_date_str = task.get('due', '').strip()
                if due_date_str:
                    try:
                        # Parse the due date - it could be in various formats
                        # Common format from CalDAV is YYYYMMDD or YYYY-MM-DD
                        parsed_date = None
                        
                        # Try different date formats
                        for fmt in ['%Y-%m-%d', '%Y%m%d', '%Y-%m-%dT%H:%M:%S', '%Y%m%dT%H%M%S']:
                            try:
                                parsed_date = datetime.strptime(due_date_str.split('T')[0], fmt.replace('T%H:%M:%S', '').replace('T%H%M%S', ''))
                                break
                            except ValueError:
                                continue
                        
                        if parsed_date:
                            task_due_date = parsed_date.date()
                            
                            # Include tasks that are due today or overdue
                            if task_due_date <= today:
                                today_tasks.append(task)
                    except Exception as e:
                        self.logger.warning(f"Could not parse due date '{due_date_str}' for task: {e}")
                        # If we can't parse the date, skip the task to be safe
                        continue
                # Only include tasks that have a due date set (the 'else' case is removed)
            
            # Sort tasks by due date (ascending)
            today_tasks = self._sort_tasks_by_due_date(today_tasks)
            
            # Update the task tree with filtered tasks
            self._update_task_tree(today_tasks)
            
            # Update status
            self.app.status_var.set(f"Today View: Showing {len(today_tasks)} tasks due today or overdue")
            
            # Set current view to today
            self.current_view = "today"
            
        except Exception as e:
            self.logger.error(f"Error showing today view: {e}", exc_info=True)
            self.app.status_var.set("Error showing today view")

    def _update_task_tree(self, tasks_to_show):
        """Helper method to update the task tree with given tasks"""
        # Clear existing tasks
        for item in self.app.task_tree.get_children():
            self.app.task_tree.delete(item)
        
        # Insert filtered tasks
        for task in tasks_to_show:
            self.app.task_tree.insert("", 'end', values=(
                task['summary'],
                task['status'],
                task['due'],
                task['calendar']
            ))

    def reset_view(self):
        """Reset to show all tasks again"""
        try:
            # Restore original tasks if available
            tasks_to_display = self.original_tasks if self.original_tasks else self.tasks
            
            # Sort tasks by due date (ascending)
            tasks_to_display = self._sort_tasks_by_due_date(tasks_to_display)
            
            # Update the task tree with sorted tasks
            self._update_task_tree(tasks_to_display)
            
            # Reset original tasks
            self.original_tasks = []
            
            # Update status
            self.app.status_var.set(f"Showing all {len(tasks_to_display)} tasks")
            
            # Set current view to all
            self.current_view = "all"
            
        except Exception as e:
            self.logger.error(f"Error resetting view: {e}", exc_info=True)
            self.app.status_var.set("Error resetting view")

    def _sort_tasks_by_due_date(self, tasks):
        """Sort tasks by due date in ascending order (earliest first)"""
        def get_sort_key(task):
            due_date_str = task.get('due', '').strip()
            if due_date_str:
                try:
                    # Parse the due date - it could be in various formats
                    for fmt in ['%Y-%m-%d', '%Y%m%d', '%Y-%m-%dT%H:%M:%S', '%Y%m%dT%H%M%S']:
                        try:
                            parsed_date = datetime.strptime(due_date_str.split('T')[0], fmt.replace('T%H:%M:%S', '').replace('T%H%M%S', ''))
                            return parsed_date.date()
                        except ValueError:
                            continue
                    # If parsing fails, return a far future date to put it at the end
                    return datetime.max.date()
                except:
                    # If parsing fails, return a far future date to put it at the end
                    return datetime.max.date()
            else:
                # Tasks without due dates go to the end
                return datetime.max.date()
        
        return sorted(tasks, key=get_sort_key)

    def connect_to_nextcloud(self, url, username, password):
        """Connect to Nextcloud and load calendars"""
        if not url or not username or not password:
            raise ValueError("Please fill in all connection fields")

        # Show connecting status
        self.app.status_var.set("Connecting...")
        self.app.root.update()

        try:
            # Connect to Nextcloud
            client = caldav.DAVClient(url=url, username=username, password=password)
            principal = client.principal()

            # Get all calendars
            calendars = principal.calendars()

            # Clear existing calendars in listbox
            self.app.calendar_listbox.delete(0, 'end')

            # Store calendar objects and populate listbox
            self.calendars = []
            for calendar in calendars:
                # Check if it's a task calendar (VTODO)
                try:
                    # Attempt to get supported components to verify it's a task calendar
                    supported_components = calendar.get_supported_components()
                    if supported_components and 'VTODO' in str(supported_components):
                        self.calendars.append(calendar)
                        self.app.calendar_listbox.insert('end', calendar.name)
                    else:
                        # Even if get_supported_components doesn't work, try to see if it contains tasks
                        # by attempting to fetch a few tasks
                        try:
                            sample_tasks = calendar.todos(include_completed=True)[:1]  # Just get first task to test
                            if len(sample_tasks) > 0 or True:  # If we can access the calendar, add it
                                self.calendars.append(calendar)
                                self.app.calendar_listbox.insert('end', calendar.name)
                        except:
                            # If it's not a task calendar, skip it
                            continue
                except:
                    # If we can't determine the supported components, try to see if it contains tasks
                    try:
                        sample_tasks = calendar.todos(include_completed=True)[:1]  # Just get first task to test
                        if len(sample_tasks) > 0 or True:  # If we can access the calendar, add it
                            self.calendars.append(calendar)
                            self.app.calendar_listbox.insert('end', calendar.name)
                    except:
                        # If it's not a task calendar, skip it
                        continue

            if not self.calendars:
                self.logger.info("No task calendars found")
            else:
                # Select all calendars by default
                for i in range(len(self.calendars)):
                    self.app.calendar_listbox.selection_set(i)

                self.app.status_var.set(f"Connected - Found {len(self.calendars)} task calendars")

                # Save calendars to cache
                self.app.cache_manager.save_calendars_to_cache(self.calendars)

                # Load tasks
                self.load_tasks()

        except Exception as e:
            self.logger.error(f"Connection Error: {e}", exc_info=True)
            raise

    def load_tasks(self):
        """Load tasks from selected calendars"""
        # Clear existing tasks
        for item in self.app.task_tree.get_children():
            self.app.task_tree.delete(item)

        # Get selected calendars
        selected_indices = self.app.calendar_listbox.curselection()
        if not selected_indices:
            return

        # Collect tasks from selected calendars
        all_tasks = []
        for idx in selected_indices:
            calendar = self.calendars[idx]
            try:
                # Log calendar info
                self.logger.debug(f"Loading tasks from calendar: {calendar.name}")
                self.logger.debug(f"Calendar URL: {calendar.url}")

                # Try different methods to get tasks
                try:
                    tasks = calendar.todos()
                except Exception as e:
                    self.logger.warning(f"Error getting tasks with default method: {e}")
                    try:
                        # Try getting all todos including completed ones
                        tasks = calendar.todos(include_completed=True)
                    except Exception as e2:
                        self.logger.warning(f"Error getting tasks with include_completed: {e2}")
                        # Last resort - try with no parameters handled
                        tasks = []

                # Log task count
                self.logger.debug(f"Found {len(tasks)} tasks in calendar {calendar.name}")

                for task in tasks:
                    # More comprehensive logging to understand task object structure
                    self.logger.debug(f"Processing task: {task}")
                    self.logger.debug(f"Task type: {type(task)}")
                    self.logger.debug(f"Task attributes: {dir(task)}")
                    self.logger.debug(f"Task data exists: {hasattr(task, 'data')}")
                    if hasattr(task, 'data'):
                        self.logger.debug(f"Task data: {task.data}")
                    self.logger.debug(f"Task instance: {task.instance}")
                    self.logger.debug(f"Task instance type: {type(task.instance)}")
                    if task.instance:
                        self.logger.debug(f"Instance attributes: {dir(task.instance)}")
                    # Try to access the ical data in multiple ways
                    try:
                        raw_data = task.get_property('data')
                        self.logger.debug(f"Raw data via get_property: {raw_data}")
                    except Exception as e:
                        self.logger.debug(f"get_property('data') failed: {e}")

                    try:
                        ical = task.ical
                        self.logger.debug(f"Ical property: {ical}")
                    except Exception as e:
                        self.logger.debug(f"task.ical failed: {e}")

                    try:
                        self.logger.debug(f"Task object dict: {vars(task) if hasattr(task, '__dict__') else 'No __dict__'}")
                    except Exception as e:
                        self.logger.debug(f"Could not access task __dict__: {e}")

                    # Extract task properties using helper methods
                    summary, status, due_date = self.app.task_parser.extract_task_properties(task)

                    # Extract related-to for parent-child relationships
                    related_to = self.app.task_parser.extract_related_to(task)

                    # Get unique identifier for the task
                    uid = None
                    if hasattr(task, 'id') and task.id:
                        uid = task.id
                    elif hasattr(task, 'url'):
                        uid = str(task.url)

                    all_tasks.append({
                        'summary': summary,
                        'status': status,
                        'due': due_date,
                        'calendar': calendar.name,
                        'task_obj': task,
                        'related_to': related_to,  # Track parent-child relationships
                        'uid': uid  # Unique identifier
                    })
            except Exception as e:
                self.logger.error(f"Error loading tasks from calendar {calendar.name}: {e}", exc_info=True)

        # Store tasks for filtering
        self.tasks = all_tasks

        self.logger.info(f"Total tasks loaded: {len(all_tasks)}")

        # Save to cache
        self.app.cache_manager.save_tasks_to_cache(all_tasks)

        # Build task hierarchy and insert into treeview
        self.build_task_hierarchy()

    def build_task_hierarchy(self):
        """Build parent-child hierarchy and insert tasks into treeview"""
        # Sort tasks by due date before building hierarchy
        sorted_tasks = self._sort_tasks_by_due_date(self.tasks)
        
        # Create a mapping of UID to task for quick lookup
        task_map = {}
        for task in sorted_tasks:
            uid = task['uid']
            if uid:
                task_map[uid] = task

        # Separate parent tasks and child tasks
        parent_tasks = []
        child_tasks = []

        for task in sorted_tasks:
            if task['related_to'] and task['related_to'] in task_map:
                # This is a child task
                child_tasks.append(task)
            else:
                # This is a parent task or a task without a parent
                parent_tasks.append(task)

        # Insert parent tasks first
        parent_items = {}  # Map UID to treeview item ID
        for task in parent_tasks:
            item_id = self.app.task_tree.insert("", 'end', values=(
                task['summary'],
                task['status'],
                task['due'],
                task['calendar']
            ))
            if task['uid']:
                parent_items[task['uid']] = item_id

        # Insert child tasks under their parents
        for task in child_tasks:
            parent_uid = task['related_to']
            if parent_uid in parent_items:
                # Insert as child of the parent
                self.app.task_tree.insert(parent_items[parent_uid], 'end', values=(
                    "  ↳ " + task['summary'],  # Indent to show it's a subtask
                    task['status'],
                    task['due'],
                    task['calendar']
                ))
            else:
                # Parent not found, add as a regular task
                self.app.task_tree.insert("", 'end', values=(
                    task['summary'],
                    task['status'],
                    task['due'],
                    task['calendar']
                ))

        # Expand all parent nodes to show children
        for item_id in parent_items.values():
            self.app.task_tree.item(item_id, open=True)
        
        # After loading tasks, restore the current view if needed
        if self.current_view == "today":
            self.show_today_view()

    def refresh_tasks(self):
        """Refresh the task list"""
        if not self.calendars:
            raise RuntimeError("Not connected to Nextcloud")
            
        self.load_tasks()
        self.app.status_var.set(f"Refreshed - Showing {len(self.tasks)} tasks")

    def load_cached_tasks_on_startup(self):
        """Load cached tasks on application startup"""
        self.app.logger.debug("Attempting to load cached tasks on startup...")
        try:
            cached_tasks, cache_timestamp = self.app.cache_manager.load_tasks_from_cache()
            if cached_tasks:
                self.app.logger.info(f"Loaded {len(cached_tasks)} tasks from cache on startup (cached at {cache_timestamp})")

                # Process cached tasks to ensure they have the right structure
                processed_tasks = []
                for task_data in cached_tasks:
                    # Ensure each task has the required fields for display
                    processed_task = {
                        'summary': task_data.get('summary', 'No Summary'),
                        'status': task_data.get('status', 'Unknown'),
                        'due': task_data.get('due', ''),
                        'calendar': task_data.get('calendar', 'Unknown'),
                        'task_obj': task_data.get('task_obj'),
                        'related_to': task_data.get('related_to'),
                        'uid': task_data.get('uid')
                    }
                    processed_tasks.append(processed_task)

                self.app.tasks = processed_tasks
                # Store original tasks for filtering
                self.original_tasks = processed_tasks[:]
                
                # Build the task hierarchy to display the cached tasks
                self.build_task_hierarchy()
                
                # Update status to show cached tasks are loaded
                self.app.status_var.set(f"Showing {len(processed_tasks)} cached tasks - Connect to refresh")
                
                # Force UI update to ensure tasks are displayed
                self.app.root.update_idletasks()
            else:
                self.app.logger.debug("No cached tasks found")
                self.app.tasks = []
        except Exception as e:
            self.app.logger.error(f"Error loading cached tasks on startup: {e}", exc_info=True)
            self.app.tasks = []

    def load_cached_calendars_on_startup(self):
        """Load cached calendars on application startup"""
        try:
            cached_calendars, cache_timestamp = self.app.cache_manager.load_calendars_from_cache()
            if cached_calendars:
                self.app.logger.info(f"Loaded {len(cached_calendars)} calendars from cache on startup (cached at {cache_timestamp})")

                # Populate the calendar listbox with cached calendar names
                self.app.calendar_listbox.delete(0, 'end')  # Clear existing entries
                for calendar_info in cached_calendars:
                    self.app.calendar_listbox.insert('end', calendar_info['name'])

                # Select all calendars by default
                for i in range(len(cached_calendars)):
                    self.app.calendar_listbox.selection_set(i)

                # Update status
                self.app.status_var.set(f"Loaded {len(cached_calendars)} calendars from cache - Connect to refresh")
                
                # Load cached tasks immediately after loading calendars
                self.load_cached_tasks_on_startup()
            else:
                self.app.logger.debug("No cached calendars found")
        except Exception as e:
            self.app.logger.error(f"Error loading cached calendars on startup: {e}", exc_info=True)

    def auto_connect_if_credentials_saved(self):
        """Auto-connect if credentials are saved"""
        try:
            # Check if credentials are saved
            if os.path.exists('credentials.json'):
                with open('credentials.json', 'r') as f:
                    creds = json.load(f)
                    if creds.get('url') and creds.get('username') and creds.get('password'):
                        # Set the saved credentials
                        self.app.url_var.set(creds.get('url', ''))
                        self.app.username_var.set(creds.get('username', ''))
                        self.app.password_var.set(creds.get('password', ''))
                        self.app.save_credentials_var.set(True)  # Check the save credentials box

                        # Auto-connect after a short delay to allow UI to initialize
                        self.app.root.after(1000, self.app.connect_to_nextcloud)
                        self.app.logger.info("Auto-connecting with saved credentials...")
        except Exception as e:
            self.app.logger.error(f"Error during auto-connect: {e}", exc_info=True)

    def start_auto_refresh(self):
        """Start the automatic refresh timer"""
        # Set refresh interval to 60 seconds (60000 ms)
        self.refresh_interval = 60000  # 60 seconds in milliseconds
        self.schedule_next_refresh()

    def schedule_next_refresh(self):
        """Schedule the next refresh"""
        # Cancel any existing refresh scheduled
        if hasattr(self, 'refresh_job_id') and self.refresh_job_id:
            self.app.root.after_cancel(self.refresh_job_id)

        # Schedule the next refresh
        self.refresh_job_id = self.app.root.after(self.refresh_interval, self.perform_auto_refresh)

    def perform_auto_refresh(self):
        """Perform the automatic refresh of tasks"""
        try:
            # Store the current view before refreshing
            current_view = self.current_view
            
            # Only refresh if we're connected (have calendars)
            if hasattr(self, 'calendars') and self.calendars:
                self.app.logger.info("Performing automatic refresh...")

                # Update status
                self.app.status_var.set("Auto-refreshing tasks...")

                # Reload tasks from selected calendars
                self.load_tasks()

                # Update status with completion message
                self.app.status_var.set(f"Auto-refresh completed - Showing {len(self.app.tasks)} tasks")

                # Restore the previous view after refresh
                if current_view == "today":
                    self.show_today_view()
                else:
                    # If we were in "all" view, make sure we're showing all tasks
                    self.reset_view()

                # Schedule the next refresh
                self.schedule_next_refresh()
            else:
                # If not connected, just schedule the next refresh without performing it
                self.schedule_next_refresh()
        except Exception as e:
            self.app.logger.error(f"Error during auto-refresh: {e}", exc_info=True)
            self.app.status_var.set("Auto-refresh failed")
            # Still schedule the next refresh even if this one failed
            self.schedule_next_refresh()