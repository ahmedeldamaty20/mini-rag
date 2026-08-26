#!/bin/bash
set -e

echo "Starting MiniRAG application..."

echo "Running database migrations..."
cd /app/src/models/db_schemas/minirag
uv run alembic upgrade head
echo "Database migrations completed."

cd /app

exec "$@"