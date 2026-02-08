"""
Test for chat bot file recognition bug fix
"""

import pytest
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.chat.chatbot_service import ChatBotService
from app.chat.database import ChatDatabase
from app.chat.storage import ConversationStorage
from app.chat.repository import ConversationRepository
from app.chat.streaming_executor import StreamingWorkflowExecutor
from app.core.config import Config


def test_file_upload_recognition_across_messages():
    """
    Test that uploaded files are recognized in subsequent message requests.
    
    This tests the bug fix where:
    1. User uploads a file
    2. User sends a message
    3. Bot should recognize the uploaded file (not ask to upload again)
    """
    # Setup
    config_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "configs", "application.yml"
    )
    config = Config(config_path)
    
    db_path = "./automation/sqlite/test_chatbot_bugfix.db"
    workflows_path = "./automation/workflows_test"
    
    # Clean up before test
    if os.path.exists(db_path):
        os.remove(db_path)
    
    database = ChatDatabase(db_path)
    storage = ConversationStorage(workflows_path, "time-based")
    repository = ConversationRepository(database, storage)
    executor = StreamingWorkflowExecutor(config)
    
    service = ChatBotService(repository, config, executor)
    
    # Test scenario
    # Step 1: Start conversation
    result = service.start_conversation()
    chat_id = result["chat_id"]
    assert chat_id is not None
    print(f"✓ Step 1: Created conversation {chat_id}")
    
    # Step 2: Upload a file
    fake_file_path = f"{workflows_path}/test_file.xlsx"
    os.makedirs(os.path.dirname(fake_file_path), exist_ok=True)
    with open(fake_file_path, "w") as f:
        f.write("fake excel content")
    
    upload_result = service.upload_file(chat_id, fake_file_path, "test_file.xlsx")
    assert upload_result["success"] is True
    assert "File uploaded successfully" in upload_result["bot_response"] or "uploaded successfully" in upload_result["bot_response"].lower()
    print(f"✓ Step 2: Uploaded file")
    
    # Verify file is in conversation
    conversation = repository.get_conversation(chat_id)
    assert fake_file_path in conversation.uploaded_files, "File should be in conversation.uploaded_files"
    print(f"✓ Step 2a: File persisted in conversation.uploaded_files")
    
    # Step 3: Send a message that requires a file
    message_result = service.send_message(chat_id, "extract columns: postal_code")
    assert message_result["success"] is True
    
    # The bot should NOT ask for file upload (requires_file should be False or not present)
    # It should suggest a workflow instead
    assert not message_result.get("requires_file", False), \
        "Bot should NOT ask for file upload since file was already uploaded"
    
    assert message_result.get("suggested_workflow") is not None, \
        "Bot should suggest a workflow since file is available"
    
    assert message_result.get("requires_confirmation", False) is True, \
        "Bot should ask for confirmation"
    
    print(f"✓ Step 3: Bot recognized uploaded file and suggested workflow")
    print(f"  Bot response: {message_result['bot_response'][:100]}...")
    
    # Step 4: Confirm workflow (this should also work now)
    modified_workflow = [
        {
            "operation": "excel/extract-columns",
            "arguments": {
                "columns": ["postal_code"],
                "remove_duplicates": True
            }
        }
    ]
    
    # Note: This will fail in actual execution since we don't have a real Excel file,
    # but we're testing that it finds the file and attempts execution
    confirm_result = service.confirm_workflow(chat_id, True, modified_workflow)
    
    # It should attempt to execute (not fail with "No uploaded file found")
    if not confirm_result.get("success"):
        # Check that the error is NOT about missing file
        error = confirm_result.get("error", "")
        assert "No uploaded file found" not in error, \
            "Should not fail with 'No uploaded file found' error"
        print(f"✓ Step 4: Workflow execution attempted (failed for other reason, which is expected)")
        print(f"  Error: {error[:100]}...")
    else:
        print(f"✓ Step 4: Workflow executed successfully")
    
    # Cleanup
    try:
        if os.path.exists(fake_file_path):
            os.remove(fake_file_path)
        if os.path.exists(db_path):
            os.remove(db_path)
    except:
        pass
    
    print("\n✅ All tests passed! Bug is fixed.")


if __name__ == "__main__":
    test_file_upload_recognition_across_messages()
