#!/usr/bin/env python3
"""
Pycelize Application Entry Point

This module serves as the main entry point for running the Pycelize
Flask application. It creates the application instance and starts
the development server.

Usage:
    python run.py

    or with Make:
    make run
"""

import os
import sys

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app


def main():
    """
    Main function to run the Flask application.

    Loads configuration and starts the development server with
    the configured host and port settings.
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

    print(
        f"""
    ╔═══════════════════════════════════════════════════════════════════╗
    ║                                                                   ║
    ║   🚀 Pycelize - Excel/CSV Processing API                          ║
    ║                                                                   ║
    ║   Version: {version}                                                 ║
    ║   Server:  {server}                                  ║
    ║   Debug:   {debug}                                                   ║
    ║                                                                   ║
    ║   API Docs: {health_url}                   ║
    ║                                                                   ║
    ╚═══════════════════════════════════════════════════════════════════╝
    """
    )

    # Run the application
    app.run(host=host, port=port, debug=debug)


if __name__ == "__main__":
    main()
