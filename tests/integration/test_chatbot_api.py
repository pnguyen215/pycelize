"""
Integration tests for Chat Bot API endpoints
"""

import pytest
import json
import os
import sys
from io import BytesIO

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app


@pytest.fixture
def app():
    """Create test application."""
    app = create_app()
    app.config['TESTING'] = True
    return app


@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()


class TestChatBotAPIEndpoints:
    """Integration tests for Chat Bot API endpoints."""
    
    def test_create_bot_conversation(self, client):
        """Test creating a new bot conversation."""
        response = client.post(
            '/api/v1/chat/bot/conversations',
            json={}
        )
        
        assert response.status_code == 201
        data = json.loads(response.data)
        
        assert data['status_code'] == 201
        assert 'data' in data
        assert 'chat_id' in data['data']
        assert 'participant_name' in data['data']
        assert 'bot_message' in data['data']
        assert data['data']['state'] == 'idle'
        
        # Verify welcome message is present
        assert 'Welcome' in data['data']['bot_message']
    
    def test_send_message_extract_columns(self, client):
        """Test sending extract columns message to bot."""
        # Create conversation
        create_response = client.post('/api/v1/chat/bot/conversations', json={})
        chat_id = json.loads(create_response.data)['data']['chat_id']
        
        # Send message
        response = client.post(
            f'/api/v1/chat/bot/conversations/{chat_id}/message',
            json={'message': 'extract columns: name, email, phone'}
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert data['status_code'] == 200
        assert 'bot_response' in data['data']
        assert 'intent' in data['data']
        assert data['data']['intent']['type'] == 'extract_columns'
        assert data['data']['requires_file'] is True
    
    def test_send_message_convert_json(self, client):
        """Test sending convert to JSON message to bot."""
        # Create conversation
        create_response = client.post('/api/v1/chat/bot/conversations', json={})
        chat_id = json.loads(create_response.data)['data']['chat_id']
        
        # Send message
        response = client.post(
            f'/api/v1/chat/bot/conversations/{chat_id}/message',
            json={'message': 'convert to JSON'}
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert 'intent' in data['data']
        assert data['data']['intent']['type'] == 'convert_format'
    
    def test_send_message_help(self, client):
        """Test sending help command to bot."""
        # Create conversation
        create_response = client.post('/api/v1/chat/bot/conversations', json={})
        chat_id = json.loads(create_response.data)['data']['chat_id']
        
        # Send help message
        response = client.post(
            f'/api/v1/chat/bot/conversations/{chat_id}/message',
            json={'message': 'help'}
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert 'bot_response' in data['data']
        assert 'help' in data['data']['bot_response'].lower()
    
    def test_send_empty_message(self, client):
        """Test sending empty message to bot."""
        # Create conversation
        create_response = client.post('/api/v1/chat/bot/conversations', json={})
        chat_id = json.loads(create_response.data)['data']['chat_id']
        
        # Send empty message
        response = client.post(
            f'/api/v1/chat/bot/conversations/{chat_id}/message',
            json={'message': ''}
        )
        
        assert response.status_code == 422
    
    def test_send_message_no_message_field(self, client):
        """Test sending request without message field."""
        # Create conversation
        create_response = client.post('/api/v1/chat/bot/conversations', json={})
        chat_id = json.loads(create_response.data)['data']['chat_id']
        
        # Send without message
        response = client.post(
            f'/api/v1/chat/bot/conversations/{chat_id}/message',
            json={}
        )
        
        assert response.status_code == 422
    
    def test_upload_file(self, client):
        """Test uploading file to bot conversation."""
        # Create conversation
        create_response = client.post('/api/v1/chat/bot/conversations', json={})
        chat_id = json.loads(create_response.data)['data']['chat_id']
        
        # Create fake Excel file
        fake_file = BytesIO(b'fake excel content')
        fake_file.name = 'test_data.xlsx'
        
        # Upload file
        response = client.post(
            f'/api/v1/chat/bot/conversations/{chat_id}/upload',
            data={'file': (fake_file, 'test_data.xlsx')},
            content_type='multipart/form-data'
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert data['status_code'] == 200
        assert 'file_path' in data['data']
        assert 'filename' in data['data']
        assert data['data']['filename'] == 'test_data.xlsx'
        assert 'download_url' in data['data']
        assert 'bot_response' in data['data']
    
    def test_upload_file_no_file(self, client):
        """Test uploading without file."""
        # Create conversation
        create_response = client.post('/api/v1/chat/bot/conversations', json={})
        chat_id = json.loads(create_response.data)['data']['chat_id']
        
        # Upload without file
        response = client.post(
            f'/api/v1/chat/bot/conversations/{chat_id}/upload',
            data={},
            content_type='multipart/form-data'
        )
        
        assert response.status_code == 422
    
    def test_confirm_workflow(self, client):
        """Test confirming workflow with async execution."""
        # Create conversation
        create_response = client.post('/api/v1/chat/bot/conversations', json={})
        chat_id = json.loads(create_response.data)['data']['chat_id']
        
        # Confirm (even though there's no pending workflow)
        response = client.post(
            f'/api/v1/chat/bot/conversations/{chat_id}/confirm',
            json={'confirmed': True}
        )
        
        # Should fail because no pending workflow
        assert response.status_code == 400
    
    def test_decline_workflow(self, client):
        """Test declining workflow."""
        # Create conversation
        create_response = client.post('/api/v1/chat/bot/conversations', json={})
        chat_id = json.loads(create_response.data)['data']['chat_id']
        
        # Decline
        response = client.post(
            f'/api/v1/chat/bot/conversations/{chat_id}/confirm',
            json={'confirmed': False}
        )
        
        assert response.status_code == 200
    
    def test_get_workflow_job_status(self, client):
        """Test getting workflow job status."""
        # Create conversation
        create_response = client.post('/api/v1/chat/bot/conversations', json={})
        chat_id = json.loads(create_response.data)['data']['chat_id']
        
        # Try to get status of non-existent job
        response = client.get(
            f'/api/v1/chat/bot/conversations/{chat_id}/workflow/status/nonexistent-job-id'
        )
        
        # Should return 404 for non-existent job
        assert response.status_code == 404
    
    def test_get_conversation_history(self, client):
        """Test getting conversation history."""
        # Create conversation
        create_response = client.post('/api/v1/chat/bot/conversations', json={})
        chat_id = json.loads(create_response.data)['data']['chat_id']
        
        # Send a message
        client.post(
            f'/api/v1/chat/bot/conversations/{chat_id}/message',
            json={'message': 'help'}
        )
        
        # Get history
        response = client.get(
            f'/api/v1/chat/bot/conversations/{chat_id}/history'
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert data['status_code'] == 200
        assert 'messages' in data['data']
        assert len(data['data']['messages']) >= 2  # Welcome + help response
        assert 'participant_name' in data['data']
        assert 'current_state' in data['data']
    
    def test_get_conversation_history_with_limit(self, client):
        """Test getting conversation history with limit."""
        # Create conversation
        create_response = client.post('/api/v1/chat/bot/conversations', json={})
        chat_id = json.loads(create_response.data)['data']['chat_id']
        
        # Send multiple messages
        for i in range(5):
            client.post(
                f'/api/v1/chat/bot/conversations/{chat_id}/message',
                json={'message': f'message {i}'}
            )
        
        # Get history with limit
        response = client.get(
            f'/api/v1/chat/bot/conversations/{chat_id}/history?limit=3'
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        # Should respect limit
        assert len(data['data']['messages']) <= 3
    
    def test_delete_bot_conversation(self, client):
        """Test deleting bot conversation."""
        # Create conversation
        create_response = client.post('/api/v1/chat/bot/conversations', json={})
        chat_id = json.loads(create_response.data)['data']['chat_id']
        
        # Delete
        response = client.delete(
            f'/api/v1/chat/bot/conversations/{chat_id}'
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert data['data']['chat_id'] == chat_id
    
    def test_delete_nonexistent_conversation(self, client):
        """Test deleting non-existent conversation."""
        response = client.delete(
            '/api/v1/chat/bot/conversations/nonexistent-id'
        )
        
        assert response.status_code == 404
    
    def test_get_supported_operations(self, client):
        """Test getting supported operations."""
        response = client.get('/api/v1/chat/bot/operations')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert 'operations' in data['data']
        assert 'total_intents' in data['data']
        assert data['data']['total_intents'] >= 8
        assert 'extract_columns' in data['data']['operations']
    
    def test_conversation_flow(self, client):
        """Test complete conversation flow."""
        # 1. Create conversation
        create_response = client.post('/api/v1/chat/bot/conversations', json={})
        assert create_response.status_code == 201
        chat_id = json.loads(create_response.data)['data']['chat_id']
        
        # 2. Send message
        message_response = client.post(
            f'/api/v1/chat/bot/conversations/{chat_id}/message',
            json={'message': 'extract columns: name, email'}
        )
        assert message_response.status_code == 200
        
        # 3. Upload file
        fake_file = BytesIO(b'fake excel content')
        upload_response = client.post(
            f'/api/v1/chat/bot/conversations/{chat_id}/upload',
            data={'file': (fake_file, 'data.xlsx')},
            content_type='multipart/form-data'
        )
        assert upload_response.status_code == 200
        
        # 4. Get history
        history_response = client.get(
            f'/api/v1/chat/bot/conversations/{chat_id}/history'
        )
        assert history_response.status_code == 200
        history_data = json.loads(history_response.data)
        assert len(history_data['data']['messages']) >= 3
        
        # 5. Delete conversation
        delete_response = client.delete(
            f'/api/v1/chat/bot/conversations/{chat_id}'
        )
        assert delete_response.status_code == 200
    
    def test_multiple_messages_in_conversation(self, client):
        """Test sending multiple messages in one conversation."""
        # Create conversation
        create_response = client.post('/api/v1/chat/bot/conversations', json={})
        chat_id = json.loads(create_response.data)['data']['chat_id']
        
        messages = [
            'help',
            'extract columns',
            'convert to JSON',
            'generate SQL'
        ]
        
        for msg in messages:
            response = client.post(
                f'/api/v1/chat/bot/conversations/{chat_id}/message',
                json={'message': msg}
            )
            assert response.status_code == 200
        
        # Verify all messages in history
        history_response = client.get(
            f'/api/v1/chat/bot/conversations/{chat_id}/history'
        )
        history_data = json.loads(history_response.data)
        
        # Should have welcome + all messages and responses
        assert len(history_data['data']['messages']) >= len(messages) + 1


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
