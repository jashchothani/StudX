from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from collections import defaultdict
import random, time, os, smtplib, base64
from math import radians, cos, sin, asin, sqrt
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, date

app = Flask(__name__)
app.secret_key = 'studx_super_secret_key_2025'

# ── Email config (update with real SMTP) ──────────────────────────
SMTP_HOST   = 'smtp.gmail.com'
SMTP_PORT   = 587
SMTP_USER   = 'jashthakkar77@gmail.com'
SMTP_PASS   = 'cuiegdqjaesgakcg'
ATTENDANCE_THRESHOLD = 75  # percent

# ── Active QR tokens {token: expiry_timestamp} ────────────────────
active_qr_tokens = {}

# ── Active attendance sessions {session_id: {token, expiry, subject}} ─
active_att_sessions = {}

# =============================================================
# DATABASE INIT
# =============================================================
def get_db():
    conn = sqlite3.connect('studx.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()
    c.executescript('''
        CREATE TABLE IF NOT EXISTS staff_users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL,
            status TEXT DEFAULT 'pending',
            otp TEXT,
            otp_expiry INTEGER
        );

        CREATE TABLE IF NOT EXISTS student_users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            roll_no TEXT,
            semester TEXT,
            division TEXT,
            role TEXT DEFAULT 'Student',
            status TEXT DEFAULT 'pending',
            otp TEXT,
            otp_expiry INTEGER
        );

        CREATE TABLE IF NOT EXISTS parent_users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            student_id INTEGER,
            role TEXT DEFAULT 'Parent',
            status TEXT DEFAULT 'pending',
            otp TEXT,
            otp_expiry INTEGER
        );

        CREATE TABLE IF NOT EXISTS attendance_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            token TEXT UNIQUE NOT NULL,
            subject TEXT,
            teacher_id INTEGER,
            semester TEXT,
            division TEXT,
            started_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            expires_at INTEGER,
            closed INTEGER DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS attendance_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER,
            student_name TEXT,
            session_id INTEGER,
            token TEXT,
            method TEXT DEFAULT 'qr',
            log_date DATE DEFAULT (date('now')),
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS assignments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            subject TEXT,
            description TEXT,
            due_date DATE,
            max_marks INTEGER DEFAULT 100,
            teacher_id INTEGER,
            semester TEXT,
            division TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS assignment_submissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            assignment_id INTEGER,
            student_id INTEGER,
            file_name TEXT,
            notes TEXT,
            grade TEXT,
            feedback TEXT,
            submitted_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sender_id INTEGER,
            sender_type TEXT,
            receiver_id INTEGER,
            receiver_type TEXT,
            body TEXT,
            sent_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            is_read INTEGER DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS meetings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            host_id INTEGER,
            host_type TEXT,
            scheduled_at DATETIME,
            audience TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS email_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER,
            email TEXT,
            subject TEXT,
            sent_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
    ''')

    # Seed admin
    admin = c.execute("SELECT id FROM staff_users WHERE role='Admin'").fetchone()
    if not admin:
        c.execute(
            'INSERT INTO staff_users (name,email,password,role,status) VALUES (?,?,?,?,?)',
            ('System Admin', 'admin@studx.com', generate_password_hash('admin123'), 'Admin', 'approved')
        )

    conn.commit()
    conn.close()

init_db()

# =============================================================
# EMAIL HELPER
# =============================================================
def send_email(to_email, subject, html_body):
    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From']    = SMTP_USER
        msg['To']      = to_email
        msg.attach(MIMEText(html_body, 'html'))
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASS)
            server.sendmail(SMTP_USER, to_email, msg.as_string())
        return True
    except Exception as e:
        print(f"[EMAIL ERROR] {e}")
        return False

def attendance_alert_html(student_name, subject, percentage):
    return f"""
    <div style="font-family:sans-serif;max-width:500px;margin:0 auto;padding:24px;background:#f9fafb;border-radius:12px">
      <div style="background:#fff;border-radius:10px;padding:24px;border:1px solid #e5e7eb">
        <h2 style="color:#b91c1c;margin:0 0 12px">⚠ Low Attendance Alert — StudX</h2>
        <p>Dear <strong>{student_name}</strong>,</p>
        <p>Your attendance in <strong>{subject}</strong> is currently at <strong style="color:#b91c1c">{percentage}%</strong>, which is below the mandatory <strong>75%</strong> threshold.</p>
        <p>Please attend upcoming lectures to avoid debarment from exams.</p>
        <div style="background:#fef2f2;border-radius:8px;padding:14px;margin:16px 0;border:1px solid #fecaca">
          <strong>Action Required:</strong> Attend at least {max(0, round((75 * 50 - percentage * 50 / 100) / 25))} more lectures in {subject} to reach 75%.
        </div>
        <p style="color:#6b7280;font-size:0.85em">This is an automated weekly report from StudX Campus System — Bhagubhai Mafatlal Polytechnic.</p>
      </div>
    </div>"""

