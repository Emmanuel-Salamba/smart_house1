import json
import uuid
import time
import traceback
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone
from django.core.cache import cache

User = get_user_model()


class MobileAppConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.house_id = self.scope['url_route']['kwargs']['house_id']
        self.user = self.scope['user']
        self.room_group_name = f'house_{self.house_id}'

        if await self._has_house_access():
            await self.channel_layer.group_add(
                self.room_group_name,
                self.channel_name
            )
            await self.accept()
            print(f"✅ Mobile app connected to house {self.house_id}")
        else:
            print(f"❌ Mobile app access denied to house {self.house_id}")
            await self.close()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
        print(f"🔴 Mobile app disconnected from house {self.house_id}")

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            message_type = data.get('type')

            if message_type == 'device_command':
                await self._handle_device_command(data)
            elif message_type == 'ping':
                await self.send(text_data=json.dumps({
                    'type': 'pong',
                    'timestamp': data.get('timestamp'),
                    'server_time': timezone.now().isoformat()
                }))
            else:
                await self.send(text_data=json.dumps({
                    'type': 'error',
                    'message': f'Unknown message type: {message_type}'
                }))
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Invalid JSON format'
            }))

    async def _handle_device_command(self, data):
        command_id = str(uuid.uuid4())
        try:
            component = await self._get_component(data['component_id'])
            if not component:
                await self.send(text_data=json.dumps({
                    'type': 'error',
                    'message': 'Component not found'
                }))
                return

            # Send command to microcontroller group
            await self.channel_layer.group_send(
                f'microcontroller_{component.microcontroller_id}',
                {
                    'type': 'device_command',
                    'command': {
                        'command_id': command_id,
                        'component_id': data['component_id'],
                        'action_name': data.get('action_name', 'device_control'),
                        'parameters': data.get('parameters', {}),
                        'user_id': str(self.user.id)
                    }
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
                'message': str(e)
            }))

    async def device_status_update(self, event):
        await self.send(text_data=json.dumps({
            'type': 'device_status_update',
            'component_id': event['component_id'],
            'status': event['status'],
            'result': event['result'],
            'timestamp': event['timestamp']
        }))

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


class MicrocontrollerConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.microcontroller_id = self.scope['url_route']['kwargs']['microcontroller_id']
        self.api_key = self.scope['url_route']['kwargs']['api_key']
        self.room_group_name = f'microcontroller_{self.microcontroller_id}'

        print(f"\n🔐 WebSocket Connection Attempt:")
        print(f"   Microcontroller ID: {self.microcontroller_id}")
        print(f"   API Key: {self.api_key}")

        try:
            # Authenticate microcontroller
            if await self._authenticate_microcontroller():
                await self.channel_layer.group_add(
                    self.room_group_name,
                    self.channel_name
                )
                await self.accept()
                print(f"✅ Microcontroller {self.microcontroller_id} CONNECTED successfully!")
                
                # Send welcome message
                await self.send(text_data=json.dumps({
                    'type': 'connection_established',
                    'message': 'Connected to Smart Home Backend',
                    'microcontroller_id': self.microcontroller_id,
                    'timestamp': timezone.now().isoformat()
                }))
            else:
                print(f"❌ Microcontroller {self.microcontroller_id} AUTHENTICATION FAILED!")
                await self.close()
        except Exception as e:
            print(f"❌ Microcontroller connect error: {e}")
            traceback.print_exc()
            await self.close()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
        print(f"🔴 Microcontroller {self.microcontroller_id} DISCONNECTED")

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
            else:
                print(f"   Unknown message type: {message_type}")
                
        except json.JSONDecodeError as e:
            print(f"   JSON parse error: {e}")
        except Exception as e:
            print(f"   Error in receive: {e}")

    async def device_command(self, event):
        try:
            command_data = event['command']
            await self.send(text_data=json.dumps({
                'type': 'device_command',
                'command': command_data,
                'server_timestamp': timezone.now().isoformat()
            }))
            print(f"📤 Sent command to {self.microcontroller_id}: {command_data.get('action_name')}")
        except Exception as e:
            print(f"   Error sending command: {e}")

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
        print(f"💓 Heartbeat received from {self.microcontroller_id}")

    @database_sync_to_async
    def _authenticate_microcontroller(self):
        from devices.models import Microcontroller
        
        print(f"\n🔐 AUTHENTICATION DEBUG:")
        print(f"   Received ID: {self.microcontroller_id}")
        print(f"   Received API Key: {self.api_key}")
        
        try:
            # Try to find the microcontroller by ID first
            microcontroller = Microcontroller.objects.filter(
                id=self.microcontroller_id
            ).first()
            
            if not microcontroller:
                print(f"   ❌ Microcontroller with ID {self.microcontroller_id} NOT FOUND in database!")
                # List all microcontrollers for debugging
                all_mc = Microcontroller.objects.all()
                print(f"   Total microcontrollers in DB: {all_mc.count()}")
                for mc in all_mc:
                    print(f"      - ID: {mc.id}, Name: {mc.name}")
                return False
            
            print(f"   ✅ Found microcontroller: {microcontroller.name}")
            print(f"   Stored API Key: {microcontroller.api_key}")
            print(f"   API Keys match: {microcontroller.api_key == self.api_key}")
            print(f"   is_approved: {microcontroller.is_approved}")
            
            # Check if approved and API key matches
            if microcontroller.api_key == self.api_key and microcontroller.is_approved:
                self.microcontroller = microcontroller
                print(f"   ✅ AUTH SUCCESS for {self.microcontroller_id}!")
                return True
            else:
                if microcontroller.api_key != self.api_key:
                    print(f"   ❌ API KEY MISMATCH!")
                    print(f"      Expected: {microcontroller.api_key}")
                    print(f"      Got: {self.api_key}")
                if not microcontroller.is_approved:
                    print(f"   ❌ MICROCONTROLLER NOT APPROVED! is_approved = False")
                return False
                
        except Exception as e:
            print(f"   ❌ Authentication error: {e}")
            return False

    @database_sync_to_async
    def _update_microcontroller_heartbeat(self):
        from devices.models import Microcontroller
        try:
            Microcontroller.objects.filter(id=self.microcontroller_id).update(
                last_heartbeat=timezone.now()
            )
        except Exception as e:
            print(f"   Heartbeat update error: {e}")

    @database_sync_to_async
    def _update_component_state(self, component_id, state):
        from devices.models import Component
        try:
            Component.objects.filter(id=component_id).update(
                current_state={'power': 'on' if state else 'off'},
                last_seen=timezone.now()
            )
        except Exception as e:
            print(f"   Component update error: {e}")

    def _get_client_ip(self):
        client = self.scope.get('client')
        return client[0] if client else 'unknown'