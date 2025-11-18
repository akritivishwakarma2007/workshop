from flask import Flask, render_template, request, redirect, url_for, flash
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import os
import json

app = Flask(__name__)
app.secret_key = 'poweronworkshop2025_secret_key_123!@#'

# ==================== GOOGLE SHEETS SETUP ====================
SCOPE = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

# For Render/Railway: use environment variable | Local: use JSON file
if os.getenv("GOOGLE_json_key"):
    creds_dict = json.loads(os.getenv("GOOGLE_json_key"))
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, SCOPE)
else:
    # Local testing → make sure gsheet-bot.json is in project folder
    creds = ServiceAccountCredentials.from_json_keyfile_name("gsheet-bot.json", SCOPE)

client = gspread.authorize(creds)

# YOUR GOOGLE SHEET ID (DO NOT CHANGE UNLESS YOU MAKE NEW SHEET)
SHEET_ID = "1_VvHyhxbZoICb3zVfiyORabGA3lCWGKihi4GjNv47Jk"

# Open sheet and tabs
spreadsheet = client.open_by_key(SHEET_ID)
reg_sheet = spreadsheet.worksheet("Registrations")
inq_sheet = spreadsheet.worksheet("Inquiries")

# ==================== AUTO-FIX HEADERS (Runs every time app starts) ====================
def ensure_headers():
    # Correct headers for Registrations
    correct_reg = ["Timestamp", "Surname", "First Name", "Middle Name",
                   "Student ID", "Department/Class", "Email", "Contact Number"]
    current_reg = reg_sheet.row_values(1)
    
    if current_reg != correct_reg:
        print("Fixing 'Registrations' headers...")
        reg_sheet.resize(rows=1)  # Clear all data (only headers will remain)
        reg_sheet.append_row(correct_reg)
        print("Registrations headers fixed!")

    # Correct headers for Inquiries
    correct_inq = ["Timestamp", "Name", "Email", "Question"]
    current_inq = inq_sheet.row_values(1)
    
    if current_inq != correct_inq:
        print("Fixing 'Inquiries' headers...")
        inq_sheet.resize(rows=1)
        inq_sheet.append_row(correct_inq)
        print("Inquiries headers fixed!")

# Run this every time the app starts → protects your sheet forever
ensure_headers()

# ==================== ROUTES ====================
@app.route('/')
def home():
    return render_template('home.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        surname = request.form.get('surname', '').strip()
        firstname = request.form.get('firstname', '').strip()
        middlename = request.form.get('middlename', '').strip()
        studentid = request.form.get('studentid', '').strip()
        department = request.form.get('department', '').strip()
        email = request.form.get('email', '').strip()
        contact = request.form.get('contact', '').strip()

        # Required fields check
        if not all([surname, firstname, studentid, department, email, contact]):
            flash('Please fill all required fields!', 'error')
            return redirect(url_for('register'))

        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            row = [timestamp, surname, firstname, middlename, studentid, department, email, contact]
            reg_sheet.append_row(row)
            flash('Thank you for registering! See you at the workshop!', 'success')
        except Exception as e:
            flash('Registration failed. Please try again.', 'error')
            print("Registration error:", e)

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
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            row = [timestamp, name or "Anonymous", email, question]
            inq_sheet.append_row(row)
            flash('Thank you! We received your question.', 'success')
        except Exception as e:
            flash('Failed to send message. Try again.', 'error')
            print("Inquiry error:", e)

        return redirect(url_for('inquire'))

    return render_template('inquire.html')

# ==================== RUN APP ====================
if __name__ == '__main__':
    if not os.path.exists('templates'):
        print("ERROR: 'templates' folder not found! Create it and add HTML files.")
    else:
        print("Power ON Workshop Website is running!")
        print("Visit: http://127.0.0.1:5000")
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))