# =============================================================
# OTP HELPER
# =============================================================
def generate_otp():
    return str(random.randint(100000, 999999))

def send_otp_email(email, otp, name):
    html = f"""
    <div style="font-family:sans-serif;max-width:440px;margin:0 auto;padding:24px">
      <h2 style="color:#6d28d9">StudX — Verify Your Identity</h2>
      <p>Hi <strong>{name}</strong>, use the code below to log in:</p>
      <div style="font-size:2.5rem;font-weight:800;letter-spacing:10px;color:#1a1d2e;text-align:center;padding:20px;background:#f5f3ff;border-radius:12px;margin:16px 0">{otp}</div>
      <p style="color:#6b7280;font-size:0.85em">This code expires in 10 minutes. Do not share it with anyone.</p>
    </div>"""
    send_email(email, 'StudX — Your Login Code', html)

# =============================================================
# PUBLIC
# =============================================================
@app.route('/')
def index():
    return render_template('index.html')

# =============================================================
# REGISTER
# =============================================================
@app.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'POST':
        name     = request.form['name']
        email    = request.form['email']
        password = generate_password_hash(request.form['password'])
        role     = request.form['role']
        conn = get_db()
        c    = conn.cursor()
        try:
            if role == 'Student':
                c.execute('INSERT INTO student_users (name,email,password,role,semester,division) VALUES (?,?,?,?,?,?)',
                          (name, email, password, role,
                           request.form.get('semester','Sem-4'),
                           request.form.get('division','A')))
            elif role == 'Parent':
                student_email = request.form.get('student_email','')
                stu = c.execute('SELECT id FROM student_users WHERE email=?',(student_email,)).fetchone()
                c.execute('INSERT INTO parent_users (name,email,password,student_id) VALUES (?,?,?,?)',
                          (name, email, password, stu['id'] if stu else None))
            else:
                c.execute('INSERT INTO staff_users (name,email,password,role) VALUES (?,?,?,?)',
                          (name, email, password, role))
            conn.commit()
            flash('Registered! Awaiting admin approval.', 'info')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('Email already exists.', 'error')
        finally:
            conn.close()
    return render_template('register.html')

# =============================================================
# LOGIN + OTP
# =============================================================
@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        email  = request.form['email']
        pwd    = request.form['password']
        portal = request.form['portal']

        conn = get_db()
        c    = conn.cursor()

        if portal == 'student':
            user = c.execute('SELECT * FROM student_users WHERE email=?',(email,)).fetchone()
        elif portal == 'parent':
            user = c.execute('SELECT * FROM parent_users WHERE email=?',(email,)).fetchone()
        else:
            user = c.execute('SELECT * FROM staff_users WHERE email=?',(email,)).fetchone()
        conn.close()

        if user and check_password_hash(user['password'], pwd):
            if user['status'] == 'pending':
                flash('Account pending approval.','warning')
                return redirect(url_for('login'))
            # Generate & send OTP
            otp     = generate_otp()
            expiry  = int(time.time()) + 600
            conn2   = get_db()
            tbl     = 'student_users' if portal=='student' else ('parent_users' if portal=='parent' else 'staff_users')
            conn2.execute(f'UPDATE {tbl} SET otp=?,otp_expiry=? WHERE id=?',(otp, expiry, user['id']))
            conn2.commit(); conn2.close()
            send_otp_email(email, otp, user['name'])
            session['otp_pending'] = {'id':user['id'],'name':user['name'],'role':user['role'] if 'role' in user.keys() else portal,'portal':portal}
            flash(f'OTP sent to {email}','info')
            return redirect(url_for('verify_otp'))
        flash('Invalid credentials.','error')
    return render_template('login.html')

