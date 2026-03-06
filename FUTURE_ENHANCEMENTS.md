# Future Enhancements for Nextcloud Task Viewer

This document outlines planned enhancements for the Nextcloud Task Viewer application.

## 1. Subtask Support
- [ ] Properly identify and display subtasks in a hierarchical tree structure
- [ ] Allow expanding/collapsing parent tasks to show/hide subtasks
- [ ] Implement visual indicators for subtask relationships
- [ ] Support for creating new subtasks from the UI

## 2. Font Improvements
- [ ] Investigate font rendering issues on different platforms
- [ ] Implement font fallback mechanisms for better cross-platform compatibility
- [ ] Add font size adjustment options for accessibility
- [ ] Ensure consistent emoji rendering across all platforms

## 3. "Today" View
- [ ] Add a dedicated view for tasks due today
- [ ] Highlight overdue tasks separately
- [ ] Show tasks without due dates in a separate section
- [ ] Add quick filters for "Today", "Overdue", "Upcoming", "No Due Date"

## 4. Recurring Task Detection
- [ ] Detect recurring tasks based on RRULE property in iCal data
- [ ] Mark recurring tasks with a special icon or indicator
- [ ] Show next occurrence date for recurring tasks
- [ ] Add option to view all instances of recurring tasks

## 5. Task Completion Support
- [ ] Add ability to mark tasks as complete/incomplete
- [ ] For recurring tasks, implement proper rescheduling of next instance
- [ ] Update task status on the server
- [ ] Add confirmation dialogs for completing tasks

## 6. UI Improvements
- [ ] Add dark/light mode toggle
- [ ] Implement keyboard shortcuts for common actions
- [ ] Add drag-and-drop support for reordering tasks
- [ ] Improve responsive design for different window sizes
- [ ] Add task statistics dashboard
- [ ] Implement better visual hierarchy with color coding
- [ ] Add progress bars for tasks with subtasks
- [ ] Add ability to customize column visibility/order

## 7. Additional Features
- [ ] Add task creation functionality
- [ ] Add task editing capabilities
- [ ] Implement task priorities with visual indicators
- [ ] Add task categories/tags support
- [ ] Export functionality (CSV, JSON, etc.)
- [ ] Add notifications for upcoming due tasks
- [ ] Add ability to assign tasks to other users (if supported by Nextcloud)

## 8. Performance & Reliability
- [ ] Implement better error handling and user feedback
- [ ] Add retry mechanisms for failed connections
- [ ] Optimize caching for large numbers of tasks
- [ ] Add offline mode with synchronization when online
- [ ] Implement incremental sync to reduce data transfer

## 9. Advanced Filtering & Sorting
- [ ] Add advanced filtering options (by status, priority, date range, etc.)
- [ ] Implement custom sorting options
- [ ] Save and recall filter presets
- [ ] Add search functionality across all task properties

## 10. Integration & Extensibility
- [ ] Add plugin architecture for extending functionality
- [ ] Implement webhook support for real-time updates
- [ ] Add integration with calendar views
- [ ] Support for importing tasks from other formats