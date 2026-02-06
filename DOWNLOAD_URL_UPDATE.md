# Download URL Update - Response Examples

## Summary of Changes

All download URLs in chat workflow responses are now **absolute URLs** that can be clicked directly, following the pattern:
- `http://{host}/api/v1/chat/workflows/{chat_id}/files/{filename}` for workflow files
- `http://{host}/api/v1/chat/downloads/{filename}` for dump files

## API Response Examples

### 1. File Upload API

**Request:**
```bash
curl --location 'http://localhost:5050/api/v1/chat/workflows/208475d4-4ed3-4d67-923e-f88967c14173/upload' \
--form 'file=@"/path/to/List_Ubigeos_JERCourier.xlsx"'
```

**Response (BEFORE):**
```json
{
    "data": {
        "file_path": "./automation/workflows/2026/02/208475d4-4ed3-4d67-923e-f88967c14173/uploads/List_Ubigeos_JERCourier.xlsx",
        "filename": "List_Ubigeos_JERCourier.xlsx",
        "download_url": "/api/v1/files/download?path=./automation/workflows/2026/02/208475d4-4ed3-4d67-923e-f88967c14173/uploads/List_Ubigeos_JERCourier.xlsx"
    }
}
```

**Response (AFTER - Clickable!):**
```json
{
    "data": {
        "file_path": "./automation/workflows/2026/02/208475d4-4ed3-4d67-923e-f88967c14173/uploads/List_Ubigeos_JERCourier.xlsx",
        "filename": "List_Ubigeos_JERCourier.xlsx",
        "download_url": "http://localhost:5050/api/v1/chat/workflows/208475d4-4ed3-4d67-923e-f88967c14173/files/List_Ubigeos_JERCourier.xlsx"
    },
    "message": "File uploaded successfully"
}
```

---

### 2. Workflow Execute API

**Request:**
```bash
curl --location 'http://localhost:5050/api/v1/chat/workflows/208475d4-4ed3-4d67-923e-f88967c14173/execute' \
--header 'Content-Type: application/json' \
--data '{
    "steps": [
        {
            "operation": "excel/extract-columns-to-file",
            "arguments": {
                "columns": ["postal_code"],
                "remove_duplicates": true
            }
        }
    ]
}'
```

**Response (BEFORE):**
```json
{
    "data": {
        "results": [
            {
                "output_file_path": "./automation/workflows/2026/02/208475d4-4ed3-4d67-923e-f88967c14173/uploads/List_Ubigeos_JERCourier_extracted_20260206_185708.xlsx"
            }
        ],
        "output_files": [
            "./automation/workflows/2026/02/208475d4-4ed3-4d67-923e-f88967c14173/outputs/List_Ubigeos_JERCourier_extracted_20260206_185537.xlsx"
        ]
    }
}
```

**Response (AFTER - With Download URLs!):**
```json
{
    "data": {
        "results": [
            {
                "output_file_path": "./automation/workflows/2026/02/208475d4-4ed3-4d67-923e-f88967c14173/uploads/List_Ubigeos_JERCourier_extracted_20260206_185708.xlsx",
                "download_url": "http://localhost:5050/api/v1/chat/workflows/208475d4-4ed3-4d67-923e-f88967c14173/files/List_Ubigeos_JERCourier_extracted_20260206_185708.xlsx"
            }
        ],
        "output_files": [
            {
                "file_path": "./automation/workflows/2026/02/208475d4-4ed3-4d67-923e-f88967c14173/outputs/List_Ubigeos_JERCourier_extracted_20260206_185537.xlsx",
                "download_url": "http://localhost:5050/api/v1/chat/workflows/208475d4-4ed3-4d67-923e-f88967c14173/files/List_Ubigeos_JERCourier_extracted_20260206_185537.xlsx"
            }
        ]
    },
    "message": "Workflow executed successfully"
}
```

---

### 3. Dump Conversation API

**Request:**
```bash
curl --location --request POST 'http://localhost:5050/api/v1/chat/workflows/b47f8e4c-7d5b-49da-81e2-0381ca9e68ae/dump'
```

**Response (BEFORE):**
```json
{
    "data": {
        "dump_file": "b47f8e4c-7d5b-49da-81e2-0381ca9e68ae_20260206_180245.tar.gz",
        "download_url": "/api/v1/chat/downloads/b47f8e4c-7d5b-49da-81e2-0381ca9e68ae_20260206_180245.tar.gz"
    }
}
```

**Response (AFTER - Clickable!):**
```json
{
    "data": {
        "dump_file": "b47f8e4c-7d5b-49da-81e2-0381ca9e68ae_20260206_180245.tar.gz",
        "download_url": "http://localhost:5050/api/v1/chat/downloads/b47f8e4c-7d5b-49da-81e2-0381ca9e68ae_20260206_180245.tar.gz"
    },
    "message": "Conversation dumped successfully"
}
```

---

## New Download Endpoint

A new endpoint has been added to handle downloads of workflow files:

**Endpoint:** `GET /api/v1/chat/workflows/{chat_id}/files/{filename}`

**Features:**
- Automatically searches in both `uploads/` and `outputs/` folders
- Respects conversation partitioning (uses partition_key)
- Path validation to prevent directory traversal attacks
- Proper MIME type detection (xlsx, csv, json, txt, sql)
- Secure filename handling

**Example:**
```bash
# Download an uploaded file
curl -O "http://localhost:5050/api/v1/chat/workflows/208475d4-4ed3-4d67-923e-f88967c14173/files/List_Ubigeos_JERCourier.xlsx"

# Download an output file
curl -O "http://localhost:5050/api/v1/chat/workflows/208475d4-4ed3-4d67-923e-f88967c14173/files/List_Ubigeos_JERCourier_extracted_20260206_185708.xlsx"
```

---

## Benefits

✅ **Clickable URLs** - Can be used directly in browsers or tools  
✅ **Environment-Aware** - Works with http or https automatically  
✅ **Port-Aware** - Includes the correct port from the request  
✅ **Partition-Aware** - Respects conversation folder structure  
✅ **Secure** - Path validation prevents directory traversal  
✅ **No Configuration Needed** - Host and scheme detected automatically  

---

## Frontend Integration

Frontend developers can now use the download URLs directly:

```javascript
// Upload file response
const uploadResponse = await uploadFile(chatId, file);
const downloadUrl = uploadResponse.data.download_url;

// Direct download link
window.open(downloadUrl);

// Or use in an anchor tag
<a href={downloadUrl} download>Download File</a>

// Execute workflow response
const executeResponse = await executeWorkflow(chatId, steps);
executeResponse.data.output_files.forEach(file => {
    console.log(`Download: ${file.download_url}`);
});
```

---

## Migration Notes

**No Breaking Changes:**
- All responses still include the original `file_path` field
- The `download_url` field is additional, not replacing anything
- Existing integrations continue to work
- New integrations can use the clickable URLs directly

**Upgrade Path:**
1. Update your frontend to use `download_url` instead of constructing URLs manually
2. Remove any URL construction logic from your code
3. Use the absolute URLs directly in links or API calls
