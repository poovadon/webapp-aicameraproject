from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, Http404, HttpResponseRedirect
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from rest_framework import viewsets ,status
from rest_framework.response import Response
from rest_framework.decorators import action
from django.db.models import Max, Count, Q

from .models import Camera, EdgeDevices, Checkpoint, AggregationDetections
from .serializers import CameraSerializer, EdgeDevicesSerializer, CheckpointSerializer, AggregationDetectionsSerializer
from .forms import LicensePlateSearchForm

import json
import threading
import base64
import altair as alt
import pandas as pd
from datetime import datetime
import asyncio
import websockets
from asgiref.sync import async_to_sync
from time import sleep
import os

class EdgeDevicesViewSet(viewsets.ViewSet):
    
    def list(self, request):
        queryset = EdgeDevices.objects.all()
        
        start_datetime = request.query_params.get('start_datetime')
        end_datetime = request.query_params.get('end_datetime')
        device_id = request.query_params.get('device_id')
        status = request.query_params.get('status')
        ip_address = request.query_params.get('ip_address')
        location_id = request.query_params.get('location_id')

        # การกรองช่วงเวลา
        if start_datetime and end_datetime:
            queryset = queryset.filter(timestamp__range=[start_datetime, end_datetime])
        if device_id:
            queryset = queryset.filter(device_id=device_id)
        if status:
            queryset = queryset.filter(status=status)
        if ip_address:
            queryset = queryset.filter(ip_address=ip_address)
        if location_id:
            queryset = queryset.filter(location_id=location_id)

        serializer = EdgeDevicesSerializer(queryset, many=True)
        return Response(serializer.data)

class CheckpointViewSet(viewsets.ViewSet):
    
    def list(self, request):
        queryset = Checkpoint.objects.all()
        
        checkpoint_id = request.query_params.get('checkpoint_id')
        location_name = request.query_params.get('location_name')

        if checkpoint_id:
            queryset = queryset.filter(checkpoint_id=checkpoint_id)
        if location_name:
            queryset = queryset.filter(location_name__icontains=location_name)

        serializer = CheckpointSerializer(queryset, many=True)
        return Response(serializer.data)

class AggregationDetectionsViewSet(viewsets.ViewSet):
    
    def list(self, request):
        queryset = AggregationDetections.objects.all()
        
        aggregation_id = request.query_params.get('aggregation_id')
        start_datetime = request.query_params.get('start_datetime')
        end_datetime = request.query_params.get('end_datetime')
        device_id = request.query_params.get('device_id')

        if aggregation_id:
            queryset = queryset.filter(aggregation_id=aggregation_id)
        # การกรองช่วงเวลา
        if start_datetime and end_datetime:
            queryset = queryset.filter(timestamp__range=[start_datetime, end_datetime])
        if device_id:
            queryset = queryset.filter(device_id=device_id)

        serializer = AggregationDetectionsSerializer(queryset, many=True)
        return Response(serializer.data)

class CameraViewSet(viewsets.ViewSet):
    def list(self, request):
        # ดึงข้อมูลล่าสุดต่อ checkpoint_id
        latest_per_checkpoint = (
            Camera.objects.values('checkpoint_id')
            .annotate(latest_timestamp=Max('timestamp'))
        )

        latest_ids = Camera.objects.filter(
            Q(checkpoint_id__in=[entry['checkpoint_id'] for entry in latest_per_checkpoint]),
            Q(timestamp__in=[entry['latest_timestamp'] for entry in latest_per_checkpoint])
        ).values_list('id', flat=True)

        # เริ่มต้น queryset
        queryset = Camera.objects.filter(id__in=latest_ids)

        # รับค่าพารามิเตอร์การกรอง
        checkpoint = request.query_params.get('checkpoint')
        start_datetime = request.query_params.get('start_datetime')
        end_datetime = request.query_params.get('end_datetime')
        plate_part1 = request.query_params.get('plate_part1')
        plate_part2 = request.query_params.get('plate_part2')
        plate_part3 = request.query_params.get('plate_part3')

        # Logs for debugging
        print(f"Filters received: checkpoint={checkpoint}, start_datetime={start_datetime}, "
              f"end_datetime={end_datetime}, plate_part1={plate_part1}, "
              f"plate_part2={plate_part2}, plate_part3={plate_part3}")

        # การกรองโดย checkpoint
        if checkpoint:
            queryset = Camera.objects.all()
            queryset = queryset.filter(checkpoint_id=checkpoint)

        # การกรองช่วงเวลา
        if start_datetime and end_datetime:
            queryset = Camera.objects.all()
            queryset = queryset.filter(timestamp__range=[start_datetime, end_datetime])

        # การกรองป้ายทะเบียน
        if plate_part1 or plate_part2 or plate_part3:
            queryset = Camera.objects.all()
            license_plate_query = Q()
            if plate_part1:
                license_plate_query &= Q(license_plate__startswith=plate_part1)
            if plate_part2:
                license_plate_query &= Q(license_plate__icontains=plate_part2)
            if plate_part3:
                license_plate_query &= Q(license_plate__endswith=plate_part3)
            queryset = queryset.filter(license_plate_query)

        # สร้าง serializer และส่งผลลัพธ์กลับ
        serializer = CameraSerializer(queryset, many=True)
        return Response(serializer.data)