@app.route('/verify-otp', methods=['GET','POST'])
def verify_otp():
    if 'otp_pending' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        entered = request.form['otp']
        info    = session['otp_pending']
        portal  = info['portal']
        tbl     = 'student_users' if portal=='student' else ('parent_users' if portal=='parent' else 'staff_users')
        conn = get_db()
        user = conn.execute(f'SELECT * FROM {tbl} WHERE id=?',(info['id'],)).fetchone()
        conn.close()
        # Convert the expiry to an int before comparing
        if user and user['otp'] == entered and int(time.time()) < int(user['otp_expiry'] or 0):
            session.pop('otp_pending', None)
            session['user_id'] = user['id']
            session['name']    = user['name']
            session['role']    = info['role']
            session['portal']  = portal
            if portal == 'staff':
                return redirect(url_for('dashboard') if info['role']=='Admin' else url_for('teacher_dashboard'))
            elif portal == 'parent':
                return redirect(url_for('parent_dashboard'))
            return redirect(url_for('student_dashboard'))
        flash('Invalid or expired OTP.','error')
    return render_template('verify_otp.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out.','info')
    return redirect(url_for('login'))

# =============================================================
# DASHBOARDS
# =============================================================
@app.route('/student')
def student_dashboard():
    if session.get('portal') != 'student':
        return redirect(url_for('login'))
    conn = get_db()
    # Assignments
    assignments = conn.execute('SELECT * FROM assignments ORDER BY due_date ASC LIMIT 10').fetchall()
    # Attendance summary per subject
    # Use 'timestamp' because 'log_date' does not exist in your table
    logs = conn.execute(
        "SELECT * FROM attendance_logs WHERE student_name=? ORDER BY timestamp DESC", 
        (session['name'],)
    ).fetchall()
    conn.close()
    return render_template('student_dashboard.html', student_name=session['name'],
                           assignments=assignments, logs=logs)

@app.route('/teacher')
def teacher_dashboard():
    if session.get('portal') != 'staff' or session.get('role') == 'Admin':
        return redirect(url_for('login'))
    conn = get_db()
    assignments = conn.execute('SELECT * FROM assignments WHERE teacher_id=? ORDER BY created_at DESC',(session['user_id'],)).fetchall()
    today_logs  = conn.execute(
        "SELECT a.student_name, a.method, a.timestamp FROM attendance_logs a WHERE date(a.timestamp)=date('now') ORDER BY a.timestamp DESC"
    ).fetchall()
    conn.close()
    return render_template('teacher_dashboard.html', teacher_name=session['name'],
                           assignments=assignments, today_logs=today_logs)

@app.route('/parent')
def parent_dashboard():
    if session.get('portal') != 'parent':
        return redirect(url_for('login'))
    conn = get_db()
    parent = conn.execute('SELECT * FROM parent_users WHERE id=?',(session['user_id'],)).fetchone()
    child  = conn.execute('SELECT * FROM student_users WHERE id=?',(parent['student_id'],)).fetchone() if parent and parent['student_id'] else None
    logs   = []
    assignments = []
    if child:
        logs        = conn.execute('SELECT * FROM attendance_logs WHERE student_id=? ORDER BY timestamp DESC LIMIT 30',(child['id'],)).fetchall()
        assignments = conn.execute('SELECT * FROM assignments ORDER BY due_date ASC LIMIT 10').fetchall()
    conn.close()
    return render_template('parent_dashboard.html', parent_name=session['name'],
                           child=child, logs=logs, assignments=assignments)

@app.route('/admin')
def dashboard():
    if session.get('portal') != 'staff' or session.get('role') != 'Admin':
        return redirect(url_for('login'))
    conn = get_db()
    pending_students = [dict(r)|{'user_type':'student'} for r in conn.execute("SELECT * FROM student_users WHERE status='pending'").fetchall()]
    pending_staff    = [dict(r)|{'user_type':'staff'}   for r in conn.execute("SELECT * FROM staff_users WHERE status='pending'").fetchall()]
    pending_parents  = [dict(r)|{'user_type':'parent'}  for r in conn.execute("SELECT * FROM parent_users WHERE status='pending'").fetchall()]
    all_students     = conn.execute('SELECT * FROM student_users ORDER BY name').fetchall()
    conn.close()
    return render_template('admin_dashboard.html',
                           pending_users=pending_students+pending_staff+pending_parents,
                           all_students=all_students,
                           admin_name=session['name'])

# =============================================================
# ADMIN ACTIONS
# =============================================================
@app.route('/admin/approve/<user_type>/<int:uid>')
def approve_user(user_type, uid):
    if session.get('role') != 'Admin': return redirect(url_for('login'))
    tbl = {'student':'student_users','staff':'staff_users','parent':'parent_users'}.get(user_type,'staff_users')
    conn = get_db(); conn.execute(f"UPDATE {tbl} SET status='approved' WHERE id=?",(uid,)); conn.commit(); conn.close()
    return redirect(url_for('dashboard'))

