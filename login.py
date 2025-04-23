from flask import Blueprint, render_template, request, redirect, url_for, session
import json
import os

# สร้าง Blueprint สำหรับ login
login_bp = Blueprint('login', __name__)

# ฟังก์ชันอ่านข้อมูลจากไฟล์ users.json
def get_users():
    # ตรวจสอบว่าโฟลเดอร์ Documents มีอยู่หรือไม่ ถ้าไม่มีก็จะใช้ os.makedirs สร้าง
    folder_path = os.path.join(os.path.expanduser('~'), 'Documents', 'Guess the Word Game')
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)

    users_file = os.path.join(folder_path, 'users.json')

    if not os.path.exists(users_file):
        # ถ้าไฟล์ users.json ไม่มี จะสร้างขึ้นใหม่และให้ข้อมูลเริ่มต้นเป็นว่าง
        with open(users_file, 'w') as f:
            json.dump({"users": []}, f)
        return []  # ถ้าไม่มีผู้ใช้ ก็คืนค่าลิสต์ว่าง

    with open(users_file, 'r') as f:
        data = json.load(f)
        return data["users"]  # คืนค่า users ทั้งหมดจากไฟล์

# ฟังก์ชันเพิ่ม user ลงในไฟล์ users.json
def add_user(username, password):
    users = get_users()
    username = username.lower()  # ทำให้ username เป็นตัวพิมพ์เล็กทั้งหมด
    # เช็คว่า username มีอยู่แล้วหรือไม่
    if any(user['username'].lower() == username for user in users):  # ตรวจสอบ username โดยไม่สนใจตัวพิมพ์ใหญ่/เล็ก
        return False  # ถ้ามีอยู่แล้วให้คืนค่า False

    # เพิ่ม user ลงในไฟล์
    users.append({"username": username, "password": password})
    users_file = os.path.join(os.path.expanduser('~'), 'Documents', 'Guess the Word Game', 'users.json')
    with open(users_file, 'w') as f:
        json.dump({"users": users}, f)
    return True  # ถ้าเพิ่มสำเร็จให้คืนค่า True

# ฟังก์ชันเช็ค username และ password
def check_user(username, password):
    users = get_users()
    username = username.lower()  # ทำให้ username เป็นตัวพิมพ์เล็กทั้งหมด
    for user in users:
        if user['username'].lower() == username and user['password'] == password:  # ตรวจสอบ username โดยไม่สนใจตัวพิมพ์ใหญ่/เล็ก
            return True
    return False

# หน้า Login
@login_bp.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # เช็คว่า username และ password ถูกต้องหรือไม่
        if check_user(username, password):
            session['username'] = username
            return redirect(url_for('home'))  # ไปที่หน้า Home
        else:
            return render_template('login.html', error="Invalid username or password!")
    return render_template('login.html')

# หน้า Register (สมัครสมาชิก)
@login_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        # ตรวจสอบว่ามี username นี้ในระบบหรือไม่
        if password != confirm_password:  # ตรวจสอบว่า password และ confirm_password ตรงกันหรือไม่
            return render_template('register.html', error="Passwords do not match!")

        if add_user(username, password):
            return redirect(url_for('login.login'))  # ไปที่หน้า Login
        else:
            return render_template('register.html', error="Username already exists!")
    return render_template('register.html')