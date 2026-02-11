"""
Unit test to verify step_id mapping in output_files
"""

import pytest
import json
from unittest.mock import Mock, patch
from app import create_app


class TestOutputFilesStepIdMapping:
    """Test step_id mapping in conversation history output_files."""
    
    @pytest.fixture
    def app(self):
        """Create test application."""
        app = create_app()
        app.config['TESTING'] = True
        return app
    
    @pytest.fixture
    def client(self, app):
        """Create test client."""
        return app.test_client()
    
    def test_output_files_with_matching_workflow_steps(self, client):
        """Test that output_files get step_id from matching workflow_steps."""
        
        # Mock the chatbot service to return data with workflow steps and output files
        mock_result = {
            "success": True,
            "chat_id": "test-chat-123",
            "participant_name": "TestUser",
            "status": "completed",
            "current_state": "idle",
            "messages": [],
            "uploaded_files": [],
            "output_files": [
                "./automation/workflows/2026/02/test-chat/outputs/file1.xlsx",
                "./automation/workflows/2026/02/test-chat/outputs/file2.xlsx",
                "./automation/workflows/2026/02/test-chat/intermediate/file3.xlsx",
            ],
            "workflow_steps": [
                {
                    "step_id": "step-001",
                    "operation": "excel/extract-columns",
                    "arguments": {"columns": ["name"]},
                    "output_file": "./automation/workflows/2026/02/test-chat/outputs/file1.xlsx",
                    "status": "completed",
                    "progress": 100,
                    "error_message": None,
                    "input_file": None,
                    "started_at": None,
                    "completed_at": "2026-02-11T10:00:00",
                },
                {
                    "step_id": "step-002",
                    "operation": "excel/extract-columns",
                    "arguments": {"columns": ["email"]},
                    "output_file": "./automation/workflows/2026/02/test-chat/outputs/file2.xlsx",
                    "status": "completed",
                    "progress": 100,
                    "error_message": None,
                    "input_file": None,
                    "started_at": None,
                    "completed_at": "2026-02-11T10:01:00",
                },
                {
                    "step_id": "step-003",
                    "operation": "excel/extract-columns",
                    "arguments": {"columns": ["phone"]},
                    "output_file": "./automation/workflows/2026/02/test-chat/intermediate/file3.xlsx",
                    "status": "completed",
                    "progress": 100,
                    "error_message": None,
                    "input_file": None,
                    "started_at": None,
                    "completed_at": "2026-02-11T10:02:00",
                },
            ],
        }
        
        # Create a conversation first
        create_response = client.post('/api/v1/chat/bot/conversations', json={})
        chat_id = json.loads(create_response.data)['data']['chat_id']
        
        # Mock the get_conversation_history method
        with patch('app.chat.chatbot_service.ChatBotService.get_conversation_history') as mock_get_history:
            mock_get_history.return_value = mock_result
            
            # Get history
            response = client.get(f'/api/v1/chat/bot/conversations/{chat_id}/history')
            
            assert response.status_code == 200
            data = json.loads(response.data)
            
            # Verify response structure
            assert data['status_code'] == 200
            assert 'output_files' in data['data']
            assert 'workflow_steps' in data['data']
            
            output_files = data['data']['output_files']
            workflow_steps = data['data']['workflow_steps']
            
            # Verify we have 3 output files
            assert len(output_files) == 3
            
            # Verify each output file has the expected fields
            for output_file in output_files:
                assert 'file_path' in output_file
                assert 'download_url' in output_file
                assert 'step_id' in output_file, "step_id should be present for matched files"
            
            # Verify specific step_id mappings
            output_file_by_path = {of['file_path']: of for of in output_files}
            
            file1_path = "./automation/workflows/2026/02/test-chat/outputs/file1.xlsx"
            assert output_file_by_path[file1_path]['step_id'] == "step-001"
            
            file2_path = "./automation/workflows/2026/02/test-chat/outputs/file2.xlsx"
            assert output_file_by_path[file2_path]['step_id'] == "step-002"
            
            file3_path = "./automation/workflows/2026/02/test-chat/intermediate/file3.xlsx"
            assert output_file_by_path[file3_path]['step_id'] == "step-003"
    
    def test_output_files_without_matching_workflow_steps(self, client):
        """Test output_files when there are no matching workflow steps."""
        
        mock_result = {
            "success": True,
            "chat_id": "test-chat-456",
            "participant_name": "TestUser",
            "status": "completed",
            "current_state": "idle",
            "messages": [],
            "uploaded_files": [],
            "output_files": [
                "./automation/workflows/2026/02/test-chat/outputs/orphan_file.xlsx",
            ],
            "workflow_steps": [
                {
                    "step_id": "step-999",
                    "operation": "excel/extract-columns",
                    "arguments": {"columns": ["name"]},
                    "output_file": "./automation/workflows/2026/02/test-chat/outputs/different_file.xlsx",
                    "status": "completed",
                    "progress": 100,
                    "error_message": None,
                    "input_file": None,
                    "started_at": None,
                    "completed_at": "2026-02-11T10:00:00",
                },
            ],
        }
        
        # Create a conversation first
        create_response = client.post('/api/v1/chat/bot/conversations', json={})
        chat_id = json.loads(create_response.data)['data']['chat_id']
        
        # Mock the get_conversation_history method
        with patch('app.chat.chatbot_service.ChatBotService.get_conversation_history') as mock_get_history:
            mock_get_history.return_value = mock_result
            
            # Get history
            response = client.get(f'/api/v1/chat/bot/conversations/{chat_id}/history')
            
            assert response.status_code == 200
            data = json.loads(response.data)
            
            output_files = data['data']['output_files']
            
            # Verify we have 1 output file
            assert len(output_files) == 1
            
            # The orphan file should not have a step_id since there's no matching workflow step
            orphan_file = output_files[0]
            assert 'file_path' in orphan_file
            assert 'download_url' in orphan_file
            assert 'step_id' not in orphan_file, "step_id should not be present for unmatched files"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
