import os, random, time, smtplib, base64, re
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, date
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'studx_super_secret_key_2025')

# ── Email config ──────────────────────────────────────────────
SMTP_HOST            = os.environ.get('SMTP_HOST', 'smtp.gmail.com')
SMTP_PORT            = int(os.environ.get('SMTP_PORT', 587))
SMTP_USER            = os.environ.get('SMTP_USER', '')
SMTP_PASS            = os.environ.get('SMTP_PASS', '')
ATTENDANCE_THRESHOLD = int(os.environ.get('ATTENDANCE_THRESHOLD', 75))
GEMINI_API_KEY       = os.environ.get('GEMINI_API_KEY', '')

# ── Allowed email domains ─────────────────────────────────────
ALLOWED_EMAIL_REGEX = re.compile(
    r'^[a-zA-Z0-9._%+\-]+@(gmail\.com|svkmmumbai\.onmicrosoft\.com)$',
    re.IGNORECASE
)

# ── Active QR tokens {token: expiry_timestamp} ────────────────
active_qr_tokens = {}

# =============================================================
# DATABASE
# =============================================================
def get_db():
   conn = sqlite3.connect('studx.db', check_same_thread=False)
   conn.row_factory = sqlite3.Row
   conn.execute("PRAGMA journal_mode=WAL")
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
            token TEXT NOT NULL,
            qr_token TEXT,
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
            subject TEXT,
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
            ('System Admin', 'admin@gmail.com',
             generate_password_hash('admin123'), 'Admin', 'approved')
        )
    conn.commit()
    conn.close()

init_db()

