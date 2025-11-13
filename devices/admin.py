from django.contrib import admin
from .models import ComponentType, Component, Microcontroller, ActionType


@admin.register(ComponentType)
class ComponentTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'capabilities_preview')
    search_fields = ('name', 'description')
    list_filter = ('name',)
    filter_horizontal = ()  # For ManyToMany fields if you add any later
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description')
        }),
        ('Capabilities & Configuration', {
            'fields': ('capabilities', 'default_config')
        }),
    )

    def capabilities_preview(self, obj):
        return ', '.join(obj.capabilities) if obj.capabilities else 'None'
    capabilities_preview.short_description = 'Capabilities'


@admin.register(Component)
class ComponentAdmin(admin.ModelAdmin):
    list_display = (
        'name', 
        'device_id', 
        'component_type', 
        'house', 
        'room', 
        'status', 
        'is_active',
        'last_seen'
    )
    list_filter = (
        'status', 
        'is_active', 
        'component_type', 
        'house',
        'room',
        'created_at'
    )
    search_fields = (
        'name', 
        'device_id', 
        'mac_address',
        'room',
        'house__name',
        'component_type__name'
    )
    readonly_fields = ('created_at', 'updated_at', 'last_seen')
    date_hierarchy = 'created_at'
    list_select_related = ('component_type', 'house')
    
    fieldsets = (
        ('Basic Information', {
            'fields': (
                'name', 
                'device_id', 
                'component_type', 
                'house'
            )
        }),
        ('Location', {
            'fields': (
                'room', 
                'location_description'
            )
        }),
        ('Network Information', {
            'fields': (
                'mac_address', 
                'ip_address'
            )
        }),
        ('Status & State', {
            'fields': (
                'status', 
                'current_state', 
                'is_active'
            )
        }),
        ('Configuration', {
            'fields': ('configuration',)
        }),
        ('Timestamps', {
            'fields': (
                'created_at', 
                'updated_at', 
                'last_seen'
            )
        })
    )

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = queryset.select_related('component_type', 'house')
        return queryset

    actions = ['mark_as_online', 'mark_as_offline', 'activate_components', 'deactivate_components']

    def mark_as_online(self, request, queryset):
        updated = queryset.update(status='online')
        self.message_user(request, f'{updated} components marked as online.')
    mark_as_online.short_description = "Mark selected components as online"

    def mark_as_offline(self, request, queryset):
        updated = queryset.update(status='offline')
        self.message_user(request, f'{updated} components marked as offline.')
    mark_as_offline.short_description = "Mark selected components as offline"

    def activate_components(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} components activated.')
    activate_components.short_description = "Activate selected components"

    def deactivate_components(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} components deactivated.')
    deactivate_components.short_description = "Deactivate selected components"


@admin.register(Microcontroller)
class MicrocontrollerAdmin(admin.ModelAdmin):
    list_display = (
        'name', 
        'mac_address', 
        'house', 
        'status', 
        'firmware_version', 
        'is_approved',
        'last_heartbeat'
    )
    list_filter = (
        'status', 
        'is_approved', 
        'house',
        'created_at'
    )
    search_fields = (
        'name', 
        'mac_address', 
        'ip_address',
        'firmware_version',
        'house__name'
    )
    readonly_fields = ('created_at', 'updated_at', 'last_heartbeat')
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Basic Information', {
            'fields': (
                'name', 
                'house'
            )
        }),
        ('Hardware Information', {
            'fields': (
                'mac_address', 
                'firmware_version', 
                'hardware_version'
            )
        }),
        ('Status & Communication', {
            'fields': (
                'status', 
                'ip_address', 
                'last_heartbeat', 
                'heartbeat_interval'
            )
        }),
        ('Security', {
            'fields': (
                'api_key', 
                'is_approved'
            )
        }),
        ('Timestamps', {
            'fields': (
                'created_at', 
                'updated_at'
            )
        })
    )

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = queryset.select_related('house')
        return queryset

    actions = ['approve_microcontrollers', 'disapprove_microcontrollers', 'mark_as_online', 'mark_as_offline']

    def approve_microcontrollers(self, request, queryset):
        updated = queryset.update(is_approved=True)
        self.message_user(request, f'{updated} microcontrollers approved.')
    approve_microcontrollers.short_description = "Approve selected microcontrollers"

    def disapprove_microcontrollers(self, request, queryset):
        updated = queryset.update(is_approved=False)
        self.message_user(request, f'{updated} microcontrollers disapproved.')
    disapprove_microcontrollers.short_description = "Disapprove selected microcontrollers"

    def mark_as_online(self, request, queryset):
        updated = queryset.update(status='online')
        self.message_user(request, f'{updated} microcontrollers marked as online.')
    mark_as_online.short_description = "Mark selected microcontrollers as online"

    def mark_as_offline(self, request, queryset):
        updated = queryset.update(status='offline')
        self.message_user(request, f'{updated} microcontrollers marked as offline.')
    mark_as_offline.short_description = "Mark selected microcontrollers as offline"


@admin.register(ActionType)
class ActionTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'allowed_component_types_count')
    search_fields = ('name', 'description')
    list_filter = ('name',)
    filter_horizontal = ('allowed_component_types',)
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description')
        }),
        ('Configuration', {
            'fields': ('allowed_component_types', 'parameters_schema')
        }),
    )

    def allowed_component_types_count(self, obj):
        return obj.allowed_component_types.count()
    allowed_component_types_count.short_description = 'Allowed Component Types Count'

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = queryset.prefetch_related('allowed_component_types')
        return queryset