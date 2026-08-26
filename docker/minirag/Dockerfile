FROM astral/uv:0.12.5-python3.12-alpine

WORKDIR /app

# Prevent Python from creating .pyc files
ENV PYTHONDONTWRITEBYTECODE=1

# Enable unbuffered Python output
ENV PYTHONUNBUFFERED=1

# Don't create a virtual environment inside the container
ENV UV_SYSTEM_PYTHON=1

# Set the Python path to include the application source directory
ENV PYTHONPATH=/app/src

# Copy dependency files first to leverage Docker cache
COPY pyproject.toml uv.lock README.md ./

# Copy application source
COPY src ./src

# Install system dependencies required for building Python packages and PostgreSQL client libraries
RUN apk add --no-cache \
    bash \
    postgresql-dev \
    gcc \
    musl-dev \
    python3-dev

# Install dependencies
RUN uv sync --locked --no-dev

# Create directory structure for alembic migrations
RUN mkdir -p /app/models/db_schemas/minirag

# Copy alembic configuration and migration scripts
COPY docker/minirag/alembic.ini /app/models/db_schemas/minirag/alembic.ini

# Copy the entrypoint script
COPY docker/minirag/entrypoint.sh /entrypoint.sh

# Make the entrypoint script executable
RUN chmod +x /entrypoint.sh

# Set the entrypoint
ENTRYPOINT ["/entrypoint.sh"]

# Expose FastAPI port
EXPOSE 8000

# Run FastAPI
CMD ["uv", "run", "uvicorn", "mini_rag.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
