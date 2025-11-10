import uuid
from django.db import models
from users.models import User


class House(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    address = models.TextField()
    gps_coordinates = models.CharField(max_length=100, blank=True)  # Store as "lat,lng"

    # Security and identification
    house_code = models.CharField(max_length=20, unique=True, db_index=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    # Status
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'house'
        verbose_name = 'House'
        verbose_name_plural = 'Houses'
        indexes = [
            models.Index(fields=['house_code', 'is_active']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"{self.name} ({self.house_code})"


class HouseUser(models.Model):
    ACCESS_LEVELS = [
        ('owner', 'Owner'),
        ('admin', 'Administrator'),
        ('resident', 'Resident'),
        ('guest', 'Guest'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='house_memberships')
    house = models.ForeignKey(House, on_delete=models.CASCADE, related_name='house_users')
    access_level = models.CharField(max_length=20, choices=ACCESS_LEVELS, default='resident')

    # Permissions (granular control)
    can_control_devices = models.BooleanField(default=True)
    can_invite_users = models.BooleanField(default=False)
    can_manage_house = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'house_user'
        verbose_name = 'House User'
        verbose_name_plural = 'House Users'
        unique_together = ['user', 'house']
        indexes = [
            models.Index(fields=['user', 'house']),
            models.Index(fields=['access_level']),
        ]

    def __str__(self):
        return f"{self.user.email} - {self.house.name} ({self.access_level})"