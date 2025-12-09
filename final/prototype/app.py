"""
Remote Patient Triage & Monitoring System - Flask Prototype
Demonstrates integration of cloud services for healthcare data management.
"""

from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from werkzeug.utils import secure_filename
import sqlite3
import json
import os
from datetime import datetime, timedelta
import csv
import io
import hashlib

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

# Database configuration
DATABASE = os.environ.get('DATABASE_PATH', 'patient_triage.db')
UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER', 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# ==================== DATABASE SETUP ====================

def init_db():
    """Initialize SQLite database with required tables."""
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    
    # Patients table
    c.execute('''CREATE TABLE IF NOT EXISTS patients (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        first_name TEXT NOT NULL,
        last_name TEXT NOT NULL,
        dob TEXT NOT NULL,
        phone TEXT,
        email TEXT,
        medical_history TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    # Vital signs table
    c.execute('''CREATE TABLE IF NOT EXISTS vitals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        patient_id INTEGER NOT NULL,
        heart_rate INTEGER,
        systolic_bp INTEGER,
        diastolic_bp INTEGER,
        oxygen_sat REAL,
        temperature REAL,
        weight REAL,
        recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (patient_id) REFERENCES patients(id)
    )''')
    
    # Symptoms table
    c.execute('''CREATE TABLE IF NOT EXISTS symptoms (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        patient_id INTEGER NOT NULL,
        symptom_text TEXT NOT NULL,
        severity INTEGER,
        onset_time TIMESTAMP,
        duration_hours INTEGER,
        reported_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (patient_id) REFERENCES patients(id)
    )''')
    
    # Assessments table
    c.execute('''CREATE TABLE IF NOT EXISTS assessments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        patient_id INTEGER NOT NULL,
        risk_score REAL NOT NULL,
        risk_level TEXT,
        notes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (patient_id) REFERENCES patients(id)
    )''')
    
    # Clinician users table
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        name TEXT,
        role TEXT DEFAULT 'clinician'
    )''')
    
    conn.commit()
    conn.close()

# ==================== DATABASE HELPERS ====================

def get_db_connection():
    """Get database connection with row factory."""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def hash_password(password):
    """Hash password for storage."""
    return hashlib.sha256(password.encode()).hexdigest()

# ==================== RISK SCORING LOGIC ====================

def calculate_risk_score(patient_id):
    """
    Calculate patient risk score based on vitals and symptoms.
    This simulates ML model integration (Vertex AI in production).
    """
    conn = get_db_connection()
    c = conn.cursor()
    
    # Get latest vitals
    c.execute('''SELECT * FROM vitals WHERE patient_id = ? 
                 ORDER BY recorded_at DESC LIMIT 1''', (patient_id,))
    vital = c.fetchone()
    
    # Get recent symptoms
    c.execute('''SELECT * FROM symptoms WHERE patient_id = ? 
                 AND reported_at > datetime('now', '-24 hours')
                 ORDER BY reported_at DESC''', (patient_id,))
    symptoms = c.fetchall()
    
    conn.close()
    
    risk_score = 0.0
    risk_level = "LOW"
    
    # Vital signs scoring
    if vital:
        # Abnormal heart rate
        if vital['heart_rate'] and (vital['heart_rate'] < 60 or vital['heart_rate'] > 100):
            risk_score += 0.2
        
        # Abnormal blood pressure
        if vital['systolic_bp'] and (vital['systolic_bp'] > 140 or vital['systolic_bp'] < 90):
            risk_score += 0.2
        
        # Low oxygen
        if vital['oxygen_sat'] and vital['oxygen_sat'] < 95:
            risk_score += 0.3
        
        # Fever
        if vital['temperature'] and vital['temperature'] > 38.5:
            risk_score += 0.2
    
    # Symptom scoring
    for symptom in symptoms:
        risk_score += (symptom['severity'] / 50.0)  # Severity 1-10 scaled to 0.02-0.2
    
    # Cap score at 1.0 and determine risk level
    risk_score = min(risk_score, 1.0)
    if risk_score >= 0.7:
        risk_level = "HIGH"
    elif risk_score >= 0.4:
        risk_level = "MEDIUM"
    else:
        risk_level = "LOW"
    
    return risk_score, risk_level

# ==================== ROUTES ====================

