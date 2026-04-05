"""
ASGI config for smart_house_backend project.

It exposes the ASGI callable as a module-level variable named ``application``.
"""

import os
import django
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from channels.security.websocket import AllowedHostsOriginValidator

# ============================================
# CRITICAL: Set settings module FIRST
# ============================================
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'smart_house_backend.settings')

# ============================================
# CRITICAL: Setup Django BEFORE importing any app modules
# This ensures the app registry is ready
# ============================================
django.setup()

# ============================================
# Now import your routing modules AFTER django.setup()
# ============================================
import devices.routing
import activities.routing

# ============================================
# Get Django ASGI application for HTTP requests
# ============================================
django_asgi_app = get_asgi_application()

# ============================================
# Main ASGI application with WebSocket support
# ============================================
application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": AllowedHostsOriginValidator(
        AuthMiddlewareStack(
            URLRouter(
                devices.routing.websocket_urlpatterns 
               
            )
        )
    ),
})

# ============================================
# For compatibility with various deployment platforms
# ============================================
app = application