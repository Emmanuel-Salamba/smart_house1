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

# Import your app routing
import devices.routing
import activities.routing

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'smart_house_backend.settings')

# Initialize Django
django.setup()

# Initialize Django ASGI application early
django_asgi_app = get_asgi_application()

# Application with WebSocket support for Render
application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": AllowedHostsOriginValidator(
        AuthMiddlewareStack(
            URLRouter(
                devices.routing.websocket_urlpatterns +
                activities.routing.websocket_urlpatterns
            )
        )
    ),
})

# For compatibility with various deployment platforms
app = application