@login_required
def camera(request):
    return render(request, 'table/data_table.html')

@login_required
def check(request):
    return render(request, 'table/check.html')

@login_required
def detections(request):
    return render(request, 'table/detections.html')

@login_required
def camera_table(request):
    start_date_time = request.GET.get('start_datetime')
    end_date_time = request.GET.get('end_datetime')
    checkpoint_id = request.GET.get('checkpoint')
    plate_part1 = request.GET.get('plate_part1')
    plate_part2 = request.GET.get('plate_part2')
    plate_part3 = request.GET.get('plate_part3')

    # เริ่มต้นด้วย QuerySet ทั้งหมด และเลือก 50 ค่าล่าสุด
    camera_data = Camera.objects.all().order_by('-timestamp')[:50]

    # ฟิลเตอร์ข้อมูลตามที่ผู้ใช้ระบุ
    if checkpoint_id:
        camera_data = Camera.objects.filter(checkpoint_id=checkpoint_id)

    if start_date_time and end_date_time:
        start_datetime = timezone.make_aware(datetime.strptime(start_date_time, '%Y-%m-%dT%H:%M'))
        end_datetime = timezone.make_aware(datetime.strptime(end_date_time, '%Y-%m-%dT%H:%M'))
        camera_data = Camera.objects.filter(timestamp__range=(start_datetime, end_datetime))

    if plate_part1 and plate_part2 and plate_part3:
        license_plate = f"{plate_part1}-{plate_part2}-{plate_part3}"
        camera_data = Camera.objects.filter(license_plate=license_plate)

    # หา conflict ข้อมูลที่ประเภทหรือสีไม่ตรงกัน และแสดงผลทะเบียนรถด้วย
    conflicting_results = Camera.objects.values('license_plate', 'vehicle_type', 'vehicle_color') \
        .annotate(count=Count('id')) \
        .filter(count__gt=1)

    context = {
        'camera_data': camera_data,
        'conflicting_results': conflicting_results,
    }
    
    return render(request, 'table/checkpoint.html', context)

@login_required
def data_table(request):
    return render(request, 'table/checkpoint.html')

@login_required
def contact(request):
    return render(request, 'cameraapp/contact.html')

@login_required
def about(request):
    return render(request, 'cameraapp/about.html')

@login_required
def home(request):
    return render(request, 'cameraapp/home.html')

