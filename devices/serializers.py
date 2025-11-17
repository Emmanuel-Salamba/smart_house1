from rest_framework import serializers
from .models import Component, ComponentType, Microcontroller, ActionType

class ComponentTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ComponentType
        fields = '__all__'

class MicrocontrollerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Microcontroller
        fields = '__all__'
        read_only_fields = ['api_key', 'last_heartbeat']

class ActionTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ActionType
        fields = '__all__'

class ComponentSerializer(serializers.ModelSerializer):
    component_type_name = serializers.CharField(source='component_type.name', read_only=True)
    house_name = serializers.CharField(source='house.name', read_only=True)
    microcontroller_name = serializers.CharField(source='microcontroller.name', read_only=True)
    
    class Meta:
        model = Component
        fields = '__all__'
        read_only_fields = ['device_id', 'last_seen', 'current_state']


        