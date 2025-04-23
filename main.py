from flask import Flask, render_template, request, session, redirect, url_for
import random
import sqlite3
import os
from datetime import datetime
from login import login_bp  # เพิ่มการนำเข้า login blueprint

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # ใช้เซสชัน

# ลงทะเบียน blueprint ของ login
app.register_blueprint(login_bp, url_prefix='/login')

word_image_pairs = [
    {"word": "Dog", "image": "dog.gif"},
    {"word": "Cat", "image": "cat.gif"},
    {"word": "Car", "image": "car.gif"},
    {"word": "Bird", "image": "bird.gif"},
]


# ฟังก์ชันเชื่อมต่อฐานข้อมูล
def get_db_connection():
    conn = sqlite3.connect('game.db')
    conn.row_factory = sqlite3.Row  # จะได้ข้อมูลเป็น dictionary
    return conn

# ฟังก์ชันสร้างตาราง used_images และ game_history (หากยังไม่มี)
def create_db():
    conn = get_db_connection()
    # เพิ่มคอลัมน์ username ในตาราง game_history
    conn.execute('CREATE TABLE IF NOT EXISTS used_images (image TEXT)')
    conn.execute('''CREATE TABLE IF NOT EXISTS game_history (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        score INTEGER,
                        date TEXT,
                        username TEXT)''')  # เพิ่มคอลัมน์ username
    conn.commit()
    conn.close()

# หน้าแรก - เปลี่ยนเส้นทางไปที่หน้า login ถ้ายังไม่ได้ล็อกอิน
@app.route('/')
def home():
    # ตรวจสอบว่า user เข้าสู่ระบบหรือยัง
    if 'username' not in session:  # ถ้าไม่มี username ในเซสชัน (ยังไม่ได้ล็อกอิน)
        return redirect(url_for('login.login'))  # ไปที่หน้าล็อกอิน    
    # รีเซ็ตคะแนนก่อนเริ่มเกม
    session['score'] = 0  # เซ็ตคะแนนให้เป็น 0
    # ลบข้อมูลที่เคยใช้ไปในฐานข้อมูล
    conn = get_db_connection()
    conn.execute('DELETE FROM used_images')  # ลบข้อมูลภาพที่เคยใช้
    conn.commit()
    conn.close()
    return render_template('home.html')  # ไปที่หน้า home.html

# ฟังก์ชันอัปเดตคะแนน
@app.route('/update_score/<int:history_id>', methods=['POST'])
def update_score(history_id):
    if 'username' not in session or session['username'].lower() != 'admin':
        return redirect(url_for('home'))

    new_score = request.form['score']

    # อัปเดตข้อมูลในฐานข้อมูล
    conn = get_db_connection()
    conn.execute('UPDATE game_history SET score = ? WHERE id = ?', (new_score, history_id))
    conn.commit()
    conn.close()

    return redirect(url_for('career'))  # กลับไปที่หน้าประวัติการเล่น

# ฟังก์ชันลบคะแนน
@app.route('/delete_score/<int:history_id>', methods=['POST'])
def delete_score(history_id):
    if 'username' not in session or session['username'].lower() != 'admin':
        return redirect(url_for('home'))

    # ลบข้อมูลจากฐานข้อมูล
    conn = get_db_connection()
    conn.execute('DELETE FROM game_history WHERE id = ?', (history_id,))
    conn.commit()
    conn.close()

    return redirect(url_for('career'))  # กลับไปที่หน้าประวัติการเล่น

# หน้าเครดิต
@app.route('/credit')
def credit():
    return render_template('credit.html')  # ไปที่หน้า credit.html

# หน้าเกม
@app.route('/start_game')
def start_game():
    if 'score' not in session:
        session['score'] = 0
        session['score_saved'] = False  # เพิ่มไว้ตอนเริ่มเกมใหม่ด้วย

    # เชื่อมต่อฐานข้อมูล
    conn = get_db_connection()
    # ดึงข้อมูลภาพที่ทายถูกแล้วจากฐานข้อมูล
    used_images_query = conn.execute('SELECT image FROM used_images').fetchall()
    used_images = [row['image'] for row in used_images_query]
    conn.close()

    # เลือกรูปที่ยังไม่ถูกใช้
    available_pairs = [pair for pair in word_image_pairs if pair["image"] not in used_images]

    # ถ้าทายครบหมดแล้ว
    if not available_pairs:
        return redirect(url_for('win'))  # ไปที่หน้า "You Win!"

    # เลือกรูปภาพที่ยังไม่ถูกทาย
    random_pair = random.choice(available_pairs)

    # ส่งข้อมูลไปยัง index.html
    return render_template('index.html', image=random_pair["image"], word=random_pair["word"], result=None, score=session['score'])

# ตรวจสอบคำตอบ
@app.route('/check_answer', methods=['POST'])
def check_answer():
    if 'user_answer' not in request.form or 'correct_answer' not in request.form or 'image' not in request.form:
        return redirect(url_for('home'))  # ถ้าไม่มีคีย์เหล่านี้ ให้ไปที่หน้าแรกใหม่

    user_answer = request.form['user_answer']
    correct_answer = request.form['correct_answer']
    image = request.form['image']

    # ตรวจสอบคำตอบ
    if user_answer.strip().lower() == correct_answer.strip().lower():
        # ถ้าทายถูก จะเพิ่มภาพที่ถูกใช้ไปในฐานข้อมูล
        conn = get_db_connection()
        conn.execute('INSERT INTO used_images (image) VALUES (?)', (image,))
        conn.commit()
        conn.close()

        # เพิ่มคะแนน
        session['score'] += 1
        result = "Correct!"  # แต่จะไม่แสดงผลใน HTML
    else:
        # หากทายผิด
        result = "Incorrect Answer!"  # แสดงข้อความทายผิด

        # บันทึกคะแนนปัจจุบันในฐานข้อมูลเหมือนตอนชนะ
        username = session.get('username', 'Guest')  # ดึงชื่อผู้เล่นจาก session
        score = session.get('score', 0)
        date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # บันทึกข้อมูลลงในฐานข้อมูล
        conn = get_db_connection()
        conn.execute('INSERT INTO game_history (score, date, username) VALUES (?, ?, ?)', (score, date, username))
        conn.commit()
        conn.close()

    # ส่งผลลัพธ์ไปยังหน้า lose.html หรือแสดงภาพถัดไป
    if result == "Incorrect Answer!":
        user_answer_display = user_answer
        return render_template('lose.html', result=result, user_answer=user_answer_display, correct_answer=correct_answer, image=image, score=session['score'])  # ส่งคะแนนไปยัง lose.html
    else:
        return redirect(url_for('start_game'))  # แสดงภาพถัดไป

