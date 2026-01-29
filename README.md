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
- **Excel-to-Excel Binding**: Bind values from source to target files
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
│   │       └── file_routes.py
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
│   │   ├── normalization_service.py
│   │   ├── sql_generation_service.py
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

The application will start at `http://localhost:5000`

## ⚙️ Configuration

Configuration is managed through `configs/application.yml`:

```yaml
app:
  name: "Pycelize"
  version: "v0.0.1"
  environment: "development"
  debug: true
  host: "0.0.0.0"
  port: 5000

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
http://localhost:5000/api/v1
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
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| GET | `/health/ready` | Readiness check |

#### Excel Operations
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/excel/info` | Get Excel file information |
| POST | `/excel/extract-columns` | Extract column data |
| POST | `/excel/map-columns` | Apply column mapping |

#### CSV Operations
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/csv/info` | Get CSV file information |
| POST | `/csv/convert-to-excel` | Convert CSV to Excel |

#### Normalization
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/normalization/types` | List normalization types |
| POST | `/normalization/apply` | Apply normalization |

#### SQL Generation
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/sql/databases` | List supported databases |
| POST | `/sql/generate` | Generate SQL statements |

#### File Binding
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/files/bind` | Bind source to target file |
| POST | `/files/bind/preview` | Preview binding operation |

## 🔧 Usage Examples (cURL)

### 1. Health Check
```bash
curl http://localhost:5000/api/v1/health
```

### 2. Get Excel File Information
```bash
curl -X POST \
  -F "file=@data.xlsx" \
  http://localhost:5000/api/v1/excel/info
```

### 3. Extract Columns from Excel
```bash
curl -X POST \
  -F "file=@data.xlsx" \
  -F 'columns=["name", "email", "phone"]' \
  -F "remove_duplicates=true" \
  http://localhost:5000/api/v1/excel/extract-columns
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
  http://localhost:5000/api/v1/excel/map-columns \
  --output mapped_data.xlsx
```

### 5. Convert CSV to Excel
```bash
curl -X POST \
  -F "file=@data.csv" \
  -F "sheet_name=MyData" \
  http://localhost:5000/api/v1/csv/convert-to-excel \
  --output converted.xlsx
```

### 6. Get Normalization Types
```bash
curl http://localhost:5000/api/v1/normalization/types
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
  http://localhost:5000/api/v1/normalization/apply \
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
  http://localhost:5000/api/v1/sql/generate \
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
  http://localhost:5000/api/v1/sql/generate
```

### 10. Bind Excel Files
```bash
curl -X POST \
  -F "source_file=@source_data.xlsx" \
  -F "target_file=@template.xlsx" \
  -F 'column_mapping={
    "Target_Name": "Source_Name",
    "Target_Email": "Source_Email",
    "Target_Phone": "Source_Phone"
  }' \
  http://localhost:5000/api/v1/files/bind \
  --output bound_result.xlsx
```

### 11. Preview Binding Operation
```bash
curl -X POST \
  -F "source_file=@source.xlsx" \
  -F "target_file=@target.xlsx" \
  -F 'column_mapping={"Target_Col": "Source_Col"}' \
  http://localhost:5000/api/v1/files/bind/preview
```

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

| Type | Description |
|------|-------------|
| `uppercase` | Convert to uppercase |
| `lowercase` | Convert to lowercase |
| `title_case` | Convert to title case |
| `trim_whitespace` | Remove leading/trailing whitespace |
| `remove_special_chars` | Remove special characters |
| `phone_format` | Format phone numbers |
| `email_format` | Format email addresses |
| `name_format` | Format personal names |
| `min_max_scale` | Scale to 0-1 range |
| `z_score` | Standardize using z-score |
| `round_decimal` | Round to decimals |
| `integer_convert` | Convert to integer |
| `currency_format` | Parse currency values |
| `date_format` | Format dates |
| `datetime_format` | Format datetime |
| `boolean_convert` | Convert to boolean |
| `yes_no_convert` | Convert to Yes/No |
| `regex_replace` | Replace using regex |
| `fill_null_values` | Fill null values |
| `outlier_removal` | Remove outliers |

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