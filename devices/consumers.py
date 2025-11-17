import json
import uuid
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist
from .command_service import command_service
from .models import Microcontroller, Component
from houses.models import HouseUser

User = get_user_model()

class MobileAppConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.house_id = self.scope['url_route']['kwargs']['house_id']
        self.user = self.scope['user']
        self.room_group_name = f'house_{self.house_id}'
        
        # Check if user has access to this house
        if await self._has_house_access():
            # Join house group
            await self.channel_layer.group_add(
                self.room_group_name,
                self.channel_name
            )
            await self.accept()
        else:
            await self.close()
    
    async def disconnect(self, close_code):
        # Leave house group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
    
    async def receive(self, text_data):
        """
        Receive command from mobile app
        """
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            if message_type == 'device_command':
                await self._handle_device_command(data)
            elif message_type == 'ping':
                await self.send(text_data=json.dumps({
                    'type': 'pong',
                    'timestamp': data.get('timestamp')
                }))
                
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Invalid JSON'
            }))
    
    async def _handle_device_command(self, data):
        """
        Handle device control command from mobile app
        """
        command_data = {
            'house_id': self.house_id,
            'component_id': data['component_id'],
            'action_type_id': data['action_type_id'],
            'action_name': data.get('action_name'),
            'parameters': data.get('parameters', {}),
            'user_id': str(self.user.id)
        }
        
        # Buffer command and wait for ACK
        command_id = await command_service.buffer_command(command_data)
        
        # Send immediate response with command ID
        await self.send(text_data=json.dumps({
            'type': 'command_ack',
            'command_id': command_id,
            'status': 'pending',
            'message': 'Command sent to device'
        }))
    
    async def device_status_update(self, event):
        """
        Send device status updates to mobile app
        """
        await self.send(text_data=json.dumps({
            'type': 'device_status_update',
            'component_id': event['component_id'],
            'status': event['status'],
            'result': event['result'],
            'timestamp': event['timestamp']
        }))
    
    @database_sync_to_async
    def _has_house_access(self):
        """Check if user has access to this house"""
        try:
            return HouseUser.objects.filter(
                user=self.user,
                house_id=self.house_id,
                can_control_devices=True
            ).exists()
        except Exception:
            return False

class MicrocontrollerConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.microcontroller_id = self.scope['url_route']['kwargs']['microcontroller_id']
        self.api_key = self.scope['url_route']['kwargs']['api_key']
        self.room_group_name = f'microcontroller_{self.microcontroller_id}'
        
        # Authenticate microcontroller
        if await self._authenticate_microcontroller():
            # Join microcontroller group
            await self.channel_layer.group_add(
                self.room_group_name,
                self.channel_name
            )
            await self.accept()
            
            # Update microcontroller status
            await self._update_microcontroller_status('online')
        else:
            await self.close()
    
    async def disconnect(self, close_code):
        # Leave microcontroller group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
        
        # Update microcontroller status
        await self._update_microcontroller_status('offline')
    
    async def receive(self, text_data):
        """
        Receive messages from microcontroller
        """
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            if message_type == 'command_ack':
                await self._handle_command_ack(data)
            elif message_type == 'device_status_update':
                await self._handle_device_status_update(data)
            elif message_type == 'heartbeat':
                await self._handle_heartbeat(data)
                
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Invalid JSON'
            }))
    
    async def device_command(self, event):
        """
        Send command to microcontroller
        """
        await self.send(text_data=json.dumps({
            'type': 'device_command',
            'command': event['command']
        }))
    
    async def _handle_command_ack(self, data):
        """
        Handle command acknowledgment from microcontroller
        """
        ack_data = {
            'command_id': data['command_id'],
            'status': data.get('status', 'success'),
            'result': data.get('result', {}),
            'microcontroller_id': self.microcontroller_id
        }
        
        # Process ACK through command service
        await command_service.handle_microcontroller_ack(ack_data)
    
    async def _handle_device_status_update(self, data):
        """
        Handle device status updates from physical switches
        """
        # Log the physical action
        await self._log_physical_action(data)
        
        # Notify all mobile apps in the house
        house_id = await self._get_house_id()
        if house_id:
            await self.channel_layer.group_send(
                f"house_{house_id}",
                {
                    'type': 'device_status_update',
                    'component_id': data['component_id'],
                    'status': 'updated',
                    'result': data.get('state', {}),
                    'timestamp': data.get('timestamp')
                }
            )
    
    async def _handle_heartbeat(self, data):
        """
        Handle microcontroller heartbeat
        """
        await self._update_microcontroller_heartbeat()
    
    @database_sync_to_async
    def _authenticate_microcontroller(self):
        """Authenticate microcontroller using API key"""
        try:
            microcontroller = Microcontroller.objects.get(
                id=self.microcontroller_id,
                api_key=self.api_key,
                is_approved=True
            )
            self.microcontroller = microcontroller
            return True
        except ObjectDoesNotExist:
            return False
    
    @database_sync_to_async
    def _update_microcontroller_status(self, status):
        """Update microcontroller status"""
        try:
            microcontroller = Microcontroller.objects.get(id=self.microcontroller_id)
            microcontroller.status = status
            if status == 'online':
                microcontroller.last_heartbeat = timezone.now()
            microcontroller.save()
        except ObjectDoesNotExist:
            pass
    
    @database_sync_to_async
    def _update_microcontroller_heartbeat(self):
        """Update microcontroller heartbeat timestamp"""
        try:
            microcontroller = Microcontroller.objects.get(id=self.microcontroller_id)
            microcontroller.last_heartbeat = timezone.now()
            microcontroller.save()
        except ObjectDoesNotExist:
            pass
    
    @database_sync_to_async
    def _get_house_id(self):
        """Get house ID for this microcontroller"""
        try:
            microcontroller = Microcontroller.objects.get(id=self.microcontroller_id)
            return str(microcontroller.house.id)
        except ObjectDoesNotExist:
            return None
    
    @database_sync_to_async
    def _log_physical_action(self, data):
        """Log physical device action"""
        from activities.models import ActivityLog
        
        try:
            component = Component.objects.get(id=data['component_id'])
            ActivityLog.objects.create(
                house=component.house,
                component=component,
                action_name='physical_control',
                action_parameters=data.get('parameters', {}),
                action_result=data.get('state', {}),
                log_level='info',
                is_automated=True,
                automation_source='physical_switch'
            )
        except ObjectDoesNotExist:
            pass