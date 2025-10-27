from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Component, ComponentState, ActionType
from .serializers import ComponentSerializer, ComponentStateSerializer, ActionSerializer
from activities.models import ActivityLog


class ComponentViewSet(viewsets.ModelViewSet):
    queryset = Component.objects.all()
    serializer_class = ComponentSerializer

    @action(detail=True, methods=['post'])
    def execute_action(self, request, pk=None):
        component = self.get_object()
        action_type_id = request.data.get('action_type_id')
        action_value = request.data.get('action_value')

        try:
            action_type = ActionType.objects.get(action_type_id=action_type_id)

            # Create activity log
            ActivityLog.objects.create(
                user=request.user,
                component=component,
                action_type=action_type,
                action_value=action_value,
                execution_status='pending'
            )

            # Send command to ESP32 via WebSocket
            # This will be implemented in the next step

            return Response({
                'status': 'command_sent',
                'message': f'Command sent to {component.component_name}'
            })

        except ActionType.DoesNotExist:
            return Response(
                {'error': 'Invalid action type'},
                status=status.HTTP_400_BAD_REQUEST
            )