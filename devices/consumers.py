import json
import uuid
import time
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone
from django.core.cache import cache

# DO NOT import models at the top - import inside methods instead

User = get_user_model()


class MobileAppConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.house_id = self.scope['url_route']['kwargs']['house_id']
        self.user = self.scope['user']
        self.room_group_name = f'house_{self.house_id}'

        # Check if user has access to this house
        if await self._has_house_access():
            await self.channel_layer.group_add(
                self.room_group_name,
                self.channel_name
            )
            await self._log_connection_activity('connected')
            await self.accept()
        else:
            await self._log_security_event('unauthorized_connection_attempt')
            await self.close()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
        if close_code != 1000:
            await self._log_connection_activity('disconnected_abnormally', close_code)
        else:
            await self._log_connection_activity('disconnected')

    async def receive(self, text_data):
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
            await self._log_error_activity('json_decode_error', str(e))
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Invalid JSON format'
            }))

    async def _handle_device_command(self, data, request_timestamp):
        command_start_time = time.time()
        command_id = str(uuid.uuid4())

        try:
            component = await self._get_component(data['component_id'])
            if not component:
                await self.send(text_data=json.dumps({
                    'type': 'error',
                    'message': 'Component not found'
                }))
                return

            action_type = await self._get_action_type(data.get('action_type_id'))

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

            # Send to microcontroller group
            await self.channel_layer.group_send(
                f'microcontroller_{component.microcontroller_id}',
                {
                    'type': 'device_command',
                    'command': command_data
                }
            )

            await self.send(text_data=json.dumps({
                'type': 'command_ack',
                'command_id': command_id,
                'status': 'pending',
                'message': 'Command sent to device',
                'timestamp': timezone.now().isoformat()
            }))

        except Exception as e:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'command_id': command_id,
                'message': f'Failed to process command: {str(e)}'
            }))

    async def _handle_status_request(self, data):
        try:
            component_id = data.get('component_id')
            if component_id:
                component = await self._get_component(component_id)
                if component:
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
        update_data = {
            'type': 'device_status_update',
            'component_id': event['component_id'],
            'status': event['status'],
            'result': event['result'],
            'timestamp': event['timestamp'],
            'source': event.get('source', 'microcontroller'),
            'microcontroller_id': event.get('microcontroller_id'),
        }
        await self.send(text_data=json.dumps(update_data))

    @database_sync_to_async
    def _has_house_access(self):
        from houses.models import HouseUser
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
        from devices.models import Component
        try:
            return Component.objects.get(id=component_id, house_id=self.house_id)
        except Component.DoesNotExist:
            return None

    @database_sync_to_async
    def _get_action_type(self, action_type_id):
        from devices.models import ActionType
        try:
            return ActionType.objects.get(id=action_type_id)
        except ActionType.DoesNotExist:
            return None

    @database_sync_to_async
    def _log_connection_activity(self, action, close_code=None):
        try:
            from activities.services.activity_logger import ActivityLogger
            from houses.models import House
            house = None
            if self.house_id:
                house = House.objects.filter(id=self.house_id).first()

            ActivityLogger.log_user_authentication(
                user=self.user,
                house=house,
                action=f'websocket_{action}',
                result={
                    'success': True,
                    'house_id': self.house_id,
                    'close_code': close_code,
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
        try:
            from activities.services.activity_logger import ActivityLogger
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
        try:
            from activities.services.activity_logger import ActivityLogger
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

        if await self._authenticate_microcontroller():
            await self.channel_layer.group_add(
                self.room_group_name,
                self.channel_name
            )
            await self._update_microcontroller_status('online')
            await self.accept()
            print(f"✅ Microcontroller {self.microcontroller_id} connected")
            
            await self.send(text_data=json.dumps({
                'type': 'connection_established',
                'message': 'Connected to Smart Home Backend',
                'microcontroller_id': self.microcontroller_id,
                'timestamp': timezone.now().isoformat()
            }))
        else:
            print(f"❌ Authentication failed for {self.microcontroller_id}")
            await self.close()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
        await self._update_microcontroller_status('offline')
        print(f"🔴 Microcontroller {self.microcontroller_id} disconnected")

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            print(f"📨 Received from {self.microcontroller_id}: {message_type}")
            
            if message_type == 'command_ack':
                await self._handle_command_ack(data)
            elif message_type == 'device_status_update':
                await self._handle_device_status_update(data)
            elif message_type == 'heartbeat':
                await self._handle_heartbeat(data)
            elif message_type == 'auth':
                await self._handle_auth(data)
        except json.JSONDecodeError as e:
            print(f"JSON parse error: {e}")
        except Exception as e:
            print(f"Error in receive: {e}")

    async def device_command(self, event):
        try:
            command_data = event['command']
            await self.send(text_data=json.dumps({
                'type': 'device_command',
                'command': command_data,
                'server_timestamp': timezone.now().isoformat()
            }))
            print(f"📤 Sent command to {self.microcontroller_id}")
        except Exception as e:
            print(f"Error sending command: {e}")

    async def _handle_auth(self, data):
        await self.send(text_data=json.dumps({
            'type': 'auth_response',
            'status': 'success',
            'message': 'Authentication successful',
            'timestamp': timezone.now().isoformat()
        }))

    async def _handle_command_ack(self, data):
        command_id = data.get('command_id')
        status = data.get('status')
        print(f"✅ Command {command_id} acknowledged: {status}")

    async def _handle_device_status_update(self, data):
        devices = data.get('devices', [])
        for device in devices:
            component_id = device.get('id')
            state = device.get('state')
            await self._update_component_state(component_id, state)
        print(f"📊 Device status update: {len(devices)} devices")

    async def _handle_heartbeat(self, data):
        await self._update_microcontroller_heartbeat()
        await self.send(text_data=json.dumps({
            'type': 'heartbeat_response',
            'status': 'ok',
            'timestamp': timezone.now().isoformat()
        }))

    @database_sync_to_async
    def _authenticate_microcontroller(self):
        from devices.models import Microcontroller
        try:
            microcontroller = Microcontroller.objects.get(
                id=self.microcontroller_id,
                api_key=self.api_key,
                is_approved=True
            )
            self.microcontroller = microcontroller
            return True
        except Microcontroller.DoesNotExist:
            return False

    @database_sync_to_async
    def _update_microcontroller_status(self, status):
        from devices.models import Microcontroller
        try:
            Microcontroller.objects.filter(id=self.microcontroller_id).update(
                status=status,
                last_seen=timezone.now()
            )
        except Exception as e:
            print(f"Status update error: {e}")

    @database_sync_to_async
    def _update_microcontroller_heartbeat(self):
        from devices.models import Microcontroller
        try:
            Microcontroller.objects.filter(id=self.microcontroller_id).update(
                last_heartbeat=timezone.now()
            )
        except Exception as e:
            print(f"Heartbeat update error: {e}")

    @database_sync_to_async
    def _update_component_state(self, component_id, state):
        from devices.models import Component
        try:
            Component.objects.filter(id=component_id).update(
                current_state={'power': 'on' if state else 'off'},
                last_seen=timezone.now()
            )
        except Exception as e:
            print(f"Component update error: {e}")

    def _get_client_ip(self):
        client = self.scope.get('client')
        return client[0] if client else 'unknown'