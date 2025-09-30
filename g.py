# app.py
from flask import Flask, request, jsonify, render_template, redirect, url_for, session
import mysql.connector
import os
import sys

app = Flask(name)

# ------------------------------------
# إجبار التطبيق على استخدام SECRET_KEY من متغير البيئة فقط
# إذا لم يتم تعيينه — يوقف التطبيق ويطبع رسالة واضحة
# ------------------------------------
secret = os.environ.get('SECRET_KEY')
if not secret:
    sys.exit("ERROR: يجب تعيين متغير البيئة SECRET_KEY قبل تشغيل التطبيق.")
app.secret_key = secret

# ------------------------------------
# إعدادات قاعدة البيانات
# يقرأ القيم من متغيرات البيئة إن وُجدت، وإلا يستخدم القيم الافتراضية للاختبار المحلي
# يمكنك تعديل القيم الافتراضية هنا إذا أردت تجربة محلية بدون متغيرات بيئة
# ------------------------------------
db_config = {
    'host': os.environ.get('DB_HOST', 'localhost'),
    'user': os.environ.get('DB_USER', 'root'),
    'password': os.environ.get('DB_PASSWORD', 'password'),   # اترك فارغاً إن لم تكن لديك كلمة سر محلية
    'database': os.environ.get('DB_NAME', 'school')
}

def get_db_connection():
    """
    يرجع اتصالًا بقاعدة البيانات حسب db_config.
    تأكد أن قاعدة البيانات متاحة (محليًا أو عن بعد) قبل استدعاء هذه الدالة.
    """
    return mysql.connector.connect(**db_config)

# ---------------------------
# صفحات الموقع وواجهات API
# ---------------------------

@app.route('/', methods=['GET', 'POST'])
def login_page():
    """
    صفحة تسجيل الدخول (نموذج HTML)
    إذا نجح الدخول يحفظ student_id في session ويحول للوحة dashboard
    """
    if request.method == 'POST':
        name = request.form.get('name')
        password = request.form.get('password')
        # تحقق بسيط من المدخلات
        if not name or not password:
            return render_template('login.html', error="الرجاء إدخال اسم المستخدم وكلمة المرور")
        try:
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM students WHERE name=%s AND password=%s", (name, password))
            student = cursor.fetchone()
            cursor.close()
            conn.close()
        except Exception as e:
            # خطأ بالاتصال بقاعدة البيانات
            return render_template('login.html', error=f"خطأ في الاتصال بقاعدة البيانات: {e}")
        if student:
            session['student_id'] = student['id']
            return redirect(url_for('dashboard'))
        else:
            return render_template('login.html', error="اسم أو كلمة مرور خاطئة")
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    """
    صفحة لوحة الدرجات (تحتاج أن يكون المستخدم مسجل دخول عبر session)
    """
    student_id = session.get('student_id')
    if not student_id:
        return redirect(url_for('login_page'))
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT subject, grade FROM grades WHERE student_id=%s", (student_id,))
        grades = cursor.fetchall()
        cursor.close()
        conn.close()
    except Exception as e:
        return render_template('dashboard.html', grades=[], error=f"خطأ في تحميل الدرجات: {e}")
    return render_template('dashboard.html', grades=grades)

# API لتسجيل الدخول (يمكن استخدامه عبر AJAX)
@app.route('/api/login', methods=['POST'])
def api_login():
    """
    يتوقع JSON: { "name": "...", "password": "..." }
    يعيد JSON بوجود success و student_id إذا نجح
    """
    data = request.get_json(silent=True) or {}
    name = data.get('name')
    password = data.get('password')
    if not name or not password:
        return jsonify({"success": False, "message": "الرجاء إرسال الاسم وكلمة المرور"}), 400
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM students WHERE name=%s AND password=%s", (name, password))
        student = cursor.fetchone()
        cursor.close()
        conn.close()
    except Exception as e:
        return jsonify({"success": False, "message": f"DB error: {e}"}), 500
    if student:
        return jsonify({"success": True, "student_id": student['id']})
    else:
        return jsonify({"success": False, "message": "اسم أو كلمة مرور خاطئة"}), 401

# API لجلب الدرجات
@app.route('/api/grades/<int:student_id>', methods=['GET'])
def get_grades(student_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT subject, grade FROM grades WHERE student_id=%s", (student_id,))
        grades = cursor.fetchall()
        cursor.close()
        conn.close()
    except Exception as e:
        return jsonify({"success": False, "message": f"DB error: {e}"}), 500
    return jsonify({"success": True, "grades": grades})

# مسار لتسجيل الخروج (يحذف الجلسة)
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login_page'))

# ---------------------------
# تشغيل التطبيق
# ---------------------------
if name == 'main':
    # يستخدم متغير PORT إن وُجد (Render يوفّر PORT)، وإلا يستخدم 5000 محليًا
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
