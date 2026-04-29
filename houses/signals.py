# houses/signals.py
from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from django.utils import timezone
from .models import House
from activities.models import ActivityLog

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
    """Log when a house is created or updated"""
    
    if created:
        # Log house creation
        ActivityLog.objects.create(
            action_name='house_created',
            house=instance,
            action_parameters={
                'name': instance.name,
                'address': instance.address,
                'house_code': instance.house_code,
            },
            action_result={
                'success': True,
                'message': f'House "{instance.name}" was created',
                'house_id': str(instance.id),
            },
            log_level='info',
            source='admin'
        )
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
                action_name='house_updated',
                house=instance,
                action_parameters={
                    'house_id': str(instance.id),
                    'house_name': instance.name,
                    'changes': changes,
                },
                action_result={
                    'success': True,
                    'message': f'House "{instance.name}" was updated',
                    'updated_fields': list(changes.keys()),
                },
                log_level='info',
                source='admin'
            )

@receiver(post_delete, sender=House)
def log_house_deletion(sender, instance, **kwargs):
    """Log when a house is deleted"""
    ActivityLog.objects.create(
        action_name='house_deleted',
        house=None,  # This is now allowed because we changed to SET_NULL
        action_parameters={
            'house_id': str(instance.id),
            'name': instance.name,
            'address': instance.address,
            'house_code': instance.house_code,
        },
        action_result={
            'success': True,
            'message': f'House "{instance.name}" was deleted',
        },
        log_level='warning',
        source='admin'
    )