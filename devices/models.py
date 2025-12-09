import uuid
from django.db import models
from houses.models import House
import secrets  # Already imported at the top


class ComponentType(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)
    capabilities = models.JSONField(default=list)  # ['turn_on', 'turn_off', 'dim', etc.]
    default_config = models.JSONField(default=dict)  # Default settings for this component type

    class Meta:
        db_table = 'component_type'
        verbose_name = 'Component Type'
        verbose_name_plural = 'Component Types'

    def __str__(self):
        return self.name


class Component(models.Model):
    STATUS_CHOICES = [
        ('online', 'Online'),
        ('offline', 'Offline'),
        ('error', 'Error'),
        ('maintenance', 'Maintenance'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    component_type = models.ForeignKey(ComponentType, on_delete=models.PROTECT, related_name='components')
    house = models.ForeignKey(House, on_delete=models.CASCADE, related_name='components')

    # Identification
    name = models.CharField(max_length=100)
    device_id = models.CharField(max_length=100, unique=True, db_index=True)  # Physical device ID

    # Location
    room = models.CharField(max_length=100, blank=True)
    location_description = models.TextField(blank=True)

    # Network information
    mac_address = models.CharField(max_length=17, db_index=True)  # Format: XX:XX:XX:XX:XX:XX
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    # Status and state
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='offline')
    current_state = models.JSONField(default=dict)  # Current device state {power: on, brightness: 80}

    # Configuration
    configuration = models.JSONField(default=dict)  # Device-specific configuration
    is_active = models.BooleanField(default=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_seen = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'component'
        verbose_name = 'Component'
        verbose_name_plural = 'Components'
        indexes = [
            models.Index(fields=['house', 'status']),
            models.Index(fields=['mac_address']),
            models.Index(fields=['device_id']),
            models.Index(fields=['last_seen']),
        ]

    def __str__(self):
        return f"{self.name} ({self.device_id})"


class Microcontroller(models.Model):
    STATUS_CHOICES = [
        ('online', 'Online'),
        ('offline', 'Offline'),
        ('updating', 'Updating'),
        ('error', 'Error'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    house = models.ForeignKey(House, on_delete=models.CASCADE, related_name='microcontrollers')

    # Identification
    name = models.CharField(max_length=100)
    mac_address = models.CharField(max_length=17, unique=True, db_index=True)

    # Status and info
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='offline')
    firmware_version = models.CharField(max_length=50)
    hardware_version = models.CharField(max_length=50, blank=True)

    # Communication
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    last_heartbeat = models.DateTimeField(null=True, blank=True)
    heartbeat_interval = models.IntegerField(default=60)  # seconds

    # Security - MODIFIED THIS FIELD
    api_key = models.CharField(
        max_length=100, 
        unique=True, 
        db_index=True,
        blank=True,      # Allow blank in forms
        null=True,       # Allow null in database
        help_text="Leave empty to auto-generate"
    )
    is_approved = models.BooleanField(default=False)  # Manual approval for security

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # ADD THIS METHOD for auto-generating API keys
    def save(self, *args, **kwargs):
        """Save method with auto-generated API key"""
        # Generate API key ONLY if it doesn't exist
        if not self.api_key:
            self.api_key = secrets.token_urlsafe(32)
        super().save(*args, **kwargs)

    class Meta:
        db_table = 'microcontroller'
        verbose_name = 'Microcontroller'
        verbose_name_plural = 'Microcontrollers'
        indexes = [
            models.Index(fields=['house', 'status']),
            models.Index(fields=['mac_address']),
            models.Index(fields=['last_heartbeat']),
        ]

    def __str__(self):
        return f"{self.name} ({self.mac_address})"


class ActionType(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)
    allowed_component_types = models.ManyToManyField(ComponentType, blank=True)
    parameters_schema = models.JSONField(default=dict)  # JSON schema for action parameters

    class Meta:
        db_table = 'action_type'
        verbose_name = 'Action Type'
        verbose_name_plural = 'Action Types'

    def __str__(self):
        return self.name