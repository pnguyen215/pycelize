#!/usr/bin/env python3
"""
Pycelize Application Entry Point

This module serves as the main entry point for running the Pycelize
Flask application. It creates the application instance and starts
the development server along with the WebSocket server for chat workflows.

Usage:
    python run.py

    or with Make:
    make run
"""

import os
import sys
import threading
import asyncio
import logging

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def start_websocket_server(config):
    """
    Start the WebSocket server in a separate thread.
    
    Args:
        config: Application configuration
    """
    try:
        # Check if chat workflows is enabled
        chat_config = config.get_section("chat_workflows")
        if not chat_config or not chat_config.get("enabled", False):
            logger.info("Chat workflows disabled - WebSocket server not started")
            return
        
        # Get WebSocket configuration
        ws_config = chat_config.get("websocket", {})
        host = ws_config.get("host", "127.0.0.1")
        port = ws_config.get("port", 5051)
        max_connections = chat_config.get("max_connections", 10)
        
        # Import WebSocket server and bridge
        from app.chat.websocket_server import ChatWebSocketServer
        from app.chat.websocket_bridge import websocket_bridge
        
        # Create and start WebSocket server
        logger.info(f"Starting WebSocket server on ws://{host}:{port}")
        ws_server = ChatWebSocketServer(host, port, max_connections)
        
        # Create new event loop for this thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # Register connection manager with bridge for cross-thread communication
        websocket_bridge.set_connection_manager(ws_server.connection_manager, loop)
        logger.info("WebSocket bridge configured for cross-thread communication")
        
        # Start the WebSocket server
        loop.run_until_complete(ws_server.start())
        logger.info(f"✓ WebSocket server started successfully on ws://{host}:{port}")
        
        # Keep the loop running
        loop.run_forever()
        
    except Exception as e:
        logger.error(f"Failed to start WebSocket server: {e}")
        import traceback
        traceback.print_exc()


def main():
    """
    Main function to run the Flask application.

    Loads configuration and starts the development server with
    the configured host and port settings. Also starts the WebSocket
    server for chat workflows in a separate thread.
    """
    # Create application instance
    app = create_app()

    # Get configuration
    config = app.config.get("PYCELIZE")

    # Extract server settings
    host = config.get("app.host", "0.0.0.0") if config else "0.0.0.0"
    port = config.get("app.port", 5050) if config else 5050
    debug = config.get("app.debug", True) if config else True
    version = config.get("app.version", "v0.0.1") if config else "v0.0.1"
    server = f"http://{host}:{port}".format(host=host, port=port)
    health_url = f"{server}/api/v1/health".format(host=host, port=port)
    
    # Check if WebSocket should be started
    chat_config = config.get_section("chat_workflows") if config else None
    ws_enabled = chat_config.get("enabled", False) if chat_config else False
    ws_host = chat_config.get("websocket", {}).get("host", "127.0.0.1") if chat_config else "127.0.0.1"
    ws_port = chat_config.get("websocket", {}).get("port", 5051) if chat_config else 5051
    ws_url = f"ws://{ws_host}:{ws_port}"

    # Start WebSocket server in separate thread if enabled
    if ws_enabled:
        logger.info("Starting WebSocket server in background thread...")
        ws_thread = threading.Thread(
            target=start_websocket_server, 
            args=(config,),
            daemon=True,
            name="WebSocketServer"
        )
        ws_thread.start()
        # Give WebSocket server time to start
        import time
        time.sleep(2)

    # Print startup banner
    ws_status = f"✓ Running on {ws_url}" if ws_enabled else "✗ Disabled"
    print(
        f"""
    ╔═══════════════════════════════════════════════════════════════════╗
    ║                                                                   ║
    ║   🚀 Pycelize - Excel/CSV Processing API                          ║
    ║                                                                   ║
    ║   Version:    {version}                                              ║
    ║   REST API:   {server}                                  ║
    ║   WebSocket:  {ws_status}                            ║
    ║   Debug:      {debug}                                                ║
    ║                                                                   ║
    ║   Health:     {health_url}                   ║
    ║                                                                   ║
    ╚═══════════════════════════════════════════════════════════════════╝
    """
    )

    # Run the Flask application
    try:
        app.run(host=host, port=port, debug=debug, use_reloader=False)
    except KeyboardInterrupt:
        logger.info("Shutting down servers...")
    except Exception as e:
        logger.error(f"Server error: {e}")
        raise


if __name__ == "__main__":
    main()
