import uuid
from django.db import models
from users.models import User
from devices.models import Component, ActionType


class ActivityLog(models.Model):
    EXECUTION_STATUS = [
        ('success', 'Success'),
        ('failed', 'Failed'),
        ('pending', 'Pending'),
    ]

    log_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    component = models.ForeignKey(Component, on_delete=models.CASCADE)
    action_type = models.ForeignKey(ActionType, on_delete=models.PROTECT)
    action_value = models.CharField(max_length=100, blank=True, null=True)
    previous_state = models.JSONField(blank=True, null=True)
    new_state = models.JSONField(blank=True, null=True)
    execution_status = models.CharField(max_length=20, choices=EXECUTION_STATUS, default='pending')
    error_message = models.TextField(blank=True, null=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user} - {self.component} - {self.action_type}"