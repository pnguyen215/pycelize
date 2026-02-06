"""
WebSocket Server for Chat Workflows

This module provides a lightweight WebSocket server for real-time
communication and streaming progress updates.
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, Set, Optional, Any
import websockets
from websockets.server import WebSocketServerProtocol

logger = logging.getLogger(__name__)


class WebSocketConnectionManager:
    """
    Manages WebSocket connections for chat workflows.

    Handles connection lifecycle, broadcasting, and per-conversation messaging.
    """

    def __init__(self, max_connections: int = 10):
        """
        Initialize connection manager.

        Args:
            max_connections: Maximum concurrent connections
        """
        self.max_connections = max_connections
        self.active_connections: Dict[str, Set[WebSocketServerProtocol]] = {}
        self.connection_metadata: Dict[WebSocketServerProtocol, Dict[str, Any]] = {}

    async def connect(
        self, websocket: WebSocketServerProtocol, chat_id: Optional[str] = None
    ) -> bool:
        """
        Register a new WebSocket connection.

        Args:
            websocket: WebSocket connection
            chat_id: Optional conversation ID to subscribe to

        Returns:
            True if connected successfully
        """
        # Check connection limit
        total_connections = sum(len(conns) for conns in self.active_connections.values())
        if total_connections >= self.max_connections:
            await websocket.send(
                json.dumps(
                    {"type": "error", "message": "Maximum connections reached"}
                )
            )
            await websocket.close()
            return False

        # Store connection metadata
        self.connection_metadata[websocket] = {
            "chat_id": chat_id,
            "connected_at": datetime.utcnow().isoformat(),
        }

        # Add to chat-specific connections
        if chat_id:
            if chat_id not in self.active_connections:
                self.active_connections[chat_id] = set()
            self.active_connections[chat_id].add(websocket)

        logger.info(f"WebSocket connected - chat_id: {chat_id}")

        # Send welcome message
        await websocket.send(
            json.dumps(
                {
                    "type": "connected",
                    "chat_id": chat_id,
                    "timestamp": datetime.utcnow().isoformat(),
                }
            )
        )

        return True

    async def disconnect(self, websocket: WebSocketServerProtocol) -> None:
        """
        Unregister a WebSocket connection.

        Args:
            websocket: WebSocket connection
        """
        # Get metadata
        metadata = self.connection_metadata.get(websocket, {})
        chat_id = metadata.get("chat_id")

        # Remove from chat-specific connections
        if chat_id and chat_id in self.active_connections:
            self.active_connections[chat_id].discard(websocket)
            if not self.active_connections[chat_id]:
                del self.active_connections[chat_id]

        # Remove metadata
        if websocket in self.connection_metadata:
            del self.connection_metadata[websocket]

        logger.info(f"WebSocket disconnected - chat_id: {chat_id}")

    async def send_to_chat(self, chat_id: str, message: Dict[str, Any]) -> None:
        """
        Send message to all connections subscribed to a chat.

        Args:
            chat_id: Conversation ID
            message: Message to send
        """
        if chat_id not in self.active_connections:
            return

        # Add timestamp
        message["timestamp"] = datetime.utcnow().isoformat()

        # Send to all connections for this chat
        disconnected = set()
        for websocket in self.active_connections[chat_id]:
            try:
                await websocket.send(json.dumps(message))
            except Exception as e:
                logger.error(f"Error sending to websocket: {e}")
                disconnected.add(websocket)

        # Clean up disconnected websockets
        for websocket in disconnected:
            await self.disconnect(websocket)

    async def broadcast(self, message: Dict[str, Any]) -> None:
        """
        Broadcast message to all active connections.

        Args:
            message: Message to broadcast
        """
        # Add timestamp
        message["timestamp"] = datetime.utcnow().isoformat()

        # Send to all connections
        for chat_id in list(self.active_connections.keys()):
            await self.send_to_chat(chat_id, message)

    def get_connection_count(self, chat_id: Optional[str] = None) -> int:
        """
        Get number of active connections.

        Args:
            chat_id: Optional chat ID to filter

        Returns:
            Number of connections
        """
        if chat_id:
            return len(self.active_connections.get(chat_id, set()))
        else:
            return sum(len(conns) for conns in self.active_connections.values())


class ChatWebSocketServer:
    """
    WebSocket server for chat workflows.

    Provides real-time communication and streaming progress updates.
    """

    def __init__(self, host: str = "127.0.0.1", port: int = 5051, max_connections: int = 10):
        """
        Initialize WebSocket server.

        Args:
            host: Server host
            port: Server port
            max_connections: Maximum concurrent connections
        """
        self.host = host
        self.port = port
        self.connection_manager = WebSocketConnectionManager(max_connections)
        self.server = None

    async def handle_connection(self, websocket: WebSocketServerProtocol, path: str) -> None:
        """
        Handle WebSocket connection.

        Args:
            websocket: WebSocket connection
            path: Connection path
        """
        # Extract chat_id from path (e.g., /chat/<chat_id>)
        chat_id = None
        if path.startswith("/chat/"):
            chat_id = path.split("/")[2] if len(path.split("/")) > 2 else None

        # Register connection
        connected = await self.connection_manager.connect(websocket, chat_id)
        if not connected:
            return

        try:
            # Handle incoming messages
            async for message in websocket:
                try:
                    data = json.loads(message)
                    await self.handle_message(websocket, chat_id, data)
                except json.JSONDecodeError:
                    await websocket.send(
                        json.dumps({"type": "error", "message": "Invalid JSON"})
                    )
                except Exception as e:
                    logger.error(f"Error handling message: {e}")
                    await websocket.send(
                        json.dumps({"type": "error", "message": str(e)})
                    )

        except websockets.exceptions.ConnectionClosed:
            logger.info("WebSocket connection closed")
        finally:
            await self.connection_manager.disconnect(websocket)

    async def handle_message(
        self, websocket: WebSocketServerProtocol, chat_id: Optional[str], data: Dict[str, Any]
    ) -> None:
        """
        Handle incoming WebSocket message.

        Args:
            websocket: WebSocket connection
            chat_id: Chat ID
            data: Message data
        """
        message_type = data.get("type")

        if message_type == "ping":
            await websocket.send(json.dumps({"type": "pong"}))

        elif message_type == "subscribe":
            # Subscribe to a different chat
            new_chat_id = data.get("chat_id")
            if new_chat_id:
                await self.connection_manager.disconnect(websocket)
                await self.connection_manager.connect(websocket, new_chat_id)

        else:
            # Echo unknown message types
            await websocket.send(
                json.dumps({"type": "ack", "original": data})
            )

    async def send_progress_update(
        self, chat_id: str, step_id: str, progress: int, status: str, message: str
    ) -> None:
        """
        Send progress update to all connections for a chat.

        Args:
            chat_id: Conversation ID
            step_id: Step ID
            progress: Progress percentage (0-100)
            status: Step status
            message: Progress message
        """
        await self.connection_manager.send_to_chat(
            chat_id,
            {
                "type": "progress",
                "step_id": step_id,
                "progress": progress,
                "status": status,
                "message": message,
            },
        )

    async def send_step_result(
        self, chat_id: str, step_id: str, result: Dict[str, Any]
    ) -> None:
        """
        Send step execution result.

        Args:
            chat_id: Conversation ID
            step_id: Step ID
            result: Step result data
        """
        await self.connection_manager.send_to_chat(
            chat_id,
            {
                "type": "step_result",
                "step_id": step_id,
                "result": result,
            },
        )

    async def send_error(
        self, chat_id: str, step_id: Optional[str], error_message: str
    ) -> None:
        """
        Send error message.

        Args:
            chat_id: Conversation ID
            step_id: Optional step ID
            error_message: Error message
        """
        await self.connection_manager.send_to_chat(
            chat_id,
            {
                "type": "error",
                "step_id": step_id,
                "message": error_message,
            },
        )

    async def start(self) -> None:
        """Start the WebSocket server."""
        # Create a wrapper to handle the connection properly
        async def connection_handler(websocket):
            # In websockets 12+, path is part of websocket.request
            path = websocket.request.path if hasattr(websocket, 'request') else "/"
            await self.handle_connection(websocket, path)
        
        self.server = await websockets.serve(
            connection_handler,
            self.host,
            self.port,
            ping_interval=30,
            ping_timeout=10,
        )
        logger.info(f"WebSocket server started on ws://{self.host}:{self.port}")

    async def stop(self) -> None:
        """Stop the WebSocket server."""
        if self.server:
            self.server.close()
            await self.server.wait_closed()
            logger.info("WebSocket server stopped")

    def run(self) -> None:
        """Run the WebSocket server (blocking)."""
        asyncio.run(self.start())
        asyncio.get_event_loop().run_forever()
