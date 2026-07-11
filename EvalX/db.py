import sqlite3

def init_db():
    conn = sqlite3.connect('exam.db')
    cursor = conn.cursor()

    # ---------------- USERS ----------------
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL
        )
    ''')

    # ---------------- EXAMS ----------------
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS exams (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            subject TEXT,
            duration INTEGER,
            start_time TEXT,
            end_time TEXT,
            created_by INTEGER
        )
    ''')

    # ---------------- QUESTIONS ----------------
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            exam_id INTEGER,
            question TEXT,
            option1 TEXT,
            option2 TEXT,
            option3 TEXT,
            option4 TEXT,
            correct_answer TEXT
        )
    ''')

    # ---------------- RESULTS ----------------
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER,
            exam_id INTEGER,
            score INTEGER,
            status TEXT,
            released INTEGER DEFAULT 0
        )
    ''')

    # ---------------- VIOLATIONS ----------------
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS violations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER,
            exam_id INTEGER,
            type TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # ---------------- SNAPSHOTS ----------------
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS snapshots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER,
            exam_id INTEGER,
            image_path TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # ---------------- CLEAN RESET ----------------
    cursor.execute("DELETE FROM exams")
    cursor.execute("DELETE FROM questions")
    cursor.execute("DELETE FROM results")

    # ---------------- DEFAULT USERS (FIXED 🔥) ----------------

    # ADMIN (force create/update)
    cursor.execute("""
    INSERT OR REPLACE INTO users (id, username, password, role)
    VALUES (
        (SELECT id FROM users WHERE username='admin1'),
        'admin1', '123', 'admin'
    )
    """)

    # STAFF (force create/update)
    cursor.execute("""
    INSERT OR REPLACE INTO users (id, username, password, role)
    VALUES (
        (SELECT id FROM users WHERE username='staff1'),
        'staff1', '123', 'staff'
    )
    """)

    # ---------------- INSERT EXAMS ----------------
    cursor.execute("""
        INSERT INTO exams (title, subject, duration, start_time, end_time, created_by)
        VALUES 
        ('Math Test','Math',30,'2026-03-25 17:30','2026-03-30 23:59',1),
        ('Science Quiz','Science',20,'2026-03-26 10:00','2026-03-28 18:00',1),
        ('Java Exam','Programming',45,'2026-03-27 09:00','2026-03-29 22:00',1)
    """)

    # ---------------- INSERT QUESTIONS ----------------
    exam_ids = cursor.execute("SELECT id FROM exams").fetchall()

    for exam in exam_ids:
        exam_id = exam[0]

        cursor.execute("""
            INSERT INTO questions VALUES (NULL, ?, 'What is 2+2?', '2','3','4','5','4')
        """, (exam_id,))

        cursor.execute("""
            INSERT INTO questions VALUES (NULL, ?, 'Which is correct?', 'A','B','C','D','A')
        """, (exam_id,))

    conn.commit()
    conn.close()

    print("✅ Database Ready (Users Fixed + No Errors)")


if __name__ == "__main__":
    init_db()