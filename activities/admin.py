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
        'created_at'
    )
    list_filter = (
        'log_level', 
        'is_automated', 
        'created_at', 
        'house',
        'action_type'
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
    readonly_fields = ('created_at',)
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Activity Information', {
            'fields': (
                'action_name', 
                'action_type',
                'action_parameters', 
                'action_result',
                'log_level'
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
                'is_automated', 
                'automation_source'
            )
        }),
        ('Timestamps', {
            'fields': ('created_at',)
        })
    )

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = queryset.select_related('user', 'house', 'component', 'action_type')
        return queryset


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
    readonly_fields = ('created_at',)
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
            resolved_by=request.user
        )
        self.message_user(request, f'{updated} security events marked as resolved.')
    mark_as_resolved.short_description = "Mark selected security events as resolved"