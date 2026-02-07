# Conversational Chat Workflows API Documentation

## Overview

The Pycelize conversational chat workflows system provides a Telegram-style chat interface for processing Excel/CSV files. The system consists of:

- **User**: Human participant sending messages and uploading files
- **System**: Pycelize automation engine responding with intelligent suggestions and executing workflows

## Architecture

### Components

1. **MessageService**: Intelligent message processing and operation suggestions
2. **ConversationRepository**: Manages conversations, messages, and workflow steps
3. **ChatDatabase**: SQLite persistence for all conversation data
4. **WebSocketServer**: Real-time message streaming
5. **WorkflowExecutor**: Executes workflow operations on uploaded files

### Database Schema

#### Conversations Table
```sql
CREATE TABLE conversations (
    chat_id TEXT PRIMARY KEY,
    participant_name TEXT NOT NULL,
    status TEXT NOT NULL,
    partition_key TEXT,
    metadata TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
)
```

#### Messages Table
```sql
CREATE TABLE messages (
    message_id TEXT PRIMARY KEY,
    chat_id TEXT NOT NULL,
    message_type TEXT NOT NULL,  -- 'user', 'system', 'file_upload', 'progress', 'error'
    content TEXT NOT NULL,
    metadata TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY (chat_id) REFERENCES conversations(chat_id) ON DELETE CASCADE
)
```

#### Workflow Steps Table
```sql
CREATE TABLE workflow_steps (
    step_id TEXT PRIMARY KEY,
    chat_id TEXT NOT NULL,
    operation TEXT NOT NULL,
    arguments TEXT NOT NULL,
    input_file TEXT,
    output_file TEXT,
    status TEXT NOT NULL,
    progress INTEGER DEFAULT 0,
    error_message TEXT,
    started_at TEXT,
    completed_at TEXT,
    FOREIGN KEY (chat_id) REFERENCES conversations(chat_id) ON DELETE CASCADE
)
```

## REST API Endpoints

### 1. Create Conversation

**Endpoint:** `POST /api/v1/chat/workflows`

Creates a new chat conversation with auto-generated participant name.

**Response:**
```json
{
  "data": {
    "chat_id": "550e8400-e29b-41d4-a716-446655440000",
    "participant_name": "BlueWhale-4821",
    "status": "created",
    "messages": [],
    "created_at": "2026-02-07T16:00:00.000000",
    "partition_key": "2026/02"
  },
  "message": "Conversation created successfully"
}
```

### 2. Get Available Operations

**Endpoint:** `GET /api/v1/workflow/operations`

Lists all available workflow operations with their arguments.

**Response:**
```json
{
  "data": {
    "operations": [
      {
        "name": "excel/extract-columns",
        "display_name": "Extract Columns to File",
        "description": "Extract specific columns from Excel file to a new file",
        "category": "excel",
        "arguments": [
          {
            "name": "columns",
            "type": "list",
            "required": true,
            "description": "List of column names to extract"
          }
        ]
      }
    ],
    "count": 7
  }
}
```

### 3. Send User Message

**Endpoint:** `POST /api/v1/chat/workflows/{chat_id}/messages`

Sends a user message and receives intelligent system response with operation suggestions.

**Request:**
```json
{
  "content": "I want to extract customer_id column from my data"
}
```

**Response:**
```json
{
  "data": {
    "user_message": {
      "message_id": "abc-123",
      "message_type": "user",
      "content": "I want to extract customer_id column from my data",
      "created_at": "2026-02-07T16:00:01.000000"
    },
    "system_message": {
      "message_id": "def-456",
      "message_type": "system",
      "content": "I can help you with the following operations:\n\n1. **Extract Columns to File**\n   Extract specific columns from Excel file...",
      "metadata": {
        "suggested_operations": [...],
        "response_type": "operation_suggestions"
      }
    },
    "suggested_operations": [
      {
        "name": "excel/extract-columns",
        "display_name": "Extract Columns to File",
        "description": "...",
        "arguments": [...]
      }
    ]
  }
}
```

