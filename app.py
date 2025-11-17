from flask import Flask, render_template, request, redirect, url_for, flash
import pandas as pd
import os
import time

app = Flask(__name__)
app.secret_key = 'poweronworkshop2025_secret_key_123!@#'  # Change if you want

# Excel file paths
REG_FILE = 'registrations.xlsx'
INQ_FILE = 'inquiries.xlsx'

# Safe Excel read (handles corruption)
def safe_read_excel(filepath):
    if not os.path.exists(filepath):
        return pd.DataFrame()
    try:
        return pd.read_excel(filepath, engine='openpyxl')
    except Exception as e:
        print(f"Corrupted file {filepath}, recreating...")
        try:
            os.remove(filepath)
        except:
            pass
        flash('Previous data file was corrupted and has been reset.', 'warning')
        return pd.DataFrame()

# Safe Excel write (handles file lock)
def safe_write_excel(df, filepath):
    for attempt in range(5):
        try:
            df.to_excel(filepath, index=False, engine='openpyxl')
            return True
        except PermissionError:
            print(f"File locked, retry {attempt + 1}/5...")
            time.sleep(1)
        except Exception as e:
            flash(f'Error saving data: {e}', 'error')
            return False
    flash('Cannot save: Excel file is open. Please close it!', 'error')
    return False

# Routes
@app.route('/')
def home():
    return render_template('home.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        contact = request.form.get('contact')
        institution = request.form.get('institution')
        topics = request.form.getlist('topics')

        if not all([name, email, contact, institution]):
            flash('Please fill all required fields!', 'error')
            return redirect(url_for('register'))

        new_data = {
            'Full Name': [name],
            'Email Address': [email],
            'Contact Number': [contact],
            'Educational Institution': [institution],
            'Topics Interested In': [', '.join(topics)]
        }
        df_new = pd.DataFrame(new_data)
        df_existing = safe_read_excel(REG_FILE)
        df_final = pd.concat([df_existing, df_new], ignore_index=True)

        if safe_write_excel(df_final, REG_FILE):
            flash('Thank you for registering! See you at the workshop!', 'success')
        return redirect(url_for('register'))

    return render_template('register.html')

@app.route('/inquire', methods=['GET', 'POST'])
def inquire():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email')
        question = request.form.get('question')

        if not email or not question:
            flash('Email and Question are required!', 'error')
            return redirect(url_for('inquire'))

        new_data = {'Name': [name or 'Anonymous'], 'Email': [email], 'Question': [question]}
        df_new = pd.DataFrame(new_data)
        df_existing = safe_read_excel(INQ_FILE)
        df_final = pd.concat([df_existing, df_new], ignore_index=True)

        if safe_write_excel(df_final, INQ_FILE):
            flash('Thank you! We received your question and will reply soon.', 'success')
        return redirect(url_for('inquire'))

    return render_template('inquire.html')

if __name__ == '__main__':
    # Create templates folder message if missing
    if not os.path.exists('templates'):
        print("ERROR: 'templates' folder not found! Create it and add HTML files.")
    app.run(debug=True)