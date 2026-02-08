"""
Unit tests for ConversationStateManager
"""

import pytest
from datetime import datetime
from app.chat.state_manager import (
    ConversationStateManager,
    BotState,
    ConversationContext
)


class TestConversationStateManager:
    """Test suite for ConversationStateManager."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.manager = ConversationStateManager()
        self.chat_id = "test-chat-123"
    
    def test_initialization(self):
        """Test state manager initialization."""
        assert self.manager is not None
        assert len(self.manager._contexts) == 0
    
    def test_get_or_create_context(self):
        """Test creating new conversation context."""
        context = self.manager.get_or_create_context(self.chat_id)
        
        assert context is not None
        assert context.chat_id == self.chat_id
        assert context.current_state == BotState.IDLE
        assert context.previous_state is None
        assert len(context.uploaded_files) == 0
    
    def test_get_or_create_context_idempotent(self):
        """Test that get_or_create_context is idempotent."""
        context1 = self.manager.get_or_create_context(self.chat_id)
        context2 = self.manager.get_or_create_context(self.chat_id)
        
        assert context1 is context2
        assert id(context1) == id(context2)
    
    def test_get_context(self):
        """Test getting existing context."""
        # Create context first
        self.manager.get_or_create_context(self.chat_id)
        
        # Get it
        context = self.manager.get_context(self.chat_id)
        assert context is not None
        assert context.chat_id == self.chat_id
    
    def test_get_context_nonexistent(self):
        """Test getting non-existent context."""
        context = self.manager.get_context("nonexistent")
        assert context is None
    
    def test_transition_state_valid(self):
        """Test valid state transitions."""
        context = self.manager.get_or_create_context(self.chat_id)
        
        # IDLE -> AWAITING_FILE
        success = self.manager.transition_state(self.chat_id, BotState.AWAITING_FILE)
        assert success is True
        assert context.current_state == BotState.AWAITING_FILE
        assert context.previous_state == BotState.IDLE
        
        # AWAITING_FILE -> AWAITING_CONFIRMATION
        success = self.manager.transition_state(self.chat_id, BotState.AWAITING_CONFIRMATION)
        assert success is True
        assert context.current_state == BotState.AWAITING_CONFIRMATION
        assert context.previous_state == BotState.AWAITING_FILE
    
    def test_transition_state_invalid(self):
        """Test invalid state transitions."""
        context = self.manager.get_or_create_context(self.chat_id)
        
        # Try invalid transition: IDLE -> PROCESSING (not allowed)
        success = self.manager.transition_state(self.chat_id, BotState.PROCESSING)
        assert success is False
        assert context.current_state == BotState.IDLE  # Should remain unchanged
    
    def test_transition_state_updates_timestamp(self):
        """Test that state transition updates timestamp."""
        context = self.manager.get_or_create_context(self.chat_id)
        
        old_time = context.last_message_time
        self.manager.transition_state(self.chat_id, BotState.AWAITING_FILE)
        new_time = context.last_message_time
        
        assert new_time is not None
        assert new_time != old_time
    
    def test_set_pending_workflow(self):
        """Test setting pending workflow."""
        steps = [
            {"operation": "excel/extract-columns", "arguments": {}},
            {"operation": "csv/convert-to-excel", "arguments": {}}
        ]
        
        self.manager.set_pending_workflow(self.chat_id, steps)
        
        context = self.manager.get_context(self.chat_id)
        assert context.pending_workflow == steps
    
    def test_get_pending_workflow(self):
        """Test getting pending workflow."""
        steps = [{"operation": "test", "arguments": {}}]
        self.manager.set_pending_workflow(self.chat_id, steps)
        
        retrieved = self.manager.get_pending_workflow(self.chat_id)
        assert retrieved == steps
    
    def test_clear_pending_workflow(self):
        """Test clearing pending workflow."""
        steps = [{"operation": "test", "arguments": {}}]
        self.manager.set_pending_workflow(self.chat_id, steps)
        self.manager.clear_pending_workflow(self.chat_id)
        
        context = self.manager.get_context(self.chat_id)
        assert context.pending_workflow is None
    
    def test_add_uploaded_file(self):
        """Test adding uploaded file."""
        file_path = "/path/to/file.xlsx"
        
        self.manager.add_uploaded_file(self.chat_id, file_path)
        
        context = self.manager.get_context(self.chat_id)
        assert file_path in context.uploaded_files
    
    def test_get_latest_file(self):
        """Test getting latest uploaded file."""
        files = ["/file1.xlsx", "/file2.xlsx", "/file3.xlsx"]
        
        for file in files:
            self.manager.add_uploaded_file(self.chat_id, file)
        
        latest = self.manager.get_latest_file(self.chat_id)
        assert latest == files[-1]
    
    def test_get_latest_file_no_files(self):
        """Test getting latest file when none exist."""
        latest = self.manager.get_latest_file(self.chat_id)
        assert latest is None
    
    def test_add_intent(self):
        """Test adding intent to history."""
        intent = {
            "intent_type": "extract_columns",
            "confidence": 0.9,
            "message": "extract columns"
        }
        
        self.manager.add_intent(self.chat_id, intent)
        
        context = self.manager.get_context(self.chat_id)
        assert len(context.intent_history) == 1
        assert "timestamp" in context.intent_history[0]
    
    def test_get_recent_intents(self):
        """Test getting recent intents."""
        intents = [
            {"intent_type": f"intent_{i}", "confidence": 0.9}
            for i in range(10)
        ]
        
        for intent in intents:
            self.manager.add_intent(self.chat_id, intent)
        
        recent = self.manager.get_recent_intents(self.chat_id, limit=5)
        assert len(recent) == 5
        assert recent[-1]["intent_type"] == "intent_9"
    
    def test_set_workflow_params(self):
        """Test setting workflow parameters."""
        params = {"columns": ["name", "email"], "remove_duplicates": True}
        
        self.manager.set_workflow_params(self.chat_id, params)
        
        retrieved = self.manager.get_workflow_params(self.chat_id)
        assert retrieved == params
    
    def test_clear_workflow_params(self):
        """Test clearing workflow parameters."""
        params = {"test": "value"}
        self.manager.set_workflow_params(self.chat_id, params)
        self.manager.clear_workflow_params(self.chat_id)
        
        retrieved = self.manager.get_workflow_params(self.chat_id)
        assert retrieved == {}
    
    def test_set_user_preference(self):
        """Test setting user preference."""
        self.manager.set_user_preference(self.chat_id, "theme", "dark")
        
        value = self.manager.get_user_preference(self.chat_id, "theme")
        assert value == "dark"
    
    def test_get_user_preference_default(self):
        """Test getting user preference with default."""
        value = self.manager.get_user_preference(
            self.chat_id, "nonexistent", default="default_value"
        )
        assert value == "default_value"
    
    def test_reset_context(self):
        """Test resetting conversation context."""
        # Create context and add data
        self.manager.add_uploaded_file(self.chat_id, "/file.xlsx")
        self.manager.add_intent(self.chat_id, {"test": "intent"})
        
        # Reset
        self.manager.reset_context(self.chat_id)
        
        # Context should be gone
        context = self.manager.get_context(self.chat_id)
        assert context is None
    
    def test_is_processing(self):
        """Test checking if conversation is processing."""
        context = self.manager.get_or_create_context(self.chat_id)
        
        assert self.manager.is_processing(self.chat_id) is False
        
        self.manager.transition_state(self.chat_id, BotState.AWAITING_CONFIRMATION)
        self.manager.transition_state(self.chat_id, BotState.PROCESSING)
        
        assert self.manager.is_processing(self.chat_id) is True
    
    def test_is_awaiting_input(self):
        """Test checking if conversation is awaiting input."""
        context = self.manager.get_or_create_context(self.chat_id)
        
        # IDLE is not awaiting input
        assert self.manager.is_awaiting_input(self.chat_id) is False
        
        # AWAITING_FILE is awaiting input
        self.manager.transition_state(self.chat_id, BotState.AWAITING_FILE)
        assert self.manager.is_awaiting_input(self.chat_id) is True
        
        # AWAITING_CONFIRMATION is awaiting input
        self.manager.transition_state(self.chat_id, BotState.AWAITING_CONFIRMATION)
        assert self.manager.is_awaiting_input(self.chat_id) is True
    
    def test_get_state_description(self):
        """Test getting state description."""
        context = self.manager.get_or_create_context(self.chat_id)
        
        desc = self.manager.get_state_description(self.chat_id)
        assert isinstance(desc, str)
        assert len(desc) > 0
        
        # Change state and check description changes
        self.manager.transition_state(self.chat_id, BotState.AWAITING_FILE)
        desc2 = self.manager.get_state_description(self.chat_id)
        assert desc != desc2
    
    def test_get_all_contexts(self):
        """Test getting all contexts."""
        chat_ids = ["chat1", "chat2", "chat3"]
        
        for chat_id in chat_ids:
            self.manager.get_or_create_context(chat_id)
        
        contexts = self.manager.get_all_contexts()
        assert len(contexts) == 3
        assert all(cid in contexts for cid in chat_ids)
    
    def test_cleanup_old_contexts(self):
        """Test cleaning up old contexts."""
        # Create completed context
        context1 = self.manager.get_or_create_context("chat1")
        context1.current_state = BotState.COMPLETED
        context1.last_message_time = datetime(2020, 1, 1)  # Old timestamp
        
        # Create active context
        context2 = self.manager.get_or_create_context("chat2")
        context2.current_state = BotState.IDLE
        context2.last_message_time = datetime.utcnow()
        
        # Cleanup
        removed = self.manager.cleanup_old_contexts(max_age_seconds=1)
        
        assert removed == 1
        assert self.manager.get_context("chat1") is None
        assert self.manager.get_context("chat2") is not None
    
    def test_context_to_dict(self):
        """Test converting context to dictionary."""
        context = self.manager.get_or_create_context(self.chat_id)
        self.manager.add_uploaded_file(self.chat_id, "/file.xlsx")
        
        context_dict = context.to_dict()
        
        assert isinstance(context_dict, dict)
        assert context_dict["chat_id"] == self.chat_id
        assert context_dict["current_state"] == BotState.IDLE.value
        assert "/file.xlsx" in context_dict["uploaded_files"]
    
    def test_state_transitions_workflow(self):
        """Test complete workflow state transitions."""
        # Start new conversation
        context = self.manager.get_or_create_context(self.chat_id)
        assert context.current_state == BotState.IDLE
        
        # User requests something, needs file
        self.manager.transition_state(self.chat_id, BotState.AWAITING_FILE)
        assert context.current_state == BotState.AWAITING_FILE
        
        # User uploads file
        self.manager.add_uploaded_file(self.chat_id, "/file.xlsx")
        
        # Bot suggests workflow
        self.manager.transition_state(self.chat_id, BotState.AWAITING_CONFIRMATION)
        assert context.current_state == BotState.AWAITING_CONFIRMATION
        
        # User confirms
        self.manager.transition_state(self.chat_id, BotState.PROCESSING)
        assert context.current_state == BotState.PROCESSING
        
        # Workflow completes
        self.manager.transition_state(self.chat_id, BotState.COMPLETED)
        assert context.current_state == BotState.COMPLETED
        
        # Back to idle for next request
        self.manager.transition_state(self.chat_id, BotState.IDLE)
        assert context.current_state == BotState.IDLE


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
