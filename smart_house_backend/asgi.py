"""
ASGI config for smart_house_backend project.

It exposes the ASGI callable as a module-level variable named ``application``.
"""

import os
import django
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack

# ============================================
# Step 1: Set settings module FIRST
# ============================================
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'smart_house_backend.settings')

# ============================================
# Step 2: Setup Django BEFORE importing any app modules
# This ensures the app registry is ready
# ============================================
django.setup()

# ============================================
# Step 3: Import routing modules AFTER django.setup()
# ============================================
import devices.routing

# activities.routing is optional - handle gracefully if missing
try:
    import activities.routing
    has_activities_routing = True
except ImportError:
    has_activities_routing = False

# ============================================
# Step 4: Combine URL patterns from all apps
# ============================================
websocket_urlpatterns = list(devices.routing.websocket_urlpatterns)

if has_activities_routing:
    websocket_urlpatterns += activities.routing.websocket_urlpatterns

# ============================================
# Step 5: Get Django ASGI application for HTTP requests
# ============================================
django_asgi_app = get_asgi_application()

# ============================================
# Step 6: Main ASGI application with WebSocket support
# ============================================
# Note: We don't use AllowedHostsOriginValidator for WebSocket because:
# 1. Microcontrollers (ESP32) don't send proper origin headers
# 2. wscat and embedded clients may not comply with origin restrictions
# 3. Authentication is handled by the consumer's API key validation
application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": AuthMiddlewareStack(
        URLRouter(websocket_urlpatterns)
    ),
})

# ============================================
# For compatibility with various deployment platforms
# ============================================
app = application