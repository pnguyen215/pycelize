#!/usr/bin/env python3
"""
Test Script for Chat Workflow Fixes

This script tests:
1. File download endpoint (fix for Config object error)
2. WebSocket integration during workflow execution
"""

import asyncio
import json
import time
import websockets
from threading import Thread

# Configuration
BASE_URL = "http://localhost:5050/api/v1"
WS_URL = "ws://127.0.0.1:5051"


def test_download_endpoint():
    """Test file download endpoint fix."""
    import requests
    
    print("\n" + "="*70)
    print("TEST 1: File Download Endpoint (Config Object Fix)")
    print("="*70)
    
    # Step 1: Create conversation
    print("\n1. Creating conversation...")
    response = requests.post(f"{BASE_URL}/chat/workflows")
    if response.status_code != 201:
        print(f"❌ Failed to create conversation: {response.status_code}")
        print(response.text)
        return None
    
    data = response.json()
    chat_id = data["data"]["chat_id"]
    print(f"✅ Conversation created: {chat_id}")
    
    # Step 2: Upload file
    print("\n2. Uploading test file...")
    test_content = "postal_code,city\n10001,New York\n10002,New York\n10003,Boston\n"
    files = {"file": ("test_data.csv", test_content, "text/csv")}
    
    response = requests.post(
        f"{BASE_URL}/chat/workflows/{chat_id}/upload",
        files=files
    )
    
    if response.status_code != 200:
        print(f"❌ Failed to upload file: {response.status_code}")
        print(response.text)
        return None
    
    data = response.json()
    print(f"✅ File uploaded successfully")
    print(f"   Download URL: {data['data']['download_url']}")
    
    # Step 3: Test download endpoint
    print("\n3. Testing download endpoint...")
    download_url = data['data']['download_url']
    
    try:
        response = requests.get(download_url)
        
        if response.status_code == 200:
            print(f"✅ Download successful!")
            print(f"   Content length: {len(response.content)} bytes")
            print(f"   Content type: {response.headers.get('Content-Type')}")
            return chat_id
        else:
            print(f"❌ Download failed: {response.status_code}")
            print(f"   Error: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Download exception: {e}")
        return None


async def test_websocket_integration(chat_id):
    """Test WebSocket integration during workflow execution."""
    print("\n" + "="*70)
    print("TEST 2: WebSocket Integration During Workflow Execution")
    print("="*70)
    
    messages_received = []
    
    try:
        # Connect to WebSocket
        uri = f"{WS_URL}/chat/{chat_id}"
        print(f"\n1. Connecting to WebSocket: {uri}")
        
        async with websockets.connect(uri) as websocket:
            print("✅ WebSocket connected")
            
            # Receive welcome message
            welcome = await asyncio.wait_for(websocket.recv(), timeout=5.0)
            welcome_data = json.loads(welcome)
            print(f"✅ Received welcome: {welcome_data['type']}")
            
            # Start workflow execution in background thread
            print("\n2. Starting workflow execution...")
            
            import requests
            def execute_workflow():
                response = requests.post(
                    f"{BASE_URL}/chat/workflows/{chat_id}/execute",
                    json={
                        "steps": [
                            {
                                "operation": "excel/extract-columns-to-file",
                                "arguments": {
                                    "columns": ["postal_code"],
                                    "remove_duplicates": True
                                }
                            }
                        ]
                    }
                )
                print(f"\n   Workflow API response: {response.status_code}")
            
            thread = Thread(target=execute_workflow, daemon=True)
            thread.start()
            
            # Listen for WebSocket messages
            print("\n3. Listening for WebSocket messages...")
            print("   (Timeout after 30 seconds)")
            
            try:
                while True:
                    message = await asyncio.wait_for(websocket.recv(), timeout=30.0)
                    data = json.loads(message)
                    messages_received.append(data)
                    
                    msg_type = data.get("type", "unknown")
                    
                    if msg_type == "workflow_started":
                        print(f"\n   ✅ Received: workflow_started")
                        print(f"      Total steps: {data.get('total_steps')}")
                    
                    elif msg_type == "progress":
                        print(f"   ✅ Received: progress")
                        print(f"      Operation: {data.get('operation')}")
                        print(f"      Progress: {data.get('progress')}%")
                        print(f"      Status: {data.get('status')}")
                        print(f"      Message: {data.get('message')}")
                    
                    elif msg_type == "workflow_completed":
                        print(f"\n   ✅ Received: workflow_completed")
                        print(f"      Output files: {data.get('output_files_count')}")
                        break
                    
                    elif msg_type == "workflow_failed":
                        print(f"\n   ❌ Received: workflow_failed")
                        print(f"      Error: {data.get('error')}")
                        break
                        
            except asyncio.TimeoutError:
                print("\n   ⚠️  Timeout waiting for messages")
            
            # Wait for thread to finish
            thread.join(timeout=5.0)
            
    except Exception as e:
        print(f"\n❌ WebSocket error: {e}")
        import traceback
        traceback.print_exc()
    
    # Summary
    print("\n" + "="*70)
    print("WebSocket Test Summary")
    print("="*70)
    print(f"Total messages received: {len(messages_received)}")
    
    message_types = {}
    for msg in messages_received:
        msg_type = msg.get("type", "unknown")
        message_types[msg_type] = message_types.get(msg_type, 0) + 1
    
    print(f"\nMessage types received:")
    for msg_type, count in message_types.items():
        print(f"  - {msg_type}: {count}")
    
    # Check if we got the expected messages
    expected_types = ["workflow_started", "progress", "workflow_completed"]
    missing_types = [t for t in expected_types if t not in message_types]
    
    if missing_types:
        print(f"\n⚠️  Missing message types: {missing_types}")
        return False
    else:
        print(f"\n✅ All expected message types received!")
        return True


def main():
    """Main test function."""
    print("\n" + "="*70)
    print("CHAT WORKFLOWS FIX VERIFICATION")
    print("="*70)
    print("\nTesting two fixes:")
    print("1. Download endpoint (Config object error)")
    print("2. WebSocket integration during workflow execution")
    
    # Test 1: Download endpoint
    chat_id = test_download_endpoint()
    
    if not chat_id:
        print("\n❌ Test 1 failed - cannot proceed with Test 2")
        return
    
    # Give Flask time to process
    time.sleep(2)
    
    # Test 2: WebSocket integration
    result = asyncio.run(test_websocket_integration(chat_id))
    
    # Final summary
    print("\n" + "="*70)
    print("FINAL RESULTS")
    print("="*70)
    print(f"✅ Test 1: Download Endpoint - PASSED")
    print(f"{'✅' if result else '❌'} Test 2: WebSocket Integration - {'PASSED' if result else 'FAILED'}")
    print("="*70)


if __name__ == "__main__":
    main()
