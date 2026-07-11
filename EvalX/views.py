from datetime import datetime, timedelta
from flask import render_template, request, redirect, session
import sqlite3
import os
from EvalX import app


# ---------------- DATABASE ----------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def get_db_connection():
    db_path = os.path.join(BASE_DIR, 'exam.db')
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


# ---------------- DATETIME FIX ----------------
def parse_datetime(dt):
    if not dt:
        return None

    formats = [
        "%Y-%m-%d %H:%M",
        "%Y-%m-%dT%H:%M",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%dT%H:%M:%S"
    ]

    for fmt in formats:
        try:
            return datetime.strptime(dt, fmt)
        except:
            continue

    return None


# ---------------- LOGIN ----------------
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        conn = get_db_connection()

        user = conn.execute(
            "SELECT * FROM users WHERE username=? AND password=?",
            (username, password)
        ).fetchone()

        conn.close()

        if user:
            session['user_id'] = user['id']
            session['role'] = user['role']

            return redirect(f"/{user['role']}")

        return render_template('login.html', message="Invalid credentials")

    return render_template('login.html')


# ---------------- REGISTER ----------------
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        conn = get_db_connection()

        existing = conn.execute(
            "SELECT * FROM users WHERE username=?",
            (username,)
        ).fetchone()

        if existing:
            conn.close()
            return render_template('register.html', message="Username exists")

        conn.execute(
            "INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
            (username, password, 'student')
        )

        conn.commit()
        conn.close()

        return redirect('/')

    return render_template('register.html')


# ---------------- STUDENT DASHBOARD ----------------
@app.route('/student')
def student_dashboard():
    if session.get('role') != 'student':
        return redirect('/')

    conn = get_db_connection()
    exams = conn.execute("SELECT * FROM exams").fetchall()

    updated_exams = []

    for exam in exams:
        now = datetime.now()

        attempted = conn.execute(
            "SELECT * FROM results WHERE student_id=? AND exam_id=?",
            (session['user_id'], exam['id'])
        ).fetchone()

        if attempted:
            status = "Attempted"

        else:
            start = parse_datetime(exam['start_time'])
            end = parse_datetime(exam['end_time'])

            if start and end:
                if now < start:
                    status = "Upcoming"
                elif now > end:
                    status = "Expired"
                else:
                    status = "Active"
            else:
                status = "No Schedule"

        exam_dict = dict(exam)
        exam_dict['status'] = status
        updated_exams.append(exam_dict)

    conn.close()
    return render_template('student.html', exams=updated_exams)


# ---------------- START EXAM ----------------
@app.route('/start_exam/<int:exam_id>')
def start_exam(exam_id):
    if session.get('role') != 'student':
        return redirect('/')

    conn = get_db_connection()

    exam = conn.execute(
        "SELECT * FROM exams WHERE id=?",
        (exam_id,)
    ).fetchone()

    questions = conn.execute(
        "SELECT * FROM questions WHERE exam_id=?",
        (exam_id,)
    ).fetchall()

    conn.close()

    # ✅ Timer fix (based on duration)
    end_time = datetime.now() + timedelta(minutes=exam['duration'])

    return render_template(
        'exam.html',
        questions=questions,
        exam_id=exam_id,
        end_time=end_time.strftime("%Y-%m-%d %H:%M:%S")
    )


# ---------------- SUBMIT EXAM ----------------
@app.route('/submit_exam/<int:exam_id>', methods=['POST'])
def submit_exam(exam_id):
    if session.get('role') != 'student':
        return redirect('/')

    conn = get_db_connection()

    questions = conn.execute(
        "SELECT * FROM questions WHERE exam_id=?",
        (exam_id,)
    ).fetchall()

    violations = int(request.form.get('violations', 0))

    score = 0

    for q in questions:
        selected = request.form.get(f"q{q['id']}")
        if selected == q['correct_answer']:
            score += 1

    if violations >= 5:
        status = "Malpractice"
        score = 0
    else:
        status = "Completed"

    conn.execute(
        "INSERT INTO results (student_id, exam_id, score, status, released) VALUES (?, ?, ?, ?, 0)",
        (session['user_id'], exam_id, score, status)
    )

    conn.commit()
    conn.close()

    return redirect('/student')


# ---------------- LOG VIOLATION ----------------
@app.route('/log_violation', methods=['POST'])
def log_violation():
    print("Violation:", request.form.get('type'))
    return "OK"


# ---------------- STUDENT RESULTS ----------------
@app.route('/results')
def student_results():
    if session.get('role') != 'student':
        return redirect('/')

    conn = get_db_connection()

    results = conn.execute("""
        SELECT exams.title, exams.subject, exams.duration,
               results.score, results.status, results.released
        FROM results
        JOIN exams ON exams.id = results.exam_id
        WHERE results.student_id=?
    """, (session['user_id'],)).fetchall()

    conn.close()

    return render_template('results.html', results=results)


