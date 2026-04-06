#!/bin/bash
set -e

echo "=== Smart House Backend Startup ==="

# Try to run migrations with retries
echo "Attempting migrations..."
for i in {1..5}; do
    if python manage.py migrate --noinput 2>&1; then
        echo "✅ Migrations successful"
        break
    else
        if [ $i -lt 5 ]; then
            echo "⚠️  Migrations failed, retrying in 5 seconds... (attempt $i/5)"
            sleep 5
        else
            echo "⚠️  Migrations skipped - database not yet ready"
        fi
    fi
done

# Try to create superuser with retries
echo "Attempting superuser creation..."
for i in {1..3}; do
    if python manage.py create_superuser 2>&1; then
        echo "✅ Superuser creation successful"
        break
    else
        if [ $i -lt 3 ]; then
            echo "⚠️  Superuser creation failed, retrying... (attempt $i/3)"
            sleep 3
        else
            echo "⚠️  Superuser creation skipped - database not yet ready"
        fi
    fi
done

# Start Daphne for ASGI/Channels support regardless of database status
echo "Starting daphne..."
exec daphne smart_house_backend.asgi:application \
    --bind 0.0.0.0 \
    --port $PORT \
    --access-log - \
    --proxy-headers
