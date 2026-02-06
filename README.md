# Pycelize

A professional Flask application for Excel/CSV processing with comprehensive API support.

![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)
![Flask](https://img.shields.io/badge/Flask-2.3+-green.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Project Structure](#project-structure)
- [Installation](#installation)
- [Configuration](#configuration)
- [API Documentation](#api-documentation)
- [Usage Examples](#usage-examples)
- [Chat Workflows Feature](#-chat-workflows-feature)
- [Design Patterns](#design-patterns)
- [Testing](#testing)
- [Contributing](#contributing)

## 🎯 Overview

Pycelize is a production-ready Flask application designed for processing Excel and CSV files. It provides RESTful APIs for common data operations including extraction, normalization, mapping, SQL generation, and file binding.

## ✨ Features

- **Column Extraction**: Extract data from specific columns with optional deduplication
- **CSV to Excel Conversion**: Convert CSV files to Excel format
- **Data Normalization**: Apply various normalization strategies (uppercase, trim, phone format, etc.)
- **Column Mapping**: Map and transform column names
- **SQL Generation**: Generate SQL statements with auto-increment support
- **JSON Generation**: Generate JSON from Excel with column mapping or custom templates
- **Excel-to-Excel Binding**: Bind values from source to target files
- **Search and Filter**: Advanced data filtering with multiple conditions and operators
- **Operator Suggestions**: Automatic suggestions of valid search operators based on column types
- **Chat Workflows**: Chat-based interface for sequential file processing with real-time updates
- **WebSocket Streaming**: Real-time progress updates for workflow execution
- **Conversation Management**: Create, list, retrieve, and delete chat conversations
- **Dump & Restore**: Backup and restore complete conversation data
- **SQLite Integration**: Fast metadata indexing with backup support
- **Standardized API Responses**: Consistent response format using Builder pattern

## 📁 Project Structure

```
pycelize/
├── app/
│   ├── __init__.py              # Application factory
│   ├── api/
│   │   └── routes/              # API route definitions
│   │       ├── health_routes.py
│   │       ├── excel_routes.py
│   │       ├── csv_routes.py
│   │       ├── normalization_routes.py
│   │       ├── sql_routes.py
│   │       ├── json_routes.py
│   │       ├── file_routes.py
│   │       └── chat_routes.py    # Chat Workflows API
│   ├── chat/                     # Chat Workflows module
│   │   ├── models.py             # Data models
│   │   ├── database.py           # SQLite management
│   │   ├── storage.py            # File storage
│   │   ├── repository.py         # Repository layer
│   │   ├── workflow_executor.py  # Workflow engine
│   │   ├── websocket_server.py   # WebSocket server
│   │   └── name_generator.py     # Name generator
│   ├── core/
│   │   ├── config.py            # Configuration management
│   │   ├── exceptions.py        # Custom exceptions
│   │   └── logging.py           # Logging setup
│   ├── models/
│   │   ├── enums.py             # Enumeration definitions
│   │   ├── request.py           # Request models
│   │   └── response.py          # Response models
│   ├── services/
│   │   ├── excel_service.py     # Excel operations
│   │   ├── csv_service.py       # CSV operations
│   │   ├── search_service.py    # Search and filter operations
│   │   ├── normalization_service.py
│   │   ├── sql_generation_service.py
│   │   ├── json_generation_service.py
│   │   └── binding_service.py
│   ├── builders/
│   │   ├── response_builder.py  # Builder pattern implementation
│   │   └── sql_builder.py       # SQL statement builder
│   ├── factories/
│   │   ├── normalizer_factory.py # Factory pattern implementation
│   │   └── service_factory.py
│   ├── strategies/
│   │   ├── base_strategy.py     # Strategy interface
│   │   └── normalization_strategies.py
│   └── utils/
│       ├── file_utils.py
│       ├── validators.py
│       └── helpers.py
├── configs/
│   └── application.yml          # Application configuration
├── automation/                  # Chat Workflows storage
│   ├── workflows/               # Conversation files
│   ├── dumps/                   # Conversation backups
│   └── sqlite/                  # SQLite database
│       ├── chat.db
│       └── snapshots/
├── tests/
│   ├── test_excel_service.py
│   ├── test_csv_service.py
│   └── test_normalization.py
├── uploads/                     # Uploaded files (auto-created)
├── outputs/                     # Generated files (auto-created)
├── logs/                        # Log files (auto-created)
├── requirements.txt
├── Makefile
├── run.py                       # Application entry point
└── README.md
```

## 🚀 Installation

### Prerequisites

- Python 3.9 or higher
- pip (Python package manager)

### Steps

1. **Clone the repository**

```bash
git clone https://github.com/yourusername/pycelize.git
cd pycelize
```

2. **Create a virtual environment** (recommended)

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**

```bash
make install
# or
pip install -r requirements.txt
```

4. **Run the application**

```bash
make run
# or
python run.py
```

The application will start at `http://localhost:5050`

## ⚙️ Configuration

Configuration is managed through `configs/application.yml`:

```yaml
app:
  name: "Pycelize"
  version: "v0.0.1"
  environment: "development"
  debug: true
  host: "0.0.0.0"
  port: 5050

api:
  version: "v1"
  prefix: "/api/v1"
  locale: "en_US"

file:
  upload_folder: "uploads"
  output_folder: "outputs"
  allowed_extensions:
    - ".csv"
    - ".xlsx"
    - ".xls"
  max_file_size_mb: 50

excel:
  default_sheet_name: "Sheet1"
  max_column_width: 50
  include_info_sheet: true

sql:
  supported_databases:
    - "postgresql"
    - "mysql"
    - "sqlite"
  default_database: "postgresql"
  default_batch_size: 1000

normalization:
  enabled: true
  backup_original: false
  generate_report: true

logging:
  level: "INFO"
  file: "logs/pycelize.log"
```

## 📚 API Documentation

### Base URL

```
http://localhost:5050/api/v1
```

### Response Format

All API responses follow this structure:

```json
{
  "data": { ... },
  "message": "Success message",
  "meta": {
    "api_version": "v0.0.1",
    "locale": "en_US",
    "request_id": "unique-request-id",
    "requested_time": "2024-01-29T10:00:00+00:00"
  },
  "status_code": 200,
  "total": 0
}
```

### Endpoints

#### Health Check

| Method | Endpoint        | Description     |
| ------ | --------------- | --------------- |
| GET    | `/health`       | Health check    |
| GET    | `/health/ready` | Readiness check |

#### Excel Operations

| Method | Endpoint                          | Description                                    |
| ------ | --------------------------------- | ---------------------------------------------- |
| POST   | `/excel/info`                     | Get Excel file information                     |
| POST   | `/excel/extract-columns`          | Extract column data (returns JSON)             |
| POST   | `/excel/extract-columns-to-file`  | Extract columns and save to Excel file         |
| POST   | `/excel/map-columns`              | Apply column mapping                           |
| POST   | `/excel/bind-single-key`          | Bind columns using single comparison column    |
| POST   | `/excel/bind-multi-key`           | Bind columns using multiple comparison columns |
| POST   | `/excel/search`                   | Search and filter Excel data with conditions   |
| POST   | `/excel/search/suggest-operators` | Get suggested search operators for each column |

#### CSV Operations

| Method | Endpoint                        | Description                                    |
| ------ | ------------------------------- | ---------------------------------------------- |
| POST   | `/csv/info`                     | Get CSV file information                       |
| POST   | `/csv/convert-to-excel`         | Convert CSV to Excel                           |
| POST   | `/csv/search`                   | Search and filter CSV data with conditions     |
| POST   | `/csv/search/suggest-operators` | Get suggested search operators for each column |

#### Normalization

| Method | Endpoint               | Description              |
| ------ | ---------------------- | ------------------------ |
| GET    | `/normalization/types` | List normalization types |
| POST   | `/normalization/apply` | Apply normalization      |

#### SQL Generation

| Method | Endpoint                       | Description                                        |
| ------ | ------------------------------ | -------------------------------------------------- |
| GET    | `/sql/databases`               | List supported databases                           |
| POST   | `/sql/generate`                | Generate SQL statements (returns JSON or SQL file) |
| POST   | `/sql/generate-to-text`        | Generate SQL from extracted columns to text file   |
| POST   | `/sql/generate-custom-to-text` | Generate SQL using custom template to text file    |

#### JSON Generation

| Method | Endpoint                       | Description                                  |
| ------ | ------------------------------ | -------------------------------------------- |
| POST   | `/json/generate`               | Generate JSON from Excel with column mapping |
| POST   | `/json/generate-with-template` | Generate JSON using custom template          |

#### File Operations

| Method | Endpoint                      | Description                |
| ------ | ----------------------------- | -------------------------- |
| GET    | `/files/downloads/<filename>` | Download generated files   |
| POST   | `/files/bind`                 | Bind source to target file |
| POST   | `/files/bind/preview`         | Preview binding operation  |

## 🔧 Usage Examples (cURL)

### 1. Health Check

```bash
curl http://localhost:5050/api/v1/health
```

### 2. Get Excel File Information

```bash
curl -X POST \
  -F "file=@data.xlsx" \
  http://localhost:5050/api/v1/excel/info
```

### 3. Extract Columns from Excel

```bash
curl -X POST \
  -F "file=@data.xlsx" \
  -F 'columns=["name", "email", "phone"]' \
  -F "remove_duplicates=true" \
  http://localhost:5050/api/v1/excel/extract-columns
```

### 4. Apply Column Mapping

```bash
curl -X POST \
  -F "file=@data.xlsx" \
  -F 'mapping={
    "Customer Name": "name",
    "Email Address": {"source": "email", "default": "N/A"},
    "Status": {"default": "Active"}
  }' \
  http://localhost:5050/api/v1/excel/map-columns \
  --output mapped_data.xlsx
```

### 5. Convert CSV to Excel

```bash
curl -X POST \
  -F "file=@data.csv" \
  -F "sheet_name=MyData" \
  http://localhost:5050/api/v1/csv/convert-to-excel \
  --output converted.xlsx
```

### 6. Get Normalization Types

```bash
curl http://localhost:5050/api/v1/normalization/types
```

### 7. Apply Normalization

```bash
curl -X POST \
  -F "file=@data.xlsx" \
  -F 'normalizations=[
    {"column_name": "name", "normalization_type": "trim_whitespace"},
    {"column_name": "name", "normalization_type": "title_case"},
    {"column_name": "email", "normalization_type": "lowercase"},
    {"column_name": "phone", "normalization_type": "phone_format"}
  ]' \
  http://localhost:5050/api/v1/normalization/apply \
  --output normalized.xlsx
```

### 8. Generate SQL Statements

```bash
curl -X POST \
  -F "file=@data.xlsx" \
  -F "table_name=customers" \
  -F 'column_mapping={
    "name": "Customer Name",
    "email": "Email",
    "phone": "Phone"
  }' \
  -F "database_type=postgresql" \
  -F 'auto_increment={
    "enabled": true,
    "column_name": "id",
    "increment_type": "postgresql_serial",
    "start_value": 1
  }' \
  -F "return_file=true" \
  http://localhost:5050/api/v1/sql/generate \
  --output insert_customers.sql
```

### 9. Generate SQL with Custom Template

```bash
curl -X POST \
  -F "file=@data.xlsx" \
  -F "table_name=users" \
  -F 'column_mapping={"name": "Name", "email": "Email"}' \
  -F "database_type=postgresql" \
  -F 'template=INSERT INTO users (id, name, email, created_at) VALUES ({auto_id}, {name}, {email}, {current_timestamp});' \
  -F 'auto_increment={"enabled": true, "column_name": "id", "increment_type": "manual_sequence", "sequence_name": "users_id_seq", "start_value": 100}' \
  http://localhost:5050/api/v1/sql/generate
```

### 10. Generate JSON from Excel (Standard Mapping)

```bash
curl -X POST \
  -F "file=@data.xlsx" \
  -F 'column_mapping={"Name": "full_name", "Email": "email", "Age": "age"}' \
  -F "pretty_print=true" \
  -F "null_handling=exclude" \
  -F "array_wrapper=true" \
  http://localhost:5050/api/v1/json/generate
```

**Response:**

```json
{
  "data": {
    "download_url": "/api/v1/files/downloads/data_generated_20260130_101437.json",
    "total_records": 150,
    "file_size": 45632
  },
  "message": "JSON file generated successfully",
  "status_code": 200
}
```

**Generated JSON (data_generated_20260130_101437.json):**

```json
[
  {
    "full_name": "Alice",
    "email": "alice@example.com",
    "age": 25
  },
  {
    "full_name": "Bob",
    "email": "bob@example.com",
    "age": 30
  }
]
```

### 11. Generate JSON with Custom Template

```bash
curl -X POST \
  -F "file=@users.xlsx" \
  -F 'template={"user":{"id":"{user_id}","name":"{first_name} {last_name}"},"contact":{"email":"{email}"}}' \
  -F 'column_mapping={"user_id":"UserID","first_name":"FirstName","last_name":"LastName","email":"Email"}' \
  -F "aggregation_mode=array" \
  -F "pretty_print=true" \
  http://localhost:5050/api/v1/json/generate-with-template
```

**Generated JSON:**

```json
[
  {
    "user": {
      "id": "1",
      "name": "Alice Smith"
    },
    "contact": {
      "email": "alice@example.com"
    }
  },
  {
    "user": {
      "id": "2",
      "name": "Bob Jones"
    },
    "contact": {
      "email": "bob@example.com"
    }
  }
]
```

### 12. Bind Excel Files

```bash
curl -X POST \
  -F "source_file=@source_data.xlsx" \
  -F "target_file=@template.xlsx" \
  -F 'column_mapping={
    "Target_Name": "Source_Name",
    "Target_Email": "Source_Email",
    "Target_Phone": "Source_Phone"
  }' \
  http://localhost:5050/api/v1/files/bind \
  --output bound_result.xlsx
```

### 13. Preview Binding Operation

```bash
curl -X POST \
  -F "source_file=@source.xlsx" \
  -F "target_file=@target.xlsx" \
  -F 'column_mapping={"Target_Col": "Source_Col"}' \
  http://localhost:5050/api/v1/files/bind/preview
```

### 14. Extract Columns to Excel File (New Feature)

Extract specific columns from an Excel file and save the result to a new Excel file. Returns a download URL for the generated file.

**Description:** This endpoint extracts specified columns from an uploaded Excel file and creates a new Excel file containing only those columns. The extracted data can optionally have duplicates removed. The response includes a download URL in the standardized format.

**Request Parameters:**

- `file`: Excel file to extract columns from
- `columns`: JSON array of column names to extract
- `remove_duplicates`: Optional boolean to remove duplicate rows (default: false)

**Response Example:**

```json
{
  "data": {
    "download_url": "http://127.0.0.1:5050/api/v1/files/downloads/extracted_columns_20260129_120000.xlsx"
  },
  "message": "Extracted Excel file generated successfully",
  "status_code": 200
}
```

**cURL Example:**

```bash
curl -X POST \
  -F "file=@data.xlsx" \
  -F 'columns=["name", "email", "phone"]' \
  -F "remove_duplicates=true" \
  http://localhost:5050/api/v1/excel/extract-columns-to-file
```

### 13. Generate SQL to Text File - Standard (New Feature)

Generate SQL INSERT statements from Excel data and save to a text file. This endpoint supports column extraction, column mapping, and auto-increment primary key generation.

**Description:** This endpoint reads an Excel file, optionally extracts specific columns, applies column mapping, and generates SQL INSERT statements with optional auto-increment ID support. The generated SQL is saved to a `.txt` file and a download URL is returned.

**Request Parameters:**

- `file`: Excel file with source data
- `columns`: Optional JSON array of column names to extract
- `table_name`: Target database table name
- `column_mapping`: JSON object mapping SQL column names to Excel column names
- `database_type`: Database type (postgresql, mysql, sqlite) - default: postgresql
- `auto_increment`: Optional JSON object for auto-increment configuration
- `remove_duplicates`: Optional boolean to remove duplicate rows (default: false)

**Auto-increment Configuration:**

```json
{
  "enabled": true,
  "column_name": "id",
  "increment_type": "postgresql_serial",
  "start_value": 1
}
```

**Response Example:**

```json
{
  "data": {
    "download_url": "http://127.0.0.1:5050/api/v1/files/downloads/sql_statements_20260129_120000.txt"
  },
  "message": "SQL text file generated successfully",
  "status_code": 200
}
```

**cURL Example:**

```bash
curl -X POST \
  -F "file=@data.xlsx" \
  -F 'columns=["Name", "Email", "Phone"]' \
  -F "table_name=customers" \
  -F 'column_mapping={"name": "Name", "email": "Email", "phone": "Phone"}' \
  -F "database_type=postgresql" \
  -F 'auto_increment={"enabled": true, "column_name": "id", "start_value": 1}' \
  -F "remove_duplicates=false" \
  http://localhost:5050/api/v1/sql/generate-to-text
```

**Generated SQL Example:**

```sql
-- Generated by Pycelize
-- Generated at: 2026-01-29T15:03:39.969444
-- Total statements: 7

BEGIN;
INSERT INTO customers (name, email, phone) VALUES ('John Doe', 'john@example.com', '555-1234');
INSERT INTO customers (name, email, phone) VALUES ('Jane Smith', 'jane@example.com', '555-5678');
COMMIT;
```

### 14. Generate SQL to Text File - Custom Template (New Feature)

Generate SQL statements using a custom template with placeholder substitution and save to a text file.

**Description:** This endpoint provides full flexibility for SQL generation by accepting a custom SQL template string with placeholders. Placeholders are substituted with actual values from the Excel data. Supports auto-increment IDs and timestamp placeholders.

**Request Parameters:**

- `file`: Excel file with source data
- `columns`: Optional JSON array of column names to extract
- `template`: Custom SQL template string with placeholders
- `column_mapping`: JSON object mapping placeholder names to Excel columns
- `auto_increment`: Optional JSON object for auto-increment configuration
- `remove_duplicates`: Optional boolean to remove duplicate rows (default: false)

**Template Placeholders:**

- `{placeholder_name}`: Replaced with value from mapped column
- `{auto_id}`: Auto-incremented ID value (if auto_increment is enabled)
- `{current_timestamp}`: Replaced with CURRENT_TIMESTAMP

**Response Example:**

```json
{
  "data": {
    "download_url": "http://127.0.0.1:5050/api/v1/files/downloads/custom_sql_20260129_120000.txt"
  },
  "message": "Custom SQL text file generated successfully",
  "status_code": 200
}
```

**cURL Example:**

```bash
curl -X POST \
  -F "file=@data.xlsx" \
  -F 'columns=["Name", "Email"]' \
  -F 'template=INSERT INTO users (id, name, email, created_at) VALUES ({auto_id}, {name}, {email}, {current_timestamp});' \
  -F 'column_mapping={"name": "Name", "email": "Email"}' \
  -F 'auto_increment={"enabled": true, "column_name": "id", "start_value": 100}' \
  http://localhost:5050/api/v1/sql/generate-custom-to-text
```

**Generated SQL Example:**

```sql
-- Generated by Pycelize
-- Generated at: 2026-01-29T15:04:06.412720
-- Total statements: 3

INSERT INTO users (id, name, email, created_at) VALUES (100, 'John Doe', 'john@example.com', CURRENT_TIMESTAMP);
INSERT INTO users (id, name, email, created_at) VALUES (101, 'Jane Smith', 'jane@example.com', CURRENT_TIMESTAMP);
INSERT INTO users (id, name, email, created_at) VALUES (102, 'Bob Wilson', 'bob@example.com', CURRENT_TIMESTAMP);
```

### 15. Download Generated Files

Download files that were generated by other endpoints (extracted Excel files, SQL text files, etc.).

**Description:** This endpoint serves generated files from the outputs folder. Files are automatically cleaned up after a certain period. The filename should match the one provided in the download URL from other endpoints.

**cURL Example:**

```bash
# Download extracted Excel file
curl http://localhost:5050/api/v1/files/downloads/extracted_columns_20260129_120000.xlsx \
  --output result.xlsx

# Download SQL text file
curl http://localhost:5050/api/v1/files/downloads/sql_statements_20260129_120000.txt \
  --output inserts.sql
```

## 🔍 Search and Filter APIs

The Search and Filter APIs provide powerful data filtering capabilities for Excel and CSV files. You can apply multiple search conditions across different columns with various operators, and export the filtered results in different formats.

### API 1: Search and Filter Data

Search and filter Excel or CSV files based on multiple conditions with support for different operators and logical combinations.

#### Excel Search Endpoint

**Endpoint:** `POST /api/v1/excel/search`

**Description:** Filter Excel file data using multiple conditions across columns. Supports various operators (equals, contains, greater_than, etc.) and logical combinations (AND/OR). Results can be exported as Excel, CSV, or JSON.

**Request Parameters:**

- `file`: Excel file (required)
- `conditions`: JSON array of search conditions (required)
  - Each condition contains: `column`, `operator`, `value`
- `logic`: Logical operator between conditions - "AND" or "OR" (default: "AND")
- `output_format`: Output file format - "xlsx", "csv", or "json" (default: "xlsx")
- `output_filename`: Optional custom output filename

**Supported Operators:**

**String Operators:**

- `equals` - Exact match
- `not_equals` - Not equal to
- `contains` - Contains substring (case-insensitive)
- `not_contains` - Does not contain substring
- `starts_with` - Starts with string
- `ends_with` - Ends with string
- `is_empty` - Field is empty or null
- `is_not_empty` - Field is not empty

**Numeric Operators:**

- `equals` - Equal to number
- `not_equals` - Not equal to number
- `greater_than` - Greater than
- `greater_than_or_equal` - Greater than or equal
- `less_than` - Less than
- `less_than_or_equal` - Less than or equal
- `between` - Between two values (value must be [min, max])

**Date Operators:**

- `equals` - Exact date match
- `before` - Before date
- `after` - After date
- `between` - Between two dates

**Response Example:**

```json
{
  "data": {
    "download_url": "http://localhost:5050/api/v1/files/downloads/search_results_20260206_120000.xlsx",
    "total_rows": 1000,
    "filtered_rows": 45,
    "conditions_applied": 2
  },
  "message": "Search completed successfully. 45 rows matched.",
  "meta": {
    "api_version": "v0.0.1",
    "locale": "en_US",
    "request_id": "abc123...",
    "requested_time": "2026-02-06T12:00:00+00:00"
  },
  "status_code": 200,
  "total": 0
}
```

**cURL Examples:**

**Simple equals search:**

```bash
curl -X POST \
  -F "file=@data.xlsx" \
  -F 'conditions=[{"column": "customer_id", "operator": "equals", "value": "021201"}]' \
  -F "logic=AND" \
  -F "output_format=xlsx" \
  http://localhost:5050/api/v1/excel/search
```

**Multiple conditions with AND logic:**

```bash
curl -X POST \
  -F "file=@sales_data.xlsx" \
  -F 'conditions=[
    {"column": "status", "operator": "equals", "value": "active"},
    {"column": "amount", "operator": "greater_than", "value": 1000}
  ]' \
  -F "logic=AND" \
  -F "output_format=csv" \
  http://localhost:5050/api/v1/excel/search
```

**Search with OR logic:**

```bash
curl -X POST \
  -F "file=@customers.xlsx" \
  -F 'conditions=[
    {"column": "region", "operator": "equals", "value": "North"},
    {"column": "region", "operator": "equals", "value": "South"}
  ]' \
  -F "logic=OR" \
  -F "output_format=json" \
  http://localhost:5050/api/v1/excel/search
```

**Search with contains operator:**

```bash
curl -X POST \
  -F "file=@products.xlsx" \
  -F 'conditions=[{"column": "name", "operator": "contains", "value": "phone"}]' \
  -F "logic=AND" \
  http://localhost:5050/api/v1/excel/search
```

**Search with between operator:**

```bash
curl -X POST \
  -F "file=@transactions.xlsx" \
  -F 'conditions=[{"column": "amount", "operator": "between", "value": [100, 500]}]' \
  -F "logic=AND" \
  http://localhost:5050/api/v1/excel/search
```

#### CSV Search Endpoint

**Endpoint:** `POST /api/v1/csv/search`

**Description:** Same functionality as Excel search but for CSV files. All parameters, operators, and response format are identical.

**cURL Example:**

```bash
curl -X POST \
  -F "file=@data.csv" \
  -F 'conditions=[
    {"column": "email", "operator": "contains", "value": "@gmail.com"},
    {"column": "age", "operator": "greater_than", "value": 25}
  ]' \
  -F "logic=AND" \
  -F "output_format=csv" \
  http://localhost:5050/api/v1/csv/search
```

### API 2: Suggest Search Operators

Get suggested search operators for each column in your file based on the column's data type. This helps you understand which operators are valid for each column.

#### Excel Suggest Operators Endpoint

**Endpoint:** `POST /api/v1/excel/search/suggest-operators`

**Description:** Analyzes an Excel file and suggests valid search operators for each column based on the detected data type.

**Request Parameters:**

- `file`: Excel file (required)

**Response Example:**

```json
{
  "data": {
    "customer_id": {
      "type": "object",
      "operators": [
        "equals",
        "not_equals",
        "contains",
        "not_contains",
        "starts_with",
        "ends_with",
        "is_empty",
        "is_not_empty"
      ]
    },
    "amount": {
      "type": "float64",
      "operators": [
        "equals",
        "not_equals",
        "greater_than",
        "greater_than_or_equal",
        "less_than",
        "less_than_or_equal",
        "between"
      ]
    },
    "created_at": {
      "type": "object",
      "operators": [
        "equals",
        "not_equals",
        "contains",
        "not_contains",
        "starts_with",
        "ends_with",
        "is_empty",
        "is_not_empty"
      ]
    },
    "is_active": {
      "type": "object",
      "operators": [
        "equals",
        "not_equals",
        "contains",
        "not_contains",
        "starts_with",
        "ends_with",
        "is_empty",
        "is_not_empty"
      ]
    }
  },
  "message": "Operator suggestions generated successfully",
  "meta": {
    "api_version": "v0.0.1",
    "locale": "en_US",
    "request_id": "xyz789...",
    "requested_time": "2026-02-06T12:00:00+00:00"
  },
  "status_code": 200,
  "total": 0
}
```

**cURL Example:**

```bash
curl -X POST \
  -F "file=@data.xlsx" \
  http://localhost:5050/api/v1/excel/search/suggest-operators
```

#### CSV Suggest Operators Endpoint

**Endpoint:** `POST /api/v1/csv/search/suggest-operators`

**Description:** Same functionality as Excel suggest operators but for CSV files.

**cURL Example:**

```bash
curl -X POST \
  -F "file=@data.csv" \
  http://localhost:5050/api/v1/csv/search/suggest-operators
```

### Search API Use Cases

**1. Filter Active Customers with High Value:**

```bash
curl -X POST \
  -F "file=@customers.xlsx" \
  -F 'conditions=[
    {"column": "status", "operator": "equals", "value": "active"},
    {"column": "lifetime_value", "operator": "greater_than", "value": 10000}
  ]' \
  -F "logic=AND" \
  http://localhost:5050/api/v1/excel/search
```

**2. Find All Gmail Users:**

```bash
curl -X POST \
  -F "file=@users.csv" \
  -F 'conditions=[{"column": "email", "operator": "ends_with", "value": "@gmail.com"}]' \
  http://localhost:5050/api/v1/csv/search
```

**3. Filter Products in Price Range:**

```bash
curl -X POST \
  -F "file=@products.xlsx" \
  -F 'conditions=[{"column": "price", "operator": "between", "value": [50, 150]}]' \
  -F "output_format=json" \
  http://localhost:5050/api/v1/excel/search
```

**4. Find Records with Empty Fields:**

```bash
curl -X POST \
  -F "file=@data.xlsx" \
  -F 'conditions=[{"column": "phone", "operator": "is_empty", "value": null}]' \
  http://localhost:5050/api/v1/excel/search
```

## 📊 Excel Binding APIs

### Overview

The Excel Binding APIs provide advanced column binding capabilities that allow you to merge data from two Excel files based on matching column values. This is useful for enriching data with reference information, adding lookup values, or combining related datasets.

### Use Cases

- **Data Enrichment**: Add customer details (email, phone) to transaction records by matching customer IDs
- **Reference Lookups**: Append product information to order data using product codes
- **Data Integration**: Merge employee data from multiple sources using composite keys (first name + last name)

### 16. Bind Excel Files - Single Key

Bind columns from a bind file to a source file using a single comparison column. This performs a left join operation, preserving all rows from the source file.

**Description:**

- Takes two Excel files: source file (File A) and bind file (File B)
- Matches rows based on a single comparison column
- Appends specified columns from File B to File A
- Preserves all original columns and data in File A
- Returns NaN for rows without matches

**Request Parameters:**

- `source_file`: Excel file to be extended with new columns (File A)
- `bind_file`: Excel file containing data to bind (File B)
- `comparison_column`: Column name used to match rows between files
- `bind_columns`: JSON array of column names to append from File B
- `output_filename`: Optional custom output filename

**Response Example:**

```json
{
  "data": {
    "download_url": "http://localhost:5050/api/v1/files/downloads/source_data_bound_single_20260129_143022.xlsx"
  },
  "message": "Excel binding completed successfully",
  "meta": {
    "api_version": "v0.0.1",
    "locale": "en_US",
    "request_id": "abc123...",
    "requested_time": "2026-01-29T14:30:22+00:00"
  },
  "status_code": 200,
  "total": 0
}
```

**cURL Example:**

```bash
curl -X POST \
  -F "source_file=@source.xlsx" \
  -F "bind_file=@bind.xlsx" \
  -F "comparison_column=s_1_name" \
  -F 'bind_columns=["s_1_id"]' \
  http://localhost:5050/api/v1/excel/bind-single-key
```

**Example Scenario:**

**File A (source.xlsx) - Before:**
| s_1_name | existing_col |
|----------|--------------|
| Alice | data1 |
| Bob | data2 |
| Charlie | data3 |

**File B (bind.xlsx):**
| s_1_name | s_1_id |
|----------|--------|
| Alice | 101 |
| Bob | 102 |
| David | 103 |

**Result (source_data_bound_single.xlsx) - After:**
| s_1_name | existing_col | s_1_id |
|----------|--------------|--------|
| Alice | data1 | 101 |
| Bob | data2 | 102 |
| Charlie | data3 | NaN |

**Note:** Charlie's row remains but has NaN for s_1_id since there's no match in File B.

### 17. Bind Excel Files - Multi Key (Composite Key)

Bind columns from a bind file to a source file using multiple comparison columns for matching. This is useful when a single column isn't unique enough for matching.

**Description:**

- Similar to single-key binding but uses multiple columns together as a composite key
- Matches rows only when ALL comparison columns match
- Useful for matching on combinations like (first_name + last_name) or (country + city)
- All original data in File A is preserved

**Request Parameters:**

- `source_file`: Excel file to be extended (File A)
- `bind_file`: Excel file with data to bind (File B)
- `comparison_columns`: JSON array of column names used together for matching
- `bind_columns`: JSON array of column names to append from File B
- `output_filename`: Optional custom output filename

**Response Example:**

```json
{
  "data": {
    "download_url": "http://localhost:5050/api/v1/files/downloads/source_data_bound_multi_20260129_143530.xlsx"
  },
  "message": "Excel binding completed successfully",
  "meta": {
    "api_version": "v0.0.1",
    "locale": "en_US",
    "request_id": "xyz789...",
    "requested_time": "2026-01-29T14:35:30+00:00"
  },
  "status_code": 200,
  "total": 0
}
```

**cURL Example:**

```bash
curl -X POST \
  -F "source_file=@source.xlsx" \
  -F "bind_file=@bind.xlsx" \
  -F 'comparison_columns=["first_name", "last_name"]' \
  -F 'bind_columns=["email", "phone"]' \
  http://localhost:5050/api/v1/excel/bind-multi-key
```

**Example Scenario:**

**File A (source.xlsx) - Before:**
| first_name | last_name | department |
|------------|-----------|------------|
| John | Doe | IT |
| Jane | Smith | HR |
| John | Smith | Finance |

**File B (bind.xlsx):**
| first_name | last_name | email | phone |
|------------|-----------|--------------------|--------------|
| John | Doe | john.doe@corp.com | 555-0101 |
| Jane | Smith | jane.smith@corp.com| 555-0102 |
| Mike | Johnson | mike.j@corp.com | 555-0103 |

**Result (source_data_bound_multi.xlsx) - After:**
| first_name | last_name | department | email | phone |
|------------|-----------|------------|---------------------|----------|
| John | Doe | IT | john.doe@corp.com | 555-0101 |
| Jane | Smith | HR | jane.smith@corp.com | 555-0102 |
| John | Smith | Finance | NaN | NaN |

**Note:** "John Smith" in File A doesn't match any row in File B (only "John Doe" and "Jane Smith" exist), so email and phone are NaN.

### Binding Features & Behavior

**Key Features:**

- **Preserves Original Data**: All columns and rows from source file are kept
- **Left Join Logic**: All source rows appear in output, matched or not
- **Duplicate Handling**: If bind file has duplicate keys, first match is used
- **NaN for Unmatched**: Rows without matches get NaN in bound columns
- **Column Conflict Detection**: Raises error if bind columns already exist in source
- **Type Preservation**: Data types are maintained during binding

**Error Handling:**

- `422 Validation Error`: Missing columns, column conflicts, invalid JSON
- `400 File Processing Error`: File read/write failures
- `500 Server Error`: Unexpected internal errors

**Performance Tips:**

- Remove duplicates from bind file before uploading for faster processing
- Use single-key binding when possible (faster than multi-key)
- Consider file size limits when working with large datasets

## 📄 JSON Generation Features

The JSON generation feature provides flexible ways to transform Excel data into JSON format with support for standard column mapping and custom template-based generation.

### Standard JSON Generation

Generate JSON from Excel data by mapping Excel columns to JSON keys.

**Parameters:**

- `file`: Excel file (required)
- `column_mapping`: JSON object mapping Excel columns to JSON keys (optional, uses all columns if not provided)
- `columns`: JSON array of column names to extract before generation (optional)
- `pretty_print`: Boolean to format JSON with indentation (default: true)
- `null_handling`: Strategy for null values - "include", "exclude", "default" (default: "include")
- `array_wrapper`: Boolean to wrap objects in array (default: true)
- `output_filename`: Optional custom filename

**Null Handling Strategies:**

- `include`: Keep null values as `null` in JSON
- `exclude`: Remove keys with null values from JSON objects
- `default`: Replace null values with empty strings

**Example:**

```bash
curl -X POST \
  -F "file=@data.xlsx" \
  -F 'column_mapping={"Name": "full_name", "Email": "email", "Age": "age"}' \
  -F "null_handling=exclude" \
  http://localhost:5050/api/v1/json/generate
```

### Template-Based JSON Generation

Generate JSON using custom templates with placeholder substitution. This allows for nested structures and complex JSON schemas.

**Parameters:**

- `file`: Excel file (required)
- `template`: JSON template string or object with placeholders (required)
- `column_mapping`: JSON object mapping placeholders to Excel columns (required)
- `pretty_print`: Boolean to format JSON with indentation (default: true)
- `aggregation_mode`: Output format - "array", "single", "nested" (default: "array")
- `output_filename`: Optional custom filename

**Aggregation Modes:**

- `array`: Returns array of objects (default)
- `single`: Returns single object (for one row) or array (for multiple rows)
- `nested`: Returns object with `items` array and `count` field

**Placeholder Syntax:**

- `{column_name}`: Basic substitution
- `{column_name:int}`: Convert to integer
- `{column_name:float}`: Convert to float
- `{column_name:bool}`: Convert to boolean
- `{column_name:datetime}`: Keep as datetime string
- `{column_name|default}`: Use default if value is null

**Template Examples:**

1. **Simple Template:**

```json
{
  "id": "{user_id}",
  "name": "{full_name}",
  "email": "{email_address}"
}
```

2. **Nested Structure:**

```json
{
  "user": {
    "personal": {
      "firstName": "{first_name}",
      "lastName": "{last_name}"
    },
    "contact": {
      "email": "{email}",
      "phone": "{phone}"
    }
  },
  "metadata": {
    "source": "excel_import"
  }
}
```

3. **With Type Conversion:**

```json
{
  "id": "{user_id:int}",
  "score": "{score:float}",
  "active": "{is_active:bool}"
}
```

4. **With Default Values:**

```json
{
  "name": "{name}",
  "email": "{email|no-email@example.com}",
  "status": "{status|pending}"
}
```

**Example Usage:**

```bash
curl -X POST \
  -F "file=@users.xlsx" \
  -F 'template={"user":{"id":"{user_id}","name":"{first} {last}"},"contact":{"email":"{email}"}}' \
  -F 'column_mapping={"user_id":"UserID","first":"FirstName","last":"LastName","email":"Email"}' \
  -F "aggregation_mode=nested" \
  http://localhost:5050/api/v1/json/generate-with-template
```

### Edge Cases Handled

- **Empty DataFrame**: Returns empty array `[]`
- **Missing Columns**: Returns 422 validation error with details
- **Invalid Template**: Returns 422 validation error
- **Null/NaN Values**: Handled according to strategy
- **Special Characters**: Properly escaped in JSON
- **Mixed Data Types**: Automatic type conversion

### Response Format

Both endpoints return the same response structure:

```json
{
  "data": {
    "download_url": "/api/v1/files/downloads/data_generated_20260130_101437.json",
    "total_records": 150,
    "file_size": 45632
  },
  "message": "JSON file generated successfully",
  "meta": {
    "api_version": "v0.0.1",
    "locale": "en_US",
    "request_id": "abc123...",
    "requested_time": "2026-01-30T10:14:37.232310+00:00"
  },
  "status_code": 200,
  "total": 0
}
```

### File Naming Convention

Generated files follow the pattern:

- Standard generation: `{original_name}_generated_{timestamp}.json`
- Template generation: `{original_name}_generated_template_{timestamp}.json`

Example: `data_generated_20260130_143022.json`

## 💬 Chat Workflows Feature

### Overview

The Chat Workflows feature provides a chat-based interface for processing Excel/CSV files through sequential workflow operations. Users can upload files, define processing steps, and execute them as workflows with real-time progress updates via WebSocket streaming.

**Key Features:**

- ✅ **Chat-based workflow interface** - Intuitive conversation-driven file processing
- ✅ **Sequential step execution** - Chain multiple operations with automatic input/output passing
- ✅ **WebSocket streaming** - Real-time progress updates and status notifications
- ✅ **File storage** - Organized conversation-based file management
- ✅ **SQLite database** - Fast metadata indexing and conversation tracking
- ✅ **Dump & restore** - Backup and restore complete conversations
- ✅ **Auto-generated names** - Unique participant names (sea animals, land animals, celestial objects)
- ✅ **Partitioning** - Time-based conversation organization for scalability

### Architecture

**Design Patterns:**

- **Chain of Responsibility Pattern** - Workflow step execution
- **Repository Pattern** - Data access abstraction
- **Strategy Pattern** - Flexible partitioning strategies

**Components:**

- **Conversation Repository** - Manages conversation CRUD operations
- **Workflow Executor** - Executes sequential workflow steps
- **WebSocket Server** - Real-time communication and streaming
- **SQLite Database** - Conversation metadata and indexing
- **File Storage** - Organized file management with partitioning

### Configuration

Chat Workflows configuration in `configs/application.yml`:

```yaml
chat_workflows:
  # Enable/disable the feature
  enabled: true

  # Maximum concurrent WebSocket connections
  max_connections: 10

  # WebSocket server settings
  websocket:
    host: "127.0.0.1"
    port: 5051
    ping_interval: 30
    ping_timeout: 10

  # Storage paths
  storage:
    workflows_path: "./automation/workflows"
    dumps_path: "./automation/dumps"
    sqlite_path: "./automation/sqlite/chat.db"

  # Backup configuration
  backup:
    enabled: true
    interval_minutes: 60
    snapshot_path: "./automation/sqlite/snapshots"
    retention_days: 30

  # Conversation partitioning
  partition:
    enabled: true
    strategy: "time-based"  # Options: time-based, hash-based, folder-based
    subfolder_format: "%Y/%m"

  # File handling
  file:
    max_upload_size_mb: 50
    allowed_extensions: [".csv", ".xlsx", ".xls", ".json"]
    chunk_size_bytes: 8192

  # Workflow execution
  execution:
    max_steps: 50
    step_timeout_seconds: 300
    stream_progress: true
    save_intermediate_files: true

  # Dump and restore
  dump:
    compression: "gzip"
    include_metadata: true
    include_logs: true
```

### REST API Endpoints

#### 1. Create Conversation

**Endpoint:** `POST /api/v1/chat/workflows`

**Description:** Create a new chat workflow conversation with auto-generated participant name.

**Response Example:**

```json
{
  "data": {
    "chat_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "participant_name": "BlueWhale-4821",
    "status": "created",
    "messages": [],
    "workflow_steps": [],
    "uploaded_files": [],
    "output_files": [],
    "created_at": "2026-02-06T17:00:00Z",
    "updated_at": "2026-02-06T17:00:00Z"
  },
  "message": "Conversation created successfully",
  "status_code": 201
}
```

**cURL Example:**

```bash
curl -X POST http://localhost:5050/api/v1/chat/workflows
```

#### 2. List Conversations

**Endpoint:** `GET /api/v1/chat/workflows`

**Query Parameters:**
- `status` (optional): Filter by status (created, active, processing, completed, failed, archived)
- `limit` (optional): Maximum results (default: 100)
- `offset` (optional): Pagination offset (default: 0)

**Response Example:**

```json
{
  "data": {
    "conversations": [
      {
        "chat_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
        "participant_name": "BlueWhale-4821",
        "status": "completed",
        "created_at": "2026-02-06T17:00:00Z",
        "updated_at": "2026-02-06T17:30:00Z"
      }
    ],
    "count": 1
  },
  "message": "Conversations retrieved successfully",
  "status_code": 200
}
```

**cURL Examples:**

```bash
# List all conversations
curl http://localhost:5050/api/v1/chat/workflows

# Filter by status
curl "http://localhost:5050/api/v1/chat/workflows?status=completed&limit=10"
```

#### 3. Get Conversation Details

**Endpoint:** `GET /api/v1/chat/workflows/{chat_id}`

**Description:** Retrieve complete conversation details including messages, steps, and files.

**Response Example:**

```json
{
  "data": {
    "chat_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "participant_name": "BlueWhale-4821",
    "status": "completed",
    "messages": [...],
    "workflow_steps": [...],
    "uploaded_files": ["/path/to/data.xlsx"],
    "output_files": ["/path/to/result.xlsx"],
    "created_at": "2026-02-06T17:00:00Z",
    "updated_at": "2026-02-06T17:30:00Z"
  },
  "message": "Conversation retrieved successfully",
  "status_code": 200
}
```

**cURL Example:**

```bash
curl http://localhost:5050/api/v1/chat/workflows/a1b2c3d4-e5f6-7890-abcd-ef1234567890
```

#### 4. Upload File to Conversation

**Endpoint:** `POST /api/v1/chat/workflows/{chat_id}/upload`

**Description:** Upload a file to a conversation for processing. Returns an absolute download URL that can be used directly.

**Request Parameters:**
- `file`: File to upload (multipart/form-data)

**Response Example:**

```json
{
  "data": {
    "file_path": "./automation/workflows/2026/02/a1b2c3d4.../uploads/data.xlsx",
    "filename": "data.xlsx",
    "download_url": "http://localhost:5050/api/v1/chat/workflows/a1b2c3d4-e5f6-7890-abcd-ef1234567890/files/data.xlsx"
  },
  "message": "File uploaded successfully",
  "status_code": 200
}
```

**cURL Example:**

```bash
curl -X POST \
  -F "file=@data.xlsx" \
  http://localhost:5050/api/v1/chat/workflows/a1b2c3d4-e5f6-7890-abcd-ef1234567890/upload
```

#### 5. Execute Workflow Steps

**Endpoint:** `POST /api/v1/chat/workflows/{chat_id}/execute`

**Description:** Execute sequential workflow steps with automatic input/output chaining. Each output file includes an absolute download URL. Real-time progress updates are sent via WebSocket.

**Request Body:**

```json
{
  "steps": [
    {
      "operation": "excel/extract-columns",
      "arguments": {
        "columns": ["customer_id", "amount", "status"],
        "remove_duplicates": false
      }
    },
    {
      "operation": "excel/search",
      "arguments": {
        "conditions": [
          {"column": "status", "operator": "equals", "value": "active"}
        ],
        "logic": "AND",
        "output_format": "excel"
      }
    },
    {
      "operation": "normalization/apply",
      "arguments": {
        "normalizations": [
          {
            "column": "customer_id",
            "type": "uppercase"
          }
        ]
      }
    }
  ]
}
```

**Response Example:**

```json
{
  "data": {
    "results": [
      {
        "output_file_path": "./automation/workflows/.../uploads/step1_output.xlsx",
        "download_url": "http://localhost:5050/api/v1/chat/workflows/a1b2c3d4.../files/step1_output.xlsx"
      },
      {
        "output_file_path": "./automation/workflows/.../uploads/step2_output.xlsx",
        "download_url": "http://localhost:5050/api/v1/chat/workflows/a1b2c3d4.../files/step2_output.xlsx"
      }
    ],
    "output_files": [
      {
        "file_path": "./automation/workflows/.../outputs/step1_output.xlsx",
        "download_url": "http://localhost:5050/api/v1/chat/workflows/a1b2c3d4.../files/step1_output.xlsx"
      },
      {
        "file_path": "./automation/workflows/.../outputs/step2_output.xlsx",
        "download_url": "http://localhost:5050/api/v1/chat/workflows/a1b2c3d4.../files/step2_output.xlsx"
      }
    ]
  },
  "message": "Workflow executed successfully",
  "status_code": 200
}
```

**cURL Example:**

```bash
curl -X POST \
  -H "Content-Type: application/json" \
  -d '{
    "steps": [
      {
        "operation": "excel/extract-columns-to-file",
        "arguments": {
          "columns": ["customer_id", "amount"],
          "remove_duplicates": true
        }
      }
    ]
  }' \
  http://localhost:5050/api/v1/chat/workflows/a1b2c3d4-e5f6-7890-abcd-ef1234567890/execute
```

#### 6. Delete Conversation

**Endpoint:** `DELETE /api/v1/chat/workflows/{chat_id}`

**Description:** Delete a conversation and all associated files.

**Response Example:**

```json
{
  "data": {
    "chat_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
  },
  "message": "Conversation deleted successfully",
  "status_code": 200
}
```

**cURL Example:**

```bash
curl -X DELETE http://localhost:5050/api/v1/chat/workflows/a1b2c3d4-e5f6-7890-abcd-ef1234567890
```

#### 7. Dump Conversation

**Endpoint:** `POST /api/v1/chat/workflows/{chat_id}/dump`

**Description:** Create a compressed archive of all conversation data including files, messages, and metadata. Returns an absolute download URL.

**Response Example:**

```json
{
  "data": {
    "dump_file": "a1b2c3d4-e5f6-7890-abcd-ef1234567890_20260206_173000.tar.gz",
    "download_url": "http://localhost:5050/api/v1/chat/downloads/a1b2c3d4-e5f6-7890-abcd-ef1234567890_20260206_173000.tar.gz"
  },
  "message": "Conversation dumped successfully",
  "status_code": 200
}
```

**cURL Example:**

```bash
# Create dump
curl -X POST http://localhost:5050/api/v1/chat/workflows/a1b2c3d4-e5f6-7890-abcd-ef1234567890/dump

# Download the dump file using the returned URL
curl -O "http://localhost:5050/api/v1/chat/downloads/a1b2c3d4-e5f6-7890-abcd-ef1234567890_20260206_173000.tar.gz"
```

#### 8. Restore Conversation

**Endpoint:** `POST /api/v1/chat/workflows/restore`

**Description:** Restore a conversation from a dump file.

**Request Parameters:**
- `dump_file`: Dump file to restore (multipart/form-data)

**Response Example:**

```json
{
  "data": {
    "chat_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "participant_name": "BlueWhale-4821",
    "status": "completed",
    ...
  },
  "message": "Conversation restored successfully",
  "status_code": 200
}
```

**cURL Example:**

```bash
curl -X POST \
  -F "dump_file=@conversation_dump.tar.gz" \
  http://localhost:5050/api/v1/chat/workflows/restore
```

#### 9. Backup SQLite Database

**Endpoint:** `POST /api/v1/chat/sqlite/backup`

**Description:** Create a snapshot backup of the SQLite database.

**Response Example:**

```json
{
  "data": {
    "backup_file": "chat_backup_20260206_173000.db",
    "path": "./automation/sqlite/snapshots/chat_backup_20260206_173000.db"
  },
  "message": "Database backup created successfully",
  "status_code": 200
}
```

**cURL Example:**

```bash
curl -X POST http://localhost:5050/api/v1/chat/sqlite/backup
```

#### 10. Download Workflow File

**Endpoint:** `GET /api/v1/chat/workflows/{chat_id}/files/{filename}`

**Description:** Download uploaded or output files from a conversation. This endpoint handles both files in the uploads/ and outputs/ directories.

**Response:** File download (application/octet-stream or specific MIME type)

**cURL Example:**

```bash
# Download an output file
curl -O "http://localhost:5050/api/v1/chat/workflows/a1b2c3d4.../files/extracted_data.xlsx"

# Or use with wget
wget "http://localhost:5050/api/v1/chat/workflows/a1b2c3d4.../files/result.xlsx"
```

#### 11. Download Dump File

**Endpoint:** `GET /api/v1/chat/downloads/{filename}`

**Description:** Download a conversation dump file.

**cURL Example:**

```bash
curl -O http://localhost:5050/api/v1/chat/downloads/conversation_dump.tar.gz
```

### Supported Workflow Operations

All existing APIs are available as workflow operations (except `/file/bind`):

**Excel Operations:**
- `excel/extract-columns`
- `excel/extract-columns-to-file`
- `excel/map-columns`
- `excel/bind-single-key`
- `excel/bind-multi-key`
- `excel/search`

**CSV Operations:**
- `csv/convert-to-excel`
- `csv/search`

**Normalization Operations:**
- `normalization/apply`

**SQL Generation Operations:**
- `sql/generate`
- `sql/generate-to-text`
- `sql/generate-custom-to-text`

**JSON Generation Operations:**
- `json/generate`
- `json/generate-with-template`

### WebSocket Real-Time Updates

Chat Workflows provides real-time progress updates via WebSocket during workflow execution.

#### Connection

**WebSocket URL:** `ws://127.0.0.1:5051/chat/{chat_id}`

Replace `{chat_id}` with your conversation ID. The WebSocket server runs on port 5051 by default.

#### Connection Flow

1. **Connect** to `ws://127.0.0.1:5051/chat/{chat_id}`
2. **Receive** welcome message confirming connection
3. **Listen** for workflow messages during execution
4. **Send** ping messages to keep connection alive (optional)

#### Message Types

All messages are JSON objects with clean, frontend-friendly structure. No unnecessary fields.

##### 1. Connected (Welcome Message)

Sent immediately after connection is established.

```json
{
  "type": "connected",
  "chat_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "timestamp": "2026-02-06T17:00:00.123456"
}
```

##### 2. Workflow Started

Sent when workflow execution begins.

```json
{
  "type": "workflow_started",
  "chat_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "total_steps": 3,
  "message": "Workflow execution started"
}
```

##### 3. Progress Update

Sent during step execution with real-time progress.

```json
{
  "type": "progress",
  "chat_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "step_id": "550e8400-e29b-41d4-a716-446655440000",
  "operation": "excel/extract-columns-to-file",
  "progress": 45,
  "status": "running",
  "message": "Processing column 'customer_id'"
}
```

**Fields:**
- `progress`: Integer 0-100 representing completion percentage
- `status`: One of: "pending", "running", "completed", "failed"
- `operation`: The operation being executed
- `message`: Human-readable progress description

##### 4. Workflow Completed

Sent when all steps complete successfully.

```json
{
  "type": "workflow_completed",
  "chat_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "total_steps": 3,
  "output_files_count": 2,
  "message": "Workflow execution completed successfully"
}
```

##### 5. Workflow Failed

Sent if any step fails.

```json
{
  "type": "workflow_failed",
  "chat_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "error": "Column 'invalid_col' not found in Excel file",
  "message": "Workflow execution failed"
}
```

#### Client Messages (Optional)

##### Ping/Pong (Keepalive)

Send ping to keep connection alive:

```json
{
  "type": "ping"
}
```

Server responds with:

```json
{
  "type": "pong"
}
```

##### Change Subscription

Switch to a different conversation:

```json
{
  "type": "subscribe",
  "chat_id": "new-chat-id-here"
}
```

#### Frontend Integration Examples

##### JavaScript (Browser)

```javascript
// Connect to WebSocket
const chatId = 'a1b2c3d4-e5f6-7890-abcd-ef1234567890';
const ws = new WebSocket(`ws://127.0.0.1:5051/chat/${chatId}`);

// Handle connection
ws.onopen = () => {
  console.log('Connected to chat workflow');
};

// Handle messages
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  
  switch(data.type) {
    case 'connected':
      console.log('Welcome:', data);
      break;
      
    case 'workflow_started':
      console.log(`Workflow started with ${data.total_steps} steps`);
      updateUI('Workflow started...');
      break;
      
    case 'progress':
      console.log(`Progress: ${data.progress}% - ${data.message}`);
      updateProgressBar(data.progress);
      updateStatusText(data.message);
      break;
      
    case 'workflow_completed':
      console.log('Workflow completed!');
      updateUI('Workflow completed successfully!');
      // Fetch final results from API
      fetchWorkflowResults(chatId);
      break;
      
    case 'workflow_failed':
      console.error('Workflow failed:', data.error);
      updateUI(`Error: ${data.error}`);
      break;
  }
};

// Handle errors
ws.onerror = (error) => {
  console.error('WebSocket error:', error);
};

// Handle disconnection
ws.onclose = () => {
  console.log('Disconnected from chat workflow');
};

// Optional: Send keepalive ping every 20 seconds
setInterval(() => {
  if (ws.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify({ type: 'ping' }));
  }
}, 20000);
```

##### React Example

```jsx
import { useEffect, useState } from 'react';

function WorkflowProgress({ chatId }) {
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
          setMessage('Starting workflow...');
          break;

        case 'progress':
          setProgress(data.progress);
          setMessage(data.message);
          break;

        case 'workflow_completed':
          setProgress(100);
          setStatus('completed');
          setMessage('Workflow completed!');
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
    <div className="workflow-progress">
      <div className="progress-bar">
        <div 
          className="progress-fill" 
          style={{ width: `${progress}%` }}
        />
      </div>
      <p className={`status-${status}`}>{message}</p>
    </div>
  );
}
```

##### Python Client

```python
import asyncio
import websockets
import json

async def listen_workflow_updates(chat_id):
    uri = f"ws://127.0.0.1:5051/chat/{chat_id}"
    
    async with websockets.connect(uri) as websocket:
        print(f"Connected to chat workflow: {chat_id}")
        
        async for message in websocket:
            data = json.loads(message)
            msg_type = data['type']
            
            if msg_type == 'connected':
                print(f"✓ Connected: {data['chat_id']}")
                
            elif msg_type == 'workflow_started':
                print(f"▶ Workflow started ({data['total_steps']} steps)")
                
            elif msg_type == 'progress':
                progress = data['progress']
                msg = data['message']
                print(f"⏳ {progress}% - {msg}")
                
            elif msg_type == 'workflow_completed':
                print(f"✓ Workflow completed! ({data['output_files_count']} files)")
                break
                
            elif msg_type == 'workflow_failed':
                print(f"✗ Workflow failed: {data['error']}")
                break

# Usage
asyncio.run(listen_workflow_updates('a1b2c3d4-e5f6-7890-abcd-ef1234567890'))
```

#### Best Practices

1. **Error Handling**: Always handle `onerror` and `onclose` events
2. **Reconnection**: Implement automatic reconnection with exponential backoff
3. **Message Validation**: Validate message structure before processing
4. **Progress Display**: Update UI smoothly based on progress percentage
5. **Connection State**: Track WebSocket connection state in your app
6. **Keepalive**: Send ping messages if your connection might be idle
7. **Cleanup**: Close WebSocket connections when component unmounts

### Workflow Execution Examples

#### Example 1: Data Extraction and Filtering

```bash
# 1. Create conversation
CHAT_ID=$(curl -s -X POST http://localhost:5050/api/v1/chat/workflows | jq -r '.data.chat_id')

# 2. Upload file
curl -X POST -F "file=@sales_data.xlsx" \
  http://localhost:5050/api/v1/chat/workflows/$CHAT_ID/upload

# 3. Execute workflow
curl -X POST \
  -H "Content-Type: application/json" \
  -d '{
    "steps": [
      {
        "operation": "excel/extract-columns",
        "arguments": {
          "columns": ["customer_id", "amount", "status", "date"]
        }
      },
      {
        "operation": "excel/search",
        "arguments": {
          "conditions": [
            {"column": "status", "operator": "equals", "value": "completed"},
            {"column": "amount", "operator": "greater_than", "value": 1000}
          ],
          "logic": "AND",
          "output_format": "excel"
        }
      }
    ]
  }' \
  http://localhost:5050/api/v1/chat/workflows/$CHAT_ID/execute
```

#### Example 2: CSV to Excel with Normalization

```bash
# Create conversation and upload CSV
CHAT_ID=$(curl -s -X POST http://localhost:5050/api/v1/chat/workflows | jq -r '.data.chat_id')
curl -X POST -F "file=@customers.csv" \
  http://localhost:5050/api/v1/chat/workflows/$CHAT_ID/upload

# Convert and normalize
curl -X POST \
  -H "Content-Type: application/json" \
  -d '{
    "steps": [
      {
        "operation": "csv/convert-to-excel",
        "arguments": {
          "sheet_name": "Customers"
        }
      },
      {
        "operation": "normalization/apply",
        "arguments": {
          "normalizations": [
            {"column": "email", "type": "lowercase"},
            {"column": "phone", "type": "phone_format"},
            {"column": "name", "type": "title_case"}
          ]
        }
      }
    ]
  }' \
  http://localhost:5050/api/v1/chat/workflows/$CHAT_ID/execute
```

#### Example 3: SQL Generation Pipeline

```bash
# Create conversation and upload
CHAT_ID=$(curl -s -X POST http://localhost:5050/api/v1/chat/workflows | jq -r '.data.chat_id')
curl -X POST -F "file=@users.xlsx" \
  http://localhost:5050/api/v1/chat/workflows/$CHAT_ID/upload

# Filter and generate SQL
curl -X POST \
  -H "Content-Type: application/json" \
  -d '{
    "steps": [
      {
        "operation": "excel/search",
        "arguments": {
          "conditions": [
            {"column": "is_active", "operator": "equals", "value": "true"}
          ],
          "logic": "AND"
        }
      },
      {
        "operation": "sql/generate",
        "arguments": {
          "table_name": "active_users",
          "database_type": "postgresql",
          "column_mapping": {
            "user_id": "id",
            "user_name": "name",
            "user_email": "email"
          }
        }
      }
    ]
  }' \
  http://localhost:5050/api/v1/chat/workflows/$CHAT_ID/execute
```

#### Example 4: Complete Workflow with WebSocket Monitoring

This example shows how to execute a workflow while monitoring real-time progress via WebSocket.

**Terminal 1 - Start WebSocket listener (Python):**

```python
import asyncio
import websockets
import json
import sys

async def monitor_workflow(chat_id):
    uri = f"ws://127.0.0.1:5051/chat/{chat_id}"
    
    try:
        async with websockets.connect(uri) as ws:
            print(f"✓ Connected to workflow: {chat_id}\n")
            
            async for message in ws:
                data = json.loads(message)
                
                if data['type'] == 'workflow_started':
                    print(f"▶ Workflow started with {data['total_steps']} steps\n")
                    
                elif data['type'] == 'progress':
                    print(f"⏳ [{data['progress']:3d}%] {data['operation']}")
                    print(f"   {data['message']}\n")
                    
                elif data['type'] == 'workflow_completed':
                    print(f"✓ Workflow completed!")
                    print(f"   Generated {data['output_files_count']} output files\n")
                    break
                    
                elif data['type'] == 'workflow_failed':
                    print(f"✗ Workflow failed: {data['error']}\n")
                    break
    except Exception as e:
        print(f"WebSocket error: {e}")

if __name__ == "__main__":
    chat_id = sys.argv[1] if len(sys.argv) > 1 else input("Enter chat_id: ")
    asyncio.run(monitor_workflow(chat_id))
```

**Terminal 2 - Execute workflow (Bash):**

```bash
# Create conversation
CHAT_ID=$(curl -s -X POST http://localhost:5050/api/v1/chat/workflows | jq -r '.data.chat_id')
echo "Chat ID: $CHAT_ID"

# Start WebSocket monitor in Terminal 1
# python monitor_workflow.py $CHAT_ID

# Upload file
curl -X POST -F "file=@data.xlsx" \
  http://localhost:5050/api/v1/chat/workflows/$CHAT_ID/upload

# Execute workflow (WebSocket will show real-time progress)
RESPONSE=$(curl -s -X POST \
  -H "Content-Type: application/json" \
  -d '{
    "steps": [
      {
        "operation": "excel/extract-columns-to-file",
        "arguments": {
          "columns": ["customer_id", "amount", "status"],
          "remove_duplicates": true
        }
      },
      {
        "operation": "normalization/apply",
        "arguments": {
          "normalizations": [
            {"column": "customer_id", "type": "uppercase"},
            {"column": "status", "type": "trim"}
          ]
        }
      }
    ]
  }' \
  http://localhost:5050/api/v1/chat/workflows/$CHAT_ID/execute)

# Download output files
echo "$RESPONSE" | jq -r '.data.output_files[].download_url' | while read url; do
  echo "Downloading: $url"
  curl -O "$url"
done

echo "✓ Workflow complete! Files downloaded."
```

**Expected WebSocket Output:**

```
✓ Connected to workflow: a1b2c3d4-e5f6-7890-abcd-ef1234567890

▶ Workflow started with 2 steps

⏳ [  0%] excel/extract-columns-to-file
   Starting step execution

⏳ [ 25%] excel/extract-columns-to-file
   Reading Excel file

⏳ [ 50%] excel/extract-columns-to-file
   Extracting columns: customer_id, amount, status

⏳ [100%] excel/extract-columns-to-file
   Step completed successfully

⏳ [  0%] normalization/apply
   Starting step execution

⏳ [ 50%] normalization/apply
   Normalizing column 'customer_id'

⏳ [100%] normalization/apply
   Step completed successfully

✓ Workflow completed!
   Generated 2 output files
```

### Recent Improvements (All Fixed) ✅

The Chat Workflows feature has been enhanced with the following fixes and improvements:

1. **WebSocket Integration** ✅
   - **Fixed**: WebSocket server now auto-starts with Flask application
   - **Added**: Thread-safe bridge for cross-thread communication
   - **Result**: Real-time progress updates working perfectly
   - Message formats cleaned and optimized for frontend integration

2. **File Upload Persistence** ✅
   - **Fixed**: CASCADE DELETE issue that was removing uploaded files
   - **Fixed**: Files now properly saved to SQLite database
   - **Result**: Uploaded files persist correctly across API calls

3. **Workflow Executor** ✅
   - **Fixed**: Service methods now receive pandas DataFrames instead of file paths
   - **Fixed**: All workflow operations (Excel, CSV, Normalization, SQL, JSON) working correctly
   - **Result**: No more `'str' object has no attribute 'columns'` errors

4. **Absolute Download URLs** ✅
   - **Fixed**: All download URLs now include scheme and host
   - **Added**: `download_url` field to upload, execute, and dump responses
   - **Result**: URLs are directly clickable and frontend-friendly
   - Format: `http://localhost:5050/api/v1/chat/workflows/{chat_id}/files/{filename}`

5. **Download Endpoint** ✅
   - **Fixed**: Missing `storage` parameter in ConversationRepository
   - **Added**: New `/workflows/{chat_id}/files/{filename}` endpoint
   - **Result**: File downloads work correctly for both uploads and outputs

6. **Message Format Optimization** ✅
   - **Improved**: WebSocket messages now have clean, minimal structure
   - **Removed**: Unnecessary fields and timestamps
   - **Result**: Easy to integrate in React, Vue, Angular, or plain JavaScript

### Production Ready ✅

All Chat Workflows features are now fully functional and production-ready:

- ✅ **REST API**: All 11 endpoints working correctly
- ✅ **WebSocket**: Real-time updates with clean message formats
- ✅ **File Storage**: Reliable persistence with partition support
- ✅ **Workflow Execution**: All 15+ operations working correctly
- ✅ **Download URLs**: Absolute URLs ready for frontend use
- ✅ **Error Handling**: Comprehensive exception handling
- ✅ **Thread Safety**: Cross-thread communication working perfectly
- ✅ **Documentation**: Complete with examples for frontend integration

### Conversation Storage Structure

```
automation/
├── workflows/
│   └── 2026/
│       └── 02/
│           └── {chat_id}/
│               ├── metadata.json
│               ├── uploads/
│               │   └── original_file.xlsx
│               ├── intermediate/
│               │   ├── step1_output.xlsx
│               │   └── step2_output.xlsx
│               └── outputs/
│                   └── final_output.xlsx
├── dumps/
│   └── {chat_id}_20260206_173000.tar.gz
└── sqlite/
    ├── chat.db
    └── snapshots/
        └── chat_backup_20260206_173000.db
```

### Error Handling

**Common Error Responses:**

```json
{
  "status_code": 422,
  "message": "Chat workflows feature is not enabled",
  "meta": {...}
}
```

```json
{
  "status_code": 404,
  "message": "Conversation not found",
  "meta": {...}
}
```

```json
{
  "status_code": 500,
  "message": "Workflow execution failed: Column 'invalid_col' not found",
  "meta": {...}
}
```

### Best Practices

1. **Enable Feature:** Ensure `chat_workflows.enabled: true` in configuration
2. **File Uploads:** Upload files before executing workflows
3. **Step Order:** Design steps to chain outputs correctly
4. **Error Recovery:** Handle failed steps and review error messages
5. **Cleanup:** Delete old conversations to manage storage
6. **Backups:** Regular SQLite backups for data safety
7. **Monitoring:** Use WebSocket for real-time progress tracking

### Performance Considerations

- **Partitioning:** Time-based partitioning improves file system performance
- **SQLite Indexing:** Indexed queries for fast conversation retrieval
- **Intermediate Files:** Saved for debugging but can be cleaned up
- **WebSocket Connections:** Limited to configured max_connections
- **Step Timeout:** Configurable per-step timeout (default: 300 seconds)

## 🎨 Design Patterns

### 1. Builder Pattern (ResponseBuilder)

Used for constructing standardized API responses:

```python
response = (
    ResponseBuilder()
    .with_data({'id': 1, 'name': 'John'})
    .with_message('User retrieved successfully')
    .with_status_code(200)
    .build()
)
```

### 2. Factory Pattern (NormalizerFactory)

Used for creating normalization strategy instances:

```python
strategy = NormalizerFactory.create(NormalizationType.UPPERCASE)
normalized_series = strategy.normalize(data_series)
```

### 3. Strategy Pattern (Normalization Strategies)

Used for implementing interchangeable normalization algorithms:

```python
class UppercaseStrategy(NormalizationStrategy):
    def normalize(self, series: pd.Series) -> pd.Series:
        return series.astype(str).str.upper()
```

## 🧪 Testing

Run the test suite:

```bash
make test
```

Run tests with coverage:

```bash
make test-cov
```

## 📝 Available Normalization Types

| Type                   | Description                        |
| ---------------------- | ---------------------------------- |
| `uppercase`            | Convert to uppercase               |
| `lowercase`            | Convert to lowercase               |
| `title_case`           | Convert to title case              |
| `trim_whitespace`      | Remove leading/trailing whitespace |
| `remove_special_chars` | Remove special characters          |
| `phone_format`         | Format phone numbers               |
| `email_format`         | Format email addresses             |
| `name_format`          | Format personal names              |
| `min_max_scale`        | Scale to 0-1 range                 |
| `z_score`              | Standardize using z-score          |
| `round_decimal`        | Round to decimals                  |
| `integer_convert`      | Convert to integer                 |
| `currency_format`      | Parse currency values              |
| `date_format`          | Format dates                       |
| `datetime_format`      | Format datetime                    |
| `boolean_convert`      | Convert to boolean                 |
| `yes_no_convert`       | Convert to Yes/No                  |
| `regex_replace`        | Replace using regex                |
| `fill_null_values`     | Fill null values                   |
| `outlier_removal`      | Remove outliers                    |

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

Made with ❤️ using Flask and Python