@app.route('/admin/approve_all')
def approve_all():
    if session.get('role') != 'Admin': return redirect(url_for('login'))
    conn = get_db()
    for tbl in ['student_users','staff_users','parent_users']:
        conn.execute(f"UPDATE {tbl} SET status='approved' WHERE status='pending'")
    conn.commit(); conn.close()
    return redirect(url_for('dashboard'))

@app.route('/admin/delete/<user_type>/<int:uid>')
def delete_user(user_type, uid):
    if session.get('role') != 'Admin': return redirect(url_for('login'))
    tbl = {'student':'student_users','staff':'staff_users','parent':'parent_users'}.get(user_type)
    if tbl:
        conn = get_db(); conn.execute(f'DELETE FROM {tbl} WHERE id=?',(uid,)); conn.commit(); conn.close()
    return redirect(url_for('dashboard'))

# =============================================================
# ATTENDANCE API
# =============================================================
@app.route('/api/start_attendance', methods=['POST'])
def start_attendance():
    subject = request.json.get('subject')
    token = generate_otp() # or however you make yours
    
    conn = get_db()
    try:
        # Close any other active sessions first
        conn.execute('UPDATE attendance_sessions SET is_active = 0')
        expiry_time = int(time.time()) + 120
        # Insert the new session
        conn.execute('INSERT INTO attendance_sessions (token, subject, is_active) VALUES (?, ?, ?)', 
                     (token, subject, 1))
        
        conn.commit() # This is where it usually locks if another process is open
        return jsonify({"status": "ok", "token": token})
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"status": "error"}), 500
    finally:
        conn.close() # CRITICAL: Always close the connection

@app.route('/api/refresh_qr', methods=['POST'])
def refresh_qr():
    if session.get('portal') != 'staff':
        return jsonify({'status':'error'}), 403
    data     = request.json or {}
    sess_tok = data.get('session_token')
    conn = get_db()
    sess = conn.execute('SELECT * FROM attendance_sessions WHERE token=? AND closed=0',(sess_tok,)).fetchone()
    if not sess or int(time.time()) > (sess['expires_at'] or 0):
        conn.close()
        return jsonify({'status':'expired'})
    new_tok = f"STUDX-{random.randint(100000,999999)}-{int(time.time())}"
    active_qr_tokens[new_tok] = sess['expires_at']
    conn.close()
    return jsonify({'status':'ok','token':new_tok})

@app.route('/api/close_session', methods=['POST'])
def close_session():
    if session.get('portal') != 'staff':
        return jsonify({'status':'error'}), 403
    token = (request.json or {}).get('session_token')
    conn  = get_db()
    conn.execute("UPDATE attendance_sessions SET closed=1 WHERE token=?",(token,))
    conn.commit()
    # Get attendance list for approval
    sess = conn.execute('SELECT * FROM attendance_sessions WHERE token=?',(token,)).fetchone()
    logs = []
    if sess:
        # Instead of session_id, we fetch recent logs for this session
        logs = conn.execute('SELECT * FROM attendance_logs ORDER BY timestamp DESC LIMIT 100').fetchall()
    conn.close()
    if token in active_qr_tokens: del active_qr_tokens[token]
    return jsonify({'status':'ok','attendance':[dict(l) for l in logs]})

@app.route('/api/mark_attendance', methods=['POST'])
def mark_attendance():
    if session.get('portal') != 'student':
        return jsonify({'status':'error','msg':'Unauthorized'}), 403
    data   = request.json or {}
    token  = data.get('token')
    method = data.get('method','qr')
    student_id   = session['user_id']
    student_name = session['name']

    if token not in active_qr_tokens or time.time() > active_qr_tokens[token]:
        return jsonify({'status':'error','msg':'QR expired or invalid'}), 400

    conn = get_db()
    sess = conn.execute('SELECT * FROM attendance_sessions WHERE token=? AND closed=0',(token,)).fetchone()
    if not sess:
        conn.close()
        return jsonify({'status':'error','msg':'Session closed'}), 400

    dup = conn.execute('SELECT id FROM attendance_logs WHERE student_id=? AND session_id=?',(student_id, sess['id'])).fetchone()
    if dup:
        conn.close()
        return jsonify({'status':'error','msg':'Already marked'}), 400

    conn.execute('INSERT INTO attendance_logs (student_id,student_name,session_id,token,method) VALUES (?,?,?,?,?)',
                 (student_id, student_name, sess['id'], token, method))
    conn.commit(); conn.close()
    return jsonify({'status':'success','msg':'Attendance marked ✓'})

