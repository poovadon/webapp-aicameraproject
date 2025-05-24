from .models import Camera
from xmlrpc.client import DateTime
from django.core.paginator import Paginator
from django.shortcuts import render, get_object_or_404, redirect
from datetime import datetime
import json, threading, base64
import altair as alt
import pandas as pd
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from django.http import HttpRequest, HttpResponseRedirect, JsonResponse, Http404
from django.db.models import Count, Case, When, IntegerField, Subquery, OuterRef, Max
import asyncio
import websockets
from asgiref.sync import async_to_sync
from django.utils import timezone
from django.db.models import Q
from time import sleep
from threading import Thread
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
import os
from .forms import LicensePlateSearchForm
from django.db.models import Count



@login_required
def home(request):
    return render(request, 'cameraapp/home.html')
    
# @login_required
# def map(request):
#     return render(request, 'cameraapp/map.html')

def get_camera_data(request):
    # Get distinct checkpoint_id from Camera
    checkpoint_ids = Camera.objects.values_list('checkpoint_id', flat=True).distinct()

    camera_data = []

    for checkpoint_id in checkpoint_ids:
        # Fetch the latest record for each checkpoint_id
        latest_camera = Camera.objects.filter(checkpoint_id=checkpoint_id).order_by('-timestamp').first()

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

    # Sort camera_data based on timestamp
    camera_data = sorted(camera_data, key=lambda x: x['timestamp'], reverse=False)

    return JsonResponse({'camera_data': camera_data})

def search_license_plate(request):
    results = None
    conflicting_results = None
    form = LicensePlateSearchForm(request.GET or None)

    if form.is_valid():
        plate_part1 = form.cleaned_data['plate_part1']
        plate_part2 = form.cleaned_data['plate_part2']
        plate_part3 = form.cleaned_data['plate_part3']
        license_plate = f"{plate_part1}-{plate_part2}-{plate_part3}"
        
        # ค้นหาข้อมูลจากฐานข้อมูล
        results = Camera.objects.filter(license_plate=license_plate).order_by('timestamp')

        # ค้นหาทะเบียนรถที่ข้อมูลประเภทหรือสีไม่ตรงกัน
        conflicting_results = Camera.objects.filter(license_plate=license_plate).values('vehicle_type', 'vehicle_color').annotate(count=Count('id')).filter(count__gt=1)

    return render(request, 'cameraapp/map.html', {
        'form': form, 
        'results': results, 
        'conflicting_results': conflicting_results
    })