### 4. Get Message History

**Endpoint:** `GET /api/v1/chat/workflows/{chat_id}/messages`

Retrieves all messages in a conversation (Telegram-style).

**Query Parameters:**
- `limit` (optional): Maximum messages to return (default: 100)
- `offset` (optional): Pagination offset (default: 0)

**Response:**
```json
{
  "data": {
    "messages": [
      {
        "message_id": "msg-1",
        "message_type": "system",
        "sender_type": "system",
        "content": "Welcome! I'm your automation assistant...",
        "created_at": "2026-02-07T16:00:00.000000"
      },
      {
        "message_id": "msg-2",
        "message_type": "user",
        "sender_type": "user",
        "content": "Extract columns",
        "created_at": "2026-02-07T16:00:01.000000"
      },
      {
        "message_id": "msg-3",
        "message_type": "system",
        "sender_type": "system",
        "content": "I can help you with...",
        "metadata": {
          "suggested_operations": [...]
        },
        "created_at": "2026-02-07T16:00:02.000000"
      }
    ],
    "count": 3,
    "chat_id": "550e8400-e29b-41d4-a716-446655440000"
  }
}
```

### 5. Upload File

**Endpoint:** `POST /api/v1/chat/workflows/{chat_id}/upload`

Uploads a file and receives intelligent operation suggestions based on file type.

**Request:** Multipart form data with 'file' field

**Response:**
```json
{
  "data": {
    "file_path": "/path/to/uploaded/file.xlsx",
    "filename": "data.xlsx",
    "download_url": "http://localhost:5050/api/v1/chat/workflows/{chat_id}/files/data.xlsx",
    "system_response": {
      "system_message": {
        "content": "Excel file **data.xlsx** uploaded successfully! I can help you process this file...",
        "metadata": {
          "suggested_operations": [...],
          "response_type": "file_upload_response"
        }
      },
      "suggested_operations": [...]
    }
  }
}
```

### 6. Execute Workflow

**Endpoint:** `POST /api/v1/chat/workflows/{chat_id}/execute`

Executes workflow steps on uploaded files.

**Request:**
```json
{
  "steps": [
    {
      "operation": "excel/extract-columns",
      "arguments": {
        "columns": ["customer_id", "name", "email"]
      }
    }
  ]
}
```

**Response:**
```json
{
  "data": {
    "results": [
      {
        "step_id": "step-1",
        "operation": "excel/extract-columns",
        "status": "completed",
        "output_file_path": "/path/to/output.xlsx",
        "download_url": "http://localhost:5050/api/v1/chat/workflows/{chat_id}/files/output.xlsx"
      }
    ],
    "output_files": [
      {
        "file_path": "/path/to/output.xlsx",
        "download_url": "http://localhost:5050/api/v1/chat/workflows/{chat_id}/files/output.xlsx"
      }
    ]
  }
}
```

## WebSocket API

### Connection

Connect to: `ws://localhost:5051/chat/{chat_id}`

### Event Types

#### 1. Connected Event
```json
{
  "type": "connected",
  "chat_id": "550e8400-e29b-41d4-a716-446655440000",
  "timestamp": "2026-02-07T16:00:00.000000"
}
```

#### 2. Message Event (User Message)
```json
{
  "type": "message",
  "chat_id": "550e8400-e29b-41d4-a716-446655440000",
  "sender_type": "user",
  "message_type": "text",
  "content": "Extract columns",
  "message_id": "msg-123",
  "created_at": "2026-02-07T16:00:01.000000"
}
```

#### 3. Message Event (System Response)
```json
{
  "type": "message",
  "chat_id": "550e8400-e29b-41d4-a716-446655440000",
  "sender_type": "system",
  "message_type": "workflow",
  "content": "I can help you with the following operations...",
  "metadata": {
    "suggested_operations": [...]
  },
  "timestamp": "2026-02-07T16:00:02.000000"
}
```

