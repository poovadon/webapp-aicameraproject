# serializers.py
from rest_framework import serializers
from .models import Camera, EdgeDevices, Checkpoint, AggregationDetections

class CameraSerializer(serializers.ModelSerializer):
    class Meta:
        model = Camera
        fields = '__all__'

class EdgeDevicesSerializer(serializers.ModelSerializer):
    class Meta:
        model = EdgeDevices
        fields = '__all__'

class CheckpointSerializer(serializers.ModelSerializer):
    class Meta:
        model = Checkpoint
        fields = '__all__'

class AggregationDetectionsSerializer(serializers.ModelSerializer):
    class Meta:
        model = AggregationDetections
        fields = '__all__'
        