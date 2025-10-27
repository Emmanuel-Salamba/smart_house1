from rest_framework import serializers
from .models import Component, ComponentState, ActionType

class ComponentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Component
        fields = '__all__'

class ComponentStateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ComponentState
        fields = '__all__'

class ActionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ActionType
        fields = '__all__'