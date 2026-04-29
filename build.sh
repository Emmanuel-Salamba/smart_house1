#!/bin/bash
echo "=== Building Django Project for Render ==="

# Install Python dependencies
pip install -r requirements.txt

# Collect static files
python manage.py collectstatic --noinput

# Apply database migrations
python manage.py migrate --noinput

# Create superuser if environment variables are set
if [[ $CREATE_SUPERUSER ]];
then
    echo "Creating superuser..."
    python manage.py createsuperuser --no-input --username $DJANGO_SUPERUSER_USERNAME --email $DJANGO_SUPERUSER_EMAIL
    echo "Superuser created successfully!"
fi

echo "=== Build Complete ==="