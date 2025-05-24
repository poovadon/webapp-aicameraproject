# webapp-aicameraproject
### 1. ดึงโค้ดโปรเจกต์จาก GitHub
```bash
git clone https://github.com/poovadon/webapp-aicameraproject.git
cd webapp-aicameraproject/django/cameraproject
```
### 2. ติดตั้งแพ็กเกจทั้งหมดที่ระบุในไฟล์ลงใน virtual environment
```bash
pip install -r requirements.txt
```
### 3. ตั้งค่าฐานข้อมูล MySQL
```bash
CREATE DATABASE camera_database CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'your_mysql_user'@'localhost' IDENTIFIED BY 'your_password';
GRANT ALL PRIVILEGES ON camera_database.* TO 'your_mysql_user'@'localhost';
FLUSH PRIVILEGES;
```
### 4. นำเข้าโครงสร้างฐานข้อมูล MySQL
```bash
mysql -u your_mysql_user -p camera_database < camera_database.sql
```
### 5. ปรับแต่งไฟล์ตั้งค่า Django
แก้ไขไฟล์ cameraproject/settings.py เพื่อเชื่อมต่อกับฐานข้อมูล MySQL ที่ตั้งค่าไว้ และตั้งค่า ip
```bash

ALLOWED_HOSTS = ['192.168.1.224','ddns.net'] # your_ip adn domain

INTERNAL_IPS = [
    # ...
    '127.0.0.1',
    '192.168.1.224', # your_ip
    'ddns.net', # your_domain
    # ...
]
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'camera_database',
        'USER': 'your_mysql_user',
        'PASSWORD': 'your_password',
        'HOST': 'localhost',
        'PORT': '3306',
    }
}
```
### 6. ใช้ Django Migrations เพื่อสร้างตารางฐานข้อมูล
```bash
python manage.py migrate
```
### 7. สร้าง superuser เพื่อเข้าใช้งาน Django Admin 
```bash
python manage.py createsuperuser
```
### 8. รันเซิร์ฟเวอร์
เปิดเว็บเบราเซอร์ไปที่ URL นี้เพื่อใช้งาน: http://127.0.0.1:8000 หรือ ip setup
```bash
python manage.py runserver 0.0.0.0:8000
```
### 9. สร้าง Service สำหรับรัน WebApp
จะสร้าง shell script เพื่อช่วยให้สามารถรัน Django WebApp ได้ง่ายขึ้นในครั้งเดียว โดยทำตามขั้นตอนด้านล่าง
#### 9.1 สร้างไฟล์ shell script
ให้สร้างไฟล์ชื่อ aicamera-service.sh และเขียนคำสั่งต่อไปนี้ลงไปในไฟล์:

```bash
#!/bin/bash
cd ../../../..
# เปลี่ยน directory ไปยัง project directory
cd path/webapp-aicameraproject/django/cameraproject/
# เปิด virtual environment
source venv/bin/activate
# รัน Django server บน 0.0.0.0:8000 แบบ background
python3 manage.py  runserver 0.0.0.0:8000 &
```
#### 9.2 ตั้งสิทธิ์ให้ shell script สามารถรันได้
```bash
chmod +x aicamera-service.sh
```

#### 9.3 เรียกใช้ script เพื่อเริ่ม server
หากทำถูกต้อง คุณจะเห็น Django server เริ่มทำงานที่ http://0.0.0.0:8000
```bash
./aicamera-service.sh
```
### 10. เพิ่มเติม
หากคุณต้องการให้ script นี้รันอัตโนมัติหลังจากบูตเครื่อง (Linux server)
#### 10.1 สร้าง systemd service:
```bash
sudo nano /etc/systemd/system/aicamera.service
```
#### 10.2 ใส่เนื้อหานี้:
```bash
[Unit]
Description=Run Django AICamera WebApp
After=network.target

[Service]
# เปลี่ยน directory ไปยัง project script 
ExecStart=path/to/webapp-aicameraproject/django/cameraproject/django.sh
Restart=always
WorkingDirectory=path/to/webapp-aicameraproject/django/cameraproject
User=your_user
Group=your_group

[Install]
WantedBy=multi-user.target
```
#### 10.3 จากนั้น
```bash
sudo systemctl daemon-reexec
sudo systemctl daemon-reload
sudo systemctl enable aicamera
sudo systemctl start aicamera
```
