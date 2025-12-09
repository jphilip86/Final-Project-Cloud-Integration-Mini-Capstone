"""
Remote Patient Monitoring Dashboard - Flask Prototype
Demonstrates core functionality: patient intake, data storage, and dashboard display
"""

from flask import Flask, render_template, request, jsonify, session, redirect
from datetime import datetime, timedelta
import os
import json
from functools import wraps
import sqlite3

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

# Database configuration
DATABASE_PATH = 'patient_monitoring.db'

# Simple database helper
def get_db():
    """Get database connection"""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize database with schema"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    # Create tables
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS patients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            date_of_birth TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            phone TEXT,
            medical_history TEXT,
            current_medications TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS encounters (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id INTEGER NOT NULL,
            encounter_date TEXT DEFAULT CURRENT_TIMESTAMP,
            chief_complaint TEXT,
            assessment TEXT,
            plan TEXT,
            clinician_name TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(patient_id) REFERENCES patients(id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS vital_signs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id INTEGER NOT NULL,
            measurement_date TEXT DEFAULT CURRENT_TIMESTAMP,
            systolic_bp INTEGER,
            diastolic_bp INTEGER,
            heart_rate INTEGER,
            temperature REAL,
            oxygen_saturation REAL,
            blood_glucose REAL,
            notes TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(patient_id) REFERENCES patients(id)
        )
    ''')
    
    conn.commit()
    
    # Add sample data if database is empty
    cursor.execute('SELECT COUNT(*) FROM patients')
    if cursor.fetchone()[0] == 0:
        patients = [
            ('John', 'Smith', '1965-05-15', 'john.smith@email.com', '555-0101', 
             'Type 2 Diabetes, Hypertension', 'Metformin, Lisinopril'),
            ('Mary', 'Johnson', '1978-11-22', 'mary.johnson@email.com', '555-0102',
             'Asthma, Seasonal Allergies', 'Albuterol inhaler, Cetirizine'),
            ('Robert', 'Williams', '1955-03-10', 'robert.williams@email.com', '555-0103',
             'Coronary Artery Disease, Atrial Fibrillation', 'Warfarin, Atorvastatin'),
        ]
        
        for patient in patients:
            cursor.execute('''
                INSERT INTO patients 
                (first_name, last_name, date_of_birth, email, phone, medical_history, current_medications)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', patient)
        
        conn.commit()
        
        # Add sample vitals
        patient_ids = [1, 2, 3]
        for pid in patient_ids:
            vitals = [
                (pid, datetime.utcnow().isoformat(), 135, 85, 72, 36.8, 98, 110, None),
                (pid, (datetime.utcnow() - timedelta(hours=12)).isoformat(), 138, 87, 75, 36.9, 97, 115, None),
            ]
            for vital in vitals:
                cursor.execute('''
                    INSERT INTO vital_signs 
                    (patient_id, measurement_date, systolic_bp, diastolic_bp, heart_rate, 
                     temperature, oxygen_saturation, blood_glucose, notes)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', vital)
        
        conn.commit()
    
    conn.close()


# ============================================================================
# AUTHENTICATION (Simple for demo; use OAuth2 in production)
# ============================================================================

DEMO_CLINICIAN = {
    'username': 'doctor',
    'password': 'demo123',  # NEVER hardcode in production!
    'name': 'Dr. Jaison Philip'
}

def check_clinician_auth(f):
    """Decorator to check if clinician is authenticated"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'clinician_id' not in session:
            return jsonify({'error': 'Unauthorized'}), 401
        return f(*args, **kwargs)
    return decorated_function


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def calculate_age(dob_str):
    """Calculate age from date of birth string"""
    dob = datetime.fromisoformat(dob_str).date()
    today = datetime.utcnow().date()
    return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))

def check_vital_alerts(systolic_bp, diastolic_bp, heart_rate, temperature, oxygen_saturation, blood_glucose):
    """Check for abnormal vital readings"""
    alerts = []
    
    if systolic_bp and systolic_bp > 140:
        alerts.append(f"⚠️ High systolic BP: {systolic_bp} mmHg")
    if systolic_bp and systolic_bp < 90:
        alerts.append(f"⚠️ Low systolic BP: {systolic_bp} mmHg")
    
    if heart_rate and heart_rate > 100:
        alerts.append(f"⚠️ Elevated heart rate: {heart_rate} BPM")
    if heart_rate and heart_rate < 60:
        alerts.append(f"⚠️ Low heart rate: {heart_rate} BPM")
    
    if temperature and temperature > 38.5:
        alerts.append(f"🔥 High fever: {temperature}°C")
    if temperature and temperature < 36:
        alerts.append(f"❄️ Low temperature: {temperature}°C")
    
    if oxygen_saturation and oxygen_saturation < 94:
        alerts.append(f"⚠️ Low oxygen saturation: {oxygen_saturation}%")
    
    if blood_glucose and blood_glucose > 180:
        alerts.append(f"⚠️ High blood glucose: {blood_glucose} mg/dL")
    if blood_glucose and blood_glucose < 70:
        alerts.append(f"⚠️ Low blood glucose: {blood_glucose} mg/dL")
    
    return alerts


# ============================================================================
# ROUTES
# ============================================================================

@app.route('/')
def index():
    """Home page / login"""
    if 'clinician_id' in session:
        return redirect('/dashboard')
    return render_template('index.html')


@app.route('/login', methods=['POST'])
def login():
    """Authenticate clinician"""
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    if (username == DEMO_CLINICIAN['username'] and 
        password == DEMO_CLINICIAN['password']):
        session['clinician_id'] = 'clinician_001'
        session['clinician_name'] = DEMO_CLINICIAN['name']
        return jsonify({'success': True, 'message': 'Login successful'})
    
    return jsonify({'success': False, 'message': 'Invalid credentials'}), 401


@app.route('/logout')
def logout():
    """Log out clinician"""
    session.clear()
    return redirect('/')


@app.route('/dashboard')
@check_clinician_auth
def dashboard():
    """Main clinician dashboard"""
    conn = get_db()
    patients = conn.execute('SELECT * FROM patients').fetchall()
    conn.close()
    return render_template('dashboard.html',
                         clinician_name=session.get('clinician_name'),
                         patients=[dict(p) for p in patients])


@app.route('/new-patient')
@check_clinician_auth
def new_patient_form():
    """Show form to add new patient"""
    return render_template('new_patient.html',
                         clinician_name=session.get('clinician_name'))


@app.route('/patient/<int:patient_id>')
@check_clinician_auth
def patient_detail(patient_id):
    """View detailed patient information"""
    conn = get_db()
    patient = conn.execute('SELECT * FROM patients WHERE id = ?', (patient_id,)).fetchone()
    encounters = conn.execute('SELECT * FROM encounters WHERE patient_id = ? ORDER BY encounter_date DESC', 
                             (patient_id,)).fetchall()
    recent_vitals = conn.execute('SELECT * FROM vital_signs WHERE patient_id = ? ORDER BY measurement_date DESC LIMIT 10', 
                                (patient_id,)).fetchall()
    conn.close()
    
    if not patient:
        return {'error': 'Patient not found'}, 404
    
    return render_template('patient_detail.html',
                         patient=dict(patient),
                         encounters=[dict(e) for e in encounters],
                         recent_vitals=[dict(v) for v in recent_vitals])


@app.route('/api/patients', methods=['GET', 'POST'])
@check_clinician_auth
def manage_patients():
    """Get all patients or create new patient"""
    conn = get_db()
    
    if request.method == 'GET':
        patients = conn.execute('SELECT * FROM patients').fetchall()
        conn.close()
        return jsonify([dict(p) for p in patients])
    
    # POST: Create new patient
    data = request.get_json()
    try:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO patients 
            (first_name, last_name, date_of_birth, email, phone, medical_history, current_medications)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (data['first_name'], data['last_name'], data['date_of_birth'], 
              data['email'], data.get('phone'), data.get('medical_history'), 
              data.get('current_medications')))
        conn.commit()
        patient_id = cursor.lastrowid
        patient = conn.execute('SELECT * FROM patients WHERE id = ?', (patient_id,)).fetchone()
        conn.close()
        return jsonify(dict(patient)), 201
    except Exception as e:
        conn.close()
        return jsonify({'error': str(e)}), 400


@app.route('/api/patients/<int:patient_id>/vitals', methods=['GET', 'POST'])
@check_clinician_auth
def manage_vitals(patient_id):
    """Get patient vitals or record new vital signs"""
    conn = get_db()
    
    # Check patient exists
    patient = conn.execute('SELECT * FROM patients WHERE id = ?', (patient_id,)).fetchone()
    if not patient:
        conn.close()
        return jsonify({'error': 'Patient not found'}), 404
    
    if request.method == 'GET':
        vitals = conn.execute('SELECT * FROM vital_signs WHERE patient_id = ? ORDER BY measurement_date DESC LIMIT 30', 
                             (patient_id,)).fetchall()
        conn.close()
        return jsonify([dict(v) for v in vitals])
    
    # POST: Record new vital signs
    data = request.get_json()
    try:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO vital_signs 
            (patient_id, systolic_bp, diastolic_bp, heart_rate, temperature, oxygen_saturation, blood_glucose, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (patient_id, data.get('systolic_bp'), data.get('diastolic_bp'), 
              data.get('heart_rate'), data.get('temperature'), data.get('oxygen_saturation'),
              data.get('blood_glucose'), data.get('notes')))
        conn.commit()
        vital_id = cursor.lastrowid
        vital = conn.execute('SELECT * FROM vital_signs WHERE id = ?', (vital_id,)).fetchone()
        conn.close()
        
        # Check for alerts
        alerts = check_vital_alerts(
            data.get('systolic_bp'), data.get('diastolic_bp'), data.get('heart_rate'),
            data.get('temperature'), data.get('oxygen_saturation'), data.get('blood_glucose')
        )
        
        return jsonify({
            'vital': dict(vital),
            'alerts': alerts
        }), 201
    except Exception as e:
        conn.close()
        return jsonify({'error': str(e)}), 400


@app.route('/api/patients/<int:patient_id>/encounters', methods=['GET', 'POST'])
@check_clinician_auth
def manage_encounters(patient_id):
    """Get patient encounters or create new encounter"""
    conn = get_db()
    
    # Check patient exists
    patient = conn.execute('SELECT * FROM patients WHERE id = ?', (patient_id,)).fetchone()
    if not patient:
        conn.close()
        return jsonify({'error': 'Patient not found'}), 404
    
    if request.method == 'GET':
        encounters = conn.execute('SELECT * FROM encounters WHERE patient_id = ? ORDER BY encounter_date DESC', 
                                 (patient_id,)).fetchall()
        conn.close()
        return jsonify([dict(e) for e in encounters])
    
    # POST: Create new encounter
    data = request.get_json()
    try:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO encounters 
            (patient_id, chief_complaint, assessment, plan, clinician_name)
            VALUES (?, ?, ?, ?, ?)
        ''', (patient_id, data.get('chief_complaint'), data.get('assessment'),
              data.get('plan'), session.get('clinician_name')))
        conn.commit()
        encounter_id = cursor.lastrowid
        encounter = conn.execute('SELECT * FROM encounters WHERE id = ?', (encounter_id,)).fetchone()
        conn.close()
        return jsonify(dict(encounter)), 201
    except Exception as e:
        conn.close()
        return jsonify({'error': str(e)}), 400


@app.route('/api/alerts/<int:patient_id>')
@check_clinician_auth
def get_alerts(patient_id):
    """Get active alerts for a patient"""
    conn = get_db()
    vitals = conn.execute('SELECT * FROM vital_signs WHERE patient_id = ? ORDER BY measurement_date DESC LIMIT 5', 
                         (patient_id,)).fetchall()
    conn.close()
    
    all_alerts = []
    for vital in vitals:
        v = dict(vital)
        alerts = check_vital_alerts(
            v.get('systolic_bp'), v.get('diastolic_bp'), v.get('heart_rate'),
            v.get('temperature'), v.get('oxygen_saturation'), v.get('blood_glucose')
        )
        for alert in alerts:
            all_alerts.append({
                'alert': alert,
                'measured_at': v['measurement_date']
            })
    
    return jsonify(all_alerts)


@app.route('/health')
def health_check():
    """Health check endpoint for Cloud Run / deployment"""
    return jsonify({'status': 'healthy'}), 200


@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not found'}), 404


@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500



if __name__ == '__main__':
    # Initialize database on startup
    init_db()
    port = int(os.environ.get('PORT', 5000))
    print(f"Starting Flask app on port {port}...")
    app.run(debug=True, host='0.0.0.0', port=port)
