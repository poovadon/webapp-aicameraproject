from email.mime import image
from django.db import models

class Camera(models.Model):
    id = models.AutoField(primary_key=True)
    license_plate = models.CharField(max_length=255)
    checkpoint_id = models.IntegerField()
    timestamp = models.DateTimeField()
    vehicle_type = models.CharField(max_length=255)
    vehicle_color = models.CharField(max_length=255)
    latitude = models.FloatField()
    longitude = models.FloatField()

    class Meta:
        db_table = 'vehicle_lpr_simulation_data'
    
class EdgeDevices(models.Model):
    id = models.AutoField(primary_key=True)
    last_heartbeat = models.DateTimeField(null=True, blank=True)
    device_id = models.CharField(max_length=255, unique=True)
    location_id = models.IntegerField(null=True, blank=True)
    status = models.CharField(max_length=255, null=True, blank=True)
    ip_address = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        db_table = 'edge_devices'

class Checkpoint(models.Model):
    id = models.AutoField(primary_key=True)
    checkpoint_id = models.IntegerField(unique=True)
    location_name = models.CharField(max_length=255)
    gps_latitude = models.FloatField()
    gps_longitude = models.FloatField()

    class Meta:
        db_table = 'checkpoint'

class AggregationDetections(models.Model):
    id = models.AutoField(primary_key=True)
    date = models.DateTimeField()
    aggregation_id = models.IntegerField(unique=True)
    total_detections = models.IntegerField()
    intersection_id = models.IntegerField()
    device_id = models.CharField(max_length=255)

    class Meta:
        db_table = 'aggregation_detections'
        
        