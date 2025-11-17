
import uuid
import asyncio
from datetime import datetime, timedelta
from django.utils import timezone
from django.core.cache import cache
from asgiref.sync import sync_to_async
from channels.layers import get_channel_layer
from activities.models import ActivityLog
from devices.models import Component, ActionType

class CommandBufferService:
    def __init__(self):
        self.channel_layer = get_channel_layer()
        self.timeout = 30  # seconds
    
    async def buffer_command(self, command_data):
        """
        Buffer a command while waiting for microcontroller ACK
        """
        command_id = str(uuid.uuid4())
        command_data['command_id'] = command_id
        command_data['created_at'] = timezone.now().isoformat()
        
        # Store command in cache with timeout
        cache_key = f"command_{command_id}"
        cache.set(cache_key, command_data, self.timeout)
        
        # Send command to microcontroller
        await self._send_to_microcontroller(command_data)
        
        return command_id
    
    async def _send_to_microcontroller(self, command_data):
        """
        Send command to appropriate microcontroller
        """
        house_id = command_data['house_id']
        component_id = command_data['component_id']
        
        # Get microcontroller group name
        microcontroller_group = await sync_to_async(self._get_microcontroller_group)(house_id, component_id)
        
        if microcontroller_group:
            await self.channel_layer.group_send(
                microcontroller_group,
                {
                    'type': 'device_command',
                    'command': command_data
                }
            )
    
    def _get_microcontroller_group(self, house_id, component_id):
        """
        Get the microcontroller group for a component
        """
        try:
            component = Component.objects.select_related(
                'microcontroller'
            ).get(
                id=component_id, 
                house_id=house_id,
                microcontroller__is_approved=True
            )
            return f"microcontroller_{component.microcontroller.id}"
        except Component.DoesNotExist:
            return None
    
    async def handle_microcontroller_ack(self, ack_data):
        """
        Handle acknowledgment from microcontroller
        """
        command_id = ack_data.get('command_id')
        cache_key = f"command_{command_id}"
        
        # Get buffered command
        command_data = cache.get(cache_key)
        
        if command_data:
            # Remove from cache
            cache.delete(cache_key)
            
            # Log the activity
            await self._log_activity(command_data, ack_data)
            
            # Notify mobile app
            await self._notify_mobile_app(command_data, ack_data)
            
            return True
        return False
    
    async def _log_activity(self, command_data, ack_data):
        """
        Log the activity after successful ACK
        """
        await sync_to_async(self._create_activity_log)(command_data, ack_data)
    
    def _create_activity_log(self, command_data, ack_data):
        """
        Create activity log entry
        """
        try:
            ActivityLog.objects.create(
                user_id=command_data.get('user_id'),
                house_id=command_data['house_id'],
                component_id=command_data['component_id'],
                action_type_id=command_data['action_type_id'],
                action_name=command_data.get('action_name', 'device_command'),
                action_parameters=command_data.get('parameters', {}),
                action_result=ack_data.get('result', {}),
                log_level='info',
                is_automated=False
            )
        except Exception as e:
            print(f"Error creating activity log: {e}")
    
    async def _notify_mobile_app(self, command_data, ack_data):
        """
        Notify mobile app about command completion
        """
        house_id = command_data['house_id']
        
        await self.channel_layer.group_send(
            f"house_{house_id}",
            {
                'type': 'device_status_update',
                'component_id': command_data['component_id'],
                'status': ack_data.get('status', 'completed'),
                'result': ack_data.get('result', {}),
                'timestamp': timezone.now().isoformat()
            }
        )

command_service = CommandBufferService()