import uuid
from django.db import models
from django.contrib.postgres.fields import JSONField  # Use models.JSONField if not using PostgreSQL
from users.models import User
from houses.models import House
from devices.models import Component, ActionType


class ActivityLog(models.Model):
    LOG_LEVELS = [
        ('info', 'Info'),
        ('warning', 'Warning'),
        ('error', 'Error'),
        ('security', 'Security'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Relationships
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='activities')
    house = models.ForeignKey(House, on_delete=models.CASCADE, related_name='activities')
    component = models.ForeignKey(Component, on_delete=models.CASCADE, null=True, blank=True, related_name='activities')
    action_type = models.ForeignKey(ActionType, on_delete=models.PROTECT, null=True, blank=True,
                                    related_name='activities')

    # Action details
    action_name = models.CharField(max_length=100)
    action_parameters = models.JSONField(default=dict)
    action_result = models.JSONField(default=dict)

    # Log metadata
    log_level = models.CharField(max_length=10, choices=LOG_LEVELS, default='info')
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)

    # For automated actions
    is_automated = models.BooleanField(default=False)
    automation_source = models.CharField(max_length=100, blank=True)  # Which automation triggered this

    class Meta:
        db_table = 'activity_log'
        verbose_name = 'Activity Log'
        verbose_name_plural = 'Activity Logs'
        indexes = [
            models.Index(fields=['house', 'created_at']),
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['component', 'created_at']),
            models.Index(fields=['created_at']),
            models.Index(fields=['log_level', 'created_at']),
        ]
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.action_name} - {self.house.name} - {self.created_at}"


class SecurityEvent(models.Model):
    EVENT_TYPES = [
        ('failed_login', 'Failed Login'),
        ('password_change', 'Password Change'),
        ('user_invited', 'User Invited'),
        ('access_denied', 'Access Denied'),
        ('device_tamper', 'Device Tamper Detected'),
        ('unusual_activity', 'Unusual Activity'),
    ]

    SEVERITY_LEVELS = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Event details
    event_type = models.CharField(max_length=50, choices=EVENT_TYPES)
    severity = models.CharField(max_length=10, choices=SEVERITY_LEVELS, default='medium')
    description = models.TextField()

    # Related entities
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='security_events')
    house = models.ForeignKey(House, on_delete=models.CASCADE, null=True, blank=True, related_name='security_events')
    component = models.ForeignKey(Component, on_delete=models.SET_NULL, null=True, blank=True,
                                  related_name='security_events')

    # Technical details
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField(blank=True)
    request_path = models.CharField(max_length=500, blank=True)

    # Resolution
    is_resolved = models.BooleanField(default=False)
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                    related_name='resolved_events')
    resolution_notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'security_event'
        verbose_name = 'Security Event'
        verbose_name_plural = 'Security Events'
        indexes = [
            models.Index(fields=['event_type', 'created_at']),
            models.Index(fields=['severity', 'created_at']),
            models.Index(fields=['is_resolved', 'created_at']),
        ]
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.event_type} - {self.severity} - {self.created_at}"