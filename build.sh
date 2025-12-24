#!/bin/bash
echo "=== Building Django Project for Vercel ==="

# Install dependencies
pip install -r requirements.txt

# Collect static files
python manage.py collectstatic --noinput

# Create necessary directories
mkdir -p staticfiles
mkdir -p media

echo "=== Build Complete ==="