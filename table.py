import sqlite3

conn = sqlite3.connect('users.db') # Change to your actual db file name
cursor = conn.cursor()

try:
    cursor.execute("ALTER TABLE users ADD COLUMN otp TEXT")
    cursor.execute("ALTER TABLE users ADD COLUMN otp_expiry TEXT")
    print("Columns added successfully!")
except sqlite3.OperationalError:
    print("Columns might already exist.")

conn.commit()
conn.close()