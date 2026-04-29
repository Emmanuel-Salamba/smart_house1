#!/bin/bash
echo "=== Building Django Project for Render ==="

# Install Python dependencies
pip install -r requirements.txt

# Collect static files
python manage.py collectstatic --noinput

# Apply database migrations
python manage.py migrate --noinput

# ALWAYS create superuser (no condition needed)
echo "Creating superuser..."
python manage.py shell << EOF
from django.contrib.auth import get_user_model;
User = get_user_model();
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
    print('Superuser created! Password: admin123')
else:
    print('Superuser already exists')
EOF

echo "=== Build Complete ==="