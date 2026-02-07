# WebSocket Usage Guide - Chat Workflows

## Overview

The WebSocket server is now **automatically activated** when you start the Pycelize application. It runs on port 5051 alongside the Flask REST API on port 5050.

## Quick Start

### 1. Start the Application

```bash
python run.py
```

You should see both servers in the startup banner:

```
╔═══════════════════════════════════════════════════════════════════╗
║   🚀 Pycelize - Excel/CSV Processing API                          ║
║   Version:    v0.0.1                                              ║
║   REST API:   http://127.0.0.1:5050                               ║
║   WebSocket:  ✓ Running on ws://127.0.0.1:5051                    ║
╚═══════════════════════════════════════════════════════════════════╝
```

### 2. Connect to WebSocket

**URL Format:**
```
ws://127.0.0.1:5051/chat/{chat_id}
```

**Example with Python:**

```python
import asyncio
import websockets
import json

async def connect_to_chat(chat_id):
    uri = f"ws://127.0.0.1:5051/chat/{chat_id}"
    
    async with websockets.connect(uri) as websocket:
        # Receive welcome message
        welcome = await websocket.recv()
        print(f"Connected: {welcome}")
        
        # Send messages
        await websocket.send(json.dumps({
            "type": "ping"
        }))
        
        # Receive responses
        response = await websocket.recv()
        print(f"Response: {response}")

asyncio.run(connect_to_chat("my-conversation-123"))
```

**Example with JavaScript:**

```javascript
const ws = new WebSocket('ws://127.0.0.1:5051/chat/my-conversation-123');

ws.onopen = () => {
    console.log('WebSocket connected');
};

ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    console.log('Received:', data);
    
    if (data.type === 'connected') {
        console.log('Chat ID:', data.chat_id);
    }
};

// Send ping
ws.send(JSON.stringify({ type: 'ping' }));
```

## Message Types

### Client → Server

#### 1. Ping
```json
{
  "type": "ping"
}
```
Response: `{"type": "pong"}`

#### 2. Subscribe to Different Chat
```json
{
  "type": "subscribe",
  "chat_id": "new-chat-id"
}
```
Response: New connection acknowledgment

### Server → Client

#### 1. Connected Acknowledgment
```json
{
  "type": "connected",
  "chat_id": "your-chat-id",
  "timestamp": "2026-02-06T18:00:00Z"
}
```

#### 2. Progress Update
```json
{
  "type": "progress",
  "step_id": "step-uuid",
  "progress": 45,
  "status": "running",
  "message": "Processing column 'customer_id'",
  "timestamp": "2026-02-06T18:00:15Z"
}
```

#### 3. Step Result
```json
{
  "type": "step_result",
  "step_id": "step-uuid",
  "result": {
    "output_file_path": "/path/to/output.xlsx"
  },
  "timestamp": "2026-02-06T18:00:30Z"
}
```

#### 4. Error
```json
{
  "type": "error",
  "step_id": "step-uuid",
  "message": "Column 'invalid_col' not found",
  "timestamp": "2026-02-06T18:00:45Z"
}
```

## Configuration

The WebSocket server is configured in `configs/application.yml`:

```yaml
chat_workflows:
  enabled: true
  max_connections: 10
  
  websocket:
    host: "127.0.0.1"
    port: 5051
    ping_interval: 30
    ping_timeout: 10
```

### Configuration Options

| Option | Default | Description |
|--------|---------|-------------|
| `enabled` | `true` | Enable/disable WebSocket server |
| `max_connections` | `10` | Maximum concurrent connections |
| `websocket.host` | `"127.0.0.1"` | WebSocket server host |
| `websocket.port` | `5051` | WebSocket server port |
| `websocket.ping_interval` | `30` | Ping interval in seconds |
| `websocket.ping_timeout` | `10` | Ping timeout in seconds |

## Testing WebSocket Connection

### Using Python