# =============================================================
# EMAIL HELPER
# =============================================================
def send_email(to_email, subject, html_body):
    if not SMTP_USER or not SMTP_PASS:
        print(f"[EMAIL SKIP] No SMTP configured. To: {to_email} | Subject: {subject}")
        return False
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
        <p>Your attendance in <strong>{subject}</strong> is currently at
           <strong style="color:#b91c1c">{percentage}%</strong>,
           below the mandatory <strong>75%</strong> threshold.</p>
        <p>Please attend upcoming lectures to avoid debarment from exams.</p>
        <p style="color:#6b7280;font-size:0.85em">Automated report — StudX Campus System.</p>
      </div>
    </div>"""

def otp_email_html(name, otp):
    return f"""
    <div style="font-family:sans-serif;max-width:440px;margin:0 auto;padding:24px">
      <h2 style="color:#6d28d9">StudX — Verify Your Identity</h2>
      <p>Hi <strong>{name}</strong>, use the code below:</p>
      <div style="font-size:2.5rem;font-weight:800;letter-spacing:10px;color:#1a1d2e;
                  text-align:center;padding:20px;background:#f5f3ff;border-radius:12px;
                  margin:16px 0">{otp}</div>
      <p style="color:#6b7280;font-size:0.85em">Expires in 10 minutes. Do not share.</p>
    </div>"""

# =============================================================
# HELPERS
# =============================================================
def generate_otp():
    return str(random.randint(100000, 999999))

def send_otp_email(email, otp, name):
    send_email(email, 'StudX — Your Login Code', otp_email_html(name, otp))

def store_otp(tbl, uid, otp):
    expiry = int(time.time()) + 600
    conn = get_db()
    conn.execute(f'UPDATE {tbl} SET otp=?,otp_expiry=? WHERE id=?', (otp, expiry, uid))
    conn.commit()
    conn.close()

def portal_table(portal):
    return {'student': 'student_users',
            'parent':  'parent_users',
            'staff':   'staff_users'}.get(portal, 'staff_users')

# =============================================================
# PUBLIC
# =============================================================
@app.route('/')
def index():
    return render_template('index.html')

# =============================================================
# REGISTER
# =============================================================
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name     = request.form['name'].strip()
        email    = request.form['email'].strip().lower()
        password = generate_password_hash(request.form['password'])
        role     = request.form['role']

        if not ALLOWED_EMAIL_REGEX.match(email):
            flash('Only @gmail.com or @svkmmumbai.onmicrosoft.com emails are allowed.', 'error')
            return render_template('register.html')

        conn = get_db()
        c    = conn.cursor()
        try:
            if role == 'Student':
                c.execute(
                    'INSERT INTO student_users (name,email,password,role,semester,division) VALUES (?,?,?,?,?,?)',
                    (name, email, password, role,
                     request.form.get('semester', 'Sem-4'),
                     request.form.get('division', 'A'))
                )
            elif role == 'Parent':
                student_email = request.form.get('student_email', '').strip().lower()
                stu = c.execute('SELECT id FROM student_users WHERE email=?', (student_email,)).fetchone()
                c.execute('INSERT INTO parent_users (name,email,password,student_id) VALUES (?,?,?,?)',
                          (name, email, password, stu['id'] if stu else None))
            else:
                c.execute('INSERT INTO staff_users (name,email,password,role) VALUES (?,?,?,?)',
                          (name, email, password, role))
            conn.commit()
            flash('Registered! Awaiting admin approval.', 'info')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('Email already registered.', 'error')
        finally:
            conn.close()
    return render_template('register.html')

# =============================================================
# LOGIN + OTP
# =============================================================
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email  = request.form['email'].strip().lower()
        pwd    = request.form['password']
        portal = request.form['portal']

        conn = get_db()
        tbl  = portal_table(portal)
        user = conn.execute(f'SELECT * FROM {tbl} WHERE email=?', (email,)).fetchone()
        conn.close()

        if user and check_password_hash(user['password'], pwd):
            if user['status'] == 'pending':
                flash('Account pending admin approval.', 'warning')
                return redirect(url_for('login'))
            otp = generate_otp()
            store_otp(tbl, user['id'], otp)
            send_otp_email(email, otp, user['name'])
            session['otp_pending'] = {
                'id': user['id'], 'name': user['name'],
                'role': user['role'] if 'role' in user.keys() else portal,
                'portal': portal, 'email': email
            }
            flash(f'OTP sent to {email}', 'info')
            return redirect(url_for('verify_otp'))
        flash('Invalid credentials.', 'error')
    return render_template('login.html')

@app.route('/verify-otp', methods=['GET', 'POST'])
def verify_otp():
    if 'otp_pending' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        entered = request.form['otp'].strip()
        info    = session['otp_pending']
        portal  = info['portal']
        tbl     = portal_table(portal)
        conn    = get_db()
        user    = conn.execute(f'SELECT * FROM {tbl} WHERE id=?', (info['id'],)).fetchone()
        conn.close()
        if user and user['otp'] == entered and int(time.time()) < int(user['otp_expiry'] or 0):
            session.pop('otp_pending', None)
            session['user_id'] = user['id']
            session['name']    = user['name']
            session['role']    = info['role']
            session['portal']  = portal
            if portal == 'staff':
                return redirect(url_for('dashboard') if info['role'] == 'Admin' else url_for('teacher_dashboard'))
            elif portal == 'parent':
                return redirect(url_for('parent_dashboard'))
            return redirect(url_for('student_dashboard'))
        flash('Invalid or expired OTP.', 'error')
    return render_template('verify_otp.html')

@app.route('/resend-otp', methods=['POST'])
def resend_otp():
    info = session.get('otp_pending') or session.get('reset_pending')
    if not info:
        return jsonify({'status': 'error', 'msg': 'No pending session'}), 400
    tbl = portal_table(info['portal'])
    otp = generate_otp()
    store_otp(tbl, info['id'], otp)
    send_otp_email(info['email'], otp, info['name'])
    return jsonify({'status': 'ok', 'msg': 'OTP resent successfully'})

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out.', 'info')
    return redirect(url_for('login'))

# =============================================================
# FORGOT / RESET PASSWORD
# =============================================================
@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email  = request.form['email'].strip().lower()
        portal = request.form['portal']
        tbl    = portal_table(portal)
        conn   = get_db()
        user   = conn.execute(f'SELECT * FROM {tbl} WHERE email=?', (email,)).fetchone()
        conn.close()
        if not user:
            flash('No account found with that email.', 'error')
            return render_template('forgot_password.html')
        otp = generate_otp()
        store_otp(tbl, user['id'], otp)
        send_otp_email(email, otp, user['name'])
        session['reset_pending'] = {
            'id': user['id'], 'portal': portal,
            'email': email, 'name': user['name']
        }
        flash(f'Password reset OTP sent to {email}', 'info')
        return redirect(url_for('reset_password'))
    return render_template('forgot_password.html')

@app.route('/reset-password', methods=['GET', 'POST'])
def reset_password():
    if 'reset_pending' not in session:
        return redirect(url_for('forgot_password'))
    if request.method == 'POST':
        entered  = request.form['otp'].strip()
        new_pwd  = request.form['password'].strip()
        confirm  = request.form['confirm_password'].strip()
        if new_pwd != confirm:
            flash('Passwords do not match.', 'error')
            return render_template('reset_password.html')
        if len(new_pwd) < 6:
            flash('Password must be at least 6 characters.', 'error')
            return render_template('reset_password.html')
        info = session['reset_pending']
        tbl  = portal_table(info['portal'])
        conn = get_db()
        user = conn.execute(f'SELECT * FROM {tbl} WHERE id=?', (info['id'],)).fetchone()
        if not user or user['otp'] != entered or int(time.time()) >= int(user['otp_expiry'] or 0):
            conn.close()
            flash('Invalid or expired OTP.', 'error')
            return render_template('reset_password.html')
        conn.execute(f'UPDATE {tbl} SET password=?,otp=NULL,otp_expiry=NULL WHERE id=?',
                     (generate_password_hash(new_pwd), info['id']))
        conn.commit()
        conn.close()
        session.pop('reset_pending', None)
        session['user_id'] = user['id']
        session['name']    = user['name']
        session['portal']  = portal
        session['role']    = user['role'] if 'role' in user.keys() else portal
        flash('Password reset successfully! Welcome back.', 'success')
        if portal == 'staff':
            return redirect(url_for('dashboard') if user['role'] == 'Admin' else url_for('teacher_dashboard'))
        elif portal == 'parent':
            return redirect(url_for('parent_dashboard'))
        return redirect(url_for('student_dashboard'))
    return render_template('reset_password.html')

# =============================================================
# DASHBOARDS
# =============================================================
@app.route('/student')
def student_dashboard():
    if session.get('portal') != 'student':
        return redirect(url_for('login'))
    conn = get_db()
    assignments = conn.execute('SELECT * FROM assignments ORDER BY due_date ASC LIMIT 10').fetchall()
    logs = conn.execute(
        'SELECT * FROM attendance_logs WHERE student_id=? ORDER BY timestamp DESC',
        (session['user_id'],)
    ).fetchall()
    conn.close()
    return render_template('student_dashboard.html',
                           student_name=session['name'],
                           assignments=assignments, logs=logs)

@app.route('/teacher')
def teacher_dashboard():
    if session.get('portal') != 'staff' or session.get('role') == 'Admin':
        return redirect(url_for('login'))
    conn = get_db()
    assignments = conn.execute(
        'SELECT * FROM assignments WHERE teacher_id=? ORDER BY created_at DESC',
        (session['user_id'],)
    ).fetchall()
    today_logs = conn.execute(
        "SELECT * FROM attendance_logs WHERE date(timestamp)=date('now') ORDER BY timestamp DESC"
    ).fetchall()
    # Active session
    active_sess = conn.execute(
        'SELECT * FROM attendance_sessions WHERE closed=0 ORDER BY id DESC LIMIT 1'
    ).fetchone()
    conn.close()
    return render_template('teacher_dashboard.html',
                           teacher_name=session['name'],
                           assignments=assignments,
                           today_logs=today_logs,
                           active_sess=active_sess)

@app.route('/parent')
def parent_dashboard():
    if session.get('portal') != 'parent':
        return redirect(url_for('login'))
    conn   = get_db()
    parent = conn.execute('SELECT * FROM parent_users WHERE id=?', (session['user_id'],)).fetchone()
    child  = conn.execute('SELECT * FROM student_users WHERE id=?', (parent['student_id'],)).fetchone() \
             if parent and parent['student_id'] else None
    logs, assignments = [], []
    if child:
        logs        = conn.execute(
            'SELECT * FROM attendance_logs WHERE student_id=? ORDER BY timestamp DESC LIMIT 30',
            (child['id'],)
        ).fetchall()
        assignments = conn.execute('SELECT * FROM assignments ORDER BY due_date ASC LIMIT 10').fetchall()
    conn.close()
    return render_template('parent_dashboard.html',
                           parent_name=session['name'],
                           child=child, logs=logs, assignments=assignments)

@app.route('/admin')
def dashboard():
    if session.get('portal') != 'staff' or session.get('role') != 'Admin':
        return redirect(url_for('login'))
    conn = get_db()
    pending = (
        [dict(r) | {'user_type': 'student'} for r in conn.execute("SELECT * FROM student_users WHERE status='pending'").fetchall()] +
        [dict(r) | {'user_type': 'staff'}   for r in conn.execute("SELECT * FROM staff_users WHERE status='pending'").fetchall()] +
        [dict(r) | {'user_type': 'parent'}  for r in conn.execute("SELECT * FROM parent_users WHERE status='pending'").fetchall()]
    )
    all_students = conn.execute('SELECT * FROM student_users ORDER BY name').fetchall()
    conn.close()
    return render_template('admin_dashboard.html',
                           pending_users=pending,
                           all_students=all_students,
                           admin_name=session['name'])

# =============================================================
# ADMIN ACTIONS
# =============================================================
@app.route('/admin/approve/<user_type>/<int:uid>')
def approve_user(user_type, uid):
    if session.get('role') != 'Admin': return redirect(url_for('login'))
    tbl = {'student': 'student_users', 'staff': 'staff_users', 'parent': 'parent_users'}.get(user_type)
    if tbl:
        conn = get_db()
        conn.execute(f"UPDATE {tbl} SET status='approved' WHERE id=?", (uid,))
        conn.commit(); conn.close()
    return redirect(url_for('dashboard'))

@app.route('/admin/approve_all')
def approve_all():
    if session.get('role') != 'Admin': return redirect(url_for('login'))
    conn = get_db()
    for tbl in ['student_users', 'staff_users', 'parent_users']:
        conn.execute(f"UPDATE {tbl} SET status='approved' WHERE status='pending'")
    conn.commit(); conn.close()
    return redirect(url_for('dashboard'))

@app.route('/admin/delete/<user_type>/<int:uid>')
def delete_user(user_type, uid):
    if session.get('role') != 'Admin': return redirect(url_for('login'))
    tbl = {'student': 'student_users', 'staff': 'staff_users', 'parent': 'parent_users'}.get(user_type)
    if tbl:
        conn = get_db()
        conn.execute(f'DELETE FROM {tbl} WHERE id=?', (uid,))
        conn.commit(); conn.close()
    return redirect(url_for('dashboard'))

# =============================================================
# ATTENDANCE API  (FIXED)
# =============================================================
@app.route('/api/start_attendance', methods=['POST'])
def start_attendance():
    if session.get('portal') != 'staff':
        return jsonify({'status': 'error', 'msg': 'Unauthorized'}), 403
    data      = request.json or {}
    subject   = data.get('subject', 'General')
    semester  = data.get('semester', 'Sem-4')
    division  = data.get('division', 'A')
    duration  = int(data.get('duration', 120))   # seconds

    # Close any previously open session by this teacher
    conn = get_db()
    conn.execute(
        'UPDATE attendance_sessions SET closed=1 WHERE teacher_id=? AND closed=0',
        (session['user_id'],)
    )
    sess_token = f"SESS-{session['user_id']}-{int(time.time())}"
    qr_token   = f"QR-{random.randint(100000,999999)}-{int(time.time())}"
    expires_at = int(time.time()) + duration

    conn.execute(
        'INSERT INTO attendance_sessions (token,qr_token,subject,teacher_id,semester,division,expires_at) VALUES (?,?,?,?,?,?,?)',
        (sess_token, qr_token, subject, session['user_id'], semester, division, expires_at)
    )
    conn.commit()
    sess_id = conn.execute('SELECT last_insert_rowid()').fetchone()[0]
    conn.close()

    # Register QR token in memory
    active_qr_tokens[qr_token] = {'expires_at': expires_at, 'sess_id': sess_id, 'subject': subject}

    return jsonify({
        'status':       'ok',
        'session_token': sess_token,
        'qr_token':      qr_token,
        'sess_id':       sess_id,
        'expires_at':    expires_at
    })

@app.route('/api/refresh_qr', methods=['POST'])
def refresh_qr():
    if session.get('portal') != 'staff':
        return jsonify({'status': 'error'}), 403
    data      = request.json or {}
    sess_tok  = data.get('session_token')
    conn      = get_db()
    sess      = conn.execute(
        'SELECT * FROM attendance_sessions WHERE token=? AND closed=0', (sess_tok,)
    ).fetchone()
    if not sess or int(time.time()) > (sess['expires_at'] or 0):
        conn.close()
        return jsonify({'status': 'expired'})

    # Revoke old QR
    old_qr = sess['qr_token']
    if old_qr in active_qr_tokens:
        del active_qr_tokens[old_qr]

    new_qr = f"QR-{random.randint(100000,999999)}-{int(time.time())}"
    active_qr_tokens[new_qr] = {
        'expires_at': sess['expires_at'],
        'sess_id':    sess['id'],
        'subject':    sess['subject']
    }
    conn.execute('UPDATE attendance_sessions SET qr_token=? WHERE id=?', (new_qr, sess['id']))
    conn.commit(); conn.close()
    return jsonify({'status': 'ok', 'token': new_qr, 'expires_at': sess['expires_at']})

@app.route('/api/close_session', methods=['POST'])
def close_session():
    if session.get('portal') != 'staff':
        return jsonify({'status': 'error'}), 403
    token = (request.json or {}).get('session_token')
    conn  = get_db()
    sess  = conn.execute('SELECT * FROM attendance_sessions WHERE token=?', (token,)).fetchone()
    if sess:
        conn.execute('UPDATE attendance_sessions SET closed=1 WHERE token=?', (token,))
        conn.commit()
        logs = conn.execute(
            'SELECT * FROM attendance_logs WHERE session_id=? ORDER BY timestamp DESC',
            (sess['id'],)
        ).fetchall()
        # Revoke QR
        if sess['qr_token'] and sess['qr_token'] in active_qr_tokens:
            del active_qr_tokens[sess['qr_token']]
        conn.close()
        return jsonify({'status': 'ok', 'attendance': [dict(l) for l in logs]})
    conn.close()
    return jsonify({'status': 'error', 'msg': 'Session not found'}), 404

@app.route('/api/mark_attendance', methods=['POST'])
def mark_attendance():
    if session.get('portal') != 'student':
        return jsonify({'status': 'error', 'msg': 'Unauthorized'}), 403
    data   = request.json or {}
    token  = data.get('token', '').strip()
    method = data.get('method', 'qr')

    if token not in active_qr_tokens:
        return jsonify({'status': 'error', 'msg': 'Invalid or expired QR code'}), 400

    qr_info = active_qr_tokens[token]
    if int(time.time()) > qr_info['expires_at']:
        del active_qr_tokens[token]
        return jsonify({'status': 'error', 'msg': 'QR code has expired'}), 400

    sess_id = qr_info['sess_id']
    conn = get_db()

    # Check duplicate
    dup = conn.execute(
        'SELECT id FROM attendance_logs WHERE student_id=? AND session_id=?',
        (session['user_id'], sess_id)
    ).fetchone()
    if dup:
        conn.close()
        return jsonify({'status': 'error', 'msg': 'Attendance already marked'}), 400

    conn.execute(
        'INSERT INTO attendance_logs (student_id,student_name,session_id,subject,method) VALUES (?,?,?,?,?)',
        (session['user_id'], session['name'], sess_id, qr_info.get('subject', ''), method)
    )
    conn.commit(); conn.close()
    return jsonify({'status': 'success', 'msg': '✓ Attendance marked successfully'})

@app.route('/api/check_session')
def check_session_api():
    conn  = get_db()
    # Find open session (optionally filter by teacher)
    query = 'SELECT * FROM attendance_sessions WHERE closed=0 ORDER BY id DESC LIMIT 1'
    sess  = conn.execute(query).fetchone()
    conn.close()
    if sess and int(time.time()) < (sess['expires_at'] or 0):
        return jsonify({
            'status':    'open',
            'token':     sess['token'],
            'qr_token':  sess['qr_token'],
            'subject':   sess['subject'],
            'expires_at': sess['expires_at']
        })
    return jsonify({'status': 'locked'})

@app.route('/api/live_attendance')
def live_attendance():
    """Live polling endpoint for teacher dashboard."""
    if session.get('portal') != 'staff':
        return jsonify({'status': 'error'}), 403
    sess_token = request.args.get('session_token')
    conn = get_db()
    sess = conn.execute(
        'SELECT * FROM attendance_sessions WHERE token=?', (sess_token,)
    ).fetchone()
    if not sess:
        conn.close()
        return jsonify({'status': 'error', 'msg': 'Session not found'}), 404
    logs = conn.execute(
        '''SELECT al.*, su.roll_no FROM attendance_logs al
           LEFT JOIN student_users su ON al.student_id=su.id
           WHERE al.session_id=? ORDER BY al.timestamp DESC''',
        (sess['id'],)
    ).fetchall()
    total_students = conn.execute(
        'SELECT COUNT(*) FROM student_users WHERE status="approved" AND semester=? AND division=?',
        (sess['semester'], sess['division'])
    ).fetchone()[0]
    conn.close()
    remaining = max(0, (sess['expires_at'] or 0) - int(time.time()))
    return jsonify({
        'status':         'ok',
        'closed':         sess['closed'],
        'subject':        sess['subject'],
        'present_count':  len(logs),
        'total_students': total_students,
        'remaining_secs': remaining,
        'logs':           [dict(l) for l in logs]
    })

@app.route('/api/attendance_log')
def attendance_log():
    if session.get('portal') != 'staff':
        return jsonify({'status': 'error'}), 403
    conn = get_db()
    rows = conn.execute(
        'SELECT student_name,method,timestamp,subject FROM attendance_logs ORDER BY timestamp DESC LIMIT 60'
    ).fetchall()
    conn.close()
    return jsonify({'students': [dict(r) for r in rows]})

@app.route('/api/student_attendance')
def student_attendance():
    if session.get('portal') != 'student':
        return jsonify({'status': 'error'}), 403
    conn  = get_db()
    total = conn.execute('SELECT COUNT(*) FROM attendance_sessions WHERE closed=1').fetchone()[0]
    pres  = conn.execute(
        'SELECT COUNT(*) FROM attendance_logs WHERE student_id=?', (session['user_id'],)
    ).fetchone()[0]
    logs  = conn.execute(
        '''SELECT al.log_date, al.subject, al.method, al.timestamp
           FROM attendance_logs al
           WHERE al.student_id=? ORDER BY al.timestamp DESC''',
        (session['user_id'],)
    ).fetchall()
    conn.close()
    pct = round(pres / total * 100) if total else 0
    return jsonify({'total': total, 'present': pres, 'pct': pct, 'logs': [dict(r) for r in logs]})

@app.route('/api/save_attendance', methods=['POST'])
def save_attendance():
    if session.get('portal') != 'staff':
        return jsonify({'status': 'error'}), 403
    data       = request.json or {}
    records    = data.get('records', [])
    session_id = data.get('session_id')
    conn = get_db()
    for r in records:
        if not r.get('present'):
            conn.execute(
                'DELETE FROM attendance_logs WHERE student_id=? AND session_id=?',
                (r['student_id'], session_id)
            )
    conn.commit()
    # Low attendance emails
    students = conn.execute('SELECT * FROM student_users WHERE status="approved"').fetchall()
    total    = conn.execute('SELECT COUNT(*) FROM attendance_sessions WHERE closed=1').fetchone()[0]
    for stu in students:
        pres = conn.execute('SELECT COUNT(*) FROM attendance_logs WHERE student_id=?', (stu['id'],)).fetchone()[0]
        pct  = round(pres / total * 100) if total else 100
        if pct < ATTENDANCE_THRESHOLD:
            html = attendance_alert_html(stu['name'], 'Overall', pct)
            if send_email(stu['email'], '⚠ Low Attendance Alert — StudX', html):
                conn.execute('INSERT INTO email_log (student_id,email,subject) VALUES (?,?,?)',
                             (stu['id'], stu['email'], 'Low Attendance Alert'))
    conn.commit(); conn.close()
    return jsonify({'status': 'ok', 'msg': 'Attendance saved.'})

# =============================================================
# ASSIGNMENTS
# =============================================================
@app.route('/api/create_assignment', methods=['POST'])
def create_assignment():
    if session.get('portal') != 'staff':
        return jsonify({'status': 'error'}), 403
    d = request.json or {}
    conn = get_db()
    conn.execute(
        'INSERT INTO assignments (title,subject,description,due_date,max_marks,teacher_id,semester,division) VALUES (?,?,?,?,?,?,?,?)',
        (d.get('title'), d.get('subject'), d.get('description'),
         d.get('due_date'), d.get('max_marks', 100),
         session['user_id'], d.get('semester', 'Sem-4'), d.get('division', 'A'))
    )
    conn.commit(); conn.close()
    return jsonify({'status': 'ok'})

@app.route('/api/submit_assignment', methods=['POST'])
def submit_assignment():
    if session.get('portal') != 'student':
        return jsonify({'status': 'error'}), 403
    d = request.json or {}
    conn = get_db()
    conn.execute(
        'INSERT INTO assignment_submissions (assignment_id,student_id,notes) VALUES (?,?,?)',
        (d.get('assignment_id'), session['user_id'], d.get('notes', ''))
    )
    conn.commit(); conn.close()
    return jsonify({'status': 'ok'})

@app.route('/api/assignments')
def get_assignments():
    conn = get_db()
    rows = conn.execute('SELECT * FROM assignments ORDER BY due_date ASC').fetchall()
    conn.close()
    return jsonify({'assignments': [dict(r) for r in rows]})

# =============================================================
# MESSAGES
# =============================================================
@app.route('/api/send_message', methods=['POST'])
def send_message():
    d = request.json or {}
    conn = get_db()
    conn.execute(
        'INSERT INTO messages (sender_id,sender_type,receiver_id,receiver_type,body) VALUES (?,?,?,?,?)',
        (session.get('user_id'), session.get('portal'),
         d.get('receiver_id'), d.get('receiver_type'), d.get('body', ''))
    )
    conn.commit(); conn.close()
    return jsonify({'status': 'ok'})

@app.route('/api/messages/<int:other_id>')
def get_messages(other_id):
    uid  = session.get('user_id')
    conn = get_db()
    rows = conn.execute(
        'SELECT * FROM messages WHERE (sender_id=? AND receiver_id=?) OR (sender_id=? AND receiver_id=?) ORDER BY sent_at ASC',
        (uid, other_id, other_id, uid)
    ).fetchall()
    conn.close()
    return jsonify({'messages': [dict(r) for r in rows]})

# =============================================================
# MEETINGS
# =============================================================
@app.route('/api/create_meeting', methods=['POST'])
def create_meeting():
    if session.get('portal') != 'staff':
        return jsonify({'status': 'error'}), 403
    d = request.json or {}
    conn = get_db()
    conn.execute(
        'INSERT INTO meetings (title,host_id,host_type,scheduled_at,audience) VALUES (?,?,?,?,?)',
        (d.get('title'), session['user_id'], session['portal'],
         d.get('scheduled_at'), d.get('audience', 'all'))
    )
    conn.commit(); conn.close()
    return jsonify({'status': 'ok'})

@app.route('/api/meetings')
def get_meetings():
    conn = get_db()
    rows = conn.execute('SELECT * FROM meetings ORDER BY scheduled_at ASC').fetchall()
    conn.close()
    return jsonify({'meetings': [dict(r) for r in rows]})

# =============================================================
# AI TUTOR (Gemini)
# =============================================================
@app.route('/api/ai_tutor', methods=['POST'])
def ai_tutor():
    import urllib.request, json as json_mod
    if not session.get('user_id'):
        return jsonify({'status': 'error', 'msg': 'Unauthorized'}), 403
    data     = request.json or {}
    question = data.get('question', '').strip()
    history  = data.get('history', [])
    if not question:
        return jsonify({'status': 'error', 'msg': 'Empty question'}), 400
    if not GEMINI_API_KEY:
        return jsonify({'status': 'error', 'msg': 'Gemini API not configured'}), 500

    # Build Gemini contents array
    contents = []
    for msg in history[-10:]:
        contents.append({'role': msg['role'], 'parts': [{'text': msg['text']}]})
    contents.append({'role': 'user', 'parts': [{'text': question}]})

    system_instruction = {
        'parts': [{'text': (
            'You are StudX AI Tutor, an expert academic assistant for Bhagubhai Mafatlal Polytechnic students. '
            'Help with engineering subjects: Mathematics, Physics, Programming, Electronics, Mechanical. '
            'Give clear, structured answers with examples. Use emojis sparingly for clarity. '
            'Be encouraging and student-friendly.'
        )}]
    }

    payload = json_mod.dumps({
        'system_instruction': system_instruction,
        'contents': contents,
        'generationConfig': {'temperature': 0.7, 'maxOutputTokens': 1024}
    }).encode()

    url = f'https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}'
    req = urllib.request.Request(url, data=payload, headers={'Content-Type': 'application/json'}, method='POST')
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json_mod.loads(resp.read())
        answer = result['candidates'][0]['content']['parts'][0]['text']
        return jsonify({'status': 'ok', 'answer': answer})
    except Exception as e:
        return jsonify({'status': 'error', 'msg': str(e)}), 500

# =============================================================
# WEEKLY REPORTS
# =============================================================
@app.route('/api/send_weekly_reports')
def send_weekly_reports():
    if session.get('role') != 'Admin':
        return jsonify({'status': 'error'}), 403
    conn     = get_db()
    students = conn.execute('SELECT * FROM student_users WHERE status="approved"').fetchall()
    total    = conn.execute('SELECT COUNT(*) FROM attendance_sessions WHERE closed=1').fetchone()[0]
    sent     = 0
    for stu in students:
        pres = conn.execute('SELECT COUNT(*) FROM attendance_logs WHERE student_id=?', (stu['id'],)).fetchone()[0]
        pct  = round(pres / total * 100) if total else 100
        if pct < ATTENDANCE_THRESHOLD:
            html = attendance_alert_html(stu['name'], 'Overall', pct)
            if send_email(stu['email'], '⚠ Weekly Attendance Alert — StudX', html):
                conn.execute('INSERT INTO email_log (student_id,email,subject) VALUES (?,?,?)',
                             (stu['id'], stu['email'], 'Weekly Low Attendance'))
                sent += 1
    conn.commit(); conn.close()
    return jsonify({'status': 'ok', 'emails_sent': sent})

# =============================================================
# RESET DB
# =============================================================
@app.route('/reset-db')
def reset_db():
    if os.path.exists('studx.db'):
        os.remove('studx.db')
    init_db()
    return "<h3>✅ DB reset. <a href='/login'>Login</a></h3>"
@app.route('/api/admin/users_list')
def api_users_list():
    if session.get('role') != 'Admin': return jsonify({'users': []}), 403
    conn = get_db()
    # Combine all user types into one clean list for the JS table
    students = [dict(r) | {'role': 'Student'} for r in conn.execute("SELECT id, name, email, semester, status FROM student_users").fetchall()]
    staff = [dict(r) | {'role': r['role']} for r in conn.execute("SELECT id, name, email, role, status FROM staff_users").fetchall()]
    parents = [dict(r) | {'role': 'Parent'} for r in conn.execute("SELECT id, name, email, status FROM parent_users").fetchall()]
    conn.close()
    return jsonify({'users': students + staff + parents})

@app.route('/api/email_logs')
def api_email_logs():
    conn = get_db()
    logs = conn.execute("SELECT student_id, email, subject, sent_at FROM email_log ORDER BY sent_at DESC LIMIT 20").fetchall()
    conn.close()
    return jsonify({'logs': [dict(l) for l in logs]})
@app.route('/migrate')
def migrate_db():
    conn = get_db()
    tables = ['student_users', 'staff_users', 'parent_users']
    report = []
    
    for table in tables:
        # Get existing columns for this table
        cursor = conn.execute(f"PRAGMA table_info({table})")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'otp' not in columns:
            conn.execute(f'ALTER TABLE {table} ADD COLUMN otp TEXT')
            report.append(f"Added 'otp' to {table}")
        
        if 'otp_expiry' not in columns:
            conn.execute(f'ALTER TABLE {table} ADD COLUMN otp_expiry INTEGER')
            report.append(f"Added 'otp_expiry' to {table}")
            
    conn.commit()
    conn.close()
    return f"Status: {', '.join(report) if report else 'All columns already present!'}"
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=True)
