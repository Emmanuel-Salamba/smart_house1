from django.contrib import admin
from .models import Schedule, AutomationRule

@admin.register(Schedule)
class ScheduleAdmin(admin.ModelAdmin):
    list_display = ('name', 'house', 'component', 'action_type', 'scheduled_time', 'recurrence', 'is_active')
    list_filter = ('house', 'component', 'recurrence', 'is_active', 'created_at')
    search_fields = ('name', 'house__name', 'component__name')
    readonly_fields = ('id', 'created_at', 'updated_at')
    list_per_page = 20
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'house', 'component', 'action_type')
        }),
        ('Schedule Configuration', {
            'fields': ('scheduled_time', 'start_date', 'end_date', 'recurrence', 'days_of_week')
        }),
        ('Action Details', {
            'fields': ('action_parameters',)
        }),
        ('Status & Security', {
            'fields': ('is_active', 'requires_confirmation', 'max_duration_minutes')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'last_triggered', 'next_trigger'),
            'classes': ('collapse',)
        }),
    )

@admin.register(AutomationRule)
class AutomationRuleAdmin(admin.ModelAdmin):
    list_display = ('name', 'house', 'trigger_type', 'is_active', 'priority', 'last_triggered')
    list_filter = ('house', 'trigger_type', 'is_active', 'priority', 'created_at')
    search_fields = ('name', 'house__name', 'trigger_type')
    readonly_fields = ('id', 'created_at', 'updated_at', 'last_triggered')
    list_per_page = 20
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'house', 'trigger_type')
        }),
        ('Trigger Conditions', {
            'fields': ('trigger_conditions',)
        }),
        ('Actions', {
            'fields': ('actions',)
        }),
        ('Status & Security', {
            'fields': ('is_active', 'priority', 'requires_confirmation', 'max_executions_per_hour')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'last_triggered'),
            'classes': ('collapse',)
        }),
    )