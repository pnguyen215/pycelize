# Download URL Implementation - Visual Guide

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Client (Browser/App)                         │
└─────────────────────────────────────────────────────────────────────┘
                                  │
                                  ↓
┌─────────────────────────────────────────────────────────────────────┐
│                      Flask Application (Port 5050)                   │
│                                                                      │
│  ┌────────────────────────────────────────────────────────────┐    │
│  │  Chat Workflow Routes (/api/v1/chat/workflows)             │    │
│  │                                                             │    │
│  │  POST   /workflows                     → Create            │    │
│  │  POST   /workflows/{id}/upload         → Upload File       │    │
│  │  POST   /workflows/{id}/execute        → Execute Workflow  │    │
│  │  POST   /workflows/{id}/dump           → Dump Conversation │    │
│  │  GET    /workflows/{id}/files/{file}   → Download File ⭐  │    │
│  │  GET    /downloads/{file}              → Download Dump     │    │
│  └────────────────────────────────────────────────────────────┘    │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
                                  │
                                  ↓
┌─────────────────────────────────────────────────────────────────────┐
│                         File System Storage                          │
│                                                                      │
│  ./automation/                                                       │
│  ├── workflows/                                                      │
│  │   └── {partition}/         (e.g., 2026/02/)                      │
│  │       └── {chat_id}/                                             │
│  │           ├── uploads/     ← Uploaded files                      │
│  │           └── outputs/     ← Generated files                     │
│  └── dumps/                   ← Conversation backups                │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## URL Flow Comparison

### BEFORE (Relative URLs - Not Clickable)

```
┌──────────────────┐
│  Upload File     │
└────────┬─────────┘
         │
         ↓
┌─────────────────────────────────────────────────────┐
│  Response:                                           │
│  {                                                   │
│    "download_url": "/api/v1/files/download?path=..." │
│  }                                                   │
│                                                      │
│  ❌ Relative URL                                     │
│  ❌ Requires manual host construction               │
│  ❌ Cannot be clicked directly                       │
└──────────────────────────────────────────────────────┘
```

### AFTER (Absolute URLs - Clickable!)

```
┌──────────────────┐
│  Upload File     │
└────────┬─────────┘
         │
         ↓
┌──────────────────────────────────────────────────────────────────────┐
│  Response:                                                            │
│  {                                                                    │
│    "download_url": "http://localhost:5050/api/v1/chat/workflows/..." │
│  }                                                                    │
│                                                                       │
│  ✅ Absolute URL with scheme + host                                  │
│  ✅ No manual construction needed                                    │
│  ✅ Can be clicked directly                                          │
│  ✅ Works across all environments                                    │
└───────────────────────────────────────────────────────────────────────┘
         │
         ↓
┌──────────────────────────────────────────┐
│  Click URL → Download File Immediately   │
└──────────────────────────────────────────┘
```

---

## Response Structure Changes

### 1. Upload API Response

```json
// BEFORE
{
  "data": {
    "file_path": "./automation/workflows/2026/02/{chat_id}/uploads/file.xlsx",
    "filename": "file.xlsx",
    "download_url": "/api/v1/files/download?path=..."  ← Relative
  }
}

// AFTER
{
  "data": {
    "file_path": "./automation/workflows/2026/02/{chat_id}/uploads/file.xlsx",
    "filename": "file.xlsx",
    "download_url": "http://localhost:5050/api/v1/chat/workflows/{chat_id}/files/file.xlsx"  ← Absolute!
  }
}
```

### 2. Execute API Response

```json
// BEFORE
{
  "data": {
    "results": [{
      "output_file_path": "./automation/.../output.xlsx"
      // ❌ No download_url
    }],
    "output_files": [
      "./automation/.../output.xlsx"  // ❌ Just a string path
    ]
  }
}

// AFTER
{
  "data": {
    "results": [{
      "output_file_path": "./automation/.../output.xlsx",
      "download_url": "http://localhost:5050/api/v1/chat/workflows/{chat_id}/files/output.xlsx"  ← Added!
    }],
    "output_files": [{
      "file_path": "./automation/.../output.xlsx",
      "download_url": "http://localhost:5050/api/v1/chat/workflows/{chat_id}/files/output.xlsx"  ← Added!
    }]
  }
}
```

### 3. Dump API Response

```json
// BEFORE
{
  "data": {
    "dump_file": "backup.tar.gz",
    "download_url": "/api/v1/chat/downloads/backup.tar.gz"  ← Relative
  }
}

// AFTER
{
  "data": {
    "dump_file": "backup.tar.gz",
    "download_url": "http://localhost:5050/api/v1/chat/downloads/backup.tar.gz"  ← Absolute!
  }
}
```

---

## Download Endpoint Logic

### New Endpoint: `/workflows/{chat_id}/files/{filename}`

