# SQL/JSON Template Syntax Documentation

This document describes the enhanced template syntax implemented for both SQL and JSON generation APIs.

## Overview

The template syntax now supports type conversion and default values for null/empty fields, making it easier to generate properly formatted SQL statements and JSON documents.

## Supported Syntax

### Basic Substitution

```
{column_name}
```

Replaces the placeholder with the value from the mapped column.

**Example:**

```
Template: INSERT INTO users (name) VALUES ({name});
Result:   INSERT INTO users (name) VALUES ('Alice');
```

### Type Conversion

#### Integer Conversion: `{column_name:int}`

Converts the value to an integer (unquoted in SQL).

**Example:**

```
Template: INSERT INTO users (id, age) VALUES ({id:int}, {age:int});
Result:   INSERT INTO users (id, age) VALUES (1, 25);
```

#### Float Conversion: `{column_name:float}`

Converts the value to a float (unquoted in SQL).

**Example:**

```
Template: INSERT INTO scores (score) VALUES ({score:float});
Result:   INSERT INTO scores (score) VALUES (95.5);
```

#### Boolean Conversion: `{column_name:bool}`

Converts the value to a boolean.

- **SQL**: `TRUE` or `FALSE`
- **JSON**: `True` or `False` (as string)

**Example:**

```
Template: INSERT INTO users (active) VALUES ({active:bool});
Result:   INSERT INTO users (active) VALUES (TRUE);
```

#### Datetime: `{column_name:datetime}`

Keeps the value as a datetime string.

**Example:**

```
Template: INSERT INTO logs (created_at) VALUES ({timestamp:datetime});
Result:   INSERT INTO logs (created_at) VALUES ('2024-01-15T10:30:00');
```

### Default Values: `{column_name|default}`

Uses a default value when the column value is null or empty.

**Example:**

```
Template: INSERT INTO users (email) VALUES ({email|no-email@example.com});
Result (when email is null): INSERT INTO users (email) VALUES ('no-email@example.com');
Result (when email exists):  INSERT INTO users (email) VALUES ('alice@test.com');
```

### Combined Syntax

You can combine type conversion with default values:

```
Template: INSERT INTO users (count) VALUES ({count:int|0});
Result (when count is null): INSERT INTO users (count) VALUES (0);
Result (when count exists):  INSERT INTO users (count) VALUES (42);
```

## API Examples

### SQL Generation API

**Endpoint:** `POST /api/v1/sql/generate-custom-to-text`

**Example Request:**

```bash
curl -X POST http://localhost:5050/api/v1/sql/generate-custom-to-text \
  -F "file=@data.xlsx" \
  -F 'column_mapping={"id":"ID","name":"Name","age":"Age","score":"Score","active":"Active","email":"Email"}' \
  -F 'template=INSERT INTO users (id, name, age, score, active, email) VALUES ({id:int}, {name}, {age:int}, {score:float}, {active:bool}, {email|no-email@example.com});'
```

**Example Output:**

```sql
INSERT INTO users (id, name, age, score, active, email) VALUES (1, 'Alice', 25, 95.5, TRUE, 'alice@test.com');
INSERT INTO users (id, name, age, score, active, email) VALUES (2, 'Bob', 30, 88.0, FALSE, 'no-email@example.com');
INSERT INTO users (id, name, age, score, active, email) VALUES (3, 'Charlie', 35, 92.3, TRUE, 'charlie@test.com');
```

### JSON Generation API

**Endpoint:** `POST /api/v1/json/generate-with-template`

**Example Request:**

```bash
curl -X POST http://localhost:5050/api/v1/json/generate-with-template \
  -F "file=@data.xlsx" \
  -F 'template={"user":{"id":"{id:int}","name":"{name}","age":"{age:int}"},"stats":{"score":"{score:float}","active":"{active:bool}"},"contact":{"email":"{email|no-email@example.com}"}}' \
  -F 'column_mapping={"id":"ID","name":"Name","age":"Age","score":"Score","active":"Active","email":"Email"}' \
  -F 'pretty_print=true' \
  -F 'aggregation_mode=array'
```

**Example Output:**

```json
[
  {
    "user": {
      "id": 1,
      "name": "Alice",
      "age": 25
    },
    "stats": {
      "score": 95.5,
      "active": true
    },
    "contact": {
      "email": "alice@test.com"
    }
  },
  {
    "user": {
      "id": 2,
      "name": "Bob",
      "age": 30
    },
    "stats": {
      "score": 88.0,
      "active": false
    },
    "contact": {
      "email": "no-email@example.com"
    }
  }
]
```

**Note:** When a JSON template value is a pure placeholder with a type hint (e.g., `"id": "{id:int}"`), the output JSON will contain the native JSON type (number, boolean) instead of a string. Mixed content (e.g., `"display": "ID: {id:int}"`) will produce strings.

## Special Features

### JSON-Specific Features

#### Native Type Preservation

When using type hints in JSON templates, the output preserves native JSON types:

**Pure Placeholder (Native Type):**

```json
// Template: {"id": "{id:int}", "score": "{score:float}", "active": "{active:bool}"}
// Output: {"id": 1, "score": 95.5, "active": true}  // Native types
```

**Mixed Content (String):**

```json
// Template: {"display": "User {id:int}", "label": "Score: {score:float}"}
// Output: {"display": "User 1", "label": "Score: 95.5"}  // Strings
```

### SQL-Specific Features

#### Automatic Quote Escaping

Single quotes in values are automatically escaped for SQL:

```
Value: O'Brien
Result: 'O''Brien'
```

#### NULL Handling

When no default is specified and the value is null/empty:

```
Template: INSERT INTO users (email) VALUES ({email});
Result (when email is null): INSERT INTO users (email) VALUES (NULL);
```

#### Special Placeholders

- `{auto_id}`: Auto-incremented ID (when auto_increment is enabled)
- `{current_timestamp}`: Replaced with `CURRENT_TIMESTAMP`

### Type Conversion Rules

#### Integer Conversion

- Strings: `"42"` → `42`
- Floats: `42.7` → `42`
- Empty/null: `None` or default

#### Float Conversion

- Strings: `"42.5"` → `42.5`
- Integers: `42` → `42.0`
- Empty/null: `None` or default

#### Boolean Conversion

- String values: `"true"`, `"True"`, `"1"`, `"yes"`, `"on"` → `True`
- String values: `"false"`, `"False"`, `"0"`, `"no"`, `"off"` → `False`
- Numeric values: `1` → `True`, `0` → `False`
- Empty/null: `None` or default

## Backward Compatibility

The enhanced syntax is fully backward compatible with existing templates:

- Templates without type hints work exactly as before
- Basic `{column_name}` substitution is unchanged
- No changes required to existing API calls

## Error Handling

### Missing Columns

If a column referenced in the template doesn't exist in the data:

```json
{
  "status_code": 422,
  "message": "Column 'NonExistent' not found in data"
}
```

### Type Conversion Failures

If type conversion fails, the original value is used:

```
Template: {age:int}
Value: "not a number"
Result: 'not a number' (kept as string)
```

## Best Practices

1. **Use type hints for numeric fields** to avoid unnecessary quotes in SQL
2. **Provide defaults for optional fields** to avoid NULL values
3. **Test templates with sample data** before processing large files
4. **Use consistent column naming** between Excel and templates
5. **Escape special characters** in default values if needed

## Implementation Notes

- Empty strings from Excel files are treated as null when a default is specified
- Type conversion is applied before default value substitution
- For SQL, numeric types (int, float) are unquoted; strings are quoted
- For JSON, all values are converted to strings in the template
