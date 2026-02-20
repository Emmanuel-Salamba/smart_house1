from django.http import HttpResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.utils import timezone
from django.db import connection
from devices.models import Component
from users.models import User


def activity_home(request):
    return HttpResponse("📊 I am the Activity Views!")



    