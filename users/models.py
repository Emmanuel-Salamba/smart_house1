import uuid
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone


class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        
        # Set default user_type if not provided
        if 'user_type' not in extra_fields:
            # Get or create a default UserType for regular users
            user_type, created = UserType.objects.get_or_create(
                name='user',
                defaults={'description': 'Regular user'}
            )
            extra_fields['user_type'] = user_type
        
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        # Set admin user_type for superuser
        if 'user_type' not in extra_fields:
            user_type, created = UserType.objects.get_or_create(
                name='admin',
                defaults={'description': 'Administrator'}
            )
            extra_fields['user_type'] = user_type

        return self.create_user(email, password, **extra_fields)


class UserType(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)
    permissions = models.JSONField(default=dict)  # Store role-based permissions

    class Meta:
        db_table = 'user_type'
        verbose_name = 'User Type'
        verbose_name_plural = 'User Types'

    def __str__(self):
        return self.name


class User(AbstractBaseUser, PermissionsMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True, db_index=True)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    user_type = models.ForeignKey(UserType, on_delete=models.PROTECT, related_name='users')

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_login = models.DateTimeField(null=True, blank=True)

    # Status fields
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)

    # Security fields
    email_verification_token = models.CharField(max_length=100, blank=True)
    password_reset_token = models.CharField(max_length=100, blank=True)
    password_reset_token_created_at = models.DateTimeField(null=True, blank=True)

    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    class Meta:
        db_table = 'user'
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        indexes = [
            models.Index(fields=['email', 'is_active']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.email})"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"