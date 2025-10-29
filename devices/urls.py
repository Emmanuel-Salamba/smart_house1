"""from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'components', views.ComponentViewSet)

urlpatterns = [
    path('', include(router.urls)),
]

"""""


from django.urls import path
from . import views

urlpatterns = [
    path('', views.device_home, name='device-home'),
]