"""
Module for UI components and layout management.
"""
import tkinter as tk
from tkinter import messagebox, scrolledtext
import tkinter.font as tkFont
import ttkbootstrap as ttk
import logging


class UIComponents:
    """Handles all UI components and layout for the TaskViewer application."""
    
    def __init__(self, root, app_instance):
        self.root = root
        self.app = app_instance  # Reference to main app for callbacks
        self.logger = logging.getLogger(__name__)
        
    def setup_main_window(self):
        """Setup the main window properties"""
        self.root.title("Nextcloud Task Viewer")
        self.root.geometry("800x600")
        
    def setup_variables(self):
        """Setup Tkinter variables for form elements"""
        # Store variables in the app instance
        self.app.url_var = tk.StringVar()
        self.app.username_var = tk.StringVar()
        self.app.password_var = tk.StringVar()
        self.app.save_credentials_var = tk.BooleanVar()
        self.app.filter_var = tk.StringVar()
        self.app.status_var = tk.StringVar(value=" disconnected - waiting for connection ")
        
        # Also store them in UIComponents for use in UI setup
        self.url_var = self.app.url_var
        self.username_var = self.app.username_var
        self.password_var = self.app.password_var
        self.save_credentials_var = self.app.save_credentials_var
        self.filter_var = self.app.filter_var
        self.status_var = self.app.status_var
        
    def setup_styles(self):
        """Setup UI styles and themes"""
        # Configure style for modern look
        self.style = ttk.Style(theme="superhero")
        # # Use a modern theme if available, otherwise default
        # try:
        #     self.style.theme_use('clam')
        # except tk.TclError:
        #     pass  # Use default theme if clam is not available
            
    def setup_ui(self):
        """Setup the complete UI layout"""
        self.setup_styles()
        
        # Main frame
        main_frame = ttk.Frame(self.root)
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(3, weight=1)

        normal_font = tkFont.Font(family="Helvetica", size=10, weight=tkFont.NORMAL)

        # Title label
        title_label = ttk.Label(main_frame, text="☁️ Nextcloud Task Viewer", font=normal_font)
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 10), sticky=tk.W)

        # Connection settings frame with modern styling
        conn_frame = ttk.LabelFrame(main_frame, text="🔗 Connection Settings", font=normal_font)
        conn_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        conn_frame.columnconfigure(1, weight=1)

        # URL entry with better labeling
        ttk.Label(conn_frame, text="🌐 Nextcloud Server URL:", font=normal_font).grid(
            row=0, column=0, sticky=tk.W, padx=(0, 5), pady=(0, 5))
        self.url_entry = ttk.Entry(conn_frame, textvariable=self.url_var, width=50, font=normal_font)
        self.url_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(0, 5), pady=(0, 5))

        # Username entry with better labeling
        ttk.Label(conn_frame, text="👤 Username:", font=normal_font).grid(
            row=1, column=0, sticky=tk.W, padx=(0, 5), pady=(0, 5))
        self.username_entry = ttk.Entry(conn_frame, textvariable=self.username_var, width=30, font=normal_font)
        self.username_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), padx=(0, 5), pady=(0, 5))

        # Password entry with better labeling
        ttk.Label(conn_frame, text="🔒 Password:", font=normal_font).grid(
            row=2, column=0, sticky=tk.W, padx=(0, 5), pady=(0, 5))
        self.password_entry = ttk.Entry(conn_frame, textvariable=self.password_var, show="•", width=30, font=normal_font)
        self.password_entry.grid(row=2, column=1, sticky=(tk.W, tk.E), padx=(0, 5), pady=(0, 5))

        # Save credentials checkbox with better positioning
        self.save_creds_check = ttk.Checkbutton(conn_frame, text="💾 Remember Credentials",
                                          variable=self.save_credentials_var)
        self.save_creds_check.grid(row=3, column=0, columnspan=2, sticky=tk.W, pady=(5, 0))

        # Buttons frame with better spacing
        btn_frame = ttk.Frame(main_frame)
        btn_frame.grid(row=2, column=0, columnspan=2, pady=(0, 10))

        # Connect button with icon
        connect_btn = ttk.Button(btn_frame, text="🔌 Connect", command=self.app.connect_to_backend)
        connect_btn.pack(side=tk.LEFT, padx=(0, 10))

        # Refresh button with icon
        refresh_btn = ttk.Button(btn_frame, text="🔄 Refresh Tasks", command=self.app.load_tasks)
        refresh_btn.pack(side=tk.LEFT, padx=(0, 10))

        # Today view button
        today_btn = ttk.Button(btn_frame, text="📅 Today", command=self.app.show_today_view)
        today_btn.pack(side=tk.LEFT, padx=(0, 10))

        # Auto-refresh indicator
        self.auto_refresh_label = ttk.Label(btn_frame, text="⏱ Auto-refresh: Active",
                                           foreground='green', font=normal_font)
        self.auto_refresh_label.pack(side=tk.LEFT, padx=(5, 0))

        # Paned window to split calendar and task areas
        paned_window = ttk.Panedwindow(main_frame, orient=tk.HORIZONTAL)
        paned_window.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        main_frame.rowconfigure(3, weight=1)

        # Calendar selection frame
        calendar_frame = ttk.LabelFrame(paned_window, text="📅 Task Calendars", font=normal_font)
        calendar_frame.columnconfigure(0, weight=1)
        calendar_frame.rowconfigure(0, weight=1)

        # Calendar listbox with better styling
        self.calendar_listbox = tk.Listbox(calendar_frame, selectmode=tk.EXTENDED, height=12, font=normal_font)
        self.calendar_listbox.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 5))
        calendar_scrollbar = ttk.Scrollbar(calendar_frame, orient=tk.VERTICAL, command=self.calendar_listbox.yview)
        calendar_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        self.calendar_listbox.configure(yscrollcommand=calendar_scrollbar.set)

        # Add the calendar frame to the paned window
        paned_window.add(calendar_frame, weight=1)

        # Task display frame
        task_frame = ttk.LabelFrame(paned_window, text="📋 Task List", font=normal_font)
        task_frame.columnconfigure(0, weight=1)
        task_frame.rowconfigure(1, weight=1)

        # Task filter with better styling
        filter_frame = ttk.Frame(task_frame)
        filter_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 8))
        filter_frame.columnconfigure(1, weight=1)

        ttk.Label(filter_frame, text="🔍 Search Tasks:", font=normal_font).grid(
            row=0, column=0, sticky=tk.W)
        self.filter_var.trace_add("write", self.app.apply_filter)
        filter_entry = ttk.Entry(filter_frame, textvariable=self.filter_var, width=30)
        filter_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(8, 0))

        # Task treeview with improved headers and styling
        self.task_tree = ttk.Treeview(task_frame, columns=("summary", "status", "due", "calendar"), show="headings", height=15)
        self.task_tree.heading("summary", text="Task Summary", anchor=tk.W)
        self.task_tree.heading("status", text="Status", anchor=tk.CENTER)
        self.task_tree.heading("due", text="Due Date", anchor=tk.CENTER)
        self.task_tree.heading("calendar", text="Calendar", anchor=tk.W)

        self.task_tree.column("summary", width=350, anchor=tk.W)
        self.task_tree.column("status", width=100, anchor=tk.CENTER)
        self.task_tree.column("due", width=120, anchor=tk.CENTER)
        self.task_tree.column("calendar", width=150, anchor=tk.W)

        # Scrollbars for task treeview
        task_scrollbar_y = ttk.Scrollbar(task_frame, orient=tk.VERTICAL, command=self.task_tree.yview)
        task_scrollbar_x = ttk.Scrollbar(task_frame, orient=tk.HORIZONTAL, command=self.task_tree.xview)

        self.task_tree.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        task_scrollbar_y.grid(row=1, column=1, sticky=(tk.N, tk.S))
        task_scrollbar_x.grid(row=2, column=0, sticky=(tk.W, tk.E))

        self.task_tree.configure(yscrollcommand=task_scrollbar_y.set, xscrollcommand=task_scrollbar_x.set)

        # Add the task frame to the paned window
        paned_window.add(task_frame, weight=3)

        # Status bar with better styling
        self.status_bar = ttk.Label(main_frame, textvariable=self.status_var, relief=tk.FLAT,
                              anchor=tk.W, foreground='#444444', font=normal_font)
        self.status_bar.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(5, 0))
        
        # Store references to UI elements that need to be accessed by the main app
        # (Note: variables are already set in setup_variables method)
        self.app.calendar_listbox = self.calendar_listbox
        self.app.task_tree = self.task_tree