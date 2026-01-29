"""
Health Check Routes

This module provides health check endpoints for monitoring.
"""

from flask import Blueprint, jsonify, current_app
from app.builders.response_builder import ResponseBuilder

health_bp = Blueprint("health", __name__)


@health_bp.route("", methods=["GET"])
@health_bp.route("/", methods=["GET"])
def health_check():
    """
    Health check endpoint.

    Returns:
        JSON response indicating service health

    Example:
        GET /api/v1/health
    """
    config = current_app.config.get("PYCELIZE")

    data = {
        "status": "healthy",
        "service": config.get("app.name", "Pycelize") if config else "Pycelize",
        "version": config.get("app.version", "v0.0.1") if config else "v0.0.1",
    }

    response = (
        ResponseBuilder()
        .with_data(data)
        .with_message("Service is healthy")
        .with_status_code(200)
        .build()
    )

    return jsonify(response), 200


@health_bp.route("/ready", methods=["GET"])
def readiness_check():
    """
    Readiness check endpoint.

    Returns:
        JSON response indicating service readiness
    """
    response = (
        ResponseBuilder()
        .with_data({"ready": True})
        .with_message("Service is ready")
        .with_status_code(200)
        .build()
    )

    return jsonify(response), 200
