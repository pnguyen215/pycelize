#!/usr/bin/env python3
"""
Manual test script to verify conversational chat workflows
"""

import requests
import json
import time

BASE_URL = "http://localhost:5050/api/v1/chat"

def print_json(data):
    """Pretty print JSON data."""
    print(json.dumps(data, indent=2))

def main():
    print("=== Manual Test: Conversational Chat Workflows ===\n")
    
    # Test 1: Create conversation
    print("1. Creating new conversation...")
    response = requests.post(f"{BASE_URL}/workflows")
    assert response.status_code == 201
    data = response.json()
    chat_id = data['data']['chat_id']
    print(f"✓ Conversation created: {chat_id}")
    print(f"  Participant: {data['data']['participant_name']}\n")
    
    # Test 2: Get available operations
    print("2. Getting available operations...")
    response = requests.get(f"{BASE_URL}/workflow/operations")
    assert response.status_code == 200
    data = response.json()
    operations = data['data']['operations']
    print(f"✓ Found {len(operations)} operations")
    print(f"  Sample: {operations[0]['name']}\n")
    
    # Test 3: Send user message
    print("3. Sending user message...")
    response = requests.post(
        f"{BASE_URL}/workflows/{chat_id}/messages",
        json={"content": "I want to extract columns from my data"}
    )
    assert response.status_code == 200
    data = response.json()
    print(f"✓ User message sent")
    print(f"  System response: {data['data']['system_message']['content'][:100]}...")
    print(f"  Suggested operations: {len(data['data']['suggested_operations'])}\n")
    
    # Test 4: Get message history
    print("4. Getting message history...")
    response = requests.get(f"{BASE_URL}/workflows/{chat_id}/messages")
    assert response.status_code == 200
    data = response.json()
    messages = data['data']['messages']
    print(f"✓ Retrieved {len(messages)} messages")
    for i, msg in enumerate(messages[-3:], 1):
        print(f"  {i}. [{msg['sender_type']}] {msg['content'][:60]}...")
    
    print("\n=== All Tests Passed ===")

if __name__ == "__main__":
    try:
        main()
    except requests.exceptions.ConnectionError:
        print("❌ Error: Could not connect to server at http://localhost:5050")
        print("   Please start the server with: python run.py")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
