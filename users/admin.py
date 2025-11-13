# Register your models here.
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, UserType

# Custom User Admin
@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('email', 'first_name', 'last_name', 'user_type', 'is_staff', 'is_active')
    list_filter = ('user_type', 'is_staff', 'is_active', 'created_at')
    search_fields = ('email', 'first_name', 'last_name')
    ordering = ('email',)
    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal Info', {'fields': ('first_name', 'last_name', 'user_type')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important Dates', {'fields': ('last_login', 'created_at', 'updated_at')}),
        ('Security', {'fields': ('email_verification_token', 'password_reset_token', 'password_reset_token_created_at')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'first_name', 'last_name', 'user_type', 'password1', 'password2', 'is_staff', 'is_active'),
        }),
    )
    
    readonly_fields = ('created_at', 'updated_at')

# UserType Admin
@admin.register(UserType)
class UserTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name',)
    list_filter = ('name',)