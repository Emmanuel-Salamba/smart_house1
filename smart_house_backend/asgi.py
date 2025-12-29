import os
from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'smart_house_backend.settings')

# Check if we're on Vercel (no WebSocket support)
if os.environ.get('VERCEL') == '1':
    # On Vercel, use standard ASGI without WebSocket support
    application = get_asgi_application()
    app = application  # For Vercel compatibility
else:
    # Local development with WebSocket support
    from channels.routing import ProtocolTypeRouter, URLRouter
    from channels.auth import AuthMiddlewareStack
    from channels.security.websocket import AllowedHostsOriginValidator
    import devices.routing

    application = ProtocolTypeRouter({
        "http": get_asgi_application(),
        "websocket": AllowedHostsOriginValidator(
            AuthMiddlewareStack(
                URLRouter(
                    devices.routing.websocket_urlpatterns
                )
            )
        ),
    })
    app = application  # For consistency