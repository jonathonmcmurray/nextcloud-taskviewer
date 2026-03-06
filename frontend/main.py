"""
Nextcloud Task Frontend
Desktop application that connects to the Nextcloud Task Backend service
"""
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
import time
import json
import os
import logging
from datetime import datetime
import requests

from ui_components import UIComponents
from credential_manager import CredentialManager


class TaskFrontendApp:
    """Frontend application that connects to the backend service"""
    
    def __init__(self, root):
        self.root = root
        self.backend_url = "http://localhost:8000"  # Default backend URL
        
        # Set up logging
        self.logger = logging.getLogger(__name__)
        if not self.logger.handlers:
            handler = logging.FileHandler('frontend.log')
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.DEBUG)

        # Initialize managers
        self.credential_manager = CredentialManager()

        # Initialize UI components
        self.ui = UIComponents(root, self)
        self.ui.setup_main_window()
        self.ui.setup_variables()

        # Load saved credentials if they exist (before UI is set up)
        self.load_saved_credentials()

        # Store tasks and calendars
        self.calendars = []
        self.tasks = []
        
        # Track current view state
        self.current_view = "all"  # "all" or "today"

        self.ui.setup_ui()

        # Load cached tasks on startup if available (after UI is initialized)
        self.load_cached_tasks_on_startup()

        # Load cached calendars on startup if available
        self.load_cached_calendars_on_startup()

        # Auto-connect if credentials are saved
        self.auto_connect_if_credentials_saved()

        # Start automatic refresh timer (every 60 seconds)
        self.start_auto_refresh()

    def connect_to_backend(self):
        """Connect to the backend service"""
        url = self.url_var.get()
        username = self.username_var.get()
        password = self.password_var.get()

        self.logger.info(f"Connect clicked - URL: {url}, Username: {username}")

        if not url or not username or not password:
            self.logger.error("Missing connection fields")
            messagebox.showerror("Error", "Please fill in all connection fields")
            return

        # Show connecting status
        self.status_var.set("Connecting to backend...")
        self.root.update()

        try:
            self.logger.info(f"Sending POST request to {self.backend_url}/auth/login")
            # Prepare config for backend
            config = {
                "url": url,
                "username": username,
                "password": password,
                "calendars": []  # Will sync all calendars by default
            }

            # Connect to backend (increased timeout for initial connection)
            response = requests.post(f"{self.backend_url}/auth/login", json=config, timeout=30)
            self.logger.info(f"Backend response status: {response.status_code}")
            self.logger.info(f"Backend response: {response.text}")

            if response.status_code == 200:
                result = response.json()
                self.logger.info(f"Parsed result: {result}")
                if result.get("success"):
                    self.logger.info("Connection successful")
                    self.status_var.set(f"Connected - {result.get('user')} - {result.get('tasks_synced', 0)} tasks synced")

                    # Load calendars from backend
                    self.logger.info("Loading calendars...")
                    self.load_calendars()

                    # Load tasks from backend
                    self.logger.info("Loading tasks...")
                    self.load_tasks()

                    # Save credentials if the checkbox is checked
                    self.save_credentials()
                else:
                    self.logger.error(f"Connection failed: {result.get('message')}")
                    messagebox.showerror("Connection Error", f"Failed to connect: {result.get('message')}")
                    self.status_var.set("Connection failed")
            else:
                error_msg = response.json().get("detail", "Unknown error") if response.content else "Connection failed"
                self.logger.error(f"Backend returned error: {response.status_code} - {error_msg}")
                messagebox.showerror("Connection Error", f"Failed to connect: {error_msg}")
                self.status_var.set("Connection failed")

        except requests.exceptions.ConnectionError as e:
            self.logger.error(f"Connection error: {e}")
            messagebox.showerror("Connection Error", f"Cannot connect to backend at {self.backend_url}")
            self.status_var.set("Backend connection failed")
        except requests.exceptions.Timeout as e:
            self.logger.error(f"Request timeout: {e}")
            messagebox.showerror("Connection Error", f"Request timed out: {e}")
            self.status_var.set("Connection timeout")
        except Exception as e:
            self.logger.error(f"Unexpected error: {e}", exc_info=True)
            messagebox.showerror("Connection Error", f"Failed to connect: {str(e)}")
            self.status_var.set("Connection failed")

    def load_calendars(self):
        """Load calendars from backend"""
        self.logger.info("Loading calendars from backend...")
        try:
            response = requests.get(f"{self.backend_url}/tasks/calendars", timeout=10)
            self.logger.info(f"Calendars response status: {response.status_code}")
            self.logger.info(f"Calendars response: {response.text}")
            
            if response.status_code == 200:
                calendars = response.json()
                self.logger.info(f"Found {len(calendars)} calendars: {calendars}")

                # Clear existing calendars in listbox
                self.calendar_listbox.delete(0, tk.END)

                # Store calendar objects and populate listbox
                self.calendars = calendars
                for calendar in calendars:
                    self.calendar_listbox.insert(tk.END, calendar['name'])

                # Select all calendars by default
                for i in range(len(calendars)):
                    self.calendar_listbox.selection_set(i)

                self.status_var.set(f"Connected - Found {len(calendars)} calendars")
                self.logger.info("Calendars loaded successfully")
            else:
                self.logger.error(f"Failed to load calendars: {response.status_code}")

        except Exception as e:
            self.logger.error(f"Error loading calendars: {e}", exc_info=True)

    def load_tasks(self):
        """Load tasks from backend"""
        self.logger.info("Loading tasks from backend...")
        try:
            # Get selected calendar IDs
            selected_indices = self.calendar_listbox.curselection()
            if not selected_indices:
                calendar_ids = None
            else:
                calendar_ids = []
                for idx in selected_indices:
                    calendar_ids.append(self.calendars[idx]['id'])

            self.logger.info(f"Selected calendar IDs: {calendar_ids}")
            
            # Prepare filter parameters
            params = {}
            if calendar_ids:
                params['calendar_ids'] = calendar_ids

            self.logger.info(f"Sending GET request to {self.backend_url}/tasks/tasks with params: {params}")
            response = requests.get(f"{self.backend_url}/tasks/tasks", params=params, timeout=10)
            self.logger.info(f"Tasks response status: {response.status_code}")
            self.logger.info(f"Tasks response: {response.text}")
            
            if response.status_code == 200:
                tasks = response.json()
                self.logger.info(f"Found {len(tasks)} tasks")

                # Clear existing tasks
                for item in self.task_tree.get_children():
                    self.task_tree.delete(item)

                # Store tasks for filtering
                self.tasks = tasks

                # Insert tasks into treeview
                for task in tasks:
                    self.task_tree.insert("", tk.END, values=(
                        task['summary'],
                        task['status'],
                        task['due'] or "",
                        task['calendar_name']
                    ))

                self.status_var.set(f"Loaded {len(tasks)} tasks")
                self.logger.info("Tasks loaded successfully")
            else:
                self.logger.error(f"Failed to load tasks: {response.status_code}")

        except Exception as e:
            self.logger.error(f"Error loading tasks: {e}", exc_info=True)

    def load_cached_tasks_on_startup(self):
        """Load cached tasks from backend"""
        try:
            # Try to get cached tasks from backend
            response = requests.get(f"{self.backend_url}/tasks/tasks")
            if response.status_code == 200:
                tasks = response.json()
                
                # Clear existing tasks
                for item in self.task_tree.get_children():
                    self.task_tree.delete(item)

                # Store tasks for filtering
                self.tasks = tasks

                # Insert tasks into treeview
                for task in tasks:
                    self.task_tree.insert("", tk.END, values=(
                        task['summary'],
                        task['status'],
                        task['due'] or "",
                        task['calendar_name']
                    ))

                self.status_var.set(f"Showing {len(tasks)} cached tasks - Connect to refresh")
            else:
                self.logger.debug("No cached tasks found")
                
        except Exception as e:
            self.logger.error(f"Error loading cached tasks: {e}", exc_info=True)

    def load_cached_calendars_on_startup(self):
        """Load cached calendars from backend"""
        try:
            response = requests.get(f"{self.backend_url}/tasks/calendars")
            if response.status_code == 200:
                calendars = response.json()
                
                # Clear existing calendars in listbox
                self.calendar_listbox.delete(0, tk.END)

                # Store calendar objects and populate listbox
                self.calendars = calendars
                for calendar in calendars:
                    self.calendar_listbox.insert(tk.END, calendar['name'])

                # Select all calendars by default
                for i in range(len(calendars)):
                    self.calendar_listbox.selection_set(i)

                self.status_var.set(f"Loaded {len(calendars)} calendars from cache - Connect to refresh")
            else:
                self.logger.debug("No cached calendars found")
                
        except Exception as e:
            self.logger.error(f"Error loading cached calendars: {e}", exc_info=True)

    def show_today_view(self):
        """Show today view - display only tasks due today or overdue"""
        try:
            self.logger.info("Switching to Today view")
            self.current_view = "today"
            
            response = requests.get(f"{self.backend_url}/tasks/tasks/today")
            if response.status_code == 200:
                tasks = response.json()
                self.logger.info(f"Today view: Found {len(tasks)} tasks")

                # Clear existing tasks
                for item in self.task_tree.get_children():
                    self.task_tree.delete(item)

                # Insert today's tasks into treeview
                for task in tasks:
                    self.task_tree.insert("", tk.END, values=(
                        task['summary'],
                        task['status'],
                        task['due'] or "",
                        task['calendar_name']
                    ))

                self.status_var.set(f"Today View: Showing {len(tasks)} tasks due today or overdue")
            else:
                self.logger.error(f"Failed to load today's tasks: {response.status_code}")

        except Exception as e:
            self.logger.error(f"Error showing today view: {e}", exc_info=True)

    def refresh_tasks(self):
        """Refresh the task list"""
        self.current_view = "all"  # Reset to full view
        self.load_tasks()
        self.status_var.set(f"Refreshed - Showing {len(self.tasks)} tasks")

    def apply_filter(self, *args):
        """Apply filter to task list"""
        filter_text = self.filter_var.get().lower()

        # Clear existing tasks in treeview
        for item in self.task_tree.get_children():
            self.task_tree.delete(item)

        # Insert filtered tasks
        for task in self.tasks:
            if (filter_text in task['summary'].lower() or
                filter_text in task['status'].lower() or
                filter_text in task['calendar_name'].lower() or
                filter_text in (task['due'] or "").lower()):
                self.task_tree.insert("", tk.END, values=(
                    task['summary'],
                    task['status'],
                    task['due'] or "",
                    task['calendar_name']
                ))

    def save_credentials(self):
        """Save credentials to a file"""
        self.credential_manager.save_credentials(
            self.url_var.get(),
            self.username_var.get(),
            self.password_var.get(),
            self.save_credentials_var.get()
        )

    def load_saved_credentials(self):
        """Load saved credentials from file"""
        url, username, password, has_saved_creds = self.credential_manager.load_saved_credentials()
        self.url_var.set(url)
        self.username_var.set(username)
        self.password_var.set(password)
        self.save_credentials_var.set(has_saved_creds)

    def auto_connect_if_credentials_saved(self):
        """Auto-connect if credentials are saved"""
        try:
            # Check if credentials are saved
            if os.path.exists('credentials.json'):
                with open('credentials.json', 'r') as f:
                    creds = json.load(f)
                    if creds.get('url') and creds.get('username') and creds.get('password'):
                        # Auto-connect after a short delay to allow UI to initialize
                        self.root.after(1000, self.connect_to_backend)
                        self.logger.info("Auto-connecting with saved credentials...")
        except Exception as e:
            self.logger.error(f"Error during auto-connect: {e}", exc_info=True)

    def start_auto_refresh(self):
        """Start the automatic refresh timer"""
        # Set refresh interval to 60 seconds (60000 ms)
        self.refresh_interval = 60000  # 60 seconds in milliseconds
        self.schedule_next_refresh()

    def schedule_next_refresh(self):
        """Schedule the next refresh"""
        # Cancel any existing refresh scheduled
        if hasattr(self, 'refresh_job_id') and self.refresh_job_id:
            self.root.after_cancel(self.refresh_job_id)

        # Schedule the next refresh
        self.refresh_job_id = self.root.after(self.refresh_interval, self.perform_auto_refresh)

    def perform_auto_refresh(self):
        """Perform the automatic refresh of tasks"""
        try:
            # Only refresh if we're connected (have calendars)
            if hasattr(self, 'calendars') and self.calendars:
                self.logger.info(f"Performing automatic refresh... (view: {self.current_view})")

                # Update status
                self.status_var.set("Auto-refreshing tasks...")

                # Reload tasks from backend based on current view
                if self.current_view == "today":
                    self.show_today_view()
                    self.logger.info("Auto-refresh: Today view refreshed")
                else:
                    self.load_tasks()
                    self.logger.info(f"Auto-refresh: Full list refreshed - {len(self.tasks)} tasks")

                # Schedule the next refresh
                self.schedule_next_refresh()
            else:
                # If not connected, just schedule the next refresh without performing it
                self.schedule_next_refresh()
        except Exception as e:
            self.logger.error(f"Error during auto-refresh: {e}", exc_info=True)
            self.status_var.set("Auto-refresh failed")
            # Still schedule the next refresh even if this one failed
            self.schedule_next_refresh()


def main():
    root = tk.Tk()
    app = TaskFrontendApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()