# ---------------- STAFF ----------------
@app.route('/staff')
def staff_dashboard():
    if session.get('role') != 'staff':
        return redirect('/')

    conn = get_db_connection()
    exams = conn.execute("SELECT * FROM exams").fetchall()
    conn.close()

    return render_template('staff.html', exams=exams)


# ---------------- ADD EXAM ----------------
@app.route('/addexam', methods=['GET', 'POST'])
def add_exam():
    if session.get('role') != 'staff':
        return redirect('/')

    conn = get_db_connection()

    if request.method == 'POST':
        conn.execute("""
            INSERT INTO exams (title, subject, duration, start_time, end_time)
            VALUES (?, ?, ?, ?, ?)
        """, (
            request.form.get('title'),
            request.form.get('subject'),
            request.form.get('duration'),
            request.form.get('start_time'),
            request.form.get('end_time')
        ))

        conn.commit()
        conn.close()
        return redirect('/staff')

    conn.close()
    return render_template('addexam.html')


# ---------------- ADD QUESTION ----------------
@app.route('/add_question/<int:exam_id>', methods=['GET', 'POST'])
def add_question(exam_id):
    if session.get('role') != 'staff':
        return redirect('/')

    conn = get_db_connection()

    if request.method == 'POST':
        option1 = request.form.get('option1')
        option2 = request.form.get('option2')
        option3 = request.form.get('option3')
        option4 = request.form.get('option4')

        correct_key = request.form.get('correct')

        correct_value = {
            "option1": option1,
            "option2": option2,
            "option3": option3,
            "option4": option4
        }.get(correct_key)

        conn.execute("""
            INSERT INTO questions 
            (exam_id, question, option1, option2, option3, option4, correct_answer)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            exam_id,
            request.form.get('question'),
            option1,
            option2,
            option3,
            option4,
            correct_value
        ))

        conn.commit()

    questions = conn.execute(
        "SELECT * FROM questions WHERE exam_id=?",
        (exam_id,)
    ).fetchall()

    conn.close()

    return render_template('add_question.html', questions=questions, exam_id=exam_id)


# ---------------- DELETE QUESTION ----------------
@app.route('/delete_question/<int:q_id>/<int:exam_id>')
def delete_question(q_id, exam_id):
    if session.get('role') != 'staff':
        return redirect('/')

    conn = get_db_connection()
    conn.execute("DELETE FROM questions WHERE id=?", (q_id,))
    conn.commit()
    conn.close()

    return redirect(f'/add_question/{exam_id}')


# ---------------- DELETE EXAM ----------------
@app.route('/delete_exam/<int:exam_id>')
def delete_exam(exam_id):
    if session.get('role') != 'staff':
        return redirect('/')

    conn = get_db_connection()

    conn.execute("DELETE FROM questions WHERE exam_id=?", (exam_id,))
    conn.execute("DELETE FROM results WHERE exam_id=?", (exam_id,))
    conn.execute("DELETE FROM exams WHERE id=?", (exam_id,))

    conn.commit()
    conn.close()

    return redirect('/staff')


# ---------------- STAFF ATTEMPTS ----------------
@app.route('/staff/attempts/<int:exam_id>')
def staff_attempts(exam_id):
    if session.get('role') != 'staff':
        return redirect('/')

    conn = get_db_connection()

    attempts = conn.execute("""
        SELECT users.username, results.score, results.status,
               results.released, results.id as result_id
        FROM results
        JOIN users ON users.id = results.student_id
        WHERE results.exam_id=?
    """, (exam_id,)).fetchall()

    conn.close()

    return render_template('attempts.html', attempts=attempts)


# ---------------- RELEASE RESULT ----------------
@app.route('/release_result/<int:result_id>')
def release_result(result_id):
    if session.get('role') != 'staff':
        return redirect('/')

    conn = get_db_connection()

    conn.execute(
        "UPDATE results SET released=1 WHERE id=?",
        (result_id,)
    )

    conn.commit()
    conn.close()

    return redirect(request.referrer)


# ---------------- ADMIN ----------------
@app.route('/admin')
def admin():
    if session.get('role') != 'admin':
        return redirect('/')

    conn = get_db_connection()
    users = conn.execute("SELECT * FROM users").fetchall()
    conn.close()

    return render_template('admin.html', users=users)


# ---------------- DELETE USER ----------------
@app.route('/delete_user/<int:user_id>')
def delete_user(user_id):
    if session.get('role') != 'admin':
        return redirect('/')

    conn = get_db_connection()
    conn.execute("DELETE FROM users WHERE id=?", (user_id,))
    conn.commit()
    conn.close()

    return redirect('/admin')





# ---------------- LOGOUT ----------------
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')