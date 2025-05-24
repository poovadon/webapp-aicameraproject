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
def generate_checkpoints(n):
    latitudes = np.random.uniform(16.9, 17.5, n)
    longitudes = np.random.uniform(98.6, 99.2, n)
    checkpoints = pd.DataFrame({
        'checkpoint_id': range(1, n+1),
        'latitude': latitudes,
        'longitude': longitudes
    })
    return checkpoints

checkpoints = generate_checkpoints(num_checkpoints)

# ประเภทของรถยนต์
vehicle_types = ["รถยนต์กระบะ", "รถเก๋งส่วนบุคคล", "รถบรรทุก 6 ล้อ", "รถตู้โดยสาร", "รถบรรทุก 10 ล้อ", "รถบัส"]

# สีของรถ
vehicle_colors = ["ขาว", "เขียว", "เหลือง", "ชมพู", "ดำ", "แดง", "เทา"]

# สร้างห้วงเวลาที่เก็บข้อมูล (ช่วงเวลา 1 เดือน)
start_date = datetime(2024, 9, 1)
time_range = [start_date + timedelta(minutes=i) for i in range(0, num_days * 24 * 60)]

# สร้างข้อมูลจำลอง 100,000 records
simulation_data = pd.DataFrame({
    'license_plate': np.random.choice(license_plates, num_records, replace=True),
    'checkpoint_id': np.random.choice(checkpoints['checkpoint_id'], num_records, replace=True),
    'timestamp': np.random.choice(time_range, num_records, replace=True),
    'vehicle_type': np.random.choice(vehicle_types, num_records, replace=True),
    'vehicle_color': np.random.choice(vehicle_colors, num_records, replace=True)
})

# รวมข้อมูลด่านตรวจที่มีกล้อง LPR เพื่อแสดงพิกัด
simulation_data = simulation_data.merge(checkpoints, on='checkpoint_id', how='left')

# แสดงตัวอย่างข้อมูล
print(simulation_data.head())

# บันทึกข้อมูลลงไฟล์ CSV
simulation_data.to_csv("vehicle_lpr_simulation_data.csv", index=False)

# ข้อมูลการเชื่อมต่อฐานข้อมูล MySQL
db_user = 'amic'  # ชื่อผู้ใช้ MySQL
db_password = 'Amic@8836688366'  # รหัสผ่าน MySQL
db_host = '127.0.0.1'  # หรือ localhost
db_port = '3306'  # พอร์ต MySQL (ค่าเริ่มต้นคือ 3306)
db_name = 'camera_database'  # ชื่อฐานข้อมูลที่คุณต้องการบันทึกข้อมูล

# URL encode รหัสผ่าน
encoded_password = quote_plus('Amic@8836688366')

# สร้าง connection URL ใหม่
connection_url = f'mysql+pymysql://amic:{encoded_password}@127.0.0.1:3306/camera_database'

# เชื่อมต่อกับฐานข้อมูล
from sqlalchemy import create_engine
engine = create_engine(connection_url)
try:
    with engine.connect() as connection:
        print("Connected to the database successfully!")
except Exception as e:
    print(f"Failed to connect to the database: {e}")
# บันทึกข้อมูลลงในตารางในฐานข้อมูล
# โดยสร้างตารางชื่อ 'vehicle_lpr_simulation_data' ในฐานข้อมูล (ถ้ายังไม่มีตารางนี้)
simulation_data.to_sql('vehicle_lpr_simulation_data', con=engine, if_exists='append', index=False) #append

print("Data successfully inserted into the database.")