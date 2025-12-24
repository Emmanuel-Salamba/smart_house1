# ADD THIS IMPORT AT THE TOP
from activities.services.activity_logger import ActivityLogger
import time  # ADD THIS IMPORT
from django.utils import timezone  # ADD THIS IMPORT

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from .models import Component, ComponentType, Microcontroller, ActionType
from .serializers import (
    ComponentSerializer, ComponentTypeSerializer,
    MicrocontrollerSerializer, ActionTypeSerializer
)


class ComponentViewSet(viewsets.ModelViewSet):
    queryset = Component.objects.all()
    serializer_class = ComponentSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['house', 'component_type', 'status']

    def get_queryset(self):
        # Only show components from houses the user has access to
        user_houses = self.request.user.house_memberships.values_list('house_id', flat=True)
        return Component.objects.filter(house_id__in=user_houses)

    @action(detail=True, methods=['post'])
    def control(self, request, pk=None):
        """
        Control a device component
        """
        # Start timing for execution time
        start_time = time.time()

        try:
            # Get the component
            component = self.get_object()
            action_type_id = request.data.get('action_type_id')
            parameters = request.data.get('parameters', {})

            # Get the action type if provided
            action_type = None
            if action_type_id:
                try:
                    action_type = ActionType.objects.get(id=action_type_id)
                except ActionType.DoesNotExist:
                    pass

            # Get current state before change
            previous_state = component.current_state

            # ====== ADD ACTIVITY LOG HERE ======
            # Log BEFORE sending to WebSocket
            ActivityLogger.log_device_control(
                user=request.user,
                house=component.house,
                component=component,
                action_type=action_type,
                parameters=parameters,
                result={  # Initial result showing command sent
                    'success': True,
                    'message': 'Command sent to WebSocket',
                    'status': 'pending',
                    'device_status': component.status,
                },
                previous_state=previous_state,
                source='api',  # or 'mobile_app' if you can detect
                request_id=request.META.get('HTTP_X_REQUEST_ID', ''),
                ip_address=self.get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                execution_time=time.time() - start_time
            )
            # ====== END ACTIVITY LOG ======

            # This endpoint would trigger the WebSocket flow
            # In practice, you might want to use WebSockets directly for real-time control
            # This endpoint could be used for queued commands or non-real-time operations

            return Response({
                'status': 'command_received',
                'message': 'Use WebSocket connection for real-time control',
                'component_id': str(component.id),
                'house_id': str(component.house.id),
                'log_created': True  # Tell client that activity was logged
            })

        except Exception as e:
            # ====== LOG ERROR ======
            ActivityLogger.log_device_control(
                user=request.user,
                house=None,  # We don't know house if component fetch failed
                component=None,
                action_type=None,
                parameters=request.data,
                result={
                    'success': False,
                    'error_message': str(e),
                    'error_code': 'CONTROL_ERROR'
                },
                source='api',
                ip_address=self.get_client_ip(request),
                log_level='error'
            )
            # ====== END ERROR LOG ======

            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

    # ADD THIS HELPER METHOD
    def get_client_ip(self, request):
        """
        Get client IP address
        """
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class MicrocontrollerViewSet(viewsets.ModelViewSet):
    queryset = Microcontroller.objects.all()
    serializer_class = MicrocontrollerSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Only show microcontrollers from houses the user has access to
        user_houses = self.request.user.house_memberships.values_list('house_id', flat=True)
        return Microcontroller.objects.filter(house_id__in=user_houses)

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """
        Approve a microcontroller
        """
        microcontroller = self.get_object()
        microcontroller.is_approved = True
        microcontroller.save()

        # Log the approval
        ActivityLogger.log_microcontroller_activity(
            microcontroller=microcontroller,
            action='approved',
            data={'approved_by': str(request.user.id)},
            result={'success': True},
            source='admin',
            ip_address=self.get_client_ip(request)
        )

        return Response({
            'status': 'approved',
            'message': f'Microcontroller {microcontroller.name} has been approved'
        })

    def get_client_ip(self, request):
        """
        Get client IP address
        """
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class ActionTypeViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ActionType.objects.all()
    serializer_class = ActionTypeSerializer
    permission_classes = [IsAuthenticated]