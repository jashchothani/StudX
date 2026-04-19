import os

folders = [
"app",
"app/routes",
"app/services",
"app/security",
"app/siem",
"app/ai",
"app/utils",
"app/logs",

"database",
"database/migrations",

"templates",
"templates/layouts",
"templates/auth",
"templates/admin",
"templates/teacher",
"templates/student",
"templates/parent",
"templates/components",

"static",
"static/css",
"static/js",
"static/images",
"static/images/icons",
"static/uploads",
"static/uploads/assignments",
"static/uploads/profile_pics",

"analytics",
"api",
"tests",
"docs"
]

files = [
"requirements.txt",
"config.py",
"run.py",

"app/__init__.py",
"app/extensions.py",
"app/models.py",
"app/database.py",

"app/routes/auth_routes.py",
"app/routes/admin_routes.py",
"app/routes/teacher_routes.py",
"app/routes/student_routes.py",
"app/routes/parent_routes.py",
"app/routes/emergency_routes.py",

"app/services/email_service.py",
"app/services/sms_service.py",
"app/services/attendance_service.py",
"app/services/result_service.py",
"app/services/notification_service.py",

"app/security/auth.py",
"app/security/password_hashing.py",
"app/security/session_manager.py",
"app/security/security_logger.py",

"app/siem/log_collector.py",
"app/siem/threat_detection.py",
"app/siem/alert_manager.py",

"app/ai/face_recognition.py",
"app/ai/camera_capture.py",
"app/ai/attendance_ai.py",

"app/utils/helpers.py",
"app/utils/validators.py",
"app/utils/location_service.py",

"app/logs/security.log",

"database/campus_schema.sql",
"database/seed_data.sql",

"templates/layouts/base.html",

"templates/auth/login.html",
"templates/auth/register.html",

"templates/admin/dashboard.html",
"templates/admin/manage_students.html",
"templates/admin/manage_teachers.html",
"templates/admin/manage_parents.html",
"templates/admin/analytics.html",

"templates/teacher/dashboard.html",
"templates/teacher/mark_attendance.html",
"templates/teacher/upload_assignment.html",
"templates/teacher/enter_marks.html",
"templates/teacher/announcements.html",

"templates/student/dashboard.html",
"templates/student/attendance.html",
"templates/student/results.html",
"templates/student/assignments.html",
"templates/student/emergency_button.html",

"templates/parent/dashboard.html",
"templates/parent/child_attendance.html",
"templates/parent/child_results.html",
"templates/parent/alerts.html",

"templates/components/navbar.html",
"templates/components/sidebar.html",
"templates/components/footer.html",

"static/css/style.css",
"static/css/dashboard.css",
"static/css/login.css",

"static/js/main.js",
"static/js/dashboard.js",
"static/js/charts.js",
"static/js/emergency.js",

"static/images/logo.png",
"static/images/dashboard-bg.jpg",

"analytics/attendance_analytics.py",
"analytics/result_analytics.py",
"analytics/dashboard_charts.py",

"api/email_api.py",
"api/sms_api.py",
"api/maps_api.py",

"tests/test_login.py",
"tests/test_attendance.py",
"tests/test_results.py",

"docs/system_architecture.md",
"docs/database_design.md",
"docs/api_documentation.md"
]

# Create folders
for folder in folders:
    os.makedirs(folder, exist_ok=True)

# Create files
for file in files:
    with open(file, "w") as f:
        pass

print("✅ Smart Campus System project structure created successfully!")