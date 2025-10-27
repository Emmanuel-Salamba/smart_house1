import json
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async
from .models import Component, ActivityLog


class DeviceControlConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.device_id = self.scope['url_route']['kwargs']['device_id']
        self.room_group_name = f'device_{self.device_id}'

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

        # Update component status to online
        await self.update_component_status(True)

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

        # Update component status to offline
        await self.update_component_status(False)

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message_type = text_data_json['type']

        if message_type == 'status_update':
            # Handle status updates from ESP32
            await self.handle_status_update(text_data_json)
        elif message_type == 'command_response':
            # Handle command responses from ESP32
            await self.handle_command_response(text_data_json)

    async def device_command(self, event):
        # Send command to ESP32
        command = event['command']
        await self.send(text_data=json.dumps({
            'type': 'command',
            'command': command
        }))

    @sync_to_async
    def update_component_status(self, is_online):
        try:
            component = Component.objects.get(device_identifier=self.device_id)
            component.status = 'online' if is_online else 'offline'
            component.save()
        except Component.DoesNotExist:
            pass

    @sync_to_async
    def handle_status_update(self, data):
        try:
            component = Component.objects.get(device_identifier=self.device_id)
            # Update component state here
            pass
        except Component.DoesNotExist:
            pass