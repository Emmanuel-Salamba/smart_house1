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
        component = self.get_object()
        action_type_id = request.data.get('action_type_id')
        parameters = request.data.get('parameters', {})
        
        # This endpoint would trigger the WebSocket flow
        # In practice, you might want to use WebSockets directly for real-time control
        # This endpoint could be used for queued commands or non-real-time operations
        
        return Response({
            'status': 'command_received',
            'message': 'Use WebSocket connection for real-time control',
            'component_id': str(component.id),
            'house_id': str(component.house.id)
        })

class MicrocontrollerViewSet(viewsets.ModelViewSet):
    queryset = Microcontroller.objects.all()
    serializer_class = MicrocontrollerSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user_houses = self.request.user.house_memberships.values_list('house_id', flat=True)
        return Microcontroller.objects.filter(house_id__in=user_houses)

class ActionTypeViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ActionType.objects.all()
    serializer_class = ActionTypeSerializer
    permission_classes = [IsAuthenticated]