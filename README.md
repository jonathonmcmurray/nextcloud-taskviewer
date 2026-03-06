# Nextcloud Task Viewer

A cross-platform GUI application for viewing Nextcloud tasks via CalDAV.

## Features

- View tasks from multiple Nextcloud calendars
- Filter tasks by keywords
- Refresh task list
- Simple and intuitive interface
- Subtask hierarchy visualization (shows child tasks under parent tasks)
- Local caching with ETag-based updates (only fetches changed tasks)
- Due date field shows only due dates, not creation dates
- Remember connection details option

## Prerequisites

- Python 3.12+
- Nextcloud account with CalDAV enabled

## Installation

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

   Or using uv:
   ```bash
   uv sync
   ```

2. Start the backend:
   ```bash
   cd backend
   uv run uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
   ```

3. Start the frontend (in a new terminal):
   ```bash
   cd frontend
   uv run python main.py
   ```

## Usage

1. Enter your Nextcloud server URL (typically `https://your-domain.com/remote.php/dav/`)
2. Enter your username and password
3. Check "Save Credentials" if you want to remember your connection details
4. Click "Connect" to load your task calendars
5. Select which calendars to view tasks from
6. Use the filter box to search for specific tasks
7. Click "Refresh Tasks" to update the list
8. Subtasks will be shown indented under their parent tasks with an arrow symbol

## Security Note

Your credentials are stored in memory only and are not saved anywhere by default. If you check "Save Credentials", they are stored in a local file (credentials.json) in plaintext. Be cautious when using this feature on shared systems.

## Caching

The application uses local caching to improve performance:
- Tasks are cached locally after each refresh
- ETag-based comparison is used to only download updated tasks
- Application loads from cache first for faster startup
- Cache files (tasks_cache.pkl, etag_cache.json) are stored locally