@login_required
def get_camera_data(request):
    camera_data = []

    # เช็คว่าเป็นการค้นหาหรือไม่
    if request.method == 'GET' and 'search' in request.GET:
        form = LicensePlateSearchForm(request.GET)

        if form.is_valid():
            # รับค่าจากแบบฟอร์ม
            plate_part1 = form.cleaned_data['plate_part1']
            plate_part2 = form.cleaned_data['plate_part2']
            plate_part3 = form.cleaned_data['plate_part3']
            
            # แสดงค่าที่รับมาจากฟอร์มใน console
            print("Plate Part 1:", plate_part1)
            print("Plate Part 2:", plate_part2)
            print("Plate Part 3:", plate_part3)

            # สร้างค่าทะเบียนรถ
            license_plate = f"{plate_part1}-{plate_part2}-{plate_part3}"

            # ค้นหาทุกบันทึกของทะเบียนรถนี้
            camera_data = Camera.objects.filter(license_plate=license_plate).values(
                'id', 'license_plate', 'checkpoint_id', 'timestamp', 
                'vehicle_type', 'vehicle_color', 'latitude', 'longitude'
            )

            # แปลง timestamp เป็น string
            camera_data = [{
                **entry,
                'timestamp': entry['timestamp'].strftime('%Y-%m-%d %H:%M:%S')
            } for entry in camera_data]

        else:
            # แสดงข้อผิดพลาดถ้าฟอร์มไม่ถูกต้อง
            print("Form errors:", form.errors)  # แสดงข้อผิดพลาดใน console
            # คุณอาจต้องการส่งค่ากลับที่เหมาะสมในกรณีนี้ด้วย
            return JsonResponse({'error': 'Invalid form', 'form_errors': form.errors})

    else:
        # ค้นหาข้อมูลล่าสุดของแต่ละจุดตรวจในกรณีที่ไม่มีการค้นหา
        checkpoint_ids = Camera.objects.values_list('checkpoint_id', flat=True).distinct()

        for checkpoint_id in checkpoint_ids:
            # ดึงข้อมูลล่าสุดสำหรับแต่ละ checkpoint_id
            latest_camera = Camera.objects.filter(checkpoint_id=checkpoint_id).order_by('-timestamp').first()
            if latest_camera:
                camera_entry = {
                    'id': latest_camera.id,
                    'license_plate': latest_camera.license_plate,
                    'checkpoint_id': latest_camera.checkpoint_id,
                    'timestamp': latest_camera.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                    'vehicle_type': latest_camera.vehicle_type,
                    'vehicle_color': latest_camera.vehicle_color,
                    'latitude': latest_camera.latitude,
                    'longitude': latest_camera.longitude,
                }
                camera_data.append(camera_entry)

    # ส่งข้อมูลไปยัง JsonResponse
    return JsonResponse({'camera_data': camera_data})

@login_required
def search_license_plate(request):
    camera_data = []
    conflicting_results = None
    message = None
    form = LicensePlateSearchForm(request.GET or None)
    
    # ดึง checkpoint_id ทั้งหมดที่มีข้อมูล
    checkpoint_ids = Camera.objects.values_list('checkpoint_id', flat=True).distinct()

    if form.is_valid():
        # สร้างหมายเลขทะเบียนรถจาก form
        plate_part1 = form.cleaned_data['plate_part1']
        plate_part2 = form.cleaned_data['plate_part2']
        plate_part3 = form.cleaned_data['plate_part3']
        license_plate = f"{plate_part1}-{plate_part2}-{plate_part3}"
        
        # ค้นหาข้อมูลจากฐานข้อมูลสำหรับหมายเลขทะเบียนที่ค้นหา
        camera_queryset = Camera.objects.filter(license_plate=license_plate).order_by('timestamp')

        # แปลง queryset ให้เป็นรายการข้อมูลที่ส่งกลับ
        camera_data = [
            {
                'id': camera.id,
                'license_plate': camera.license_plate,
                'checkpoint_id': camera.checkpoint_id,
                'timestamp': camera.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                'vehicle_type': camera.vehicle_type,
                'vehicle_color': camera.vehicle_color,
                'latitude': camera.latitude,
                'longitude': camera.longitude,
            }
            for camera in camera_queryset
        ]

        # ค้นหาทะเบียนรถที่ข้อมูลประเภทหรือสีไม่ตรงกัน
        conflicting_results = Camera.objects.filter(license_plate=license_plate).values('vehicle_type', 'vehicle_color').annotate(count=Count('id')).filter(count__gt=1)

        if not camera_data:
            message = "ไม่พบข้อมูลทะเบียนรถที่ค้นหา"
        elif conflicting_results.exists():
            message = "พบข้อมูลทะเบียนรถและค้นหาเสร็จสิ้น"
        else :
            message = "พบข้อมูลทะเบียนรถและค้นหาเสร็จสิ้น"   
        
    else:
        message = "กรุณากรอกข้อมูลหมายเลขทะเบียนรถให้ครบถ้วน"
        # ดึงข้อมูลกล้องล่าสุดสำหรับแต่ละ checkpoint_id
        for checkpoint_id in checkpoint_ids:
            latest_camera = Camera.objects.filter(checkpoint_id=checkpoint_id).order_by('-timestamp').first()
            if latest_camera:
                camera_entry = {
                    'id': latest_camera.id,
                    'license_plate': latest_camera.license_plate,
                    'checkpoint_id': latest_camera.checkpoint_id,
                    'timestamp': latest_camera.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                    'vehicle_type': latest_camera.vehicle_type,
                    'vehicle_color': latest_camera.vehicle_color,
                    'latitude': latest_camera.latitude,
                    'longitude': latest_camera.longitude,
                }
                camera_data.append(camera_entry)

    return render(request, 'cameraapp/map.html', {
        'form': form, 
        'camera_data': camera_data, 
        'conflicting_results': conflicting_results,
        'message': message,
    })

