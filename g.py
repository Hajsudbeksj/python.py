from flask import Flask, request, jsonify
import mysql.connector

app = Flask(__name__)

# إعداد قاعدة البيانات
db_config = {
    'host': 'localhost',       # أو عنوان السيرفر
    'user': 'root',            # اسم المستخدم
    'password': 'yourpassword',
    'database': 'school'
}

def get_db_connection():
    return mysql.connector.connect(**db_config)

# API لتسجيل الدخول
@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    name = data.get('name')
    password = data.get('password')

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM students WHERE name=%s AND password=%s", (name, password))
    student = cursor.fetchone()
    conn.close()

    if student:
        return jsonify({"success": True, "student_id": student['id']})
    else:
        return jsonify({"success": False, "message": "اسم أو كلمة مرور خاطئة"})

# API لجلب الدرجات
@app.route('/api/grades/<int:student_id>', methods=['GET'])
def get_grades(student_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT subject, grade FROM grades WHERE student_id=%s", (student_id,))
    grades = cursor.fetchall()
    conn.close()
    return jsonify({"grades": grades})

if __name__ == '__main__':
    app.run(debug=True)
