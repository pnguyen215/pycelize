"""
Test for message persistence bug fix
"""

import pytest
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.chat.chatbot_service import ChatBotService
from app.chat.database import ChatDatabase
from app.chat.storage import ConversationStorage
from app.chat.repository import ConversationRepository
from app.chat.streaming_executor import StreamingWorkflowExecutor
from app.core.config import Config


def test_messages_persist_and_load():
    """
    Test that messages are persisted to database and loaded correctly.

    This tests the bug fix where messages were not being saved to the database,
    causing conversation history to return empty messages array.
    """
    # Setup
    config_path = "configs/application.yml"
    config = Config(config_path)

    db_path = "./automation/sqlite/test_message_persistence.db"
    workflows_path = "./automation/workflows_test_messages"

    # Clean up before test
    if os.path.exists(db_path):
        os.remove(db_path)

    database = ChatDatabase(db_path)
    storage = ConversationStorage(workflows_path, "time-based")
    repository = ConversationRepository(database, storage)
    executor = StreamingWorkflowExecutor(config)

    chatbot_service = ChatBotService(repository, config, executor)

    print("\n" + "=" * 70)
    print("TEST: Message Persistence and Loading")
    print("=" * 70)

    # Step 1: Start conversation
    print("\n[1] Create conversation")
    result = chatbot_service.start_conversation()
    chat_id = result["chat_id"]
    print(f"    ✓ Created conversation: {chat_id}")

    # Step 2: Send messages
    print("\n[2] Send messages to bot")
    messages_sent = [
        "Hello bot!",
        "extract columns: name, email",
        "help",
    ]

    for msg in messages_sent:
        response = chatbot_service.send_message(chat_id, msg)
        print(f"    ✓ Sent: '{msg}'")

    # Step 3: Check messages are in database
    print("\n[3] Verify messages saved to database")
    messages_from_db = database.get_messages(chat_id)
    print(f"    ✓ Found {len(messages_from_db)} messages in database")

    # Should have at least the user messages + bot responses + welcome message
    assert len(messages_from_db) > 0, "Messages should be saved to database"
    print(f"    ✓ Messages successfully saved to database")

    # Step 4: Get conversation history (this creates a NEW service instance)
    print("\n[4] Get conversation history (simulates new HTTP request)")
    # Create new service to simulate fresh request
    chatbot_service2 = ChatBotService(repository, config, executor)
    history = chatbot_service2.get_conversation_history(chat_id)

    print(f"    ✓ Retrieved history with {len(history['messages'])} messages")

    # Verify messages are loaded
    assert len(history["messages"]) > 0, "Messages should be loaded from database"
    assert len(history["messages"]) == len(
        messages_from_db
    ), "All messages should be loaded"

    # Verify message content
    for msg in history["messages"]:
        assert "message_id" in msg
        assert "message_type" in msg
        assert "content" in msg
        assert "created_at" in msg
        print(f"    ✓ Message: {msg['message_type']} - {msg['content'][:50]}...")

    print("\n" + "=" * 70)
    print("✅ TEST PASSED: Messages persist and load correctly!")
    print("=" * 70)

    # Cleanup
    try:
        if os.path.exists(db_path):
            os.remove(db_path)
        import shutil

        if os.path.exists(workflows_path):
            shutil.rmtree(workflows_path)
    except:
        pass


if __name__ == "__main__":
    test_messages_persist_and_load()
