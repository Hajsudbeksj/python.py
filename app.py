from flask import Flask, request, render_template, redirect, url_for, session
from datetime import timedelta
import os
import requests

# -------------------------
# قراءة متغيرات البيئة
# -------------------------
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
SECRET_KEY = os.environ.get("SECRET_KEY")

if not all([SUPABASE_URL, SUPABASE_KEY, SECRET_KEY]):
    raise RuntimeError("يجب تعيين جميع متغيرات البيئة: SUPABASE_URL, SUPABASE_KEY, SECRET_KEY")

# -------------------------
# إعداد Flask
# -------------------------
app = Flask(__name__)
app.config['SECRET_KEY'] = SECRET_KEY
app.permanent_session_lifetime = timedelta(hours=4)

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}"
}

# -------------------------
# صفحة تسجيل الدخول
# -------------------------
@app.route('/', methods=['GET', 'POST'])
def login_page():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        password = request.form.get('password', '')

        if not name or not password:
            return render_template('login.html', error="يرجى إدخال الاسم وكلمة المرور.")

        try:
            r = requests.get(
                f"{SUPABASE_URL}/rest/v1/students?name=eq.{name}",
                headers=HEADERS
            )
            r.raise_for_status()
            students = r.json()
        except Exception as e:
            return render_template('login.html', error=f"خطأ في الاتصال بقاعدة البيانات: {e}")

        if not students:
            return render_template('login.html', error="اسم أو كلمة مرور خاطئة")

        student = students[0]
        if student['password'] != password:
            return render_template('login.html', error="اسم أو كلمة مرور خاطئة")

        session.permanent = True
        session['student_id'] = student['id']
        return redirect(url_for('dashboard'))

    return render_template('login.html')

# -------------------------
# لوحة الدرجات
# -------------------------
@app.route('/dashboard')
def dashboard():
    student_id = session.get('student_id')
    if not student_id:
        return redirect(url_for('login_page'))

    try:
        r = requests.get(
            f"{SUPABASE_URL}/rest/v1/grades?student_id=eq.{student_id}",
            headers=HEADERS
        )
        r.raise_for_status()
        grades = r.json()
    except Exception as e:
        return f"خطأ في جلب البيانات: {e}"

    return render_template('dashboard.html', grades=grades)

# -------------------------
# تشغيل التطبيق
# -------------------------
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
