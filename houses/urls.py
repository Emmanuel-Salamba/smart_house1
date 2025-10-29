from django.urls import path
from . import views

urlpatterns = [
    path('', views.house_home, name='house-home'),
]