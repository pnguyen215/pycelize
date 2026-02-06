"""
Basic integration test for Chat Workflows feature
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.chat.database import ChatDatabase
from app.chat.storage import ConversationStorage
from app.chat.repository import ConversationRepository
from app.chat.models import MessageType


def test_chat_workflows_basic():
    """Test basic chat workflows functionality."""
    print("\n=== Testing Chat Workflows Feature ===\n")
    
    # Test 1: App creation
    print("1. Testing app creation...")
    app = create_app()
    assert app is not None
    print("   ✓ App created successfully")
    
    # Test 2: Configuration
    print("\n2. Testing configuration...")
    config = app.config.get("PYCELIZE")
    chat_config = config.get_section("chat_workflows")
    assert chat_config is not None
    assert chat_config.get("enabled") == True
    print("   ✓ Chat workflows enabled in configuration")
    
    # Test 3: Database initialization
    print("\n3. Testing database initialization...")
    db_path = "./automation/sqlite/test_chat.db"
    database = ChatDatabase(db_path)
    stats = database.get_stats()
    assert stats["total_conversations"] == 0
    print("   ✓ Database initialized successfully")
    print(f"   ✓ Stats: {stats}")
    
    # Test 4: Storage initialization
    print("\n4. Testing storage initialization...")
    storage = ConversationStorage("./automation/workflows", "time-based")
    assert storage is not None
    print("   ✓ Storage initialized successfully")
    
    # Test 5: Repository operations
    print("\n5. Testing repository operations...")
    repository = ConversationRepository(database, storage)
    
    # Create conversation
    conversation = repository.create_conversation("test-chat-001")
    assert conversation.chat_id == "test-chat-001"
    assert conversation.participant_name is not None
    print(f"   ✓ Created conversation: {conversation.chat_id}")
    print(f"   ✓ Participant name: {conversation.participant_name}")
    
    # Add message
    message = repository.add_message(
        "test-chat-001",
        MessageType.USER,
        "Test message"
    )
    assert message is not None
    print(f"   ✓ Added message: {message.message_id}")
    
    # Get conversation
    retrieved = repository.get_conversation("test-chat-001")
    assert retrieved is not None
    assert retrieved.chat_id == "test-chat-001"
    print("   ✓ Retrieved conversation successfully")
    
    # List conversations
    conversations = repository.list_conversations()
    assert len(conversations) > 0
    print(f"   ✓ Listed {len(conversations)} conversation(s)")
    
    # Delete conversation
    deleted = repository.delete_conversation("test-chat-001")
    assert deleted == True
    print("   ✓ Deleted conversation successfully")
    
    # Test 6: Name generator
    print("\n6. Testing name generator...")
    from app.chat.name_generator import NameGenerator
    
    names = NameGenerator.generate_batch(5)
    assert len(names) == 5
    assert all("-" in name for name in names)
    print(f"   ✓ Generated names: {', '.join(names)}")
    
    # Test 7: Workflow executor
    print("\n7. Testing workflow executor...")
    from app.chat.workflow_executor import WorkflowExecutor
    
    executor = WorkflowExecutor(config)
    assert executor is not None
    print("   ✓ Workflow executor initialized")
    
    # Cleanup
    print("\n8. Cleanup...")
    if os.path.exists(db_path):
        os.remove(db_path)
        print("   ✓ Test database removed")
    
    print("\n=== All Tests Passed! ===\n")


if __name__ == "__main__":
    try:
        test_chat_workflows_basic()
        print("✅ Chat Workflows feature is working correctly!\n")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}\n")
        import traceback
        traceback.print_exc()
        sys.exit(1)
