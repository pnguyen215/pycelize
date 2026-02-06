"""
WebSocket Bridge

This module provides a thread-safe bridge between Flask routes and the WebSocket server.
It allows Flask routes to send messages to WebSocket clients asynchronously.
"""

import asyncio
import json
import logging
from typing import Dict, Any, Optional
from queue import Queue
from threading import Lock

logger = logging.getLogger(__name__)


class WebSocketBridge:
    """
    Singleton bridge for sending messages from Flask routes to WebSocket clients.
    
    This bridge uses a message queue to safely communicate between the Flask
    thread and the WebSocket server thread.
    """
    
    _instance = None
    _lock = Lock()
    
    def __new__(cls):
        """Ensure singleton instance."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """Initialize the bridge."""
        if self._initialized:
            return
            
        self.message_queue = Queue()
        self.connection_manager = None
        self.event_loop = None
        self._initialized = True
        logger.info("WebSocket bridge initialized")
    
    def set_connection_manager(self, connection_manager, event_loop):
        """
        Set the WebSocket connection manager and event loop.
        
        Args:
            connection_manager: WebSocketConnectionManager instance
            event_loop: asyncio event loop from WebSocket thread
        """
        self.connection_manager = connection_manager
        self.event_loop = event_loop
        logger.info("WebSocket connection manager registered with bridge")
    
    def send_message(self, chat_id: str, message: Dict[str, Any]) -> bool:
        """
        Send a message to WebSocket clients subscribed to a chat.
        
        This method is thread-safe and can be called from Flask routes.
        
        Args:
            chat_id: Conversation ID
            message: Message dictionary to send
            
        Returns:
            True if message was queued successfully
        """
        if not self.connection_manager or not self.event_loop:
            logger.warning("WebSocket not available - message not sent")
            return False
        
        try:
            # Schedule the coroutine in the WebSocket event loop
            asyncio.run_coroutine_threadsafe(
                self.connection_manager.send_to_chat(chat_id, message),
                self.event_loop
            )
            return True
        except Exception as e:
            logger.error(f"Failed to send WebSocket message: {e}")
            return False
    
    def broadcast_message(self, message: Dict[str, Any]) -> bool:
        """
        Broadcast a message to all connected WebSocket clients.
        
        Args:
            message: Message dictionary to broadcast
            
        Returns:
            True if message was queued successfully
        """
        if not self.connection_manager or not self.event_loop:
            logger.warning("WebSocket not available - broadcast not sent")
            return False
        
        try:
            # Schedule the coroutine in the WebSocket event loop
            asyncio.run_coroutine_threadsafe(
                self.connection_manager.broadcast(message),
                self.event_loop
            )
            return True
        except Exception as e:
            logger.error(f"Failed to broadcast WebSocket message: {e}")
            return False
    
    def is_available(self) -> bool:
        """
        Check if WebSocket bridge is available.
        
        Returns:
            True if WebSocket is connected and ready
        """
        return self.connection_manager is not None and self.event_loop is not None


# Global singleton instance
websocket_bridge = WebSocketBridge()
