

import uuid
from django.db import models
from users.models import User

# Create your models here.
class House(models.Model):
    house_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    house_name = models.CharField(max_length=100)
    address = models.TextField(blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    country = models.CharField(max_length=100, blank=True, null=True)
    zip_code = models.CharField(max_length=20, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.house_name


class UserHouseAccess(models.Model):
    ACCESS_LEVELS = [
        ('owner', 'Owner'),
        ('admin', 'Admin'),
        ('guest', 'Guest'),
    ]

    access_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    house = models.ForeignKey(House, on_delete=models.CASCADE)
    access_level = models.CharField(max_length=20, choices=ACCESS_LEVELS, default='guest')
    granted_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(blank=True, null=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ['user', 'house']

    def __str__(self):
        return f"{self.user} - {self.house} ({self.access_level})"