# =============================================================================
# Pycelize Dockerfile
# =============================================================================
# Multi-stage build for optimized production image
#
# Usage:
#   docker build -t pycelize:latest .
#   docker run -p 5050:5050 pycelize:latest
# =============================================================================

# -----------------------------------------------------------------------------
# Stage 1: Builder
# -----------------------------------------------------------------------------
FROM python:3.11-slim as builder

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
    
# Set work directory
WORKDIR /app
    
# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
        gcc \
        libpq-dev \
        && rm -rf /var/lib/apt/lists/*
    
# Install Python dependencies
COPY requirements.txt .
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /app/wheels -r requirements.txt
    
# -----------------------------------------------------------------------------
# Stage 2: Production
# -----------------------------------------------------------------------------
FROM python:3.11-slim as production
    
# Labels
LABEL maintainer="arisnguyenit97"
LABEL version="0.0.1"
LABEL description="Pycelize - Professional Flask Application for Excel/CSV Processing"
    
# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV FLASK_ENV=production
ENV FLASK_DEBUG=0
ENV APP_HOME=/app
    
# Create non-root user for security
RUN groupadd --gid 1000 appgroup \
        && useradd --uid 1000 --gid appgroup --shell /bin/bash --create-home appuser
    
# Set work directory
WORKDIR $APP_HOME
    
# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
        libpq5 \
        curl \
        && rm -rf /var/lib/apt/lists/* \
        && apt-get clean
    
# Copy wheels from builder stage
COPY --from=builder /app/wheels /wheels
COPY --from=builder /app/requirements.txt .
    
# Install Python packages from wheels
RUN pip install --no-cache-dir /wheels/* \
        && rm -rf /wheels
    
# Copy application code
COPY --chown=appuser:appgroup . .

# Create required directories with proper permissions
RUN mkdir -p uploads outputs logs \
        && chown -R appuser:appgroup uploads outputs logs
    
# Switch to non-root user
USER appuser
    
# Expose port
EXPOSE 5050
    
# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
        CMD curl -f http://localhost:5050/api/v1/health || exit 1
    
# Run the application
CMD ["python", "run.py"]