```bash
# Save this as test_websocket.py
cat > test_websocket.py << 'EOF'
import asyncio
import websockets
import json

async def test():
    async with websockets.connect("ws://127.0.0.1:5051/chat/test") as ws:
        # Wait for welcome
        msg = await ws.recv()
        print("Connected:", json.loads(msg))
        
        # Send ping
        await ws.send(json.dumps({"type": "ping"}))
        
        # Get pong
        pong = await ws.recv()
        print("Response:", json.loads(pong))

asyncio.run(test())
EOF

python test_websocket.py
```

### Using websocat (CLI tool)

```bash
# Install websocat
# Ubuntu/Debian: apt install websocat
# Or: cargo install websocat

# Connect
websocat ws://127.0.0.1:5051/chat/test-chat

# Send ping
{"type":"ping"}

# You'll receive:
{"type":"pong"}
```

### Using wscat (Node.js)

```bash
# Install wscat
npm install -g wscat

# Connect
wscat -c ws://127.0.0.1:5051/chat/test-chat

# Send ping
> {"type":"ping"}

# Receive pong
< {"type":"pong"}
```

## Integration with Chat Workflows

The WebSocket server integrates seamlessly with the Chat Workflows REST API:

### Workflow Execution with Real-time Updates

```python
import asyncio
import websockets
import requests
import json

async def execute_workflow_with_progress(chat_id):
    # 1. Create conversation via REST API
    response = requests.post('http://localhost:5050/api/v1/chat/workflows')
    chat_id = response.json()['data']['chat_id']
    
    # 2. Connect to WebSocket
    uri = f"ws://127.0.0.1:5051/chat/{chat_id}"
    async with websockets.connect(uri) as ws:
        # Listen for progress updates
        async def listen_for_updates():
            while True:
                msg = await ws.recv()
                data = json.loads(msg)
                if data['type'] == 'progress':
                    print(f"Progress: {data['progress']}% - {data['message']}")
                elif data['type'] == 'step_result':
                    print(f"Step completed: {data['result']}")
        
        # Start listening in background
        asyncio.create_task(listen_for_updates())
        
        # 3. Execute workflow via REST API
        # The progress will stream via WebSocket
        # ... execute workflow steps ...

asyncio.run(execute_workflow_with_progress("my-chat"))
```

## Troubleshooting

### WebSocket Not Starting

**Check if chat workflows is enabled:**
```bash
grep -A 5 "chat_workflows:" configs/application.yml
```

Should show `enabled: true`

**Check logs:**
```bash
# Look for WebSocket startup message
grep "WebSocket" logs/pycelize.log
```

### Connection Refused

**Verify server is running:**
```bash
netstat -tuln | grep 5051
```

Should show:
```
tcp  0  0  127.0.0.1:5051  0.0.0.0:*  LISTEN
```

**Test with curl:**
```bash
curl -i -N -H "Connection: Upgrade" \
     -H "Upgrade: websocket" \
     -H "Sec-WebSocket-Version: 13" \
     -H "Sec-WebSocket-Key: test" \
     http://127.0.0.1:5051/chat/test
```

### Max Connections Reached

If you see this message:
```json
{"type": "error", "message": "Maximum connections reached"}
```

Increase `max_connections` in `configs/application.yml` or close idle connections.

## Best Practices

1. **Always handle connection errors** - WebSocket connections can drop
2. **Implement reconnection logic** - Automatic reconnection on disconnect
3. **Use heartbeat (ping/pong)** - Keep connection alive
4. **Subscribe to specific chat IDs** - Don't use generic connections
5. **Handle message queuing** - Buffer messages during disconnection
6. **Log WebSocket events** - Debug connection issues

## Security Considerations

- WebSocket server currently runs on localhost (127.0.0.1)
- For production, consider:
  - SSL/TLS (wss:// instead of ws://)
  - Authentication tokens
  - Rate limiting
  - Origin validation
  - Message validation

## Performance

- Max 10 concurrent connections by default
- Ping interval: 30 seconds
- Automatic connection cleanup on disconnect
- Non-blocking async I/O

## Support

For issues or questions:
- Check logs: `logs/pycelize.log`
- Review configuration: `configs/application.yml`
- See README: Chat Workflows section
