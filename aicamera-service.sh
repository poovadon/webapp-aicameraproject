#!/bin/bash
cd ../../../..
# เปลี่ยน directory ไปยัง project directory
cd path/webapp-aicameraproject/django/cameraproject/
# เปิด virtual environment
source venv/bin/activate
# รัน Django server บน 0.0.0.0:8000 แบบ background
python3 manage.py  runserver 0.0.0.0:8000 &
