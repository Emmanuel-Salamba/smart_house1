from django.contrib import admin
from .models import House, HouseUser


@admin.register(House)
class HouseAdmin(admin.ModelAdmin):
    list_display = (
        'name', 
        'house_code', 
        'is_active', 
        'created_at',
        'users_count'
    )
    list_filter = (
        'is_active', 
        'created_at'
    )
    search_fields = (
        'name', 
        'house_code', 
        'address',
        'gps_coordinates'
    )
    readonly_fields = ('created_at', 'updated_at', 'deleted_at')
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Basic Information', {
            'fields': (
                'name', 
                'house_code'
            )
        }),
        ('Location', {
            'fields': (
                'address', 
                'gps_coordinates'
            )
        }),
        ('Status', {
            'fields': (
                'is_active',
            )
        }),
        ('Timestamps', {
            'fields': (
                'created_at', 
                'updated_at',
                'deleted_at'
            )
        })
    )

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = queryset.prefetch_related('house_users')
        return queryset

    def users_count(self, obj):
        return obj.house_users.count()
    users_count.short_description = 'Number of Users'

    actions = ['activate_houses', 'deactivate_houses']

    def activate_houses(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} houses activated.')
    activate_houses.short_description = "Activate selected houses"

    def deactivate_houses(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} houses deactivated.')
    deactivate_houses.short_description = "Deactivate selected houses"


@admin.register(HouseUser)
class HouseUserAdmin(admin.ModelAdmin):
    list_display = (
        'user', 
        'house', 
        'access_level', 
        'can_control_devices',
        'can_invite_users',
        'can_manage_house',
        'created_at'
    )
    list_filter = (
        'access_level', 
        'can_control_devices',
        'can_invite_users',
        'can_manage_house',
        'created_at',
        'house'
    )
    search_fields = (
        'user__email', 
        'user__first_name', 
        'user__last_name',
        'house__name',
        'house__house_code'
    )
    readonly_fields = ('created_at', 'updated_at')
    date_hierarchy = 'created_at'
    list_select_related = ('user', 'house')
    
    fieldsets = (
        ('Relationship', {
            'fields': (
                'user', 
                'house'
            )
        }),
        ('Access Level', {
            'fields': (
                'access_level',
            )
        }),
        ('Permissions', {
            'fields': (
                'can_control_devices', 
                'can_invite_users', 
                'can_manage_house'
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
        queryset = queryset.select_related('user', 'house')
        return queryset

    actions = [
        'make_owners', 
        'make_admins', 
        'make_residents', 
        'make_guests',
        'grant_all_permissions',
        'revoke_all_permissions'
    ]

    def make_owners(self, request, queryset):
        updated = queryset.update(access_level='owner')
        self.message_user(request, f'{updated} users set as owners.')
    make_owners.short_description = "Set selected as owners"

    def make_admins(self, request, queryset):
        updated = queryset.update(access_level='admin')
        self.message_user(request, f'{updated} users set as administrators.')
    make_admins.short_description = "Set selected as administrators"

    def make_residents(self, request, queryset):
        updated = queryset.update(access_level='resident')
        self.message_user(request, f'{updated} users set as residents.')
    make_residents.short_description = "Set selected as residents"

    def make_guests(self, request, queryset):
        updated = queryset.update(access_level='guest')
        self.message_user(request, f'{updated} users set as guests.')
    make_guests.short_description = "Set selected as guests"

    def grant_all_permissions(self, request, queryset):
        updated = queryset.update(
            can_control_devices=True,
            can_invite_users=True,
            can_manage_house=True
        )
        self.message_user(request, f'{updated} users granted all permissions.')
    grant_all_permissions.short_description = "Grant all permissions to selected"

    def revoke_all_permissions(self, request, queryset):
        updated = queryset.update(
            can_control_devices=False,
            can_invite_users=False,
            can_manage_house=False
        )
        self.message_user(request, f'{updated} users revoked all permissions.')
    revoke_all_permissions.short_description = "Revoke all permissions from selected"