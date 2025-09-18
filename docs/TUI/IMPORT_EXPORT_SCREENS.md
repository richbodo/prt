# Import/Export Screens Implementation

This document describes the implementation of Track C: Import/Export Screens for Phase 5.

## Overview

Two new TUI screens have been implemented to handle importing contacts from Google Takeout and exporting data in various formats:

1. **Import Screen** (`prt_src/tui/screens/import.py`) - Task 5.7
2. **Export Screen** (`prt_src/tui/screens/export.py`) - Task 5.8

## Import Screen (Task 5.7)

### Features
- **File Selection**: Text input field for Google Takeout zip file path with browse button
- **File Validation**: Real-time validation of zip files and Google Takeout format
- **Preview**: Shows contact count, image count, and sample contact names before import
- **Progress Tracking**: Visual progress bar with status messages during import
- **Error Handling**: Clear error messages for invalid files or import failures
- **Results Summary**: Displays import statistics (contacts imported, images, duplicates removed)

### Integration
- Uses existing `google_takeout.py` module for parsing
- Integrates with DataService to insert contacts into database
- Follows BaseScreen pattern with proper lifecycle hooks

### Navigation
- Accessible from home screen via `[i] Import` key
- Proper ESC handling (prevents exit during import)
- Navigation to contacts screen or home after completion

## Export Screen (Task 5.8)

### Features
- **Format Selection**: JSON, CSV, or HTML export formats
- **Scope Options**:
  - All contacts
  - Current search results (if available)
  - Contacts filtered by specific tag
- **Export Options**:
  - Include profile images
  - Include relationship data
  - Include notes and tags
  - Generate directory visualization (HTML format only)
- **Output Configuration**: Customizable output path with default timestamps
- **Progress Tracking**: Visual progress with detailed status messages
- **Results Summary**: Shows export location and files created

### Integration
- Uses existing `api.py` export methods
- Integrates with `make_directory.py` for HTML directory visualization
- Follows BaseScreen pattern with proper service injection

### Navigation
- Accessible from home screen via `[e] Export` key
- Proper ESC handling (prevents exit during export)
- Option to open export folder or return to home

## Technical Implementation

### Screen Architecture
Both screens follow the established BaseScreen pattern:
- Service injection (DataService, NavigationService, NotificationService)
- Proper lifecycle hooks (on_mount, on_show, on_hide)
- ESC intent handling with custom behavior during operations
- Reactive UI updates based on state changes

### Error Handling
- Graceful handling of file system errors
- Clear user feedback for validation failures
- Recovery options for failed operations
- Logging integration for debugging

### Testing
Comprehensive test coverage including:
- Unit tests for both screens (`tests/test_import_export_screens.py`)
- Integration tests (`tests/test_import_export_integration.py`)
- Mocking of file operations and external dependencies
- Validation of UI state changes and service interactions

## Navigation Integration

### Home Screen Updates
- Added import/export options to navigation menu
- Updated key hints in footer
- Added menu action handlers for both screens

### Navigation Menu Updates
- Added import option: `[i] Import - Import contacts from Google Takeout` 📥
- Added export option: `[e] Export - Export data and create directories` 📤

## File Structure

```
prt_src/tui/screens/
├── import.py           # Import screen implementation
├── export.py           # Export screen implementation
└── __init__.py         # Updated with screen registrations

prt_src/tui/widgets/
└── navigation_menu.py  # Updated with import/export menu items

tests/
├── test_import_export_screens.py      # Unit tests
└── test_import_export_integration.py  # Integration tests

docs/
└── IMPORT_EXPORT_SCREENS.md           # This documentation
```

## Usage Examples

### Import Workflow
1. Navigate to home screen
2. Press `i` or select "Import" from menu
3. Enter path to Google Takeout zip file
4. Review preview information
5. Click "Import Contacts" to begin
6. View results summary
7. Navigate to contacts or home

### Export Workflow
1. Navigate to home screen
2. Press `e` or select "Export" from menu
3. Choose export format (JSON, CSV, HTML)
4. Select export scope (all, search results, tag filter)
5. Configure export options
6. Set output path
7. Click "Export Data" to begin
8. View results and open export folder

## Dependencies

### Import Screen
- `google_takeout.py` - Google Takeout parsing
- `DataService` - Database operations
- `pathlib.Path` - File path handling
- `asyncio` - Asynchronous operations

### Export Screen
- `api.py` - Database export methods
- `make_directory.py` - Directory visualization
- `DataService` - Data retrieval
- Various format handlers (JSON, CSV, HTML)

## Future Enhancements

### Import Screen
- Support for additional contact formats (vCard, CSV)
- Batch processing for large files
- Duplicate detection strategies
- Contact merge/update options

### Export Screen
- Additional export formats (vCard, XML)
- Advanced filtering options
- Scheduled exports
- Cloud storage integration
- Email export capabilities

## Error Scenarios

### Import Screen
- Invalid zip files → Clear error message with file format requirements
- Corrupted Google Takeout data → Partial import with error report
- Database insertion failures → Rollback with detailed error information
- Insufficient disk space → Early detection and user notification

### Export Screen
- Invalid output paths → Path validation with suggestions
- Missing permissions → Clear permission error messages
- Large dataset exports → Memory management and chunking
- Network issues (future cloud exports) → Retry mechanisms

## Performance Considerations

### Import Screen
- Streaming zip file processing for large archives
- Batched database insertions to reduce transaction overhead
- Progress reporting for user feedback during long operations
- Memory-efficient image handling

### Export Screen
- Pagination for large contact datasets
- Streaming JSON/CSV writing for large exports
- Asynchronous file operations
- Progress reporting for directory generation

This implementation provides a solid foundation for contact import/export functionality while maintaining consistency with the existing PRT TUI architecture and patterns.