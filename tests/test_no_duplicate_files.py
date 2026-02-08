"""
Test for duplicate files bug fix
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.chat.chatbot_service import ChatBotService
from app.chat.database import ChatDatabase
from app.chat.storage import ConversationStorage
from app.chat.repository import ConversationRepository
from app.chat.streaming_executor import StreamingWorkflowExecutor
from app.core.config import Config


def test_no_duplicate_files():
    """
    Test that uploading the same file multiple times doesn't create duplicates.
    """
    # Setup
    config_path = "configs/application.yml"
    config = Config(config_path)

    db_path = "./automation/sqlite/test_no_duplicate_files.db"
    workflows_path = "./automation/workflows_test_duplicates"

    # Clean up before test
    if os.path.exists(db_path):
        os.remove(db_path)

    database = ChatDatabase(db_path)
    storage = ConversationStorage(workflows_path, "time-based")
    repository = ConversationRepository(database, storage)
    executor = StreamingWorkflowExecutor(config)

    chatbot_service = ChatBotService(repository, config, executor)

    print("\n" + "=" * 70)
    print("TEST: No Duplicate Files")
    print("=" * 70)

    # Step 1: Start conversation
    print("\n[1] Create conversation")
    result = chatbot_service.start_conversation()
    chat_id = result["chat_id"]
    print(f"    ✓ Created conversation: {chat_id}")

    # Step 2: Upload same file multiple times
    print("\n[2] Upload same file 3 times")
    fake_file = f"{workflows_path}/test_file.xlsx"
    os.makedirs(os.path.dirname(fake_file), exist_ok=True)
    with open(fake_file, "w") as f:
        f.write("test content")

    for i in range(3):
        result = chatbot_service.upload_file(chat_id, fake_file, "test_file.xlsx")
        assert result["success"] is True
        print(f"    ✓ Upload {i + 1} completed")

    # Step 3: Check for duplicates
    print("\n[3] Verify no duplicates in database")
    conversation = repository.get_conversation(chat_id)

    uploaded_files = conversation.uploaded_files
    print(f"    ✓ Found {len(uploaded_files)} files in conversation.uploaded_files")

    # Should only have 1 file (no duplicates)
    assert len(uploaded_files) == 1, f"Expected 1 file but found {len(uploaded_files)}"
    print(f"    ✓ No duplicate files! Only 1 file stored.")

    # Also check database directly
    files_from_db = database.get_files(chat_id)
    uploaded_from_db = files_from_db.get("uploaded", [])
    print(f"    ✓ Database has {len(uploaded_from_db)} uploaded files")
    assert len(uploaded_from_db) == 1, f"Expected 1 file in DB but found {len(uploaded_from_db)}"

    print("\n" + "=" * 70)
    print("✅ TEST PASSED: No duplicate files!")
    print("=" * 70)

    # Cleanup
    try:
        if os.path.exists(fake_file):
            os.remove(fake_file)
        if os.path.exists(db_path):
            os.remove(db_path)
        import shutil

        if os.path.exists(workflows_path):
            shutil.rmtree(workflows_path)
    except:
        pass


if __name__ == "__main__":
    test_no_duplicate_files()
