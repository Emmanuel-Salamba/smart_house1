#!/bin/bash
echo "=== Building Django Project for Render ==="

# Install Python dependencies
pip install -r requirements.txt

# Collect static files
python manage.py collectstatic --noinput

# Apply database migrations
python manage.py migrate

echo "=== Build Complete ==="