from flask import Flask, render_template, request, redirect, url_for, flash
import pandas as pd
import os

app = Flask(__name__)
app.secret_key = 'hello world'

REG_FILE = 'registrations.xlsx'
INQ_FILE = 'inquiries.xlsx'

def safe_read_excel(filepath):
    if not os.path.exists(filepath):
        return pd.DataFrame()
    try:
        return pd.read_excel(filepath, engine='openpyxl')
    except Exception as e:
        print(f"Corrupted file {filepath}: {e}")
        try:
            os.remove(filepath)
        except:
            pass
        flash('Data file was corrupted and has been reset.', 'warning')
        return pd.DataFrame()

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/register', methods=['POST'])
def register():
    name = request.form.get('name')
    email = request.form.get('email')
    contact = request.form.get('contact')
    institution = request.form.get('institution')
    topics = request.form.getlist('topics')

    if not all([name, email, contact, institution]):
        flash('Please fill all required fields!', 'error')
        return redirect(url_for('home'))

    data = {
        'Full Name': [name],
        'Email Address': [email],
        'Contact Number': [contact],
        'Educational Institution': [institution],
        'Topics Interested In': [', '.join(topics)]
    }
    df = pd.DataFrame(data)

    # === SAFE READ & WRITE ===
    existing = safe_read_excel(REG_FILE)
    df = pd.concat([existing, df], ignore_index=True)
    df.to_excel(REG_FILE, index=False, engine='openpyxl')

    flash('Thank you for registering!', 'success')
    return redirect(url_for('home'))

@app.route('/inquire', methods=['POST'])
def inquire():
    name = request.form.get('name', '').strip()
    email = request.form.get('email')
    question = request.form.get('question')

    if not email or not question:
        flash('Email and Question are required!', 'error')
        return redirect(url_for('home'))

    data = {'Name': [name], 'Email': [email], 'Question': [question]}
    df = pd.DataFrame(data)

    existing = safe_read_excel(INQ_FILE)
    df = pd.concat([existing, df], ignore_index=True)
    df.to_excel(INQ_FILE, index=False, engine='openpyxl')

    flash('Thank you for your inquiry!', 'success')
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)