# ปุ่มรีสตาร์ทเกม
@app.route('/restart')
def restart():
    # รีเซ็ตฐานข้อมูลและคะแนน
    conn = get_db_connection()
    conn.execute('DELETE FROM used_images')
    conn.commit()
    conn.close()

    # รีเซ็ตคะแนนและสถานะในเซสชัน
    session['score'] = 0
    session['score_saved'] = False  # reset flag เพื่อเล่นรอบใหม่
    return redirect(url_for('start_game'))

# หน้า "You Win!"
@app.route('/win')
def win():
    if session.get('score_saved', False):  # ถ้าเคยบันทึกแล้วไม่ให้บันทึกซ้ำ
        return render_template('win.html', score=session.get('score', 0))

    # ดึงคะแนนและชื่อผู้ใช้
    score = session.get('score', 0)
    username = session.get('username', 'Guest')  # ดึงชื่อผู้เล่นจาก session
    date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # บันทึกคะแนนและชื่อผู้เล่นลงฐานข้อมูล
    conn = get_db_connection()
    conn.execute('INSERT INTO game_history (score, date, username) VALUES (?, ?, ?)', (score, date, username))
    conn.commit()
    conn.close()

    session['score_saved'] = True  # ตั้ง flag ว่าบันทึกแล้ว

    return render_template('win.html', score=score)

# หน้า Career (ประวัติการเล่น)
@app.route('/history')
def career():
    if 'username' not in session:
        return redirect(url_for('login.login'))  # ถ้ายังไม่ได้ล็อกอิน ให้ไปหน้า login

    # ดึงข้อมูลประวัติการเล่นจากฐานข้อมูล
    conn = get_db_connection()
    game_history_query = conn.execute('SELECT * FROM game_history ORDER BY date DESC').fetchall()
    conn.close()

    # ส่งข้อมูลไปยัง career.html
    return render_template('career.html', game_history=game_history_query)

# ฟังก์ชันรีเซ็ตข้อมูลการเล่น
@app.route('/reset_career', methods=['POST'])
def reset_career():
    conn = get_db_connection()
    conn.execute('DELETE FROM game_history')  # ลบข้อมูลในตาราง game_history
    conn.commit()
    conn.close()

    return redirect(url_for('career'))  # รีไดเรกต์ไปที่หน้า career.html

def add_username_column():
    conn = get_db_connection()
    try:
        conn.execute('ALTER TABLE game_history ADD COLUMN username TEXT')
        conn.commit()
    except sqlite3.OperationalError:
        # คอลัมน์อาจมีอยู่แล้วถ้ารันแล้วไม่เกิดข้อผิดพลาด
        pass
    conn.close()

@app.route('/logout', methods=['POST'])
def logout():
    session.pop('username', None)  # ลบข้อมูลผู้ใช้ใน session
    return redirect(url_for('login.login'))  # เปลี่ยนเส้นทางไปที่หน้าล็อกอิน

@app.after_request
def add_header(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

@app.route('/update_user/<int:history_id>', methods=['POST'])
def update_user(history_id):
    if 'username' not in session or session['username'].lower() != 'admin':
        return redirect(url_for('home'))

    new_username = request.form['username']

    # อัปเดตข้อมูลในฐานข้อมูล
    conn = get_db_connection()
    conn.execute('UPDATE game_history SET username = ? WHERE id = ?', (new_username, history_id))
    conn.commit()
    conn.close()

    return redirect(url_for('career'))  # กลับไปที่หน้าประวัติการเล่น

@app.route('/update_date/<int:history_id>', methods=['POST'])
def update_date(history_id):
    if 'username' not in session or session['username'].lower() != 'admin':
        return redirect(url_for('home'))

    new_date = request.form['date']

    # อัปเดตข้อมูลในฐานข้อมูล
    conn = get_db_connection()
    conn.execute('UPDATE game_history SET date = ? WHERE id = ?', (new_date, history_id))
    conn.commit()
    conn.close()

    return redirect(url_for('career'))  # กลับไปที่หน้าประวัติการเล่น

@app.route('/finish_game', methods=['POST'])
def finish_game():
    if 'username' in session:
        username = session['username']
        # เพิ่มคะแนนเต็มให้ผู้เล่น
        # สมมติว่า score เป็นตัวแปรที่เก็บคะแนนของผู้เล่น
        session['score'] = 4  # ปรับคะแนนเต็มที่คุณต้องการ
        return redirect(url_for('win'))  # เปลี่ยนไปหน้า win
    return redirect(url_for('home'))

# เรียกใช้ฟังก์ชันเพื่อเพิ่มคอลัมน์ username
add_username_column()

if __name__ == '__main__':
    create_db()  # เรียกใช้ฟังก์ชันสร้างฐานข้อมูลและตาราง
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
