import pandas as pd
import numpy as np
import random
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from urllib.parse import quote_plus

# ตั้งค่าเริ่มต้น
random.seed(123)
num_records = 100000
num_plates = 5000
num_checkpoints = 100
num_days = 30
num_devices = 100

# ฟังก์ชันสร้างป้ายทะเบียนรถยนต์
def generate_license_plate(n):
    letters_thai = list("กขฃคฅฆงจฉชซฌญฎฏฐฑฒณดตถทธนบปผฝพฟภมยรลวศษสหฬอฮ")
    numbers = list("0123456789")
    provinces = ["กรุงเทพมหานคร", "ตาก", "เชียงใหม่", "ชลบุรี", "ภูเก็ต", "ขอนแก่น", "นครราชสีมา"]
    
    license_plates = []
    for _ in range(n):
        plate = f"{random.choice(letters_thai)}{random.choice(letters_thai)}-{''.join(random.choices(numbers, k=4))}-{random.choice(provinces)}"
        license_plates.append(plate)
    return license_plates

# สร้างข้อมูลป้ายทะเบียนรถยนต์ 5,000 ป้าย
license_plates = generate_license_plate(num_plates)

# สร้างข้อมูลด่านตรวจที่มีกล้อง LPR พร้อมพิกัดในจังหวัดตาก
latitudes = np.random.uniform(16.9, 17.5, num_checkpoints)
longitudes = np.random.uniform(98.6, 99.2, num_checkpoints)

# ตรวจสอบให้แน่ใจว่า latitudes และ longitudes ไม่มีค่าซ้ำ
latitudes_unique = np.unique(latitudes)
longitudes_unique = np.unique(longitudes)

# หากจำนวนค่าที่ไม่ซ้ำกันน้อยกว่า num_checkpoints, สร้างค่าซ้ำใหม่จนกว่าจะได้จำนวนครบ
while len(latitudes_unique) < num_checkpoints:
    latitudes = np.random.uniform(16.9, 17.5, num_checkpoints)
    latitudes_unique = np.unique(latitudes)

while len(longitudes_unique) < num_checkpoints:
    longitudes = np.random.uniform(98.6, 99.2, num_checkpoints)
    longitudes_unique = np.unique(longitudes)

# สร้าง DataFrame ของ checkpoints
checkpoints = pd.DataFrame({
    'checkpoint_id': range(1, num_checkpoints + 1),
    'latitude': latitudes_unique,
    'longitude': longitudes_unique
})

# ประเภทของรถยนต์
vehicle_types = ["รถยนต์กระบะ", "รถเก๋งส่วนบุคคล", "รถบรรทุก 6 ล้อ", "รถตู้โดยสาร", "รถบรรทุก 10 ล้อ", "รถบัส"]

# สีของรถ
vehicle_colors = ["ขาว", "เขียว", "เหลือง", "ชมพู", "ดำ", "แดง", "เทา"]

# สร้างห้วงเวลาที่เก็บข้อมูล (ช่วงเวลา 1 เดือน)
start_date = datetime(2024, 9, 1)
time_range = [start_date + timedelta(minutes=i) for i in range(0, num_days * 24 * 60)]

# สร้างข้อมูลจำลองทั้งหมดในชุดเดียว
simulation_data = pd.DataFrame({
    'license_plate': np.random.choice(license_plates, num_records, replace=True),
    'checkpoint_id': np.random.choice(checkpoints['checkpoint_id'], num_records, replace=True),
    'timestamp': np.random.choice(time_range, num_records, replace=True),
    'vehicle_type': np.random.choice(vehicle_types, num_records, replace=True),
    'vehicle_color': np.random.choice(vehicle_colors, num_records, replace=True)
})

# รวมข้อมูลด่านตรวจที่มีกล้อง LPR เพื่อแสดงพิกัด
simulation_data = simulation_data.merge(checkpoints, on='checkpoint_id', how='left')

# บันทึกข้อมูลลงไฟล์ CSV
simulation_data.to_csv("vehicle_lpr_simulation_data.csv", index=False)

# ข้อมูลการเชื่อมต่อฐานข้อมูล MySQL
db_user = 'amic'
db_password = quote_plus('Amic@8836688366')
db_host = 'localhost'
db_port = '3306'
db_name = 'camera_database'
engine = create_engine(f'mysql+pymysql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}')

# ตรวจสอบการเชื่อมต่อ
try:
    with engine.connect() as connection:
        print("Connected to the database successfully!")
except Exception as e:
    print(f"Failed to connect to the database: {e}")

# บันทึกข้อมูล vehicle_lpr_simulation_data ลงในฐานข้อมูล
simulation_data.to_sql('vehicle_lpr_simulation_data', con=engine, if_exists='replace', index=False)

# แยกข้อมูลออกไปยังตารางอื่น ๆ จากชุดเดียวกัน
# สร้างข้อมูล edge_devices จากข้อมูล checkpoint
device_ids = [f"device_{i}" for i in range(1, num_devices + 1)]
location_ids = np.random.choice(range(1, 101), num_devices, replace=False) 

# สร้างข้อมูล edge_devices
edge_devices = pd.DataFrame({
    'device_id': device_ids,
    'last_heartbeat': [start_date + timedelta(minutes=random.randint(0, 43200)) for _ in range(num_devices)],
    'status': np.random.choice(["active", "inactive", "error"], num_devices),
    'ip_address': [f"192.168.1.{random.randint(1, 255)}" for _ in range(num_devices)],
    'location_id': location_ids  # ใช้ location_ids ที่สุ่มได้
})

# บันทึกข้อมูลลงฐานข้อมูล
edge_devices.to_sql('edge_devices', con=engine, if_exists='replace', index=False)

# สร้างข้อมูล checkpoint จากข้อมูล checkpoint ที่มีอยู่
checkpoints_detail = pd.DataFrame({
    'checkpoint_id': checkpoints['checkpoint_id'],
    'location_name': [f"Location_{i}" for i in checkpoints['checkpoint_id']],
    'gps_latitude': checkpoints['latitude'],
    'gps_longitude': checkpoints['longitude']
})
checkpoints_detail.to_sql('checkpoint', con=engine, if_exists='replace', index=False)

# สร้างข้อมูล aggregation_detections จากชุดข้อมูล simulation_data
aggregation_detections = pd.DataFrame({
    'date': np.random.choice(simulation_data['timestamp'], 500),
    'aggregation_id': range(1, 501),
    'total_detections': np.random.randint(0, 1000, 500),
    'intersection_id': np.random.choice(checkpoints['checkpoint_id'], 500, replace=True),
    'device_id': np.random.choice(edge_devices['device_id'], 500, replace=True)
})
aggregation_detections.to_sql('aggregation_detections', con=engine, if_exists='replace', index=False)

print("All data successfully inserted into the database.")
