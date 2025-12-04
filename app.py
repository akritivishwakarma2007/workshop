from flask import Flask, render_template, request, redirect, url_for, flash
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime, timedelta
import os
import json
import sys

app = Flask(__name__)
app.secret_key = 'poweronworkshop2025_secret_key_123!@#'

# ==================== REGISTRATION CLOSED? ====================
REGISTRATION_CLOSED = True  # SET THIS TO True = BLOCK ALL REGISTRATIONS
CLOSED_MESSAGE = "SEATS ARE FULL! Registration is now closed. Thank you for the amazing response!"

# ==================== GOOGLE SHEETS SETUP ====================
SCOPE = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

json_key_content = os.getenv("GOOGLE_JSON_KEY")

if json_key_content:
    print("Using GOOGLE_JSON_KEY from environment")
    try:
        creds_dict = json.loads(json_key_content)
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, SCOPE)
    except Exception as e:
        print("ERROR: Invalid GOOGLE_JSON_KEY!")
        print(e)
        sys.exit(1)
else:
    json_file = "gsheet-bot.json"
    if os.path.exists(json_file):
        print(f"Using local {json_file}")
        creds = ServiceAccountCredentials.from_json_keyfile_name(json_file, SCOPE)
    else:
        print(f"ERROR: {json_file} not found!")
        sys.exit(1)

try:
    client = gspread.authorize(creds)
    print("Connected to Google Sheets!")
except Exception as e:
    print("Failed to connect:", e)
    sys.exit(1)

SHEET_ID = "1_VvHyhxbZoICb3zVfiyORabGA3lCWGKihi4GjNv47Jk"
try:
    spreadsheet = client.open_by_key(SHEET_ID)
    reg_sheet = spreadsheet.worksheet("Registrations")
    inq_sheet = spreadsheet.worksheet("Inquiries")
except Exception as e:
    print("Cannot open Google Sheet:", e)
    sys.exit(1)

# ==================== AUTO-FIX HEADERS ====================
def ensure_headers():
    reg_headers = ["Timestamp", "Surname", "First Name", "Middle Name",
                   "Student ID", "Department/Class", "Email", "Contact Number"]
    inq_headers = ["Timestamp", "Name", "Email", "Question"]

    if reg_sheet.row_values(1) != reg_headers:
        reg_sheet.resize(rows=1)
        reg_sheet.append_row(reg_headers)
    if inq_sheet.row_values(1) != inq_headers:
        inq_sheet.resize(rows=1)
        inq_sheet.append_row(inq_headers)

ensure_headers()
print("Headers ready!")

# ==================== IST TIME ====================
def get_ist_time():
    ist = datetime.now() + timedelta(hours=5, minutes=30)
    return ist.strftime("%Y-%m-%d %H:%M:%S")

# ==================== ROUTES ====================
@app.route('/')
def home():
    return render_template('home.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    # BLOCK ALL REGISTRATIONS
    if REGISTRATION_CLOSED:
        flash(CLOSED_MESSAGE, 'warning')
        return render_template('register.html')  # Shows closed message on the same page
    
    # If registration was open (future use)
    if request.method == 'POST':
        # your existing form logic here (kept for backup)
        surname = request.form.get('surname', '').strip()
        firstname = request.form.get('firstname', '').strip()
        middlename = request.form.get('middlename', '').strip()
        studentid = request.form.get('studentid', '').strip()
        department = request.form.get('department', '').strip()
        email = request.form.get('email', '').strip()
        contact = request.form.get('contact', '').strip()

        if not all([surname, firstname, studentid, department, email, contact]):
            flash('Please fill all required fields!', 'error')
            return redirect(url_for('register'))

        try:
            row = [get_ist_time(), surname, firstname, middlename, studentid, department, email, contact]
            reg_sheet.append_row(row)
            flash('Registration successful! Welcome to Power ON!', 'success')
        except Exception as e:
            flash('Registration failed. Try again.', 'error')
            print("Reg error:", e)

        return redirect(url_for('register'))
    
    return render_template('register.html')

@app.route('/inquire', methods=['GET', 'POST'])
def inquire():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        question = request.form.get('question', '').strip()

        if not email or not question:
            flash('Email and Question are required!', 'error')
            return redirect(url_for('inquire'))

        try:
            row = [get_ist_time(), name or "Anonymous", email, question]
            inq_sheet.append_row(row)
            flash('Message sent! We’ll reply soon.', 'success')
        except Exception as e:
            flash('Failed to send. Try again.', 'error')
            print("Inquiry error:", e)

        return redirect(url_for('inquire'))
    return render_template('inquire.html')

# ==================== RUN ====================
if __name__ == '__main__':
    print("="*60)
    if REGISTRATION_CLOSED:
        print("REGISTRATION IS OFFICIALLY CLOSED")
        print("→ No new registrations allowed")
    else:
        print("Registration is OPEN")
    print("Local URL: http://127.0.0.1:5000")
    print("="*60)
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
