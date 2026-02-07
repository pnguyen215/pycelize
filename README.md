# Pycelize

A professional Flask application for Excel/CSV processing with comprehensive API support and Chat Workflows for sequential file processing.

![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)
![Flask](https://img.shields.io/badge/Flask-2.3+-green.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

## 📋 Table of Contents

1. [Overview](#1-overview)
2. [Architecture](#2-architecture)
3. [Workflow Lifecycle](#3-workflow-lifecycle)
4. [Dump and Restore System](#4-dump-and-restore-system)
5. [File Storage Structure](#5-file-storage-structure)
6. [Partition System](#6-partition-system)
7. [REST API Reference](#7-rest-api-reference)
8. [WebSocket Events](#8-websocket-events)
9. [Download System](#9-download-system)
10. [Error Handling](#10-error-handling)
11. [Testing Guide](#11-testing-guide)
12. [Frontend Integration Guide](#12-frontend-integration-guide)
13. [Deployment Notes](#13-deployment-notes)
14. [Known Issues and Fixes](#14-known-issues-and-fixes)
15. [Troubleshooting Guide](#15-troubleshooting-guide)

---

## 1. Overview

### What is Pycelize?

Pycelize is a production-ready Flask application designed for processing Excel and CSV files with a modern chat-based workflow interface. It provides:

- **RESTful APIs** for common data operations
- **Chat Workflows** for sequential file processing
- **Real-time WebSocket updates** for progress tracking
- **Dump & Restore** for conversation backup
- **Partition-based storage** for scalability
- **SQLite integration** for fast metadata queries

### Core Features

#### File Processing
- Column Extraction with deduplication
- CSV to Excel Conversion
- Data Normalization (uppercase, trim, phone format, etc.)
- Column Mapping and transformation
- SQL Generation with auto-increment support
- JSON Generation with templates
- Excel-to-Excel Binding
- Advanced Search and Filter

#### Chat Workflows
- Chat-based sequential processing
- Real-time progress via WebSocket
- Conversation management (create, list, retrieve, delete)
- File upload and download
- Workflow step execution with chaining
- Auto-generated participant names
- Dump & Restore for backup
- Partition-based file organization

---

## 2. Architecture

### System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Client Applications                      │
│  (Web Browser, Mobile App, API Clients)                    │
└────────────┬─────────────────────────────┬─────────────────┘
             │                              │
             │ HTTP/REST                    │ WebSocket
             │                              │
┌────────────▼──────────────────────────────▼────────────────┐
│                    Flask Application                         │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              API Routes Layer                         │  │
│  │  - Health   - Excel    - CSV    - Chat Workflows     │  │
│  └─────────────────────┬────────────────────────────────┘  │
│                        │                                     │
│  ┌─────────────────────▼──────────────────────────────┐   │
│  │           Service Layer                             │   │
│  │  - Excel Service  - CSV Service                     │   │
│  │  - Normalization  - SQL Generation                  │   │
│  │  - JSON Generation - Search Service                 │   │
│  └─────────────────────┬──────────────────────────────┘   │
│                        │                                     │
│  ┌─────────────────────▼──────────────────────────────┐   │
│  │       Chat Workflows Components                      │   │
│  │  ┌──────────────┐  ┌──────────────┐                │   │
│  │  │  Repository  │  │   Executor   │                 │   │
│  │  └──────┬───────┘  └──────┬───────┘                │   │
│  │         │                  │                         │   │
│  │  ┌──────▼───────┐  ┌──────▼───────┐                │   │
│  │  │   Database   │  │   Storage    │                 │   │
│  │  │  (SQLite)    │  │  (Files)     │                 │   │
│  │  └──────────────┘  └──────────────┘                 │   │
│  └──────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────┘
             │                              │
             │                              │
┌────────────▼──────────────┐  ┌───────────▼─────────────────┐
│   SQLite Database         │  │   File Storage               │
│   - Conversations         │  │   - Partition Structure      │
│   - Messages              │  │   - Uploaded Files           │
│   - Workflow Steps        │  │   - Output Files             │
│   - File Metadata         │  │   - Dumps                    │
└───────────────────────────┘  └──────────────────────────────┘
```

### Design Patterns

1. **Repository Pattern**: Separates data access logic from business logic
2. **Builder Pattern**: Constructs complex response objects
3. **Factory Pattern**: Creates service instances
4. **Strategy Pattern**: Implements different normalization strategies
5. **Chain of Responsibility**: Handles workflow step execution

### Technology Stack

- **Backend**: Python 3.9+, Flask 2.3+
- **Database**: SQLite (for metadata)
- **Storage**: File system (partitioned)
- **WebSocket**: websockets library
- **Data Processing**: pandas, openpyxl
- **Testing**: pytest

---

## 3. Workflow Lifecycle

### Workflow States

A conversation progresses through the following states:

```
created → processing → completed
    ↓          ↓           ↓
    └─────→ failed ←───────┘
```

### Lifecycle Steps

1. **Create Conversation**
   - Generate unique `chat_id`
   - Assign participant name
   - Create partition directory
   - Initialize in SQLite database
   - Status: `created`

2. **Upload Files**
   - Save files to `uploads/` folder
   - Record file paths in database
   - Generate download URLs
   - Status remains: `created`

3. **Execute Workflow**
   - Parse workflow steps
   - Execute sequentially with input/output chaining
   - Stream progress via WebSocket
   - Save outputs to `outputs/` folder
   - Status: `processing` → `completed` or `failed`

4. **Download Results**
   - Access files via download URLs
   - Both uploaded and output files available
   - Partition structure preserved

5. **Dump Conversation (Optional)**
   - Create tar.gz archive
   - Include all files and metadata
   - Generate download link
   - Store in dumps directory

6. **Restore Conversation (Optional)**
   - Extract from tar.gz archive
   - Restore to correct partition path
   - Recreate database entries
   - Preserve all metadata

7. **Delete Conversation (Optional)**
   - Remove all files from disk
   - Delete database entries
   - Cascade delete related data

---

## 4. Dump and Restore System

### Dump Process

**Purpose**: Create a complete backup of a conversation including all files and metadata.

**Process**:
1. Retrieve conversation from database
2. Create tar.gz archive of conversation directory
3. Include partition structure in archive
4. Save metadata as JSON alongside archive
5. Return download URL

**API Endpoint**:
```bash
POST /api/v1/chat/workflows/{chat_id}/dump
```

**Response**:
```json
{
  "data": {
    "dump_file": "chat-id_20260207_141939.tar.gz",
    "download_url": "http://localhost:5050/api/v1/chat/downloads/chat-id_20260207_141939.tar.gz"
  },
  "message": "Conversation dumped successfully"
}
```

**Archive Structure**:
```
chat-id_timestamp.tar.gz
└── {chat_id}/
    ├── uploads/
    │   └── file1.xlsx
    ├── outputs/
    │   └── result1.xlsx
    └── metadata.json
```

### Restore Process

**Purpose**: Restore a conversation from a backup dump file.

**Process**:
1. Upload dump file via multipart form
2. Extract to temporary directory
3. Read `metadata.json` to get `partition_key`
4. Move files to correct partition path: `{base_path}/{partition_key}/{chat_id}`
5. Recreate database entries
6. Return restored conversation details

**API Endpoint**:
```bash
POST /api/v1/chat/workflows/restore
Content-Type: multipart/form-data

dump_file: @path/to/dump.tar.gz
```

**Response**:
```json
{
  "data": {
    "chat_id": "...",
    "partition_key": "2026/02",
    "status": "completed",
    "uploaded_files": [...],
    "output_files": [...]
  },
  "message": "Conversation restored successfully"
}
```

### Important Notes

✅ **Recent Fix**: Restore now correctly places files in partitioned directories
- Old behavior: Files extracted to `./automation/workflows/{chat_id}` (flat)
- New behavior: Files extracted to `./automation/workflows/{partition_key}/{chat_id}` (partitioned)

✅ **Recent Fix**: Dump file paths now correctly resolved
- Uses `os.path.abspath()` for consistent path resolution
- Downloads work correctly

---

## 5. File Storage Structure

### Directory Layout

```
automation/
├── workflows/              # Conversation files (partitioned)
│   └── {partition_key}/    # e.g., 2026/02/
│       └── {chat_id}/
│           ├── uploads/    # Uploaded files
│           ├── outputs/    # Workflow outputs
│           └── metadata.json
├── dumps/                  # Backup archives
│   └── {chat_id}_{timestamp}.tar.gz
└── sqlite/                 # Database
    ├── chat.db
    └── snapshots/          # DB backups
        └── chat_backup_{timestamp}.db
```

### File Types

#### Uploaded Files
- Location: `{base_path}/{partition_key}/{chat_id}/uploads/`
- Naming: Original filename preserved
- Purpose: Input files for workflow processing

#### Output Files
- Location: `{base_path}/{partition_key}/{chat_id}/outputs/`
- Naming: `{original}_{operation}_{timestamp}.{ext}`
- Purpose: Results from workflow step execution

#### Dump Files
- Location: `{base_path}/dumps/`
- Naming: `{chat_id}_{timestamp}.tar.gz`
- Purpose: Complete conversation backup

### File Management

- **Upload**: Files saved to uploads folder, recorded in database
- **Processing**: Outputs saved to outputs folder, recorded in database
- **Download**: Files accessible via absolute URLs
- **Cleanup**: Files deleted on conversation deletion (cascade)

---

## 6. Partition System

### Purpose

Partitioning organizes conversations into hierarchical directories for:
- **Performance**: Faster file system operations
- **Scalability**: Handle millions of conversations
- **Organization**: Logical grouping by time or hash
- **Backup**: Easier partial backups

### Partition Strategies

#### 1. Time-Based (Default)

Partitions by year and month:
```
automation/workflows/
├── 2026/
│   ├── 01/
│   │   ├── chat-id-1/
│   │   └── chat-id-2/
│   └── 02/
│       └── chat-id-3/
└── 2027/
    └── 01/
        └── chat-id-4/
```

**Format**: `YYYY/MM`  
**Best for**: Time-series analysis, retention policies

#### 2. Hash-Based

Partitions by chat_id hash:
```
automation/workflows/
├── ab/
│   ├── cd/
│   │   └── abcd1234-5678-90ab-cdef-123456789012/
│   └── ef/
│       └── abef5678-1234-56cd-ef90-abcdef123456/
└── 12/
    └── 34/
        └── 12345678-abcd-ef12-3456-789012345678/
```

**Format**: `{first_2_chars}/{next_2_chars}`  
**Best for**: Even distribution, high volume

### Configuration

```yaml
chat_workflows:
  partition:
    enabled: true
    strategy: "time-based"  # or "hash-based"
```

### Partition Key Generation

```python
# Time-based
partition_key = created_at.strftime("%Y/%m")  # "2026/02"

# Hash-based
partition_key = f"{chat_id[:2]}/{chat_id[2:4]}"  # "ab/cd"
```

---

## 7. REST API Reference

### Base URL
```
http://localhost:5050/api/v1
```

### Chat Workflows Endpoints

#### 1. Create Conversation
```bash
POST /chat/workflows
```

**Response**:
```json
{
  "data": {
    "chat_id": "uuid",
    "participant_name": "BlueWhale-4821",
    "status": "created",
    "partition_key": "2026/02",
    "created_at": "2026-02-06T18:11:05.349996",
    "uploaded_files": [],
    "output_files": []
  }
}
```

#### 2. List Conversations
```bash
GET /chat/workflows?status=created&limit=100&offset=0
```

**Query Parameters**:
- `status`: Filter by status (created, processing, completed, failed)
- `limit`: Results per page (default: 100)
- `offset`: Pagination offset (default: 0)

#### 3. Get Conversation
```bash
GET /chat/workflows/{chat_id}
```

#### 4. Upload File
```bash
POST /chat/workflows/{chat_id}/upload
Content-Type: multipart/form-data

file: @path/to/file.xlsx
```

**Response**:
```json
{
  "data": {
    "filename": "data.xlsx",
    "file_path": "./automation/workflows/2026/02/{chat_id}/uploads/data.xlsx",
    "download_url": "http://localhost:5050/api/v1/chat/workflows/{chat_id}/files/data.xlsx"
  }
}
```

✅ **Recent Fix**: Download URLs are now absolute and clickable

#### 5. Execute Workflow
```bash
POST /chat/workflows/{chat_id}/execute
Content-Type: application/json

{
  "steps": [
    {
      "operation": "excel/extract-columns-to-file",
      "arguments": {
        "columns": ["customer_id", "amount"],
        "remove_duplicates": true
      }
    }
  ]
}
```

**Response**:
```json
{
  "data": {
    "results": [
      {
        "output_file_path": "...",
        "download_url": "http://localhost:5050/api/v1/chat/workflows/{chat_id}/files/output.xlsx"
      }
    ],
    "output_files": [
      {
        "file_path": "...",
        "download_url": "http://localhost:5050/api/v1/chat/workflows/{chat_id}/files/output.xlsx"
      }
    ]
  }
}
```

✅ **Recent Fix**: Each output file includes download_url

#### 6. Delete Conversation
```bash
DELETE /chat/workflows/{chat_id}
```

#### 7. Dump Conversation
```bash
POST /chat/workflows/{chat_id}/dump
```

✅ **Recent Fix**: Dump files now created correctly and downloadable

#### 8. Restore Conversation
```bash
POST /chat/workflows/restore
Content-Type: multipart/form-data

dump_file: @path/to/dump.tar.gz
```

✅ **Recent Fix**: Files now restored to correct partition paths

#### 9. Download Workflow File
```bash
GET /chat/workflows/{chat_id}/files/{filename}
```

✅ **New Endpoint**: Download uploaded or output files

#### 10. Download Dump File
```bash
GET /chat/downloads/{filename}
```

#### 11. Backup SQLite Database
```bash
POST /chat/sqlite/backup
```

---

## 8. WebSocket Events

### Connection

```javascript
const ws = new WebSocket('ws://127.0.0.1:5051/chat/{chat_id}');
```

### Message Types

#### 1. Connected (Welcome)
```json
{
  "type": "connected",
  "chat_id": "...",
  "message": "Connected to chat workflow"
}
```

#### 2. Workflow Started
```json
{
  "type": "workflow_started",
  "chat_id": "...",
  "total_steps": 3,
  "message": "Workflow execution started"
}
```

#### 3. Progress Update
```json
{
  "type": "progress",
  "chat_id": "...",
  "operation": "excel/extract-columns-to-file",
  "progress": 45,
  "status": "running",
  "message": "Processing column 'customer_id'"
}
```

#### 4. Workflow Completed
```json
{
  "type": "workflow_completed",
  "chat_id": "...",
  "total_steps": 3,
  "output_files_count": 2,
  "message": "Workflow execution completed successfully"
}
```

#### 5. Workflow Failed
```json
{
  "type": "workflow_failed",
  "chat_id": "...",
  "error": "Operation failed: ...",
  "message": "Workflow execution failed"
}
```

### Client Messages

#### Ping/Pong (Keepalive)
```json
// Send
{"type": "ping"}

// Receive
{"type": "pong"}
```

#### Change Subscription
```json
{"type": "subscribe", "chat_id": "new-chat-id"}
```

✅ **Recent Fix**: WebSocket auto-starts with Flask, thread-safe bridge implemented

---

## 9. Download System

### Download URLs

All file downloads use **absolute URLs** with scheme and host:

```
http://localhost:5050/api/v1/chat/workflows/{chat_id}/files/{filename}
```

✅ **Benefits**:
- Ready for use in `<a>` tags
- Works with `window.open()`
- No URL construction needed
- Environment-agnostic

### Download Endpoints

#### 1. Workflow Files
```
GET /api/v1/chat/workflows/{chat_id}/files/{filename}
```
- Handles both uploaded and output files
- Searches in uploads/ and outputs/ folders
- Respects partition structure
- Security: Path validation to prevent traversal

#### 2. Dump Files
```
GET /api/v1/chat/downloads/{filename}
```
- Downloads backup archives
- Security: Secure filename handling

### MIME Types

Automatically detected based on extension:
- `.xlsx`: `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`
- `.csv`: `text/csv`
- `.json`: `application/json`
- `.txt`, `.sql`: `text/plain`
- `.tar.gz`: `application/gzip`

---

## 10. Error Handling

### Error Response Format

```json
{
  "data": {
    "error_type": "ValidationError",
    "details": "Additional context"
  },
  "message": "Human-readable error message",
  "status_code": 422,
  "meta": {
    "api_version": "v0.0.1",
    "request_id": "...",
    "requested_time": "..."
  }
}
```

### HTTP Status Codes

- `200` OK - Success
- `201` Created - Resource created
- `400` Bad Request - Invalid input
- `404` Not Found - Resource not found
- `422` Unprocessable Entity - Validation error
- `500` Internal Server Error - Server error

### Common Errors

#### File Not Found
```json
{
  "message": "File not found",
  "status_code": 404
}
```

#### Validation Error
```json
{
  "message": "No uploaded file found for processing",
  "status_code": 422
}
```

#### Server Error
```json
{
  "message": "Workflow execution failed: ...",
  "status_code": 500
}
```

---

## 11. Testing Guide

### Test Organization

```
tests/
├── unit/                          # Unit tests
├── integration/                   # Integration tests
│   └── chat_workflows/           # Chat workflow tests
│       ├── test_chat_workflows.py
│       ├── test_chat_fixes.py
│       ├── test_download_fix.py
│       └── test_download_urls.py
└── data/                         # Test data files
```

✅ **Recent Change**: Tests moved to proper directory structure

### Running Tests

```bash
# All tests
pytest

# Specific test file
pytest tests/integration/chat_workflows/test_chat_workflows.py

# With coverage
pytest --cov=app tests/

# Verbose output
pytest -v
```

### Test Categories

#### Unit Tests
- Service layer tests
- Utility function tests
- Model tests

#### Integration Tests
- API endpoint tests
- Chat workflow tests
- Database tests

---

## 12. Frontend Integration Guide

### Quick Start

#### 1. Create Conversation
```javascript
const response = await fetch('http://localhost:5050/api/v1/chat/workflows', {
  method: 'POST'
});
const { data } = await response.json();
const chatId = data.chat_id;
```

#### 2. Connect to WebSocket
```javascript
const ws = new WebSocket(`ws://127.0.0.1:5051/chat/${chatId}`);

ws.onmessage = (event) => {
  const message = JSON.parse(event.data);
  
  switch(message.type) {
    case 'workflow_started':
      console.log('Workflow started');
      break;
    case 'progress':
      updateProgressBar(message.progress);
      break;
    case 'workflow_completed':
      console.log('Workflow completed');
      break;
    case 'workflow_failed':
      console.error('Workflow failed:', message.error);
      break;
  }
};
```

#### 3. Upload File
```javascript
const formData = new FormData();
formData.append('file', file);

const response = await fetch(
  `http://localhost:5050/api/v1/chat/workflows/${chatId}/upload`,
  {
    method: 'POST',
    body: formData
  }
);
const { data } = await response.json();
// Use data.download_url for downloads
```

#### 4. Execute Workflow
```javascript
const response = await fetch(
  `http://localhost:5050/api/v1/chat/workflows/${chatId}/execute`,
  {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      steps: [
        {
          operation: 'excel/extract-columns-to-file',
          arguments: {
            columns: ['customer_id'],
            remove_duplicates: true
          }
        }
      ]
    })
  }
);
```

#### 5. Download Results
```javascript
// Download URLs are absolute and ready to use
const downloadUrl = data.results[0].download_url;
window.open(downloadUrl);

// Or use in anchor tag
<a href={downloadUrl} download>Download</a>
```

### React Component Example

```jsx
import React, { useState, useEffect } from 'react';

function ChatWorkflow({ chatId }) {
  const [progress, setProgress] = useState(0);
  const [status, setStatus] = useState('idle');
  const [message, setMessage] = useState('');

  useEffect(() => {
    const ws = new WebSocket(`ws://127.0.0.1:5051/chat/${chatId}`);
    
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      
      switch(data.type) {
        case 'workflow_started':
          setStatus('running');
          setMessage('Workflow started');
          break;
        case 'progress':
          setProgress(data.progress);
          setMessage(data.message);
          break;
        case 'workflow_completed':
          setStatus('completed');
          setProgress(100);
          setMessage('Completed successfully');
          break;
        case 'workflow_failed':
          setStatus('failed');
          setMessage(data.error);
          break;
      }
    };
    
    return () => ws.close();
  }, [chatId]);

  return (
    <div>
      <div>Status: {status}</div>
      <div>Progress: {progress}%</div>
      <div>Message: {message}</div>
      <progress value={progress} max="100" />
    </div>
  );
}
```

### Best Practices

1. **Error Handling**: Always handle WebSocket disconnections
2. **Reconnection**: Implement exponential backoff for reconnects
3. **Progress Updates**: Update UI smoothly with progress percentage
4. **Download URLs**: Use absolute URLs directly, no construction needed
5. **Message Validation**: Validate message structure before use

---

## 13. Deployment Notes

### Prerequisites

- Python 3.9+
- pip
- SQLite3 (usually pre-installed)

### Installation

```bash
# Clone repository
git clone https://github.com/pnguyen215/pycelize.git
cd pycelize

# Install dependencies
pip install -r requirements.txt

# Verify configuration
cat configs/application.yml
```

### Configuration

Edit `configs/application.yml`:

```yaml
chat_workflows:
  enabled: true
  max_connections: 10
  storage:
    workflows_path: "./automation/workflows"
    dumps_path: "./automation/dumps"
    sqlite_path: "./automation/sqlite/chat.db"
  partition:
    enabled: true
    strategy: "time-based"
  backup:
    enabled: true
    interval_minutes: 60
    snapshot_path: "./automation/sqlite/snapshots"
```

### Running the Application

```bash
# Development
python run.py

# Production (with gunicorn)
gunicorn -w 4 -b 0.0.0.0:5050 "app:create_app()"
```

### Expected Output

```
╔═══════════════════════════════════════════════════════════════════╗
║   🚀 Pycelize - Excel/CSV Processing API                          ║
║   Version:    v0.0.1                                              ║
║   REST API:   http://127.0.0.1:5050                               ║
║   WebSocket:  ✓ Running on ws://127.0.0.1:5051                    ║
║   Debug:      True                                                ║
╚═══════════════════════════════════════════════════════════════════╝
```

### Health Check

```bash
curl http://localhost:5050/api/v1/health
```

---

## 14. Known Issues and Fixes

### Recent Fixes (All Production-Ready ✅)

#### 1. WebSocket Integration
- **Issue**: WebSocket server not activated on startup
- **Fix**: Auto-starts with Flask, thread-safe bridge implemented
- **Status**: ✅ Fixed in commit 98f71b7

#### 2. File Upload Persistence
- **Issue**: Uploaded files not saved to database (CASCADE DELETE issue)
- **Fix**: Changed `INSERT OR REPLACE` to `INSERT ... ON CONFLICT DO UPDATE`
- **Status**: ✅ Fixed in commit 63afd56

#### 3. Workflow Executor Parameters
- **Issue**: Passing file paths instead of DataFrames to service methods
- **Fix**: Read files into DataFrames before passing to services
- **Status**: ✅ Fixed in commit 9aa3d34

#### 4. Download URLs
- **Issue**: Relative URLs that couldn't be clicked directly
- **Fix**: Changed to absolute URLs with scheme and host
- **Status**: ✅ Fixed in commit 1966b30

#### 5. Download Endpoint Storage Parameter
- **Issue**: Missing storage parameter causing downloads to fail
- **Fix**: Added ConversationStorage parameter to repository initialization
- **Status**: ✅ Fixed in commit 10c6ab0

#### 6. Restore Partition Path
- **Issue**: Files restored to flat directory instead of partitioned structure
- **Fix**: Extract to temp, read partition_key, move to correct path
- **Status**: ✅ Fixed in commit 95f37c7

#### 7. Dump File Download Path
- **Issue**: Path join creating invalid paths causing download failures
- **Fix**: Use `os.path.abspath()` for consistent path resolution
- **Status**: ✅ Fixed in commit 95f37c7

---

## 15. Troubleshooting Guide

### Common Issues

#### Issue: WebSocket Not Connecting

**Symptoms**: `Connection refused` or `404 Not Found`

**Solutions**:
1. Verify WebSocket is running:
   ```bash
   netstat -tuln | grep 5051
   ```
2. Check configuration:
   ```yaml
   chat_workflows:
     enabled: true
   ```
3. Restart application

#### Issue: File Download 404

**Symptoms**: `File not found` error when downloading

**Solutions**:
1. Verify file exists:
   ```bash
   ls -la automation/workflows/{partition_key}/{chat_id}/
   ```
2. Check download URL format (must be absolute)
3. Verify partition_key is correct in database

#### Issue: Restore to Wrong Location

**Symptoms**: Files not in partitioned directories after restore

**Solutions**:
1. Verify using latest version (fix applied in commit 95f37c7)
2. Check metadata.json in dump file contains partition_key
3. Manual fix:
   ```bash
   mv automation/workflows/{chat_id} automation/workflows/{partition_key}/
   ```

#### Issue: Workflow Execution Fails

**Symptoms**: `'str' object has no attribute 'columns'`

**Solutions**:
1. Verify using latest version (fix applied in commit 9aa3d34)
2. Check uploaded file is valid Excel/CSV
3. Verify operation parameters are correct

#### Issue: Database Locked

**Symptoms**: `database is locked` error

**Solutions**:
1. Close all other connections
2. Restart application
3. Check for stale lock files:
   ```bash
   rm automation/sqlite/chat.db-journal
   ```

### Debug Mode

Enable detailed logging in `configs/application.yml`:

```yaml
debug: true
log_level: "DEBUG"
```

### Logs

Check application logs:
```bash
tail -f logs/app.log
```

### Support

For additional help:
- Check documentation: This README
- Review test files: `tests/integration/chat_workflows/`
- Examine code: `app/chat/` directory

---

## Additional Resources

- **WebSocket Usage**: See `WEBSOCKET_USAGE.md` for detailed WebSocket documentation
- **API Examples**: See test files for comprehensive examples
- **Configuration**: See `configs/application.yml` for all options

---

## License

MIT License - See LICENSE file for details

---

## Contributors

Maintained by the Pycelize team.

---

**Last Updated**: 2026-02-07  
**Version**: v0.0.1  
**Status**: Production Ready ✅

