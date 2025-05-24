# webapp-aicameraproject
### 1. ดึงโค้ดโปรเจกต์จาก GitHub
```bash
git clone https://github.com/poovadon/webapp-aicameraproject.git
cd webapp-aicameraproject/django/cameraproject
### 2. ติดตั้งแพ็กเกจทั้งหมดที่ระบุในไฟล์ลงใน virtual environment
```bash
pip install -r requirements.txt

### 3. ตั้งค่าฐานข้อมูล MySQL
```bash
CREATE DATABASE camera_database CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'your_mysql_user'@'localhost' IDENTIFIED BY 'your_password';
GRANT ALL PRIVILEGES ON camera_database.* TO 'your_mysql_user'@'localhost';
FLUSH PRIVILEGES;

### 4. นำเข้าโครงสร้างฐานข้อมูล MySQL
```bash
mysql -u your_mysql_user -p camera_database < camera_database.sql

### 5.ปรับแต่งไฟล์ตั้งค่า Django
### แก้ไขไฟล์ cameraproject/settings.py เพื่อเชื่อมต่อกับฐานข้อมูล MySQL ที่ตั้งค่าไว้
```bash
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

### 6.ใช้ Django Migrations เพื่อสร้างตารางฐานข้อมูล
```bash
python manage.py runserver 0.0.0.0:8000
### เปิดเว็บเบราเซอร์ไปที่ URL นี้เพื่อใช้งาน: http://127.0.0.1:8000
