# Nextcloud Task Backend

A REST API backend service for synchronizing and managing Nextcloud tasks with local caching.

## Features

- **Nextcloud Integration**: Connect to Nextcloud server and synchronize tasks
- **Local Caching**: SQLite database for offline access and faster queries
- **Task Management**: Full CRUD operations for tasks
- **Calendar Support**: Multi-calendar support
- **Synchronization**: Efficient sync with ETag-based change detection
- **Search & Filtering**: Advanced search and filtering capabilities
- **Authentication**: Secure credential management

## Architecture

The backend follows a clean architecture with:

- **API Layer**: FastAPI endpoints
- **Service Layer**: Business logic and task operations
- **Data Layer**: SQLite database with aiosqlite
- **Models**: Pydantic data models

## API Endpoints

### Authentication
- `POST /auth/login` - Login to Nextcloud
- `POST /auth/validate` - Validate connection
- `POST /auth/save-config` - Save configuration
- `GET /auth/saved-config` - Retrieve saved configuration

### Tasks
- `GET /tasks` - Get tasks with optional filters
- `GET /tasks/{id}` - Get specific task
- `GET /tasks/today` - Get tasks due today or overdue
- `GET /search?q={query}` - Search tasks
- `POST /tasks/sync` - Synchronize with Nextcloud

### Sync
- `POST /sync/sync-now` - Force immediate sync
- `GET /sync/status` - Get sync status
- `GET /sync/stats` - Get sync statistics
- `POST /sync/clear-cache` - Clear local cache

## Quick Start

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
   uv run uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
   ```

3. The API will be available at `http://localhost:8000`

## Configuration

The backend uses environment variables for configuration:

- `DATABASE_URL`: SQLite database path (default: nextcloud_tasks.db)
- `LOG_LEVEL`: Logging level (default: INFO)

## Database Schema

The backend uses SQLite with the following tables:

- `tasks`: Stores task information with metadata
- `calendars`: Stores calendar information
- `sync_state`: Tracks synchronization state

## Security

- Credentials are not stored in plain text (implementation needed)
- API endpoints are protected where appropriate
- Input validation using Pydantic models

## Development

To run in development mode:

```bash
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

The API documentation will be available at `http://localhost:8000/docs`