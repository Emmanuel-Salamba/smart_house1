# houses/signals.py
from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from django.utils import timezone
from .models import House
from activities.models import ActivityLog
from users.middleware import get_current_user

# Store original state before update
@receiver(pre_save, sender=House)
def store_house_original_state(sender, instance, **kwargs):
    """Store the original state before update to detect changes"""
    if instance.pk:
        try:
            instance._original_state = House.objects.get(pk=instance.pk)
        except House.DoesNotExist:
            instance._original_state = None
    else:
        instance._original_state = None

@receiver(post_save, sender=House)
def log_house_creation_or_update(sender, instance, created, **kwargs):
    """Log when a house is created or updated with the current user"""
    # Get the current logged-in user from middleware
    current_user = get_current_user()
    
    if created:
        # Log house creation
        ActivityLog.objects.create(
            user=current_user,  # ✅ NOW CAPTURES WHO CREATED
            action_name='house_created',
            house=instance,
            action_parameters={
                'name': instance.name,
                'address': instance.address,
                'house_code': instance.house_code,
            },
            action_result={
                'success': True,
                'message': f'House "{instance.name}" was created by {current_user.email if current_user else "Unknown"}',
                'house_id': str(instance.id),
            },
            log_level='info',
            source='admin',
            device_platform='web',
            is_billable=False,
        )
        print(f"✅ House creation logged by: {current_user.email if current_user else 'Unknown'}")
    else:
        # Log house update (if anything changed)
        changes = {}
        if hasattr(instance, '_original_state') and instance._original_state:
            original = instance._original_state
            
            if original.name != instance.name:
                changes['name'] = {'from': original.name, 'to': instance.name}
            if original.address != instance.address:
                changes['address'] = {'from': original.address, 'to': instance.address}
            if original.house_code != instance.house_code:
                changes['house_code'] = {'from': original.house_code, 'to': instance.house_code}
        
        if changes:
            ActivityLog.objects.create(
                user=current_user,  # ✅ NOW CAPTURES WHO UPDATED
                action_name='house_updated',
                house=instance,
                action_parameters={
                    'house_id': str(instance.id),
                    'house_name': instance.name,
                    'changes': changes,
                },
                action_result={
                    'success': True,
                    'message': f'House "{instance.name}" was updated by {current_user.email if current_user else "Unknown"}',
                    'updated_fields': list(changes.keys()),
                },
                log_level='info',
                source='admin',
                device_platform='web',
                is_billable=False,
            )
            print(f"✅ House update logged by: {current_user.email if current_user else 'Unknown'}")

@receiver(post_delete, sender=House)
def log_house_deletion(sender, instance, **kwargs):
    """Log when a house is deleted with the current user"""
    # Get the current logged-in user from middleware
    current_user = get_current_user()
    
    ActivityLog.objects.create(
        user=current_user,  # ✅ NOW CAPTURES WHO DELETED
        action_name='house_deleted',
        house=None,  # House is being deleted, so set to None
        action_parameters={
            'house_id': str(instance.id),
            'name': instance.name,
            'address': instance.address,
            'house_code': instance.house_code,
        },
        action_result={
            'success': True,
            'message': f'House "{instance.name}" was deleted by {current_user.email if current_user else "Unknown"}',
        },
        log_level='warning',
        source='admin',
        device_platform='web',
        is_billable=False,
    )
    print(f"✅ House deletion logged by: {current_user.email if current_user else 'Unknown'}")