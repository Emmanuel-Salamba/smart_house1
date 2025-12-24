"""
WSGI config for smart_house_backend project.

It exposes the WSGI callable as a module-level variable named ``application``.
"""

import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'smart_house_backend.settings')

application = get_wsgi_application()

# Fix for Vercel - they look for 'app' variable
app = application