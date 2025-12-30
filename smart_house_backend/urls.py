from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views  # ← ADD THIS IMPORT
from rest_framework.routers import DefaultRouter
from devices.views import ComponentViewSet, MicrocontrollerViewSet, ActionTypeViewSet
from django.http import JsonResponse
from django.db import connection
from django.db.utils import OperationalError


def health_check(request):
    """Health check endpoint for Render"""
    try:
        # Check database connection
        connection.ensure_connection()
        db_status = "connected"
    except OperationalError:
        db_status = "disconnected"

    return JsonResponse({
        'status': 'healthy',
        'service': 'Smart Home API',
        'database': db_status,
        'timestamp': timezone.now().isoformat()
    })


# REST Framework router for devices API
router = DefaultRouter()
router.register(r'components', ComponentViewSet)
router.register(r'microcontrollers', MicrocontrollerViewSet)
router.register(r'action-types', ActionTypeViewSet)

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),
    path('health/', health_check, name='health_check'),
    # REST API endpoints (new - for mobile app)
    path('api/', include(router.urls)),
    
    # Your existing app endpoints (keep these!)
    # path('api/devices/', include('devices.urls')),      # Keep your existing devices URLs
    path('api/users/', include('users.urls')),          # Keep your existing users URLs  
    path('api/houses/', include('houses.urls')),        # Keep your existing houses URLs
    path('api/activities/', include('activities.urls')), # Keep your existing activities URLs
    
    # Authentication (if you have separate auth endpoints)
    path('api/auth/', include('users.urls')),           # Or your auth endpoints
    
    # Custom login URL for background image ← ADD THIS LINE
    path('accounts/login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    
    # Forest Admin
    path('forest/', include('forestadmin.django_agent.urls')),
]