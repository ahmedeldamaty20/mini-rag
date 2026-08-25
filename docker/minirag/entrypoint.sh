#!/bin/bash
set -e

echo "Starting MiniRAG application..."

echo "Running database migrations..."
cd /app/models/db_schemas/minirag
alembic upgrade head
echo "Database migrations completed."

cd /app