#### 4. Progress Event
```json
{
  "type": "progress",
  "chat_id": "550e8400-e29b-41d4-a716-446655440000",
  "step_id": "step-1",
  "operation": "excel/extract-columns",
  "progress": 45,
  "status": "running",
  "message": "Processing step 1",
  "timestamp": "2026-02-07T16:00:03.000000"
}
```

#### 5. Workflow Started Event
```json
{
  "type": "workflow_started",
  "chat_id": "550e8400-e29b-41d4-a716-446655440000",
  "total_steps": 3,
  "message": "Workflow execution started",
  "timestamp": "2026-02-07T16:00:04.000000"
}
```

#### 6. Workflow Completed Event
```json
{
  "type": "workflow_completed",
  "chat_id": "550e8400-e29b-41d4-a716-446655440000",
  "total_steps": 3,
  "output_files_count": 1,
  "message": "Workflow execution completed successfully",
  "timestamp": "2026-02-07T16:00:10.000000"
}
```

#### 7. Workflow Failed Event
```json
{
  "type": "workflow_failed",
  "chat_id": "550e8400-e29b-41d4-a716-446655440000",
  "error": "Error message details",
  "message": "Workflow execution failed",
  "timestamp": "2026-02-07T16:00:10.000000"
}
```

## Available Workflow Operations

### 1. Extract Columns to File
**Operation:** `excel/extract-columns`

Extracts specific columns from an Excel file to a new file.

**Arguments:**
- `columns` (list, required): List of column names to extract

**Example:**
```json
{
  "operation": "excel/extract-columns",
  "arguments": {
    "columns": ["customer_id", "name", "email"]
  }
}
```

### 2. Normalize Column Data
**Operation:** `excel/normalize-columns`

Normalizes and cleans data in Excel columns.

**Arguments:**
- `columns` (list, required): List of column names to normalize
- `normalization_type` (string, optional): Type of normalization (default: "trim")

### 3. Convert to JSON
**Operation:** `excel/convert-to-json`

Converts Excel data to JSON format.

**Arguments:**
- `orient` (string, optional): JSON orientation - "records", "split", "index", "columns", "values" (default: "records")

### 4. Convert to CSV
**Operation:** `excel/convert-to-csv`

Converts Excel file to CSV format.

**Arguments:**
- `delimiter` (string, optional): CSV delimiter character (default: ",")

### 5. Convert CSV to Excel
**Operation:** `csv/convert-to-excel`

Converts CSV file to Excel format.

**Arguments:** None

### 6. Generate SQL Insert Statements
**Operation:** `excel/generate-sql`

Generates SQL INSERT statements from Excel data.

**Arguments:**
- `table_name` (string, required): Target database table name
- `database_type` (string, optional): Database type - "postgresql", "mysql", "sqlite" (default: "postgresql")

### 7. Search Data
**Operation:** `excel/search-data`

Searches for specific data in Excel file.

**Arguments:**
- `search_term` (string, required): Term to search for
- `columns` (list, optional): Specific columns to search in (searches all if not specified)

## Usage Examples

### Python Example

```python
import requests
import json

BASE_URL = "http://localhost:5050/api/v1/chat"

# 1. Create conversation
response = requests.post(f"{BASE_URL}/workflows")
chat_id = response.json()['data']['chat_id']
print(f"Conversation ID: {chat_id}")

# 2. Get available operations
response = requests.get(f"{BASE_URL}/workflow/operations")
operations = response.json()['data']['operations']
print(f"Available operations: {len(operations)}")

# 3. Send user message
response = requests.post(
    f"{BASE_URL}/workflows/{chat_id}/messages",
    json={"content": "I want to extract columns"}
)
result = response.json()['data']
print(f"System response: {result['system_message']['content']}")
print(f"Suggested ops: {len(result['suggested_operations'])}")

# 4. Upload file
with open('data.xlsx', 'rb') as f:
    response = requests.post(
        f"{BASE_URL}/workflows/{chat_id}/upload",
        files={'file': f}
    )
print(f"File uploaded: {response.json()['data']['filename']}")

# 5. Execute workflow
response = requests.post(
    f"{BASE_URL}/workflows/{chat_id}/execute",
    json={
        "steps": [
            {
                "operation": "excel/extract-columns",
                "arguments": {
                    "columns": ["customer_id", "email"]
                }
            }
        ]
    }
)
results = response.json()['data']['results']
print(f"Workflow executed: {results[0]['status']}")
print(f"Download: {results[0]['download_url']}")
```

