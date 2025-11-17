"""
URL configuration for smart_house_backend project.
"""

from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from devices.views import ComponentViewSet, MicrocontrollerViewSet, ActionTypeViewSet

# REST Framework router for devices API
router = DefaultRouter()
router.register(r'components', ComponentViewSet)
router.register(r'microcontrollers', MicrocontrollerViewSet)
router.register(r'action-types', ActionTypeViewSet)

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),
    
    # REST API endpoints (new - for mobile app)
    path('api/', include(router.urls)),
    
    # Your existing app endpoints (keep these!)
    path('api/devices/', include('devices.urls')),      # Keep your existing devices URLs
    path('api/users/', include('users.urls')),          # Keep your existing users URLs  
    path('api/houses/', include('houses.urls')),        # Keep your existing houses URLs
    path('api/activities/', include('activities.urls')), # Keep your existing activities URLs
    
    # Authentication (if you have separate auth endpoints)
    path('api/auth/', include('users.urls')),           # Or your auth endpoints
    
    # Forest Admin
    path('forest/', include('forestadmin.django_agent.urls')),
]