@app.route('/api/save_attendance', methods=['POST'])
def save_attendance():
    """Teacher approves the final list and saves."""
    if session.get('portal') != 'staff':
        return jsonify({'status':'error'}), 403
    data      = request.json or {}
    records   = data.get('records', [])   # [{student_id, present}]
    session_id= data.get('session_id')
    conn = get_db()
    # Update any manual overrides
    for r in records:
        if not r.get('present'):
            conn.execute('DELETE FROM attendance_logs WHERE student_id=? AND session_id=?',(r['student_id'],session_id))
    conn.commit()

    # Send email to low-attendance students (async would be better in prod)
    students = conn.execute('SELECT * FROM student_users WHERE status="approved"').fetchall()
    for stu in students:
        total_sessions = conn.execute('SELECT COUNT(*) FROM attendance_sessions WHERE closed=1').fetchone()[0]
        present        = conn.execute('SELECT COUNT(*) FROM attendance_logs WHERE student_id=?',(stu['id'],)).fetchone()[0]
        pct = round(present/total_sessions*100) if total_sessions else 100
        if pct < ATTENDANCE_THRESHOLD:
            html = attendance_alert_html(stu['name'], 'Overall', pct)
            if send_email(stu['email'], f'⚠ Low Attendance Alert — StudX', html):
                conn.execute('INSERT INTO email_log (student_id,email,subject) VALUES (?,?,?)',
                             (stu['id'], stu['email'], 'Low Attendance Alert'))
    conn.commit(); conn.close()
    return jsonify({'status':'ok','msg':'Attendance saved and emails sent.'})

@app.route('/api/attendance_log')
def attendance_log():
    if session.get('portal') != 'staff':
        return jsonify({'status':'error'}), 403
    conn = get_db()
    rows = conn.execute(
        'SELECT student_name,method,timestamp FROM attendance_logs ORDER BY timestamp DESC LIMIT 60'
    ).fetchall()
    conn.close()
    return jsonify({'students':[dict(r) for r in rows]})

@app.route('/api/student_attendance')
def student_attendance():
    if session.get('portal') != 'student':
        return jsonify({'status':'error'}), 403
    conn  = get_db()
    total = conn.execute('SELECT COUNT(*) FROM attendance_sessions WHERE closed=1').fetchone()[0]
    pres  = conn.execute('SELECT COUNT(*) FROM attendance_logs WHERE student_id=?',(session['user_id'],)).fetchone()[0]
    logs  = conn.execute(
        'SELECT l.log_date, s.subject, l.method FROM attendance_logs l LEFT JOIN attendance_sessions s ON l.session_id=s.id WHERE l.student_id=? ORDER BY l.timestamp DESC',
        (session['user_id'],)
    ).fetchall()
    conn.close()
    pct = round(pres/total*100) if total else 0
    return jsonify({'total':total,'present':pres,'pct':pct,'logs':[dict(r) for r in logs]})

# =============================================================
# ASSIGNMENTS API
# =============================================================
@app.route('/api/create_assignment', methods=['POST'])
def create_assignment():
    if session.get('portal') != 'staff':
        return jsonify({'status':'error'}), 403
    d = request.json or {}
    conn = get_db()
    conn.execute('INSERT INTO assignments (title,subject,description,due_date,max_marks,teacher_id,semester,division) VALUES (?,?,?,?,?,?,?,?)',
                 (d.get('title'), d.get('subject'), d.get('description'),
                  d.get('due_date'), d.get('max_marks',100),
                  session['user_id'], d.get('semester','Sem-4'), d.get('division','A')))
    conn.commit(); conn.close()
    return jsonify({'status':'ok'})

@app.route('/api/submit_assignment', methods=['POST'])
def submit_assignment():
    if session.get('portal') != 'student':
        return jsonify({'status':'error'}), 403
    d = request.json or {}
    conn = get_db()
    conn.execute('INSERT INTO assignment_submissions (assignment_id,student_id,notes) VALUES (?,?,?)',
                 (d.get('assignment_id'), session['user_id'], d.get('notes','')))
    conn.commit(); conn.close()
    return jsonify({'status':'ok'})

