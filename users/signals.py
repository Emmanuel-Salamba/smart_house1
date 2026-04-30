# users/signals.py
import time
import uuid
from django.contrib.auth.signals import user_logged_in, user_logged_out, user_login_failed
from django.dispatch import receiver
from django.utils import timezone
from activities.models import ActivityLog

@receiver(user_logged_in)
def log_user_login(sender, request, user, **kwargs):
    """Log when a user successfully logs in"""
    start_time = time.time()
    
    # Generate or get session ID
    session_id = request.session.session_key or str(uuid.uuid4())
    
    # Calculate duration after the operation
    duration_ms = int((time.time() - start_time) * 1000)
    
    ActivityLog.objects.create(
        user=user,
        action_name='user_login',
        action_parameters={
            'user_id': str(user.id),
            'user_email': user.email,
            'ip_address': request.META.get('REMOTE_ADDR', 'unknown'),
            'user_agent': request.META.get('HTTP_USER_AGENT', 'unknown'),
        },
        action_result={
            'success': True,
            'message': f'User {user.email} logged in successfully',
        },
        log_level='info',
        source='web_admin',
        ip_address=request.META.get('REMOTE_ADDR'),
        user_agent=request.META.get('HTTP_USER_AGENT', ''),
        request_path=request.get_full_path(),
        # Duration tracking
        duration_ms=duration_ms,
        execution_time=duration_ms / 1000,  # Convert to seconds
        # Other fields
        session_id=session_id,
        device_platform='web',
        is_billable=False,
    )
    print(f"✅ Login logged: {user.email} (took {duration_ms}ms)")

@receiver(user_logged_out)
def log_user_logout(sender, request, user, **kwargs):
    """Log when a user logs out"""
    start_time = time.time()
    
    if user:
        # Calculate duration
        duration_ms = int((time.time() - start_time) * 1000)
        
        # Get session ID if available
        session_id = request.session.session_key if hasattr(request, 'session') else ''
        
        ActivityLog.objects.create(
            user=user,
            action_name='user_logout',
            action_parameters={
                'user_id': str(user.id),
                'user_email': user.email,
                'ip_address': request.META.get('REMOTE_ADDR', 'unknown'),
            },
            action_result={
                'success': True,
                'message': f'User {user.email} logged out',
            },
            log_level='info',
            source='web_admin',
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            request_path=request.get_full_path(),
            # Duration tracking
            duration_ms=duration_ms,
            execution_time=duration_ms / 1000,
            # Other fields
            session_id=session_id,
            device_platform='web',
            is_billable=False,
        )
        print(f"✅ Logout logged: {user.email} (took {duration_ms}ms)")

@receiver(user_login_failed)
def log_failed_login(sender, credentials, request, **kwargs):
    """Log when a user fails to log in"""
    start_time = time.time()
    
    email = credentials.get('email', 'unknown') or credentials.get('username', 'unknown')
    
    # Calculate duration
    duration_ms = int((time.time() - start_time) * 1000)
    
    # Generate session ID for failed attempt
    session_id = str(uuid.uuid4())
    
    ActivityLog.objects.create(
        user=None,
        action_name='user_login_failed',
        action_parameters={
            'attempted_email': email,
            'ip_address': request.META.get('REMOTE_ADDR', 'unknown'),
            'user_agent': request.META.get('HTTP_USER_AGENT', 'unknown'),
        },
        action_result={
            'success': False,
            'message': f'Failed login attempt for {email}',
        },
        log_level='security',
        source='web_admin',
        ip_address=request.META.get('REMOTE_ADDR'),
        user_agent=request.META.get('HTTP_USER_AGENT', ''),
        request_path=request.get_full_path(),
        # Duration tracking
        duration_ms=duration_ms,
        execution_time=duration_ms / 1000,
        # Other fields
        session_id=session_id,
        device_platform='web',
        is_billable=False,
    )
    print(f"⚠️ Failed login logged: {email} (took {duration_ms}ms)")