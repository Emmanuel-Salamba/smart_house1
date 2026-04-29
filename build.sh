#!/bin/bash
echo "=== Building Django Project for Render ==="

# Install Python dependencies
pip install -r requirements.txt

# Collect static files
python manage.py collectstatic --noinput

# Apply database migrations
python manage.py migrate --noinput

# Create superuser using Python script (MOST RELIABLE METHOD)
if [[ $CREATE_SUPERUSER ]] && [[ $DJANGO_SUPERUSER_USERNAME ]] && [[ $DJANGO_SUPERUSER_PASSWORD ]];
then
    echo "Creating superuser..."
    
    # This Python one-liner creates the superuser directly in the database
    python manage.py shell << EOF
from django.contrib.auth import get_user_model;
User = get_user_model();
username = "$DJANGO_SUPERUSER_USERNAME";
email = "$DJANGO_SUPERUSER_EMAIL";
password = "$DJANGO_SUPERUSER_PASSWORD";
if not User.objects.filter(username=username).exists():
    User.objects.create_superuser(username, email, password)
    print(f"Superuser {username} created successfully!")
else:
    print(f"Superuser {username} already exists.")
EOF
    
    echo "Superuser creation attempted!"
fi

echo "=== Build Complete ==="