```
┌─────────────────────────────────────────────────────────┐
│  Request: GET /workflows/{chat_id}/files/data.xlsx      │
└────────────────────────┬────────────────────────────────┘
                         │
                         ↓
┌────────────────────────────────────────────────────────┐
│  1. Get conversation by chat_id                        │
│     → Load partition_key (e.g., "2026/02")             │
└────────────────────────┬───────────────────────────────┘
                         │
                         ↓
┌────────────────────────────────────────────────────────┐
│  2. Build partition path                               │
│     → ./automation/workflows/2026/02/{chat_id}         │
└────────────────────────┬───────────────────────────────┘
                         │
                         ↓
┌────────────────────────────────────────────────────────┐
│  3. Search for file                                    │
│     → Check: uploads/data.xlsx                         │
│     → Check: outputs/data.xlsx                         │
└────────────────────────┬───────────────────────────────┘
                         │
                         ↓
┌────────────────────────────────────────────────────────┐
│  4. Validate path (security check)                     │
│     → Must be within partition directory               │
│     → Prevent directory traversal                      │
└────────────────────────┬───────────────────────────────┘
                         │
                         ↓
┌────────────────────────────────────────────────────────┐
│  5. Determine MIME type                                │
│     → .xlsx → application/vnd.openxml...               │
│     → .csv  → text/csv                                 │
│     → .json → application/json                         │
└────────────────────────┬───────────────────────────────┘
                         │
                         ↓
┌────────────────────────────────────────────────────────┐
│  6. Send file with proper headers                      │
│     → Content-Disposition: attachment                  │
│     → Content-Type: {mimetype}                         │
└────────────────────────────────────────────────────────┘
```

---

## Frontend Integration Example

### HTML

```html
<!-- Direct download link -->
<a href="{download_url}" download>
  Download File
</a>

<!-- Button with JavaScript -->
<button onclick="downloadFile('{download_url}')">
  Download
</button>
```

### JavaScript

```javascript
// After file upload
const uploadResponse = await fetch('/api/v1/chat/workflows/' + chatId + '/upload', {
  method: 'POST',
  body: formData
});

const data = await uploadResponse.json();

// Use download URL directly - no construction needed!
window.location.href = data.data.download_url;
```

### React

```jsx
function FileDownloadButton({ downloadUrl }) {
  return (
    <a 
      href={downloadUrl} 
      download 
      className="download-button"
    >
      📥 Download File
    </a>
  );
}

// After workflow execution
const executeResponse = await executeWorkflow(chatId, steps);
executeResponse.data.output_files.map(file => (
  <FileDownloadButton downloadUrl={file.download_url} />
));
```

---

## Security Features

```
┌────────────────────────────────────────────────────────┐
│  Security Measures in Download Endpoint                │
├────────────────────────────────────────────────────────┤
│  ✓ secure_filename() - Removes dangerous characters    │
│  ✓ Path validation - Must be within partition dir      │
│  ✓ Existence check - File must exist                   │
│  ✓ Directory traversal prevention                      │
│  ✓ Conversation ownership validation                   │
└────────────────────────────────────────────────────────┘
```

---

## Migration Path

### For Frontend Developers

**Step 1:** Replace manual URL construction
```javascript
// OLD (Manual construction)
const downloadUrl = `http://${window.location.host}/api/v1/files/download?path=${filePath}`;

// NEW (Use provided URL directly)
const downloadUrl = response.data.download_url;  // Already absolute!
```

**Step 2:** Update file lists
```javascript
// OLD (String array)
response.data.output_files.forEach(filePath => {
  // Had to construct URL manually
});

// NEW (Object array with download_url)
response.data.output_files.forEach(file => {
  console.log(file.download_url);  // Ready to use!
});
```

**Step 3:** Remove hardcoded hosts
```javascript
// OLD
const API_HOST = 'http://localhost:5050';
const downloadUrl = API_HOST + '/api/v1/files/download?path=' + encodeURIComponent(path);

// NEW (No hardcoding needed!)
const downloadUrl = response.data.download_url;  // Works in any environment!
```

---

## Testing Checklist

✅ Upload file → Check download_url is absolute  
✅ Click download_url → File downloads successfully  
✅ Execute workflow → Check results have download_urls  
✅ Execute workflow → Check output_files have download_urls  
✅ Dump conversation → Check download_url is absolute  
✅ Test with different file types (xlsx, csv, json, txt)  
✅ Verify security (path traversal attempts fail)  
✅ Test across environments (dev, staging, production)  

---

## Summary

**Before:** Relative URLs requiring manual construction  
**After:** Absolute, clickable URLs ready to use  

**Impact:**
- ✅ Simpler frontend integration
- ✅ No environment-specific configuration
- ✅ Direct download capability
- ✅ Better user experience
- ✅ Less error-prone code