@login_required
def map_check(request):
    camera_data = []
    conflicting_results = None
    message = None
    form = LicensePlateSearchForm(request.GET or None)
    
    # ดึง checkpoint_id ทั้งหมดที่มีข้อมูล
    checkpoint_ids = Camera.objects.values_list('checkpoint_id', flat=True).distinct()

    if form.is_valid():
        # สร้างหมายเลขทะเบียนรถจาก form
        plate_part1 = form.cleaned_data['plate_part1']
        plate_part2 = form.cleaned_data['plate_part2']
        plate_part3 = form.cleaned_data['plate_part3']
        license_plate = f"{plate_part1}-{plate_part2}-{plate_part3}"
        
        # ค้นหาข้อมูลจากฐานข้อมูลสำหรับหมายเลขทะเบียนที่ค้นหา
        camera_queryset = Camera.objects.filter(license_plate=license_plate).order_by('timestamp')

        # แปลง queryset ให้เป็นรายการข้อมูลที่ส่งกลับ
        camera_data = [
            {
                'id': camera.id,
                'license_plate': camera.license_plate,
                'checkpoint_id': camera.checkpoint_id,
                'timestamp': camera.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                'vehicle_type': camera.vehicle_type,
                'vehicle_color': camera.vehicle_color,
                'latitude': camera.latitude,
                'longitude': camera.longitude,
            }
            for camera in camera_queryset
        ]

        # ค้นหาทะเบียนรถที่ข้อมูลประเภทหรือสีไม่ตรงกัน
        conflicting_results = Camera.objects.filter(license_plate=license_plate).values('vehicle_type', 'vehicle_color').annotate(count=Count('id')).filter(count__gt=1)

        if not camera_data:
            message = "ไม่พบข้อมูลทะเบียนรถที่ค้นหา"
        elif conflicting_results.exists():
            message = "พบข้อมูลทะเบียนรถและค้นหาเสร็จสิ้น"
        else :
            message = "พบข้อมูลทะเบียนรถและค้นหาเสร็จสิ้น"   
        
    else:
        message = "กรุณากรอกข้อมูลหมายเลขทะเบียนรถให้ครบถ้วน"
        # ดึงข้อมูลกล้องล่าสุดสำหรับแต่ละ checkpoint_id
        for checkpoint_id in checkpoint_ids:
            latest_camera = Camera.objects.filter(checkpoint_id=checkpoint_id).order_by('-timestamp').first()
            if latest_camera:
                camera_entry = {
                    'id': latest_camera.id,
                    'license_plate': latest_camera.license_plate,
                    'checkpoint_id': latest_camera.checkpoint_id,
                    'timestamp': latest_camera.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                    'vehicle_type': latest_camera.vehicle_type,
                    'vehicle_color': latest_camera.vehicle_color,
                    'latitude': latest_camera.latitude,
                    'longitude': latest_camera.longitude,
                }
                camera_data.append(camera_entry)

    return render(request, 'cameraapp/map_checkpoint.html', {
        'form': form, 
        'camera_data': camera_data, 
        'conflicting_results': conflicting_results,
        'message': message,
    })