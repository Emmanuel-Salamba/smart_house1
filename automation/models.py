import uuid
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from users.models import User
from houses.models import House
from devices.models import Component, ActionType

class Schedule(models.Model):
    RECURRENCE_CHOICES = [
        ('once', 'Once'),
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('weekdays', 'Weekdays'),
        ('weekends', 'Weekends'),
        ('custom', 'Custom'),
    ]

    DAYS_OF_WEEK = [
        (0, 'Monday'),
        (1, 'Tuesday'),
        (2, 'Wednesday'),
        (3, 'Thursday'),
        (4, 'Friday'),
        (5, 'Saturday'),
        (6, 'Sunday'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    
    # Relationships
    house = models.ForeignKey(House, on_delete=models.CASCADE, related_name='schedules')
    component = models.ForeignKey(Component, on_delete=models.CASCADE, related_name='schedules')
    action_type = models.ForeignKey(ActionType, on_delete=models.PROTECT, related_name='schedules')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_schedules')
    
    # Schedule configuration
    action_parameters = models.JSONField(default=dict)  # Parameters for the action
    scheduled_time = models.TimeField()
    start_date = models.DateField(default=timezone.now)
    end_date = models.DateField(null=True, blank=True)
    recurrence = models.CharField(max_length=20, choices=RECURRENCE_CHOICES, default='daily')
    
    # For weekly/custom recurrence
    days_of_week = models.JSONField(default=list, blank=True)  # [0,1,2,3,4] for weekdays
    
    # Status and control
    is_active = models.BooleanField(default=True)
    is_recurring = models.BooleanField(default=True)
    last_triggered = models.DateTimeField(null=True, blank=True)
    next_trigger = models.DateTimeField(null=True, blank=True)
    
    # Security
    requires_confirmation = models.BooleanField(default=False)
    max_duration_minutes = models.IntegerField(
        default=120, 
        validators=[MinValueValidator(1), MaxValueValidator(1440)]
    )  # Safety limit
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'schedule'
        verbose_name = 'Schedule'
        verbose_name_plural = 'Schedules'
        indexes = [
            models.Index(fields=['house', 'is_active']),
            models.Index(fields=['component', 'is_active']),
            models.Index(fields=['next_trigger']),
            models.Index(fields=['is_active', 'next_trigger']),
        ]

    def __str__(self):
        return f"{self.name} - {self.component.name}"

class AutomationRule(models.Model):
    TRIGGER_TYPES = [
        ('schedule', 'Schedule'),
        ('device_state', 'Device State Change'),
        ('sensor_value', 'Sensor Value'),
        ('manual', 'Manual'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    
    house = models.ForeignKey(House, on_delete=models.CASCADE, related_name='automation_rules')
    trigger_type = models.CharField(max_length=20, choices=TRIGGER_TYPES)
    
    # Trigger conditions (JSON for flexibility)
    trigger_conditions = models.JSONField(default=dict)
    
    # Actions to perform
    actions = models.JSONField(default=list)  # List of action configurations
    
    # Status
    is_active = models.BooleanField(default=True)
    priority = models.IntegerField(default=1, validators=[MinValueValidator(1), MaxValueValidator(10)])
    
    # Security
    requires_confirmation = models.BooleanField(default=False)
    max_executions_per_hour = models.IntegerField(default=10)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_triggered = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'automation_rule'
        verbose_name = 'Automation Rule'
        verbose_name_plural = 'Automation Rules'
        indexes = [
            models.Index(fields=['house', 'is_active']),
            models.Index(fields=['trigger_type', 'is_active']),
        ]

    def __str__(self):
        return f"{self.name} ({self.trigger_type})"