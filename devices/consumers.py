import json
import uuid
import time
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone
from django.core.cache import cache
from smart_house1.devices.command_service import command_service
from .models import Component
from houses.models import HouseUser
from activities.services.activity_logger import ActivityLogger
from activities.services.activity_logger import ActivityLogger

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

            # Log connection activity
            await self._log_connection_activity('connected')

            await self.accept()
        else:
            # Log unauthorized connection attempt
            await self._log_security_event('unauthorized_connection_attempt')
            await self.close()

    async def disconnect(self, close_code):
        # Leave house group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

        # Log disconnection activity
        if close_code != 1000:  # Normal closure code is 1000
            await self._log_connection_activity('disconnected_abnormally', close_code)
        else:
            await self._log_connection_activity('disconnected')

    async def receive(self, text_data):
        """
        Receive command from mobile app
        """
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            request_timestamp = timezone.now()

            if message_type == 'device_command':
                await self._handle_device_command(data, request_timestamp)
            elif message_type == 'ping':
                await self.send(text_data=json.dumps({
                    'type': 'pong',
                    'timestamp': data.get('timestamp'),
                    'server_time': timezone.now().isoformat()
                }))
            elif message_type == 'status_request':
                await self._handle_status_request(data)
            else:
                await self.send(text_data=json.dumps({
                    'type': 'error',
                    'message': f'Unknown message type: {message_type}'
                }))

        except json.JSONDecodeError as e:
            # Log JSON parsing error
            await self._log_error_activity('json_decode_error', str(e))
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Invalid JSON format'
            }))

    async def _handle_device_command(self, data, request_timestamp):
        """
        Handle device control command from mobile app
        """
        command_start_time = time.time()
        command_id = str(uuid.uuid4())

        try:
            # Get component and validate
            component = await self._get_component(data['component_id'])
            if not component:
                await self.send(text_data=json.dumps({
                    'type': 'error',
                    'message': 'Component not found'
                }))
                return

            # Get action type
            action_type = await self._get_action_type(data.get('action_type_id'))

            # Prepare command data
            command_data = {
                'command_id': command_id,
                'house_id': self.house_id,
                'component_id': data['component_id'],
                'action_type_id': data['action_type_id'],
                'action_name': data.get('action_name', 'device_control'),
                'parameters': data.get('parameters', {}),
                'user_id': str(self.user.id),
                'user_email': self.user.email,
                'request_timestamp': request_timestamp.isoformat(),
                'source': 'mobile_app',
                'session_id': self.scope.get('session', {}).get('session_key', ''),
            }

            # ===== LOG COMMAND INITIATION =====
            await database_sync_to_async(ActivityLogger.log_device_control)(
                user=self.user,
                house=component.house,
                component=component,
                action_type=action_type,
                parameters=data.get('parameters', {}),
                result={
                    'success': True,
                    'status': 'command_initiated',
                    'command_id': command_id,
                    'message': 'Command received from mobile app',
                    'device_status_before': component.status,
                    'current_state_before': component.current_state,
                },
                previous_state=component.current_state,
                source='mobile_app',
                request_id=command_id,
                ip_address=self._get_client_ip(),
                user_agent=self.scope.get('headers', {}).get(b'user-agent', b'').decode('utf-8', 'ignore'),
                execution_time=time.time() - command_start_time,
                log_level='info'
            )
            # ===== END LOG =====

            # Buffer command and wait for ACK
            buffered_command_id = await command_service.buffer_command(command_data)

            # Send immediate response with command ID
            await self.send(text_data=json.dumps({
                'type': 'command_ack',
                'command_id': buffered_command_id,
                'status': 'pending',
                'message': 'Command sent to device',
                'timestamp': timezone.now().isoformat()
            }))

        except Exception as e:
            # ===== LOG COMMAND ERROR =====
            await database_sync_to_async(ActivityLogger.log_device_control)(
                user=self.user,
                house=None,
                component=None,
                action_type=None,
                parameters=data.get('parameters', {}),
                result={
                    'success': False,
                    'status': 'error',
                    'error_message': str(e),
                    'error_type': type(e).__name__,
                },
                source='mobile_app',
                ip_address=self._get_client_ip(),
                execution_time=time.time() - command_start_time,
                log_level='error'
            )
            # ===== END LOG =====

            await self.send(text_data=json.dumps({
                'type': 'error',
                'command_id': command_id,
                'message': f'Failed to process command: {str(e)}'
            }))

    async def _handle_status_request(self, data):
        """
        Handle status request from mobile app
        """
        try:
            component_id = data.get('component_id')
            if component_id:
                component = await self._get_component(component_id)
                if component:
                    # Log status request
                    await database_sync_to_async(ActivityLogger.log_device_control)(
                        user=self.user,
                        house=component.house,
                        component=component,
                        action_type=None,
                        parameters={},
                        result={
                            'success': True,
                            'status': 'status_requested',
                            'current_state': component.current_state,
                            'device_status': component.status,
                            'last_seen': component.last_seen.isoformat() if component.last_seen else None,
                        },
                        source='mobile_app',
                        log_level='info'
                    )

                    await self.send(text_data=json.dumps({
                        'type': 'status_response',
                        'component_id': component_id,
                        'status': component.status,
                        'current_state': component.current_state,
                        'last_seen': component.last_seen.isoformat() if component.last_seen else None,
                        'timestamp': timezone.now().isoformat()
                    }))

        except Exception as e:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': f'Failed to get status: {str(e)}'
            }))

    async def device_status_update(self, event):
        """
        Send device status updates to mobile app
        """
        update_data = {
            'type': 'device_status_update',
            'component_id': event['component_id'],
            'status': event['status'],
            'result': event['result'],
            'timestamp': event['timestamp'],
            'source': event.get('source', 'microcontroller'),
            'microcontroller_id': event.get('microcontroller_id'),
        }

        # ===== LOG STATUS UPDATE TO MOBILE =====
        try:
            component = await self._get_component(event['component_id'])
            if component:
                await database_sync_to_async(ActivityLogger.log_device_control)(
                    user=self.user,
                    house=component.house,
                    component=component,
                    action_type=None,
                    parameters={},
                    result={
                        'success': True,
                        'status': 'status_update_sent',
                        'update_data': update_data,
                        'source': event.get('source', 'microcontroller'),
                    },
                    source='websocket_bridge',
                    log_level='info'
                )
        except Exception as e:
            print(f"Failed to log status update: {e}")
        # ===== END LOG =====

        await self.send(text_data=json.dumps(update_data))

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

    @database_sync_to_async
    def _get_component(self, component_id):
        """Get component by ID"""
        try:
            return Component.objects.get(id=component_id, house_id=self.house_id)
        except Component.DoesNotExist:
            return None

    @database_sync_to_async
    def _get_action_type(self, action_type_id):
        """Get action type by ID"""
        from .models import ActionType
        try:
            return ActionType.objects.get(id=action_type_id)
        except ActionType.DoesNotExist:
            return None

    @database_sync_to_async
    def _log_connection_activity(self, action, close_code=None):
        """Log connection activities"""
        try:
            house = None
            if self.house_id:
                from houses.models import House
                house = House.objects.filter(id=self.house_id).first()

            ActivityLogger.log_user_authentication(
                user=self.user,
                house=house,
                action=f'websocket_{action}',
                result={
                    'success': True,
                    'house_id': self.house_id,
                    'close_code': close_code,
                    'connection_duration': None,  # Would need to track start time
                },
                source='websocket',
                ip_address=self._get_client_ip(),
                user_agent=self.scope.get('headers', {}).get(b'user-agent', b'').decode('utf-8', 'ignore'),
                log_level='info' if action == 'connected' or action == 'disconnected' else 'warning'
            )
        except Exception as e:
            print(f"Failed to log connection activity: {e}")

    @database_sync_to_async
    def _log_security_event(self, event_type):
        """Log security events"""
        try:
            ActivityLogger.log_security_event(
                user=self.user,
                house=None,
                event_type=event_type,
                details={
                    'house_id': self.house_id,
                    'user_id': str(self.user.id) if self.user else None,
                    'ip_address': self._get_client_ip(),
                },
                source='websocket',
                ip_address=self._get_client_ip(),
                severity='medium',
                log_level='security'
            )
        except Exception as e:
            print(f"Failed to log security event: {e}")

    @database_sync_to_async
    def _log_error_activity(self, error_type, error_message):
        """Log error activities"""
        try:
            ActivityLogger.log_device_control(
                user=self.user,
                house=None,
                component=None,
                action_type=None,
                parameters={},
                result={
                    'success': False,
                    'error_type': error_type,
                    'error_message': error_message,
                },
                source='websocket',
                ip_address=self._get_client_ip(),
                log_level='error'
            )
        except Exception as e:
            print(f"Failed to log error activity: {e}")

    def _get_client_ip(self):
        """Get client IP address from scope"""
        client = self.scope.get('client')
        if client:
            return client[0]
        return 'unknown'


class MicrocontrollerConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.microcontroller_id = self.scope['url_route']['kwargs']['microcontroller_id']
        self.api_key = self.scope['url_route']['kwargs']['api_key']
        self.room_group_name = f'microcontroller_{self.microcontroller_id}'
        self.connection_time = timezone.now()

        # Authenticate microcontroller
        if await self._authenticate_microcontroller():
            # Join microcontroller group
            await self.channel_layer.group_add(
                self.room_group_name,
                self.channel_name
            )

            # Update microcontroller status
            await self._update_microcontroller_status('online')

            # ===== LOG MICROCONTROLLER CONNECTION =====
            await database_sync_to_async(ActivityLogger.log_microcontroller_activity)(
                microcontroller=self.microcontroller,
                action='connected',
                data={'api_key_used': 'valid'},
                result={
                    'success': True,
                    'connection_time': self.connection_time.isoformat(),
                    'ip_address': self._get_client_ip(),
                },
                ip_address=self._get_client_ip(),
                log_level='info'
            )
            # ===== END LOG =====

            await self.accept()
        else:
            # ===== LOG FAILED CONNECTION ATTEMPT =====
            await database_sync_to_async(ActivityLogger.log_security_event)(
                user=None,
                house=None,
                event_type='unauthorized_microcontroller_connection',
                details={
                    'microcontroller_id': self.microcontroller_id,
                    'api_key_used': self.api_key[:10] + '...' if self.api_key else 'none',
                    'ip_address': self._get_client_ip(),
                },
                source='microcontroller',
                ip_address=self._get_client_ip(),
                severity='high',
                log_level='security'
            )
            # ===== END LOG =====

            await self.close()

    async def disconnect(self, close_code):
        # Leave microcontroller group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

        # Calculate connection duration
        connection_duration = (timezone.now() - self.connection_time).total_seconds()

        # Update microcontroller status
        await self._update_microcontroller_status('offline')

        # ===== LOG DISCONNECTION =====
        await database_sync_to_async(ActivityLogger.log_microcontroller_activity)(
            microcontroller=self.microcontroller,
            action='disconnected',
            data={'close_code': close_code},
            result={
                'success': True,
                'connection_duration': connection_duration,
                'close_code': close_code,
            },
            ip_address=self._get_client_ip(),
            log_level='info' if close_code == 1000 else 'warning'
        )
        # ===== END LOG =====

    async def receive(self, text_data):
        """
        Receive messages from microcontroller
        """
        receive_time = timezone.now()

        try:
            data = json.loads(text_data)
            message_type = data.get('type')

            if message_type == 'command_ack':
                await self._handle_command_ack(data, receive_time)
            elif message_type == 'device_status_update':
                await self._handle_device_status_update(data, receive_time)
            elif message_type == 'heartbeat':
                await self._handle_heartbeat(data, receive_time)
            elif message_type == 'error':
                await self._handle_error(data, receive_time)
            else:
                # Log unknown message type
                await database_sync_to_async(ActivityLogger.log_microcontroller_activity)(
                    microcontroller=self.microcontroller,
                    action='unknown_message',
                    data=data,
                    result={
                        'success': False,
                        'error_message': f'Unknown message type: {message_type}',
                    },
                    ip_address=self._get_client_ip(),
                    log_level='warning'
                )

                await self.send(text_data=json.dumps({
                    'type': 'error',
                    'message': f'Unknown message type: {message_type}'
                }))

        except json.JSONDecodeError as e:
            # ===== LOG JSON PARSE ERROR =====
            await database_sync_to_async(ActivityLogger.log_microcontroller_activity)(
                microcontroller=self.microcontroller,
                action='json_decode_error',
                data={'raw_data': text_data[:100]},  # First 100 chars
                result={
                    'success': False,
                    'error_message': str(e),
                },
                ip_address=self._get_client_ip(),
                log_level='error'
            )
            # ===== END LOG =====

            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Invalid JSON format'
            }))

    async def device_command(self, event):
        """
        Send command to microcontroller
        """
        command_start_time = time.time()

        try:
            command_data = event['command']

            # ===== LOG COMMAND SENT TO MICROCONTROLLER =====
            await database_sync_to_async(ActivityLogger.log_microcontroller_activity)(
                microcontroller=self.microcontroller,
                action='command_sent',
                data={
                    'command_id': command_data.get('command_id'),
                    'component_id': command_data.get('component_id'),
                    'action_name': command_data.get('action_name'),
                },
                result={
                    'success': True,
                    'status': 'sent_to_hardware',
                    'command_id': command_data.get('command_id'),
                },
                ip_address=self._get_client_ip(),
                log_level='info'
            )
            # ===== END LOG =====

            await self.send(text_data=json.dumps({
                'type': 'device_command',
                'command': command_data,
                'server_timestamp': timezone.now().isoformat()
            }))

        except Exception as e:
            # ===== LOG COMMAND SEND ERROR =====
            await database_sync_to_async(ActivityLogger.log_microcontroller_activity)(
                microcontroller=self.microcontroller,
                action='command_send_error',
                data=event,
                result={
                    'success': False,
                    'error_message': str(e),
                    'error_type': type(e).__name__,
                },
                ip_address=self._get_client_ip(),
                log_level='error'
            )
            # ===== END LOG =====

    async def _handle_command_ack(self, data, receive_time):
        """
        Handle command acknowledgment from microcontroller
        """
        ack_start_time = time.time()
        command_id = data.get('command_id')

        try:
            # Get buffered command
            cache_key = f"command_{command_id}"
            command_data = cache.get(cache_key)

            if command_data:
                # Remove from cache
                cache.delete(cache_key)

                # Get component for logging
                component = await self._get_component(command_data['component_id'])

                # ===== LOG SUCCESSFUL COMMAND EXECUTION =====
                await database_sync_to_async(ActivityLogger.log_device_control)(
                    user_id=command_data