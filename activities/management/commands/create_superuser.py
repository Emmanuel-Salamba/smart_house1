"""
Custom Django management command to create a superuser if one does not exist.
This is useful for automated deployments where Shell access is not available.

Usage:
    python manage.py create_superuser

Environment Variables (optional, use defaults if not set):
    DJANGO_SUPERUSER_USERNAME: Admin username (default: 'admin')
    DJANGO_SUPERUSER_EMAIL: Admin email (default: 'admin@example.com')
    DJANGO_SUPERUSER_PASSWORD: Admin password (default: 'changeme123')

Example:
    export DJANGO_SUPERUSER_USERNAME=myadmin
    export DJANGO_SUPERUSER_EMAIL=admin@myapp.com
    export DJANGO_SUPERUSER_PASSWORD=MySecurePass123!
    python manage.py create_superuser
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
import os
import sys

User = get_user_model()


class Command(BaseCommand):
    help = 'Create a superuser if one does not exist. Useful for automated deployments.'

    def handle(self, *args, **options):
        # Get credentials from environment variables
        username = os.environ.get('DJANGO_SUPERUSER_USERNAME', 'admin')
        email = os.environ.get('DJANGO_SUPERUSER_EMAIL', 'admin@example.com')
        password = os.environ.get('DJANGO_SUPERUSER_PASSWORD', 'changeme123')
        
        try:
            # Check if superuser already exists
            if User.objects.filter(username=username).exists():
                self.stdout.write(
                    self.style.WARNING(
                        f'ℹ️  Superuser "{username}" already exists. Skipping creation.'
                    )
                )
            else:
                # Create the superuser
                User.objects.create_superuser(username, email, password)
                self.stdout.write(
                    self.style.SUCCESS(
                        f'✅ Successfully created superuser:\n'
                        f'   Username: {username}\n'
                        f'   Email: {email}'
                    )
                )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(
                    f'❌ Error creating superuser: {str(e)}'
                )
            )
            sys.exit(1)
