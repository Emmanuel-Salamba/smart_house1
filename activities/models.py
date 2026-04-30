import uuid
import json
from django.db import models
from django.core.serializers.json import DjangoJSONEncoder
from users.models import User
from houses.models import House
from devices.models import Component, ActionType


class ActivityLog(models.Model):
    LOG_LEVELS = [
        ('debug', 'Debug'),
        ('info', 'Info'),
        ('warning', 'Warning'),
        ('error', 'Error'),
        ('security', 'Security'),
    ]

    SOURCE_TYPES = [
        ('mobile_app', 'Mobile App'),
        ('web_app', 'Web App'),
        ('api', 'API'),
        ('microcontroller', 'Microcontroller'),
        ('physical_switch', 'Physical Switch'),
        ('automation', 'Automation'),
        ('admin', 'Admin Panel'),
        ('system', 'System'),
    ]

    DEVICE_PLATFORMS = [
        ('ios', 'iOS'),
        ('android', 'Android'),
        ('web', 'Web Browser'),
        ('esp32', 'ESP32 Microcontroller'),
        ('api', 'API Call'),
        ('unknown', 'Unknown'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # ========== EXISTING RELATIONSHIPS ==========
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='activities')
    house = models.ForeignKey(House, on_delete=models.SET_NULL, null=True, blank=True, related_name='activities')
    component = models.ForeignKey(Component, on_delete=models.SET_NULL, null=True, blank=True,
                                  related_name='activities')
    action_type = models.ForeignKey(ActionType, on_delete=models.PROTECT, null=True, blank=True,
                                    related_name='activities')

    # ========== ACTION DETAILS ==========
    action_name = models.CharField(max_length=100)
    action_parameters = models.JSONField(default=dict, encoder=DjangoJSONEncoder)
    action_result = models.JSONField(default=dict, encoder=DjangoJSONEncoder)

    # ========== LOG METADATA ==========
    log_level = models.CharField(max_length=10, choices=LOG_LEVELS, default='info')
    source = models.CharField(max_length=20, choices=SOURCE_TYPES, default='api')

    is_automated = models.BooleanField(default=False)
    automation_source = models.CharField(max_length=100, blank=True)

    # ========== TECHNICAL DETAILS ==========
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    request_path = models.CharField(max_length=500, blank=True)

    # ========== NEW: TRACKING & CORRELATION ==========
    session_id = models.CharField(max_length=100, blank=True, default='', db_index=True,
                                   help_text="User session ID for tracking user journey")
    request_id = models.CharField(max_length=100, blank=True, db_index=True,
                                   help_text="Unique request ID for correlating related log entries")

    # ========== NEW: PERFORMANCE METRICS ==========
    duration_ms = models.IntegerField(null=True, blank=True,
                                       help_text="Action duration in milliseconds")

    # ========== NEW: USER CONTEXT ==========
    household_member_id = models.UUIDField(null=True, blank=True,
                                            help_text="Which household member performed the action")

    # ========== NEW: CLIENT INFORMATION ==========
    device_platform = models.CharField(max_length=20, choices=DEVICE_PLATFORMS, default='unknown',
                                        help_text="Platform the action came from")
    app_version = models.CharField(max_length=20, blank=True,
                                    help_text="Mobile app version (e.g., 1.2.3)")
    firmware_version = models.CharField(max_length=20, blank=True,
                                         help_text="ESP32 firmware version")

    # ========== NEW: GEOLOCATION (if user permits) ==========
    latitude = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True,
                                    help_text="Latitude of the user/device")
    longitude = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True,
                                     help_text="Longitude of the user/device")

    # ========== NEW: BUSINESS METRICS ==========
    subscription_tier = models.CharField(max_length=20, blank=True,
                                          help_text="User's subscription plan (free, basic, premium, enterprise)")
    is_billable = models.BooleanField(default=True,
                                       help_text="Whether this action counts toward billing/usage limits")

    # ========== EXISTING PERFORMANCE METRICS ==========
    execution_time = models.FloatField(null=True, blank=True)
    memory_usage = models.IntegerField(null=True, blank=True)

    # ========== STATUS ==========
    status_code = models.IntegerField(null=True, blank=True)

    # ========== TIMESTAMPS ==========
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

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
            models.Index(fields=['source', 'created_at']),
            # NEW INDEXES
            models.Index(fields=['session_id', 'created_at']),
            models.Index(fields=['request_id']),
            models.Index(fields=['device_platform', 'created_at']),
            models.Index(fields=['subscription_tier', 'created_at']),
            models.Index(fields=['is_billable', 'created_at']),
        ]
        ordering = ['-created_at']

    def __str__(self):
        house_name = self.house.name if self.house else "Unknown House"
        return f"{self.action_name} - {house_name} - {self.created_at}"


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
    house = models.ForeignKey(House, on_delete=models.SET_NULL, null=True, blank=True, related_name='security_events')
    component = models.ForeignKey(Component, on_delete=models.SET_NULL, null=True, blank=True,
                                  related_name='security_events')

    # Technical details
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField(blank=True)
    request_path = models.CharField(max_length=500, blank=True)

    # NEW: Session tracking for security events
    session_id = models.CharField(max_length=100, blank=True, default='', db_index=True)

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
            models.Index(fields=['session_id', 'created_at']),
        ]
        ordering = ['-created_at']

    def __str__(self):
        house_name = self.house.name if self.house else "Unknown House"
        return f"{self.event_type} - {house_name} - {self.created_at}"