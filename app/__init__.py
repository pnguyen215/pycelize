"""
Pycelize Flask Application Factory

This module contains the application factory for creating Flask instances
with proper configuration and blueprint registration.
"""

from flask import Flask
from flask_cors import CORS
import os

from app.core.config import Config
from app.core.logging import setup_logging
from app.core.exceptions import register_error_handlers


def create_app(config_path: str = None) -> Flask:
    """
    Application factory for creating Flask instances.

    Args:
        config_path: Path to the configuration file.
                    Defaults to 'configs/application.yml'

    Returns:
        Flask: Configured Flask application instance

    Example:
        >>> app = create_app()
        >>> app.run()
    """
    # Create Flask instance
    app = Flask(__name__)

    # Load configuration
    if config_path is None:
        config_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), "configs", "application.yml"
        )

    # Initialize configuration
    config = Config(config_path)
    app.config["PYCELIZE"] = config

    # Apply Flask configurations
    app.config["DEBUG"] = config.get("app.debug", False)
    app.config["MAX_CONTENT_LENGTH"] = (
        config.get("file.max_file_size_mb", 50) * 1024 * 1024
    )

    # Setup CORS
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    # Setup logging
    setup_logging(config)

    # Register error handlers
    register_error_handlers(app)

    # Create upload and output directories
    _ensure_directories(config)

    # Register blueprints
    _register_blueprints(app)

    return app


def _ensure_directories(config: Config) -> None:
    """
    Ensure required directories exist.

    Args:
        config: Application configuration instance
    """
    directories = [
        config.get("file.upload_folder", "uploads"),
        config.get("file.output_folder", "outputs"),
        "logs",
    ]

    for directory in directories:
        os.makedirs(directory, exist_ok=True)


def _register_blueprints(app: Flask) -> None:
    """
    Register all API blueprints with the Flask application.

    Args:
        app: Flask application instance
    """
    from app.api.routes.health_routes import health_bp
    from app.api.routes.excel_routes import excel_bp
    from app.api.routes.csv_routes import csv_bp
    from app.api.routes.normalization_routes import normalization_bp
    from app.api.routes.sql_routes import sql_bp
    from app.api.routes.file_routes import file_bp

    # Get API prefix from config
    config = app.config.get("PYCELIZE")
    api_prefix = config.get("api.prefix", "/api/v1") if config else "/api/v1"

    # Register blueprints
    app.register_blueprint(health_bp, url_prefix=f"{api_prefix}/health")
    app.register_blueprint(excel_bp, url_prefix=f"{api_prefix}/excel")
    app.register_blueprint(csv_bp, url_prefix=f"{api_prefix}/csv")
    app.register_blueprint(normalization_bp, url_prefix=f"{api_prefix}/normalization")
    app.register_blueprint(sql_bp, url_prefix=f"{api_prefix}/sql")
    app.register_blueprint(file_bp, url_prefix=f"{api_prefix}/files")