@app.route('/api/grade_submission', methods=['POST'])
def grade_submission():
    if session.get('portal') != 'staff':
        return jsonify({'status':'error'}), 403
    d = request.json or {}
    conn = get_db()
    conn.execute('UPDATE assignment_submissions SET grade=?,feedback=? WHERE id=?',
                 (d.get('grade'), d.get('feedback'), d.get('submission_id')))
    conn.commit(); conn.close()
    return jsonify({'status':'ok'})

@app.route('/api/assignments')
def get_assignments():
    conn  = get_db()
    rows  = conn.execute('SELECT * FROM assignments ORDER BY due_date ASC').fetchall()
    conn.close()
    return jsonify({'assignments':[dict(r) for r in rows]})

# =============================================================
# MESSAGES API
# =============================================================
@app.route('/api/send_message', methods=['POST'])
def send_message():
    d = request.json or {}
    conn = get_db()
    conn.execute('INSERT INTO messages (sender_id,sender_type,receiver_id,receiver_type,body) VALUES (?,?,?,?,?)',
                 (session.get('user_id'), session.get('portal'),
                  d.get('receiver_id'), d.get('receiver_type'), d.get('body','')))
    conn.commit(); conn.close()
    return jsonify({'status':'ok'})

@app.route('/api/messages/<int:other_id>')
def get_messages(other_id):
    uid = session.get('user_id')
    conn = get_db()
    rows = conn.execute(
        'SELECT * FROM messages WHERE (sender_id=? AND receiver_id=?) OR (sender_id=? AND receiver_id=?) ORDER BY sent_at ASC',
        (uid,other_id,other_id,uid)
    ).fetchall()
    conn.close()
    return jsonify({'messages':[dict(r) for r in rows]})

# =============================================================
# MEETINGS API
# =============================================================
@app.route('/api/create_meeting', methods=['POST'])
def create_meeting():
    if session.get('portal') != 'staff':
        return jsonify({'status':'error'}), 403
    d = request.json or {}
    conn = get_db()
    conn.execute('INSERT INTO meetings (title,host_id,host_type,scheduled_at,audience) VALUES (?,?,?,?,?)',
                 (d.get('title'), session['user_id'], session['portal'],
                  d.get('scheduled_at'), d.get('audience','all')))
    conn.commit(); conn.close()
    return jsonify({'status':'ok'})

@app.route('/api/meetings')
def get_meetings():
    conn = get_db()
    rows = conn.execute('SELECT * FROM meetings ORDER BY scheduled_at ASC').fetchall()
    conn.close()
    return jsonify({'meetings':[dict(r) for r in rows]})

# =============================================================
# WEEKLY EMAIL REPORT (call via cron or admin trigger)
# =============================================================
@app.route('/api/send_weekly_reports')
def send_weekly_reports():
    if session.get('role') != 'Admin':
        return jsonify({'status':'error'}), 403
    conn     = get_db()
    students = conn.execute('SELECT * FROM student_users WHERE status="approved"').fetchall()
    total    = conn.execute('SELECT COUNT(*) FROM attendance_sessions WHERE closed=1').fetchone()[0]
    sent     = 0
    for stu in students:
        pres = conn.execute('SELECT COUNT(*) FROM attendance_logs WHERE student_id=?',(stu['id'],)).fetchone()[0]
        pct  = round(pres/total*100) if total else 100
        if pct < ATTENDANCE_THRESHOLD:
            html = attendance_alert_html(stu['name'], 'Overall', pct)
            if send_email(stu['email'], '⚠ Weekly Attendance Alert — StudX', html):
                conn.execute('INSERT INTO email_log (student_id,email,subject) VALUES (?,?,?)',
                             (stu['id'], stu['email'], 'Weekly Low Attendance'))
                sent += 1
    conn.commit(); conn.close()
    return jsonify({'status':'ok','emails_sent':sent})

# =============================================================
# RESET
# =============================================================
@app.route('/reset-db')
def reset_db():
    if os.path.exists('studx.db'):
        os.remove('studx.db')
    init_db()
    return "<h3>✅ DB reset. <a href='/login'>Login</a></h3>"
@app.route('/api/check_session')
def check_session():
    conn = get_db()
    # Find the most recent active session
    session = conn.execute('SELECT * FROM attendance_sessions WHERE is_active = 1 LIMIT 1').fetchone()
    conn.close()
    
    if session:
        return jsonify({"status": "open", "token": session['token']})
    else:
        return jsonify({"status": "locked"})
if __name__ == '__main__':
    app.run(debug=True, port=5000)