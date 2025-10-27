import uuid
from django.db import models
from houses.models import House
from users.models import User


class DeviceType(models.Model):
    type_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    type_name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    manufacturer = models.CharField(max_length=100, blank=True, null=True)
    model = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.type_name


class ActionType(models.Model):
    VALUE_TYPES = [
        ('percentage', 'Percentage'),
        ('temperature', 'Temperature'),
        ('color', 'Color'),
        ('none', 'None'),
    ]

    action_type_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    device_type = models.ForeignKey(DeviceType, on_delete=models.CASCADE)
    action_name = models.CharField(max_length=50)
    description = models.TextField(blank=True, null=True)
    requires_value = models.BooleanField(default=False)
    value_type = models.CharField(max_length=20, choices=VALUE_TYPES, default='none')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['device_type', 'action_name']

    def __str__(self):
        return f"{self.device_type} - {self.action_name}"


class Component(models.Model):
    STATUS_CHOICES = [
        ('online', 'Online'),
        ('offline', 'Offline'),
        ('error', 'Error'),
    ]

    component_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    house = models.ForeignKey(House, on_delete=models.CASCADE)
    device_type = models.ForeignKey(DeviceType, on_delete=models.PROTECT)
    component_name = models.CharField(max_length=100)
    device_identifier = models.CharField(max_length=255, unique=True)
    room_location = models.CharField(max_length=100, blank=True, null=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='offline')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.component_name} ({self.house.house_name})"


class ComponentState(models.Model):
    state_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    component = models.OneToOneField(Component, on_delete=models.CASCADE)
    current_state = models.JSONField(blank=True, null=True)
    last_updated = models.DateTimeField(auto_now=True)
    last_updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True)
    is_online = models.BooleanField(default=False)
    battery_level = models.IntegerField(blank=True, null=True)

    def __str__(self):
        return f"State of {self.component}"


class Schedule(models.Model):
    schedule_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    component = models.ForeignKey(Component, on_delete=models.CASCADE)
    action_type = models.ForeignKey(ActionType, on_delete=models.PROTECT)
    action_value = models.CharField(max_length=100, blank=True, null=True)
    schedule_time = models.TimeField()
    days_of_week = models.CharField(max_length=20, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Schedule for {self.component}"