### JavaScript Example

```javascript
const BASE_URL = 'http://localhost:5050/api/v1/chat';

// 1. Create conversation
let response = await fetch(`${BASE_URL}/workflows`, {
  method: 'POST'
});
let data = await response.json();
const chatId = data.data.chat_id;

// 2. Send user message
response = await fetch(`${BASE_URL}/workflows/${chatId}/messages`, {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({
    content: 'Extract customer_id column'
  })
});
data = await response.json();
console.log('System response:', data.data.system_message.content);

// 3. WebSocket connection
const ws = new WebSocket(`ws://localhost:5051/chat/${chatId}`);

ws.onmessage = (event) => {
  const message = JSON.parse(event.data);
  console.log('WebSocket event:', message.type);
  
  if (message.type === 'message') {
    console.log(`[${message.sender_type}]: ${message.content}`);
  } else if (message.type === 'progress') {
    console.log(`Progress: ${message.progress}%`);
  }
};
```

## Message Intent Detection

The MessageService uses keyword-based intent detection to suggest relevant operations:

| Keywords | Suggested Operations |
|----------|---------------------|
| "extract", "column" | extract-columns, normalize-columns |
| "normalize", "clean" | normalize-columns |
| "json" | convert-to-json |
| "csv" | convert-to-csv, csv-convert-to-excel |
| "sql" | generate-sql |
| "search", "find" | search-data |
| "convert" | All conversion operations |

When no specific keywords are detected, the system suggests common operations: extract-columns, convert-to-json, and convert-to-csv.

## File Type Detection

The system detects uploaded file types and suggests appropriate operations:

| File Type | Suggested Operations |
|-----------|---------------------|
| .xlsx, .xls | All Excel operations (extract, normalize, convert, SQL) |
| .csv | csv-convert-to-excel, search-data |
| Other | All available operations |

## Configuration

Edit `configs/application.yml` to configure chat workflows:

```yaml
chat_workflows:
  enabled: true
  max_connections: 10
  
  websocket:
    host: "127.0.0.1"
    port: 5051
    ping_interval: 30
    ping_timeout: 10
  
  storage:
    workflows_path: "./automation/workflows"
    dumps_path: "./automation/dumps"
    sqlite_path: "./automation/sqlite/chat.db"
  
  partition:
    enabled: true
    strategy: "time-based"
    subfolder_format: "%Y/%m"
```

## Running the Application

```bash
# Install dependencies
pip install -r requirements.txt

# Start the server (REST API on 5050, WebSocket on 5051)
python run.py

# The server will output:
# REST API:   http://127.0.0.1:5050
# WebSocket:  ws://127.0.0.1:5051
```

## Testing

```bash
# Run integration tests
python tests/integration/chat_workflows/test_conversational_chat.py

# Run manual tests (requires server running)
python tests/manual_test_conversational_chat.py
```

## Architecture Benefits

1. **OOP Design**: Clean separation of concerns with repositories, services, and models
2. **Extensible**: Easy to add new workflow operations
3. **Database Persistence**: All messages and workflow steps stored in SQLite
4. **Real-time Updates**: WebSocket streaming for live progress
5. **Intelligent Suggestions**: Context-aware operation recommendations
6. **File Partitioning**: Organized storage by time or hash
7. **Message History**: Full Telegram-style conversation history
8. **Error Handling**: Comprehensive validation and error responses
