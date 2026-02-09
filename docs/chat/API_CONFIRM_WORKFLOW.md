# Chatbot API - Confirm Workflow Documentation

## Overview

This document provides comprehensive technical documentation for the **Confirm Workflow** endpoint in the Pycelize Chatbot API. This endpoint allows developers to confirm or decline suggested workflows after the bot has analyzed user intent and uploaded files.

**Key Features:**
- **Asynchronous Execution**: Workflows run in the background for improved performance
- **Immediate Response**: Returns `202 Accepted` status immediately with a job ID
- **Real-time Updates**: Progress tracking via WebSocket or status endpoint
- **Workflow Modification**: Support for modifying suggested workflows before execution
- **Multiple Operations**: Support for 8 different intent types and 15+ operations

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [API Endpoint](#api-endpoint)
3. [Request Structure](#request-structure)
4. [Response Formats](#response-formats)
5. [Supported Operations](#supported-operations)
6. [cURL Examples](#curl-examples)
7. [Job Status Tracking](#job-status-tracking)
8. [WebSocket Integration](#websocket-integration)
9. [Error Handling](#error-handling)
10. [Frontend Integration](#frontend-integration)
11. [Backend Integration](#backend-integration)

---

## Prerequisites

### 1. Get Supported Operations

Before confirming a workflow, you should understand the available operations:

```bash
curl --location --request GET 'http://localhost:5050/api/v1/chat/bot/operations'
```

**Response:**
```json
{
    "data": {
        "operations": {
            "bind_data": [
                "excel/bind-single-key",
                "excel/bind-multi-key"
            ],
            "convert_format": [
                "csv/convert-to-excel",
                "json/generate"
            ],
            "extract_columns": [
                "excel/extract-columns-to-file"
            ],
            "generate_json": [
                "json/generate",
                "json/generate-with-template"
            ],
            "generate_sql": [
                "sql/generate",
                "sql/generate-to-text"
            ],
            "map_columns": [
                "excel/map-columns"
            ],
            "normalize_data": [
                "normalization/apply"
            ],
            "search_filter": [
                "excel/search",
                "csv/search"
            ]
        },
        "total_intents": 8
    },
    "message": "Supported operations retrieved successfully",
    "status_code": 200
}
```

### 2. Create Conversation and Upload File

Before you can confirm a workflow, you need to:

1. **Create a conversation**:
```bash
curl -X POST http://localhost:5050/api/v1/chat/bot/conversations \
  -H "Content-Type: application/json"
```

2. **Send a message** to get a suggested workflow:
```bash
curl -X POST http://localhost:5050/api/v1/chat/bot/conversations/{chat_id}/message \
  -H "Content-Type: application/json" \
  -d '{"message": "extract columns: name, email, phone"}'
```

3. **Upload a file**:
```bash
curl -X POST http://localhost:5050/api/v1/chat/bot/conversations/{chat_id}/upload \
  -F "file=@/path/to/your/data.xlsx"
```

---

## API Endpoint

### Confirm Workflow

**Endpoint:** `POST /api/v1/chat/bot/conversations/{chat_id}/confirm`

**Description:** Confirm or decline a suggested workflow. When confirmed, the workflow executes asynchronously in the background.

**Method:** `POST`

**URL:** `http://localhost:5050/api/v1/chat/bot/conversations/{chat_id}/confirm`

**Headers:**
```
Content-Type: application/json
```

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `chat_id` | string | Yes | Unique conversation identifier (UUID) |

---

## Request Structure

### Request Body

The request body is a JSON object with the following structure:

```json
{
  "confirmed": true,
  "modified_workflow": [
    {
      "operation": "excel/extract-columns-to-file",
      "arguments": {
        "columns": ["level_1"],
        "remove_duplicates": true
      }
    }
  ]
}
```

### Request Parameters

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `confirmed` | boolean | Yes | Whether to confirm (`true`) or decline (`false`) the workflow |
| `modified_workflow` | array | No | Optional modified workflow steps to execute instead of the suggested workflow |

### Modified Workflow Structure

When providing a `modified_workflow`, each step must follow this structure:

```json
{
  "operation": "string",    // Operation identifier (see Supported Operations)
  "arguments": {            // Operation-specific arguments
    // Arguments vary by operation
  }
}
```

---

## Response Formats

### Async Execution Response (202 Accepted)

When a workflow is **confirmed** and submitted for background execution:

**Status Code:** `202 Accepted`

**Response Body:**
```json
{
  "data": {
    "job_id": "f20a51f4-b954-4e48-bd8e-256c243976aa_workflow_1a2b3c4d",
    "status": "submitted",
    "message": "Workflow submitted for execution. Use WebSocket or check status endpoint for progress.",
    "bot_response": "🚀 Workflow submitted! I'm processing your request in the background. You'll receive real-time updates via WebSocket."
  },
  "message": "Workflow submitted for background execution",
  "meta": {
    "api_version": "v0.0.1",
    "locale": "en_US",
    "request_id": "ddb256bab4cc42e5bcc0d7efb5a734fb",
    "requested_time": "2026-02-09T21:50:18.648408+07:00"
  },
  "status_code": 202,
  "total": 0
}
```

**Response Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `data.job_id` | string | Unique job identifier for tracking workflow execution |
| `data.status` | string | Job status: `"submitted"` |
| `data.message` | string | Informational message about the submission |
| `data.bot_response` | string | Human-readable response from the chatbot |
| `message` | string | API response message |
| `meta` | object | Metadata including API version, locale, request ID, and timestamp |
| `status_code` | number | HTTP status code (202) |

### Decline Response (200 OK)

When a workflow is **declined** (`confirmed: false`):

**Status Code:** `200 OK`

**Response Body:**
```json
{
  "data": {
    "bot_response": "No problem! Let me know if you'd like to try something different.",
    "output_files": [],
    "results": []
  },
  "message": "Workflow confirmation processed",
  "meta": {
    "api_version": "v0.0.1",
    "locale": "en_US",
    "request_id": "abc123def456",
    "requested_time": "2026-02-09T21:50:18.648408+07:00"
  },
  "status_code": 200,
  "total": 0
}
```

### Completion Response (via WebSocket or Status Endpoint)

When a workflow **completes successfully**, you can retrieve the results via the status endpoint:

**Response Body:**
```json
{
  "data": {
    "job_id": "f20a51f4-b954-4e48-bd8e-256c243976aa_workflow_1a2b3c4d",
    "status": "completed",
    "submitted_at": "2026-02-09T14:10:00.000Z",
    "started_at": "2026-02-09T14:10:00.100Z",
    "completed_at": "2026-02-09T14:10:05.500Z",
    "result": {
      "bot_response": "✅ Workflow completed successfully!",
      "output_files": [
        {
          "file_path": "/path/to/output.xlsx",
          "download_url": "http://localhost:5050/api/v1/chat/workflows/f20a51f4-b954-4e48-bd8e-256c243976aa/files/output.xlsx"
        }
      ],
      "results": [
        {
          "step_id": "step-1",
          "operation": "excel/extract-columns-to-file",
          "status": "success",
          "output_file": "/path/to/output.xlsx"
        }
      ]
    },
    "error": null
  },
  "message": "Job status retrieved successfully",
  "status_code": 200
}
```

---

## Supported Operations

The following operations can be included in the `modified_workflow` array:

### 1. Extract Columns

**Operations:**
- `excel/extract-columns-to-file`

**Example Arguments:**
```json
{
  "operation": "excel/extract-columns-to-file",
  "arguments": {
    "columns": ["name", "email", "phone"],
    "remove_duplicates": true,
    "output_file": "extracted_data.xlsx"
  }
}
```

**Arguments:**

| Argument | Type | Required | Description |
|----------|------|----------|-------------|
| `columns` | array[string] | Yes | List of column names to extract |
| `remove_duplicates` | boolean | No | Remove duplicate rows (default: `false`) |
| `output_file` | string | No | Output filename (default: auto-generated) |

---

### 2. Convert Format

**Operations:**
- `csv/convert-to-excel` - Convert CSV to Excel format
- `json/generate` - Convert data to JSON format

**Example Arguments (CSV to Excel):**
```json
{
  "operation": "csv/convert-to-excel",
  "arguments": {
    "output_file": "converted_data.xlsx",
    "sheet_name": "Sheet1"
  }
}
```

**Example Arguments (JSON Generation):**
```json
{
  "operation": "json/generate",
  "arguments": {
    "output_file": "data.json",
    "pretty": true
  }
}
```

---

### 3. Normalize Data

**Operations:**
- `normalization/apply`

**Example Arguments:**
```json
{
  "operation": "normalization/apply",
  "arguments": {
    "operations": ["trim", "uppercase"],
    "columns": ["name", "email"],
    "output_file": "normalized_data.xlsx"
  }
}
```

**Normalization Operations:**
- `trim` - Remove leading/trailing whitespace
- `uppercase` - Convert to uppercase
- `lowercase` - Convert to lowercase
- `remove_special_chars` - Remove special characters
- `remove_duplicates` - Remove duplicate rows

---

### 4. Generate SQL

**Operations:**
- `sql/generate` - Generate SQL INSERT statements
- `sql/generate-to-text` - Generate SQL to text file

**Example Arguments:**
```json
{
  "operation": "sql/generate",
  "arguments": {
    "table_name": "users",
    "output_file": "insert_statements.sql"
  }
}
```

**Arguments:**

| Argument | Type | Required | Description |
|----------|------|----------|-------------|
| `table_name` | string | Yes | Database table name |
| `output_file` | string | No | Output filename |

---

### 5. Generate JSON

**Operations:**
- `json/generate` - Generate JSON from data
- `json/generate-with-template` - Generate JSON with custom template

**Example Arguments (with Template):**
```json
{
  "operation": "json/generate-with-template",
  "arguments": {
    "template": {
      "id": "{{id}}",
      "user": {
        "name": "{{name}}",
        "email": "{{email}}"
      }
    },
    "output_file": "formatted_data.json"
  }
}
```

---

### 6. Search/Filter

**Operations:**
- `excel/search` - Search in Excel files
- `csv/search` - Search in CSV files

**Example Arguments:**
```json
{
  "operation": "excel/search",
  "arguments": {
    "column": "status",
    "operator": "equals",
    "value": "active",
    "output_file": "filtered_data.xlsx"
  }
}
```

**Search Operators:**
- `equals` - Exact match
- `contains` - Substring match
- `starts_with` - Starts with value
- `ends_with` - Ends with value
- `greater_than` - Greater than (numeric)
- `less_than` - Less than (numeric)

---

### 7. Bind/Merge Data

**Operations:**
- `excel/bind-single-key` - Merge using a single key column
- `excel/bind-multi-key` - Merge using multiple key columns

**Example Arguments (Single Key):**
```json
{
  "operation": "excel/bind-single-key",
  "arguments": {
    "bind_file": "customer_info.xlsx",
    "key_column": "customer_id",
    "output_file": "merged_data.xlsx"
  }
}
```

**Example Arguments (Multi Key):**
```json
{
  "operation": "excel/bind-multi-key",
  "arguments": {
    "bind_file": "orders.xlsx",
    "key_columns": ["customer_id", "order_date"],
    "output_file": "merged_orders.xlsx"
  }
}
```

---

### 8. Map Columns

**Operations:**
- `excel/map-columns` - Rename columns

**Example Arguments:**
```json
{
  "operation": "excel/map-columns",
  "arguments": {
    "column_mapping": {
      "old_name": "new_name",
      "customer_id": "id",
      "customer_name": "name"
    },
    "output_file": "remapped_data.xlsx"
  }
}
```

---

## cURL Examples

### Example 1: Confirm Suggested Workflow (Basic)

Confirm the workflow suggested by the bot without modifications:

```bash
curl --location 'http://localhost:5050/api/v1/chat/bot/conversations/f20a51f4-b954-4e48-bd8e-256c243976aa/confirm' \
--header 'Content-Type: application/json' \
--data '{
  "confirmed": true
}'
```

**Expected Response:** `202 Accepted` with job ID

---

### Example 2: Decline Workflow

Decline the suggested workflow:

```bash
curl --location 'http://localhost:5050/api/v1/chat/bot/conversations/f20a51f4-b954-4e48-bd8e-256c243976aa/confirm' \
--header 'Content-Type: application/json' \
--data '{
  "confirmed": false
}'
```

**Expected Response:** `200 OK` with decline message

---

### Example 3: Confirm with Modified Workflow (Extract Columns)

Confirm and execute a modified workflow to extract specific columns:

```bash
curl --location 'http://localhost:5050/api/v1/chat/bot/conversations/f20a51f4-b954-4e48-bd8e-256c243976aa/confirm' \
--header 'Content-Type: application/json' \
--data '{
  "confirmed": true,
  "modified_workflow": [
    {
      "operation": "excel/extract-columns-to-file",
      "arguments": {
        "columns": ["level_1"],
        "remove_duplicates": true
      }
    }
  ]
}'
```

**Expected Response:** `202 Accepted` with job ID

---

### Example 4: Extract Multiple Columns with Output File

```bash
curl --location 'http://localhost:5050/api/v1/chat/bot/conversations/abc123-def456/confirm' \
--header 'Content-Type: application/json' \
--data '{
  "confirmed": true,
  "modified_workflow": [
    {
      "operation": "excel/extract-columns-to-file",
      "arguments": {
        "columns": ["name", "email", "phone", "status"],
        "remove_duplicates": false,
        "output_file": "customer_contacts.xlsx"
      }
    }
  ]
}'
```

---

### Example 5: Convert CSV to Excel

```bash
curl --location 'http://localhost:5050/api/v1/chat/bot/conversations/abc123-def456/confirm' \
--header 'Content-Type: application/json' \
--data '{
  "confirmed": true,
  "modified_workflow": [
    {
      "operation": "csv/convert-to-excel",
      "arguments": {
        "output_file": "converted_data.xlsx",
        "sheet_name": "Data"
      }
    }
  ]
}'
```

---

### Example 6: Normalize Data

```bash
curl --location 'http://localhost:5050/api/v1/chat/bot/conversations/abc123-def456/confirm' \
--header 'Content-Type: application/json' \
--data '{
  "confirmed": true,
  "modified_workflow": [
    {
      "operation": "normalization/apply",
      "arguments": {
        "operations": ["trim", "uppercase"],
        "columns": ["name", "email"],
        "output_file": "normalized_customers.xlsx"
      }
    }
  ]
}'
```

---

### Example 7: Generate SQL Statements

```bash
curl --location 'http://localhost:5050/api/v1/chat/bot/conversations/abc123-def456/confirm' \
--header 'Content-Type: application/json' \
--data '{
  "confirmed": true,
  "modified_workflow": [
    {
      "operation": "sql/generate",
      "arguments": {
        "table_name": "users",
        "output_file": "user_inserts.sql"
      }
    }
  ]
}'
```

---

### Example 8: Search and Filter Data

```bash
curl --location 'http://localhost:5050/api/v1/chat/bot/conversations/abc123-def456/confirm' \
--header 'Content-Type: application/json' \
--data '{
  "confirmed": true,
  "modified_workflow": [
    {
      "operation": "excel/search",
      "arguments": {
        "column": "status",
        "operator": "equals",
        "value": "active",
        "output_file": "active_customers.xlsx"
      }
    }
  ]
}'
```

---

### Example 9: Merge Data with Single Key

```bash
curl --location 'http://localhost:5050/api/v1/chat/bot/conversations/abc123-def456/confirm' \
--header 'Content-Type: application/json' \
--data '{
  "confirmed": true,
  "modified_workflow": [
    {
      "operation": "excel/bind-single-key",
      "arguments": {
        "bind_file": "customer_info.xlsx",
        "key_column": "customer_id",
        "output_file": "merged_customers.xlsx"
      }
    }
  ]
}'
```

---

### Example 10: Rename Columns

```bash
curl --location 'http://localhost:5050/api/v1/chat/bot/conversations/abc123-def456/confirm' \
--header 'Content-Type: application/json' \
--data '{
  "confirmed": true,
  "modified_workflow": [
    {
      "operation": "excel/map-columns",
      "arguments": {
        "column_mapping": {
          "cust_id": "customer_id",
          "cust_name": "customer_name",
          "email_addr": "email"
        },
        "output_file": "remapped_customers.xlsx"
      }
    }
  ]
}'
```

---

### Example 11: Multi-Step Workflow

Execute multiple operations in sequence:

```bash
curl --location 'http://localhost:5050/api/v1/chat/bot/conversations/abc123-def456/confirm' \
--header 'Content-Type: application/json' \
--data '{
  "confirmed": true,
  "modified_workflow": [
    {
      "operation": "normalization/apply",
      "arguments": {
        "operations": ["trim", "uppercase"],
        "columns": ["name", "email"]
      }
    },
    {
      "operation": "excel/extract-columns-to-file",
      "arguments": {
        "columns": ["name", "email", "phone"],
        "remove_duplicates": true,
        "output_file": "clean_contacts.xlsx"
      }
    }
  ]
}'
```

---

### Example 12: Generate JSON with Template

```bash
curl --location 'http://localhost:5050/api/v1/chat/bot/conversations/abc123-def456/confirm' \
--header 'Content-Type: application/json' \
--data '{
  "confirmed": true,
  "modified_workflow": [
    {
      "operation": "json/generate-with-template",
      "arguments": {
        "template": {
          "id": "{{id}}",
          "customer": {
            "name": "{{name}}",
            "email": "{{email}}",
            "phone": "{{phone}}"
          },
          "metadata": {
            "created_at": "{{timestamp}}"
          }
        },
        "output_file": "customers.json"
      }
    }
  ]
}'
```

---

## Job Status Tracking

After confirming a workflow, you receive a `job_id`. Use this to track the job status.

### Get Job Status Endpoint

**Endpoint:** `GET /api/v1/chat/bot/conversations/{chat_id}/workflow/status/{job_id}`

**cURL Example:**
```bash
curl --location 'http://localhost:5050/api/v1/chat/bot/conversations/f20a51f4-b954-4e48-bd8e-256c243976aa/workflow/status/f20a51f4-b954-4e48-bd8e-256c243976aa_workflow_1a2b3c4d'
```

**Response:**
```json
{
  "data": {
    "job_id": "f20a51f4-b954-4e48-bd8e-256c243976aa_workflow_1a2b3c4d",
    "status": "running",
    "submitted_at": "2026-02-09T14:10:00.000Z",
    "started_at": "2026-02-09T14:10:00.100Z",
    "completed_at": null,
    "result": null,
    "error": null
  },
  "message": "Job status retrieved successfully",
  "status_code": 200
}
```

### Job Status Values

| Status | Description |
|--------|-------------|
| `pending` | Job is queued but hasn't started yet |
| `running` | Job is currently executing |
| `completed` | Job finished successfully |
| `failed` | Job failed with an error |
| `cancelled` | Job was cancelled |

### Polling Example

```bash
#!/bin/bash

CHAT_ID="f20a51f4-b954-4e48-bd8e-256c243976aa"
JOB_ID="f20a51f4-b954-4e48-bd8e-256c243976aa_workflow_1a2b3c4d"
BASE_URL="http://localhost:5050/api/v1/chat/bot/conversations"

while true; do
  STATUS=$(curl -s "${BASE_URL}/${CHAT_ID}/workflow/status/${JOB_ID}" | jq -r '.data.status')
  echo "Job Status: $STATUS"
  
  if [ "$STATUS" = "completed" ] || [ "$STATUS" = "failed" ] || [ "$STATUS" = "cancelled" ]; then
    echo "Job finished with status: $STATUS"
    break
  fi
  
  sleep 2
done
```

---

## WebSocket Integration

For real-time updates during workflow execution, connect to the WebSocket server.

### WebSocket Connection

**URL:** `ws://localhost:5051`

**Connection Example (JavaScript):**
```javascript
const ws = new WebSocket('ws://localhost:5051');

ws.onopen = () => {
  console.log('WebSocket connected');
};

ws.onmessage = (event) => {
  const message = JSON.parse(event.data);
  console.log('Received:', message);
  
  switch (message.type) {
    case 'workflow_started':
      console.log(`Workflow started: ${message.total_steps} steps`);
      break;
    case 'progress':
      console.log(`Progress: ${message.progress}% - ${message.message}`);
      break;
    case 'workflow_completed':
      console.log('Workflow completed successfully!');
      break;
    case 'workflow_failed':
      console.error('Workflow failed:', message.error);
      break;
  }
};

ws.onerror = (error) => {
  console.error('WebSocket error:', error);
};

ws.onclose = () => {
  console.log('WebSocket disconnected');
};
```

### WebSocket Message Types

#### 1. Workflow Started
```json
{
  "type": "workflow_started",
  "chat_id": "abc123-def456",
  "total_steps": 3,
  "message": "🚀 Starting workflow execution...",
  "timestamp": "2026-02-09T14:10:00.000Z"
}
```

#### 2. Progress Update
```json
{
  "type": "progress",
  "chat_id": "abc123-def456",
  "step_id": "step-1",
  "operation": "excel/extract-columns-to-file",
  "progress": 50,
  "status": "running",
  "message": "Extracting columns...",
  "timestamp": "2026-02-09T14:10:02.500Z"
}
```

#### 3. Workflow Completed
```json
{
  "type": "workflow_completed",
  "chat_id": "abc123-def456",
  "message": "✅ Workflow completed successfully!",
  "output_files": [
    {
      "file_path": "/path/to/output.xlsx",
      "download_url": "http://localhost:5050/api/v1/chat/workflows/abc123-def456/files/output.xlsx"
    }
  ],
  "timestamp": "2026-02-09T14:10:05.000Z"
}
```

#### 4. Workflow Failed
```json
{
  "type": "workflow_failed",
  "chat_id": "abc123-def456",
  "error": "Invalid column name: 'nonexistent_column'",
  "message": "❌ Workflow failed",
  "timestamp": "2026-02-09T14:10:03.000Z"
}
```

#### 5. Step Completed
```json
{
  "type": "step_completed",
  "chat_id": "abc123-def456",
  "step_id": "step-1",
  "operation": "excel/extract-columns-to-file",
  "status": "success",
  "message": "Step completed successfully",
  "output_file": "/path/to/output.xlsx",
  "timestamp": "2026-02-09T14:10:04.000Z"
}
```

---

## Error Handling

### HTTP Error Responses

#### 400 Bad Request
```json
{
  "error": "Workflow confirmation failed",
  "message": "Invalid workflow configuration",
  "status_code": 400,
  "meta": {
    "api_version": "v0.0.1",
    "request_id": "xyz789"
  }
}
```

**Common Causes:**
- Invalid workflow structure
- Missing required arguments
- Unsupported operation

---

#### 404 Not Found
```json
{
  "error": "Conversation not found",
  "message": "The specified conversation does not exist",
  "status_code": 404,
  "meta": {
    "api_version": "v0.0.1",
    "request_id": "xyz789"
  }
}
```

**Common Causes:**
- Invalid `chat_id`
- Conversation was deleted
- Conversation expired

---

#### 422 Unprocessable Entity
```json
{
  "error": "No workflow to confirm",
  "message": "No suggested workflow found for this conversation",
  "status_code": 422,
  "meta": {
    "api_version": "v0.0.1",
    "request_id": "xyz789"
  }
}
```

**Common Causes:**
- No file uploaded
- No message sent to generate workflow
- Invalid conversation state

---

#### 500 Internal Server Error
```json
{
  "error": "Failed to confirm workflow: Database connection error",
  "message": "Internal server error",
  "status_code": 500,
  "meta": {
    "api_version": "v0.0.1",
    "request_id": "xyz789"
  }
}
```

**Common Causes:**
- Database errors
- File system errors
- Unexpected exceptions

---

### Error Handling Best Practices

#### For Frontend Developers

```javascript
async function confirmWorkflow(chatId, confirmed, modifiedWorkflow = null) {
  try {
    const response = await fetch(
      `http://localhost:5050/api/v1/chat/bot/conversations/${chatId}/confirm`,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          confirmed,
          modified_workflow: modifiedWorkflow,
        }),
      }
    );
    
    const data = await response.json();
    
    if (response.status === 202) {
      // Workflow submitted successfully
      const jobId = data.data.job_id;
      console.log('Workflow submitted with job ID:', jobId);
      
      // Start tracking via WebSocket or polling
      startJobTracking(chatId, jobId);
      
      return { success: true, jobId, data };
      
    } else if (response.status === 200) {
      // Workflow declined or completed immediately
      console.log('Workflow processed:', data.data.bot_response);
      return { success: true, data };
      
    } else {
      // Error occurred
      console.error('Error confirming workflow:', data.error);
      return { success: false, error: data.error };
    }
    
  } catch (error) {
    console.error('Network error:', error);
    return { success: false, error: error.message };
  }
}

// Usage
const result = await confirmWorkflow('abc123-def456', true);
if (result.success) {
  console.log('Success!');
} else {
  console.error('Failed:', result.error);
}
```

#### For Backend Developers

```python
import requests
import json
from typing import Dict, Any, Optional

class ChatBotClient:
    def __init__(self, base_url: str = "http://localhost:5050"):
        self.base_url = base_url
        
    def confirm_workflow(
        self,
        chat_id: str,
        confirmed: bool,
        modified_workflow: Optional[list] = None
    ) -> Dict[str, Any]:
        """
        Confirm or decline a chatbot workflow.
        
        Args:
            chat_id: Conversation identifier
            confirmed: Whether to confirm or decline
            modified_workflow: Optional modified workflow steps
            
        Returns:
            Dictionary with response data
            
        Raises:
            requests.HTTPError: If the request fails
        """
        url = f"{self.base_url}/api/v1/chat/bot/conversations/{chat_id}/confirm"
        
        payload = {"confirmed": confirmed}
        if modified_workflow:
            payload["modified_workflow"] = modified_workflow
            
        try:
            response = requests.post(
                url,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            data = response.json()
            
            if response.status_code == 202:
                # Async execution started
                job_id = data["data"]["job_id"]
                print(f"Workflow submitted with job ID: {job_id}")
                return {
                    "success": True,
                    "job_id": job_id,
                    "status": "submitted",
                    "data": data
                }
                
            elif response.status_code == 200:
                # Declined or completed
                return {
                    "success": True,
                    "status": "completed",
                    "data": data
                }
                
            else:
                # Error response
                return {
                    "success": False,
                    "error": data.get("error", "Unknown error"),
                    "status_code": response.status_code,
                    "data": data
                }
                
        except requests.exceptions.RequestException as e:
            return {
                "success": False,
                "error": str(e),
                "status_code": None
            }

# Usage
client = ChatBotClient()
result = client.confirm_workflow(
    chat_id="abc123-def456",
    confirmed=True,
    modified_workflow=[
        {
            "operation": "excel/extract-columns-to-file",
            "arguments": {
                "columns": ["name", "email"],
                "remove_duplicates": True
            }
        }
    ]
)

if result["success"]:
    if result["status"] == "submitted":
        print(f"Job ID: {result['job_id']}")
    else:
        print("Workflow processed")
else:
    print(f"Error: {result['error']}")
```

---

## Frontend Integration

### Complete React Example

```typescript
import React, { useState, useEffect } from 'react';

interface WorkflowStep {
  operation: string;
  arguments: Record<string, any>;
}

interface ConfirmWorkflowProps {
  chatId: string;
  suggestedWorkflow: WorkflowStep[];
}

const ConfirmWorkflow: React.FC<ConfirmWorkflowProps> = ({
  chatId,
  suggestedWorkflow,
}) => {
  const [workflow, setWorkflow] = useState<WorkflowStep[]>(suggestedWorkflow);
  const [isProcessing, setIsProcessing] = useState(false);
  const [jobId, setJobId] = useState<string | null>(null);
  const [jobStatus, setJobStatus] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleConfirm = async () => {
    setIsProcessing(true);
    setError(null);

    try {
      const response = await fetch(
        `http://localhost:5050/api/v1/chat/bot/conversations/${chatId}/confirm`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            confirmed: true,
            modified_workflow: workflow,
          }),
        }
      );

      const data = await response.json();

      if (response.status === 202) {
        // Workflow submitted for background execution
        setJobId(data.data.job_id);
        setJobStatus('submitted');
        
        // Start polling for status
        pollJobStatus(data.data.job_id);
      } else if (response.ok) {
        setJobStatus('completed');
      } else {
        setError(data.error || 'Failed to confirm workflow');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Network error');
    } finally {
      setIsProcessing(false);
    }
  };

  const handleDecline = async () => {
    setIsProcessing(true);
    setError(null);

    try {
      const response = await fetch(
        `http://localhost:5050/api/v1/chat/bot/conversations/${chatId}/confirm`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            confirmed: false,
          }),
        }
      );

      const data = await response.json();

      if (response.ok) {
        console.log('Workflow declined:', data.data.bot_response);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Network error');
    } finally {
      setIsProcessing(false);
    }
  };

  const pollJobStatus = async (jid: string) => {
    const interval = setInterval(async () => {
      try {
        const response = await fetch(
          `http://localhost:5050/api/v1/chat/bot/conversations/${chatId}/workflow/status/${jid}`
        );
        
        const data = await response.json();
        const status = data.data.status;
        
        setJobStatus(status);
        
        if (status === 'completed' || status === 'failed' || status === 'cancelled') {
          clearInterval(interval);
          
          if (status === 'completed') {
            console.log('Workflow completed:', data.data.result);
          } else if (status === 'failed') {
            setError(data.data.error || 'Workflow failed');
          }
        }
      } catch (err) {
        console.error('Error polling status:', err);
      }
    }, 2000); // Poll every 2 seconds
  };

  return (
    <div className="confirm-workflow">
      <h3>Confirm Workflow</h3>
      
      <div className="workflow-steps">
        {workflow.map((step, index) => (
          <div key={index} className="workflow-step">
            <strong>Operation:</strong> {step.operation}
            <pre>{JSON.stringify(step.arguments, null, 2)}</pre>
          </div>
        ))}
      </div>

      {jobStatus && (
        <div className={`job-status ${jobStatus}`}>
          Job Status: {jobStatus}
        </div>
      )}

      {error && (
        <div className="error">
          Error: {error}
        </div>
      )}

      <div className="actions">
        <button
          onClick={handleConfirm}
          disabled={isProcessing}
        >
          {isProcessing ? 'Processing...' : 'Confirm'}
        </button>
        
        <button
          onClick={handleDecline}
          disabled={isProcessing}
        >
          Decline
        </button>
      </div>
    </div>
  );
};

export default ConfirmWorkflow;
```

---

## Backend Integration

### Python Service Example

```python
import requests
import time
from typing import List, Dict, Any, Optional

class PycelizeChatBotService:
    """Service class for interacting with Pycelize Chatbot API."""
    
    def __init__(self, base_url: str = "http://localhost:5050"):
        self.base_url = base_url
        self.api_base = f"{base_url}/api/v1/chat/bot"
        
    def create_conversation(self) -> str:
        """Create a new chatbot conversation."""
        response = requests.post(
            f"{self.api_base}/conversations",
            json={},
            headers={"Content-Type": "application/json"}
        )
        response.raise_for_status()
        data = response.json()
        return data["data"]["chat_id"]
    
    def send_message(self, chat_id: str, message: str) -> Dict[str, Any]:
        """Send a message to the chatbot."""
        response = requests.post(
            f"{self.api_base}/conversations/{chat_id}/message",
            json={"message": message},
            headers={"Content-Type": "application/json"}
        )
        response.raise_for_status()
        return response.json()
    
    def upload_file(self, chat_id: str, file_path: str) -> Dict[str, Any]:
        """Upload a file to the conversation."""
        with open(file_path, 'rb') as f:
            response = requests.post(
                f"{self.api_base}/conversations/{chat_id}/upload",
                files={"file": f}
            )
        response.raise_for_status()
        return response.json()
    
    def confirm_workflow(
        self,
        chat_id: str,
        confirmed: bool = True,
        modified_workflow: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """Confirm or decline a workflow."""
        payload = {"confirmed": confirmed}
        if modified_workflow:
            payload["modified_workflow"] = modified_workflow
            
        response = requests.post(
            f"{self.api_base}/conversations/{chat_id}/confirm",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        data = response.json()
        
        return {
            "status_code": response.status_code,
            "data": data,
            "job_id": data.get("data", {}).get("job_id") if response.status_code == 202 else None
        }
    
    def get_job_status(self, chat_id: str, job_id: str) -> Dict[str, Any]:
        """Get the status of a background job."""
        response = requests.get(
            f"{self.api_base}/conversations/{chat_id}/workflow/status/{job_id}"
        )
        response.raise_for_status()
        return response.json()
    
    def wait_for_completion(
        self,
        chat_id: str,
        job_id: str,
        poll_interval: int = 2,
        timeout: int = 300
    ) -> Dict[str, Any]:
        """
        Wait for a job to complete by polling its status.
        
        Args:
            chat_id: Conversation ID
            job_id: Job ID to monitor
            poll_interval: Seconds between polls (default: 2)
            timeout: Maximum seconds to wait (default: 300)
            
        Returns:
            Final job status data
            
        Raises:
            TimeoutError: If job doesn't complete within timeout
        """
        start_time = time.time()
        
        while True:
            if time.time() - start_time > timeout:
                raise TimeoutError(f"Job {job_id} did not complete within {timeout}s")
                
            status_data = self.get_job_status(chat_id, job_id)
            status = status_data["data"]["status"]
            
            print(f"Job status: {status}")
            
            if status in ["completed", "failed", "cancelled"]:
                return status_data
                
            time.sleep(poll_interval)


# Example usage
def main():
    # Initialize service
    service = PycelizeChatBotService()
    
    # Create conversation
    chat_id = service.create_conversation()
    print(f"Created conversation: {chat_id}")
    
    # Send a message
    message_response = service.send_message(
        chat_id,
        "extract columns: name, email, phone"
    )
    print(f"Bot response: {message_response['data']['bot_response']}")
    
    # Upload file
    upload_response = service.upload_file(chat_id, "data.xlsx")
    print(f"File uploaded: {upload_response['data']['filename']}")
    
    # Confirm workflow with modifications
    confirm_response = service.confirm_workflow(
        chat_id,
        confirmed=True,
        modified_workflow=[
            {
                "operation": "excel/extract-columns-to-file",
                "arguments": {
                    "columns": ["name", "email", "phone"],
                    "remove_duplicates": True,
                    "output_file": "extracted_contacts.xlsx"
                }
            }
        ]
    )
    
    if confirm_response["status_code"] == 202:
        # Workflow submitted for background execution
        job_id = confirm_response["job_id"]
        print(f"Workflow submitted with job ID: {job_id}")
        
        # Wait for completion
        try:
            final_status = service.wait_for_completion(chat_id, job_id)
            
            if final_status["data"]["status"] == "completed":
                print("✅ Workflow completed successfully!")
                result = final_status["data"]["result"]
                print(f"Output files: {result.get('output_files', [])}")
            else:
                print(f"❌ Workflow failed: {final_status['data'].get('error')}")
                
        except TimeoutError as e:
            print(f"⏱️ Timeout: {e}")
    else:
        print("Workflow processed immediately")


if __name__ == "__main__":
    main()
```

---

## Additional Resources

### Related Documentation

- [Backend Chatbot Documentation](./BACKEND_CHATBOT.md) - Complete backend implementation details
- [Frontend Chatbot Integration](./FRONTEND_CHATBOT_INTEGRATION.md) - Frontend integration guide with React components
- [Async Workflow API](../ASYNC_WORKFLOW_API.md) - Detailed async execution documentation
- [WebSocket Usage](../WEBSOCKET_USAGE.md) - WebSocket protocol and message formats
- [JSON Generation](../JSON_GENERATION.md) - JSON generation operation details
- [SQL Generation](../SQL_JSON_SYNTAX_GENERATION.md) - SQL generation syntax

### API Endpoints Reference

| Endpoint | Method | Description | Documentation |
|----------|--------|-------------|---------------|
| `/bot/conversations` | POST | Create conversation | [BACKEND_CHATBOT.md](./BACKEND_CHATBOT.md) |
| `/bot/conversations/{id}/message` | POST | Send message | [BACKEND_CHATBOT.md](./BACKEND_CHATBOT.md) |
| `/bot/conversations/{id}/upload` | POST | Upload file | [BACKEND_CHATBOT.md](./BACKEND_CHATBOT.md) |
| `/bot/conversations/{id}/confirm` | POST | Confirm workflow | **This document** |
| `/bot/conversations/{id}/workflow/status/{job_id}` | GET | Get job status | [ASYNC_WORKFLOW_API.md](../ASYNC_WORKFLOW_API.md) |
| `/bot/conversations/{id}/history` | GET | Get history | [BACKEND_CHATBOT.md](./BACKEND_CHATBOT.md) |
| `/bot/operations` | GET | Get operations | **This document** |

---

## Summary

The **Confirm Workflow** endpoint is a powerful feature that allows developers to:

1. ✅ **Confirm or decline** suggested workflows
2. 🔧 **Modify workflows** before execution with custom arguments
3. ⚡ **Execute asynchronously** with immediate response and background processing
4. 📊 **Track progress** via WebSocket or status polling
5. 🎯 **Support 15+ operations** across 8 intent types
6. 🔄 **Chain multiple operations** in a single workflow
7. 📁 **Process files** with Excel, CSV, JSON, and SQL operations

### Key Takeaways for Developers

**Frontend Developers:**
- Always handle both `202 Accepted` (async) and `200 OK` (sync/declined) responses
- Implement WebSocket connection for real-time updates
- Provide user feedback during background processing
- Allow users to modify workflows before confirmation

**Backend Developers:**
- Use the Python service class for easy integration
- Implement proper error handling and retries
- Poll job status or use WebSocket for updates
- Handle timeout scenarios gracefully

**Best Practices:**
- Validate workflow structure before submission
- Use meaningful output filenames
- Monitor job status until completion
- Handle all error scenarios
- Provide clear user feedback

---

## Support

For issues, questions, or contributions:
- **Repository**: https://github.com/pnguyen215/pycelize
- **Issues**: https://github.com/pnguyen215/pycelize/issues

---

**Last Updated:** 2026-02-09  
**API Version:** v0.0.1  
**Document Version:** 1.0.0
