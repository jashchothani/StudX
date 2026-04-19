# StudX — Smart Campus Platform

A full-stack Flask web application for Bhagubhai Mafatlal Polytechnic.

## Features

- **4 Role Portals** — Student, Teacher, Parent, Admin (distinct themes & features)
- **2-Step OTP Login** — Email OTP verification on every login
- **QR + Face Biometric Attendance** — Teacher starts session (2 min window), QR refreshes every 10s, students scan or use face recognition
- **Attendance Approval** — Teacher reviews & toggles present/absent before saving
- **Automated Email Alerts** — Weekly reports to students below 75% attendance
- **Assignment Centre** — Teachers post, students submit, parents view
- **WhatsApp-style Chat** — Between students, teachers, and parents
- **Group Video Calls** — Meeting scheduler with live call UI
- **AI Tutor / Assistant** — Integrated AI chat per portal
- **Timetable** — Live "NOW" indicator for current lecture

## Setup

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Configure email in app.py
SMTP_USER = 'your@gmail.com'
SMTP_PASS = 'your_app_password'   # Use Gmail App Password

# 3. (Optional) Train face recognition model
#    Run face_trainer.py to generate trainer.yml

# 4. Run the app
python app.py
```

## Default Admin Login

- **URL:** http://localhost:5000/login
- **Portal:** Staff/Admin
- **Email:** admin@studx.com
- **Password:** admin123
- **OTP:** (sent to email — configure SMTP first)

## File Structure

```
studx/
├── app.py                  # Main Flask app, all routes & API
├── requirements.txt
├── studx.db               # SQLite DB (auto-created)
├── trainer.yml            # Face recognition model (generate separately)
├── static/
│   ├── css/
│   │   └── portal.css     # Shared portal styles for all roles
│   └── js/
│       ├── portal.js      # Tab navigation (shared)
│       └── student.js     # Student-specific logic
└── templates/
    ├── base.html          # Base layout with flash messages
    ├── login.html         # Role-selector login page
    ├── verify_otp.html    # 6-digit OTP verification
    ├── register.html      # Registration with role-specific fields
    ├── student_dashboard.html
    ├── teacher_dashboard.html
    ├── parent_dashboard.html
    └── admin_dashboard.html
```

## API Endpoints

| Method | Route | Description |
|--------|-------|-------------|
| POST | /api/start_attendance | Teacher starts QR session |
| POST | /api/refresh_qr | Refresh QR token (every 10s) |
| POST | /api/close_session | End attendance session |
| POST | /api/mark_attendance | Student marks via QR |
| POST | /api/verify_face | Student marks via Face+QR |
| POST | /api/save_attendance | Teacher saves approved list |
| GET  | /api/attendance_log | Live roster for teacher |
| GET  | /api/student_attendance | Student's own attendance |
| POST | /api/create_assignment | Teacher posts assignment |
| POST | /api/submit_assignment | Student submits |
| POST | /api/grade_submission | Teacher grades |
| GET  | /api/assignments | List all assignments |
| POST | /api/send_message | Send chat message |
| GET  | /api/messages/<id> | Get conversation |
| POST | /api/create_meeting | Schedule meeting |
| GET  | /api/meetings | List meetings |
| GET  | /api/send_weekly_reports | Admin triggers weekly emails |

## Email Configuration (Gmail)

1. Enable 2FA on your Gmail account
2. Go to Google Account → Security → App Passwords
3. Create an app password for "Mail"
4. Use that 16-character password as `SMTP_PASS`

## Face Recognition Setup

```bash
pip install opencv-contrib-python
python face_trainer.py   # Trains model on student photos
```

Photos should be stored as `dataset/User.{student_id}.{sample}.jpg`

## Deployment

For production, use Gunicorn:
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

Consider adding:
- Redis + Celery for async email sending
- WebSockets (Flask-SocketIO) for real-time QR push to students
- PostgreSQL instead of SQLite for production scale