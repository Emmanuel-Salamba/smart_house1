#!/bin/bash
echo "=== Building Django Project for Render ==="

# Install Python dependencies
pip install -r requirements.txt

# Collect static files
python manage.py collectstatic --noinput

# Apply database migrations
python manage.py migrate --noinput

# Create superuser using EMAIL from environment variables
echo "Creating superuser..."
python manage.py shell << EOF
from django.contrib.auth import get_user_model;
import os;
User = get_user_model();
email = os.environ.get('DJANGO_SUPERUSER_EMAIL', 'admin@example.com');
password = os.environ.get('DJANGO_SUPERUSER_PASSWORD', 'admin123');
if not User.objects.filter(email=email).exists():
    User.objects.create_superuser(email=email, password=password)
    print(f"Superuser created! Email: {email}")
else:
    print(f"Superuser with email {email} already exists")
EOF

echo "=== Build Complete ==="