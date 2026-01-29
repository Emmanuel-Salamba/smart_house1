"""
Custom Django management command to create a superuser if one does not exist.
This is useful for automated deployments where Shell access is not available.

This command is customized for the Smart House app which uses email as the primary user identifier.

Usage:
    python manage.py create_superuser

Environment Variables (optional, use defaults if not set):
    DJANGO_SUPERUSER_EMAIL: Admin email (default: 'admin@example.com')
    DJANGO_SUPERUSER_PASSWORD: Admin password (default: 'changeme123')
    DJANGO_SUPERUSER_FIRST_NAME: Admin first name (default: 'Admin')
    DJANGO_SUPERUSER_LAST_NAME: Admin last name (default: 'User')

Example:
    export DJANGO_SUPERUSER_EMAIL=admin@smarthouse.com
    export DJANGO_SUPERUSER_PASSWORD=MySecurePass123!
    export DJANGO_SUPERUSER_FIRST_NAME=Admin
    export DJANGO_SUPERUSER_LAST_NAME=User
    python manage.py create_superuser
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import connections
from django.db.utils import OperationalError
import os
import sys

User = get_user_model()


class Command(BaseCommand):
    help = 'Create a superuser if one does not exist. Customized for email-based User model.'

    def handle(self, *args, **options):
        # Get credentials from environment variables
        email = os.environ.get('DJANGO_SUPERUSER_EMAIL', 'admin@example.com')
        password = os.environ.get('DJANGO_SUPERUSER_PASSWORD', 'changeme123')
        first_name = os.environ.get('DJANGO_SUPERUSER_FIRST_NAME', 'Admin')
        last_name = os.environ.get('DJANGO_SUPERUSER_LAST_NAME', 'User')
        
        try:
            # Check database connection before attempting to create superuser
            connections['default'].ensure_connection()
            
            # Check if superuser already exists by email
            if User.objects.filter(email=email).exists():
                self.stdout.write(
                    self.style.WARNING(
                        f'ℹ️  Superuser with email "{email}" already exists. Skipping creation.'
                    )
                )
            else:
                # Create the superuser using email (no username field in custom User model)
                User.objects.create_superuser(
                    email=email,
                    password=password,
                    first_name=first_name,
                    last_name=last_name
                )
                self.stdout.write(
                    self.style.SUCCESS(
                        f'✅ Successfully created superuser:\n'
                        f'   Email: {email}\n'
                        f'   Name: {first_name} {last_name}'
                    )
                )
        except OperationalError as e:
            # Database not available - log warning but don't fail deployment
            self.stdout.write(
                self.style.WARNING(
                    f'⚠️  Database unavailable: {str(e)}\n'
                    f'   Superuser creation will be skipped. You can create it manually later.\n'
                    f'   Run: python manage.py create_superuser'
                )
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(
                    f'❌ Error creating superuser: {str(e)}'
                )
            )
            sys.exit(1)