@app.route('/')
def home():
    """Home page with navigation."""
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Clinician login page."""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        conn = get_db_connection()
        c = conn.cursor()
        c.execute('SELECT * FROM users WHERE username = ?', (username,))
        user = c.fetchone()
        conn.close()
        
        if user and user['password_hash'] == hash_password(password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            return redirect(url_for('dashboard'))
        else:
            return render_template('login.html', error='Invalid credentials'), 401
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    """Logout user."""
    session.clear()
    return redirect(url_for('login'))

@app.route('/dashboard')
def dashboard():
    """Clinician dashboard showing all patients and risk scores."""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    c = conn.cursor()
    
    # Get all patients
    c.execute('SELECT * FROM patients ORDER BY created_at DESC')
    patients = c.fetchall()
    
    # Calculate risk scores for each patient
    patient_data = []
    for patient in patients:
        risk_score, risk_level = calculate_risk_score(patient['id'])
        patient_data.append({
            'id': patient['id'],
            'name': f"{patient['first_name']} {patient['last_name']}",
            'email': patient['email'],
            'risk_score': round(risk_score, 2),
            'risk_level': risk_level
        })
    
    conn.close()
    
    return render_template('dashboard.html', patients=patient_data, username=session['username'])

@app.route('/patient/<int:patient_id>')
def patient_detail(patient_id):
    """Detailed patient view with vitals history and symptoms."""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    c = conn.cursor()
    
    # Get patient info
    c.execute('SELECT * FROM patients WHERE id = ?', (patient_id,))
    patient = c.fetchone()
    
    if not patient:
        return "Patient not found", 404
    
    # Get recent vitals (last 7 days)
    c.execute('''SELECT * FROM vitals WHERE patient_id = ? 
                 AND recorded_at > datetime('now', '-7 days')
                 ORDER BY recorded_at DESC LIMIT 20''', (patient_id,))
    vitals = c.fetchall()
    
    # Get recent symptoms
    c.execute('''SELECT * FROM symptoms WHERE patient_id = ? 
                 ORDER BY reported_at DESC LIMIT 10''', (patient_id,))
    symptoms = c.fetchall()
    
    # Get latest assessment
    c.execute('''SELECT * FROM assessments WHERE patient_id = ? 
                 ORDER BY created_at DESC LIMIT 1''', (patient_id,))
    assessment = c.fetchone()
    
    conn.close()
    
    risk_score, risk_level = calculate_risk_score(patient_id)
    
    return render_template('patient_detail.html', 
                         patient=patient,
                         vitals=vitals,
                         symptoms=symptoms,
                         assessment=assessment,
                         risk_score=round(risk_score, 2),
                         risk_level=risk_level)

@app.route('/register-patient', methods=['GET', 'POST'])
def register_patient():
    """Patient registration form."""
    if request.method == 'POST':
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        dob = request.form.get('dob')
        phone = request.form.get('phone')
        email = request.form.get('email')
        medical_history = request.form.get('medical_history')
        
        conn = get_db_connection()
        c = conn.cursor()
        c.execute('''INSERT INTO patients 
                     (first_name, last_name, dob, phone, email, medical_history)
                     VALUES (?, ?, ?, ?, ?, ?)''',
                  (first_name, last_name, dob, phone, email, medical_history))
        patient_id = c.lastrowid
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'patient_id': patient_id}), 201
    
    return render_template('register_patient.html')

@app.route('/api/vitals/upload', methods=['POST'])
def upload_vitals():
    """Upload vital signs CSV file."""
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    patient_id = request.form.get('patient_id')
    if not patient_id:
        return jsonify({'error': 'patient_id required'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if not file.filename.endswith('.csv'):
        return jsonify({'error': 'Only CSV files allowed'}), 400
    
    try:
        # Parse CSV and insert into database
        stream = io.StringIO(file.stream.read().decode('utf-8'), newline=None)
        reader = csv.DictReader(stream)
        
        conn = get_db_connection()
        c = conn.cursor()
        
        for row in reader:
            c.execute('''INSERT INTO vitals
                         (patient_id, heart_rate, systolic_bp, diastolic_bp, 
                          oxygen_sat, temperature, weight, recorded_at)
                         VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                      (patient_id,
                       int(row.get('heart_rate', 0)) or None,
                       int(row.get('systolic_bp', 0)) or None,
                       int(row.get('diastolic_bp', 0)) or None,
                       float(row.get('oxygen_sat', 0)) or None,
                       float(row.get('temperature', 0)) or None,
                       float(row.get('weight', 0)) or None,
                       row.get('recorded_at', datetime.now().isoformat())))
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Vitals uploaded successfully'}), 201
    
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/symptoms/report', methods=['POST'])
def report_symptoms():
    """Report patient symptoms."""
    data = request.get_json()
    patient_id = data.get('patient_id')
    symptom_text = data.get('symptom_text')
    severity = data.get('severity', 5)
    
    if not patient_id or not symptom_text:
        return jsonify({'error': 'patient_id and symptom_text required'}), 400
    
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('''INSERT INTO symptoms
                 (patient_id, symptom_text, severity, reported_at)
                 VALUES (?, ?, ?, ?)''',
              (patient_id, symptom_text, severity, datetime.now().isoformat()))
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'message': 'Symptom reported'}), 201

@app.route('/api/assessment/<int:patient_id>')
def get_assessment(patient_id):
    """Get risk assessment for patient."""
    risk_score, risk_level = calculate_risk_score(patient_id)
    
    return jsonify({
        'patient_id': patient_id,
        'risk_score': round(risk_score, 2),
        'risk_level': risk_level,
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/patients')
def list_patients():
    """Get all patients as JSON (for dashboard API)."""
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('SELECT * FROM patients')
    patients = c.fetchall()
    conn.close()
    
    patient_list = []
    for p in patients:
        risk_score, risk_level = calculate_risk_score(p['id'])
        patient_list.append({
            'id': p['id'],
            'first_name': p['first_name'],
            'last_name': p['last_name'],
            'email': p['email'],
            'risk_score': round(risk_score, 2),
            'risk_level': risk_level
        })
    
    return jsonify(patient_list)

# ==================== INITIALIZATION ====================

@app.before_first_request
def setup():
    """Initialize database and create demo user."""
    if not os.path.exists(DATABASE):
        init_db()
        
        # Create demo clinician user
        conn = get_db_connection()
        c = conn.cursor()
        try:
            c.execute('''INSERT INTO users (username, password_hash, name, role)
                         VALUES (?, ?, ?, ?)''',
                      ('clinician', hash_password('password123'), 'Demo Clinician', 'clinician'))
            conn.commit()
        except:
            pass  # User already exists
        conn.close()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
