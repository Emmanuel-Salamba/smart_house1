from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from . import views

urlpatterns = [
    # Authentication
    path('token/', views.CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # Registration
    path('register/', views.register_user, name='register'),

    # User profile
    path('profile/', views.get_user_profile, name='user_profile'),
    path('profile/update/', views.update_user_profile, name='update_profile'),

    # User types
    path('types/', views.get_user_types, name='user_types'),
]