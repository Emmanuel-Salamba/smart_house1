from django.contrib import admin
from .models import ActivityLog, SecurityEvent


@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    list_display = (
        'action_name',
        'house',
        'user',
        'component',
        'log_level',
        'is_automated',
        'created_at',
        'source'  # ADDED
    )
    list_filter = (
        'log_level',
        'is_automated',
        'created_at',
        'house',
        'action_type',
        'source'  # ADDED
    )
    search_fields = (
        'action_name',
        'user__email',
        'user__first_name',
        'user__last_name',
        'house__name',
        'component__name',
        'ip_address'
    )
    readonly_fields = ('created_at', 'updated_at')  # ADDED updated_at
    date_hierarchy = 'created_at'

    # ADD THESE PERMISSION METHODS FOR SECURITY:
    def has_add_permission(self, request):
        """Prevent manual creation of activity logs"""
        return False

    def has_change_permission(self, request, obj=None):
        """Prevent editing of activity logs"""
        return False

    def has_delete_permission(self, request, obj=None):
        """Only superusers can delete logs"""
        return request.user.is_superuser

    fieldsets = (
        ('Activity Information', {
            'fields': (
                'action_name',
                'action_type',
                'action_parameters',
                'action_result',
                'log_level',
                'source',  # ADDED
                'status_code'  # ADDED
            )
        }),
        ('Related Entities', {
            'fields': (
                'user',
                'house',
                'component'
            )
        }),
        ('Technical Details', {
            'fields': (
                'ip_address',
                'user_agent',
                'request_path',
                'is_automated',
                'automation_source',
                'execution_time',  # ADDED
                'memory_usage'  # ADDED if you want to show it
            )
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        })
    )

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = queryset.select_related('user', 'house', 'component', 'action_type')
        return queryset

    # OPTIONAL: Add custom column for action_parameters preview
    def action_params_preview(self, obj):
        """Show a preview of action parameters"""
        params = obj.action_parameters
        if isinstance(params, dict) and params:
            return str(params)[:100] + '...' if len(str(params)) > 100 else str(params)
        return '-'

    action_params_preview.short_description = 'Parameters Preview'


@admin.register(SecurityEvent)
class SecurityEventAdmin(admin.ModelAdmin):
    list_display = (
        'event_type',
        'severity',
        'house',
        'user',
        'is_resolved',
        'created_at'
    )
    list_filter = (
        'event_type',
        'severity',
        'is_resolved',
        'created_at',
        'house'
    )
    search_fields = (
        'event_type',
        'description',
        'user__email',
        'user__first_name',
        'user__last_name',
        'house__name',
        'component__name',
        'ip_address',
        'request_path'
    )
    readonly_fields = ('created_at', 'resolved_at')  # ADDED resolved_at
    date_hierarchy = 'created_at'

    fieldsets = (
        ('Event Details', {
            'fields': (
                'event_type',
                'severity',
                'description'
            )
        }),
        ('Related Entities', {
            'fields': (
                'user',
                'house',
                'component'
            )
        }),
        ('Technical Information', {
            'fields': (
                'ip_address',
                'user_agent',
                'request_path'
            )
        }),
        ('Resolution', {
            'fields': (
                'is_resolved',
                'resolved_at',
                'resolved_by',
                'resolution_notes'
            )
        }),
        ('Timestamps', {
            'fields': ('created_at',)
        })
    )

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = queryset.select_related('user', 'house', 'component', 'resolved_by')
        return queryset

    actions = ['mark_as_resolved']

    def mark_as_resolved(self, request, queryset):
        updated = queryset.update(
            is_resolved=True,
            resolved_by=request.user,
            resolved_at=timezone.now()  # ADD THIS
        )
        self.message_user(request, f'{updated} security events marked as resolved.')

    mark_as_resolved.short_description = "Mark selected security events as resolved"

    # ADD PERMISSION METHODS FOR SECURITY:
    def has_add_permission(self, request):
        """Allow adding security events (for testing/admin)"""
        return True

    def has_change_permission(self, request, obj=None):
        """Allow editing security events"""
        return True

    def has_delete_permission(self, request, obj=None):
        """Only superusers can delete security events"""
        return request.user.is_superuser