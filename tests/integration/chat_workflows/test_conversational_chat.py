"""
Integration test for Conversational Chat Workflows feature

Tests the new conversational message API, operation discovery,
and intelligent message processing.
"""

import sys
import os
import json
import pytest

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from app import create_app
from app.chat.database import ChatDatabase
from app.chat.storage import ConversationStorage
from app.chat.repository import ConversationRepository
from app.chat.message_service import MessageService
from app.chat.models import MessageType


def test_conversational_chat_workflows():
    """Test conversational chat workflows functionality."""
    print("\n=== Testing Conversational Chat Workflows ===\n")
    
    # Test 1: App creation with test client
    print("1. Testing Flask app with test client...")
    app = create_app()
    assert app is not None
    client = app.test_client()
    print("   ✓ App and test client created successfully")
    
    # Test 2: Create conversation
    print("\n2. Testing conversation creation...")
    response = client.post('/api/v1/chat/workflows')
    assert response.status_code == 201
    data = json.loads(response.data)
    assert 'data' in data
    assert 'message' in data
    chat_id = data['data']['chat_id']
    print(f"   ✓ Conversation created with ID: {chat_id}")
    print(f"   ✓ Participant: {data['data']['participant_name']}")
    
    # Test 3: Get workflow operations
    print("\n3. Testing workflow operations discovery...")
    response = client.get('/api/v1/chat/workflow/operations')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'data' in data
    assert 'operations' in data['data']
    operations = data['data']['operations']
    assert len(operations) > 0
    print(f"   ✓ Retrieved {len(operations)} available operations")
    print(f"   ✓ Sample operations: {[op['name'] for op in operations[:3]]}")
    
    # Test 4: Send user message
    print("\n4. Testing user message submission...")
    response = client.post(
        f'/api/v1/chat/workflows/{chat_id}/messages',
        json={'content': 'I want to extract columns from my data'}
    )
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'data' in data
    assert 'user_message' in data['data']
    assert 'system_message' in data['data']
    assert 'suggested_operations' in data['data']
    print(f"   ✓ User message sent successfully")
    print(f"   ✓ System response: {data['data']['system_message']['content'][:100]}...")
    print(f"   ✓ Suggested operations: {len(data['data']['suggested_operations'])}")
    
    # Test 5: Get message history
    print("\n5. Testing message history retrieval...")
    response = client.get(f'/api/v1/chat/workflows/{chat_id}/messages')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'data' in data
    assert 'messages' in data['data']
    messages = data['data']['messages']
    # Should have: welcome message + user message + system response
    assert len(messages) >= 3
    print(f"   ✓ Retrieved {len(messages)} messages")
    
    # Verify sender_type mapping
    has_user = any(msg['sender_type'] == 'user' for msg in messages)
    has_system = any(msg['sender_type'] == 'system' for msg in messages)
    assert has_user
    assert has_system
    print(f"   ✓ Messages contain both user and system sender types")
    
    # Test 6: Test different message intents
    print("\n6. Testing message intent analysis...")
    test_messages = [
        ('convert my data to JSON', 'json conversion'),
        ('normalize the column names', 'normalization'),
        ('generate SQL statements', 'SQL generation'),
        ('search for specific data', 'search functionality')
    ]
    
    for content, intent_desc in test_messages:
        response = client.post(
            f'/api/v1/chat/workflows/{chat_id}/messages',
            json={'content': content}
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        suggestions = data['data']['suggested_operations']
        print(f"   ✓ '{content}' -> {len(suggestions)} suggestions ({intent_desc})")
    
    # Test 7: Test MessageService directly
    print("\n7. Testing MessageService directly...")
    config = app.config.get("PYCELIZE")
    chat_config = config.get_section("chat_workflows")
    db_path = chat_config.get("storage", {}).get("sqlite_path", "./automation/sqlite/chat.db")
    workflows_path = chat_config.get("storage", {}).get("workflows_path", "./automation/workflows")
    partition_strategy = chat_config.get("partition", {}).get("strategy", "time-based")
    
    database = ChatDatabase(db_path)
    storage = ConversationStorage(workflows_path, partition_strategy)
    repository = ConversationRepository(database, storage)
    message_service = MessageService(repository)
    
    # Test operation discovery
    operations = MessageService.get_available_operations()
    assert len(operations) > 0
    print(f"   ✓ MessageService has {len(operations)} operations defined")
    
    # Test get operation by name
    extract_op = MessageService.get_operation_by_name('excel/extract-columns')
    assert extract_op is not None
    assert extract_op['display_name'] == 'Extract Columns to File'
    print(f"   ✓ Operation lookup works correctly")
    
    # Test 8: Test conversation not found error
    print("\n8. Testing error handling...")
    response = client.get('/api/v1/chat/workflows/nonexistent-id/messages')
    assert response.status_code == 404
    print(f"   ✓ Proper 404 error for nonexistent conversation")
    
    # Test 9: Test message validation
    response = client.post(
        f'/api/v1/chat/workflows/{chat_id}/messages',
        json={}
    )
    assert response.status_code == 422
    print(f"   ✓ Proper validation error for empty message")
    
    print("\n=== All Conversational Chat Tests Passed ===\n")


def test_message_service_suggestions():
    """Test MessageService suggestion logic in detail."""
    print("\n=== Testing MessageService Suggestions ===\n")
    
    app = create_app()
    config = app.config.get("PYCELIZE")
    chat_config = config.get_section("chat_workflows")
    db_path = chat_config.get("storage", {}).get("sqlite_path", "./automation/sqlite/chat.db")
    workflows_path = chat_config.get("storage", {}).get("workflows_path", "./automation/workflows")
    
    database = ChatDatabase(db_path)
    storage = ConversationStorage(workflows_path, "time-based")
    repository = ConversationRepository(database, storage)
    message_service = MessageService(repository)
    
    # Test 1: Extract keywords
    print("1. Testing 'extract' keyword suggestions...")
    suggestions = message_service._suggest_operations("extract columns")
    assert any('extract' in op['name'] for op in suggestions)
    print(f"   ✓ Found {len(suggestions)} suggestions")
    
    # Test 2: JSON conversion keywords
    print("\n2. Testing 'json' keyword suggestions...")
    suggestions = message_service._suggest_operations("convert to json")
    assert any('json' in op['name'] for op in suggestions)
    print(f"   ✓ Found {len(suggestions)} suggestions")
    
    # Test 3: SQL keywords
    print("\n3. Testing 'sql' keyword suggestions...")
    suggestions = message_service._suggest_operations("generate sql")
    assert any('sql' in op['name'] for op in suggestions)
    print(f"   ✓ Found {len(suggestions)} suggestions")
    
    # Test 4: Default suggestions (no keywords)
    print("\n4. Testing default suggestions...")
    suggestions = message_service._suggest_operations("help me")
    assert len(suggestions) > 0
    print(f"   ✓ Found {len(suggestions)} default suggestions")
    
    # Test 5: Operation formatting
    print("\n5. Testing operation formatting...")
    formatted = message_service._generate_operation_suggestions(suggestions[:2])
    assert "**" in formatted  # Should have markdown formatting
    assert "Required:" in formatted or "operations:" in formatted
    print(f"   ✓ Formatted suggestions properly")
    
    print("\n=== MessageService Suggestions Tests Passed ===\n")


def test_database_message_persistence():
    """Test message persistence in database."""
    print("\n=== Testing Message Persistence ===\n")
    
    app = create_app()
    config = app.config.get("PYCELIZE")
    chat_config = config.get_section("chat_workflows")
    db_path = "./automation/sqlite/test_messages.db"
    
    # Clean up any existing test db
    if os.path.exists(db_path):
        os.remove(db_path)
    
    database = ChatDatabase(db_path)
    storage = ConversationStorage("./automation/workflows", "time-based")
    repository = ConversationRepository(database, storage)
    
    # Test 1: Create conversation
    print("1. Creating test conversation...")
    import uuid
    chat_id = str(uuid.uuid4())
    conversation = repository.create_conversation(chat_id)
    print(f"   ✓ Conversation created: {chat_id}")
    
    # Test 2: Add user message
    print("\n2. Adding user message...")
    user_msg = repository.add_message(
        chat_id=chat_id,
        message_type=MessageType.USER,
        content="Test user message",
        metadata={"test": True}
    )
    assert user_msg.message_id is not None
    print(f"   ✓ User message added: {user_msg.message_id}")
    
    # Test 3: Add system message
    print("\n3. Adding system message...")
    system_msg = repository.add_message(
        chat_id=chat_id,
        message_type=MessageType.SYSTEM,
        content="Test system response",
        metadata={"test": True}
    )
    assert system_msg.message_id is not None
    print(f"   ✓ System message added: {system_msg.message_id}")
    
    # Test 4: Retrieve messages
    print("\n4. Retrieving messages...")
    messages = repository.get_messages(chat_id)
    assert len(messages) == 2
    print(f"   ✓ Retrieved {len(messages)} messages")
    
    # Verify message order (should be chronological)
    assert messages[0].message_type == MessageType.USER
    assert messages[1].message_type == MessageType.SYSTEM
    print(f"   ✓ Messages in correct chronological order")
    
    # Test 5: Pagination
    print("\n5. Testing pagination...")
    messages_page1 = repository.get_messages(chat_id, limit=1, offset=0)
    messages_page2 = repository.get_messages(chat_id, limit=1, offset=1)
    assert len(messages_page1) == 1
    assert len(messages_page2) == 1
    assert messages_page1[0].message_id != messages_page2[0].message_id
    print(f"   ✓ Pagination works correctly")
    
    # Test 6: Database stats
    print("\n6. Checking database stats...")
    stats = database.get_stats()
    assert stats['total_messages'] == 2
    assert stats['total_conversations'] == 1
    print(f"   ✓ Database stats: {stats}")
    
    # Cleanup
    if os.path.exists(db_path):
        os.remove(db_path)
    
    print("\n=== Message Persistence Tests Passed ===\n")


if __name__ == "__main__":
    # Run tests
    test_conversational_chat_workflows()
    test_message_service_suggestions()
    test_database_message_persistence()
    print("\n✓✓✓ All Tests Passed Successfully ✓✓✓\n")
