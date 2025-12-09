# Remote Patient Triage & Monitoring System - Prototype

A Flask-based prototype demonstrating cloud integration for healthcare patient management. This application showcases how multiple cloud services (databases, storage, compute, and AI) work together to build a scalable healthcare solution.

## Features

✅ **Patient Registration & Management**
- Create and store patient profiles with demographics and medical history
- Intuitive web forms for data entry

✅ **Vital Signs Tracking**
- Upload wearable device data via CSV files
- Store and retrieve historical vital signs
- Tracks: heart rate, blood pressure, oxygen saturation, temperature, weight

✅ **Symptom Reporting**
- Patient symptom submissions with severity ratings
- Time-stamped reports for trend analysis

✅ **Automated Risk Assessment**
- Calculates patient triage risk scores based on vitals and symptoms
- Color-coded risk levels: LOW (green), MEDIUM (yellow), HIGH (red)
- Simulates ML model integration (Vertex AI in production)

✅ **Clinician Dashboard**
- Real-time patient overview with risk indicators
- Patient detail views with vital history and symptoms
- Quick triage prioritization

✅ **Data Persistence**
- SQLite database (local development) / Cloud SQL (production)
- Secure credential management via environment variables

## Architecture Components

```
┌─────────────────────────────────────────┐
│   Flask Web Application                 │
│  (Patient Forms + Clinician Dashboard)  │
└────────────────┬────────────────────────┘
                 │
         ┌───────┴────────┐
         │                │
    ┌────▼─────┐     ┌────▼──────┐
    │  SQLite   │     │   File    │
    │ Database  │     │  Storage  │
    │(Local Dev)│     │  (CSV)    │
    └───────────┘     └───────────┘

Production: Replace with Cloud SQL + Google Cloud Storage + Vertex AI
```

## Quick Start

### Prerequisites
- Python 3.8+
- pip package manager
- Virtual environment (recommended)

### Installation

1. **Clone/Download the Project**
   ```bash
   cd prototype
   ```

2. **Create Virtual Environment**
   ```bash
   python -m venv venv
   # On Windows:
   venv\Scripts\activate
   # On macOS/Linux:
   source venv/bin/activate
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the Application**
   ```bash
   python app.py
   ```

5. **Access the Application**
   - Open browser and navigate to: `http://localhost:5000`

### Demo Credentials

**Clinician Login:**
- **Username:** `clinician`
- **Password:** `password123`

## Usage Guide

### 1. Clinician Dashboard
- After login, view all registered patients
- Each patient card shows:
  - Patient name and contact info
  - Risk level (HIGH, MEDIUM, LOW)
  - Risk score (0.0 - 1.0)

### 2. Register a Patient
- Click "Register Patient" button
- Fill in demographics, DOB, medical history
- Patient is immediately available for data entry

### 3. Upload Vital Signs
- Click on a patient to view details
- Upload CSV file with vital data

**CSV Format Example:**
```csv
heart_rate,systolic_bp,diastolic_bp,oxygen_sat,temperature,weight,recorded_at
72,120,80,98.5,37.2,70.5,2024-01-15T09:00:00
88,135,85,97.2,37.5,70.6,2024-01-15T10:00:00
65,118,78,99.0,36.8,70.4,2024-01-15T14:00:00
```

### 4. Report Symptoms
- Patients can submit symptoms with severity ratings (1-10)
- Examples: fever, cough, shortness of breath, nausea

### 5. View Risk Assessment
- System automatically calculates risk scores
- Risk assessment combines:
  - Abnormal vitals (heart rate, BP, O2 sat, temperature)
  - Severity of reported symptoms
- Clinicians use risk scores to prioritize patient follow-ups

## Cloud Integration (Production)

### Services Used

| Service | Purpose | Relation to Course |
|---------|---------|-------------------|
| **Cloud SQL** | Managed PostgreSQL database | Assignment 4, Module 7-8 |
| **Cloud Storage** | Store CSV uploads & backups | Module 6 |
| **Cloud Run** | Containerized Flask deployment | Assignment 3, Module 5 |
| **Vertex AI** | Risk prediction ML models | Module 9 |
| **Service Accounts** | Secure credential management | Assignment 4 |

### Environment Variables (.env)

Create a `.env` file for local development:

```bash
# Database
DATABASE_PATH=patient_triage.db
DATABASE_URL=postgresql://user:password@host/db

# Cloud Storage (GCP)
GCS_BUCKET=patient-vitals-bucket
GOOGLE_CLOUD_PROJECT=your-gcp-project-id

# Flask
SECRET_KEY=your-secret-key-here
FLASK_ENV=development
```

**.env file should NEVER be committed to version control** - add to `.gitignore`

## API Endpoints

All endpoints return JSON responses.

### Authentication
```
POST /login                    # Clinician login
GET  /logout                   # Logout
```

### Patient Management
```
GET  /api/patients             # List all patients
POST /register-patient         # Register new patient
GET  /patient/<id>             # Patient detail page
```

### Vital Signs
```
POST /api/vitals/upload        # Upload vital signs CSV
GET  /api/vitals/<patient_id>  # Get patient vitals
```

### Symptoms
```
POST /api/symptoms/report      # Report patient symptoms
```

### Assessment
```
GET  /api/assessment/<id>      # Get risk assessment for patient
```

## Database Schema

### Patients
```sql
CREATE TABLE patients (
    id INTEGER PRIMARY KEY,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    dob TEXT NOT NULL,
    phone TEXT,
    email TEXT,
    medical_history TEXT,
    created_at TIMESTAMP
);
```

### Vitals
```sql
CREATE TABLE vitals (
    id INTEGER PRIMARY KEY,
    patient_id INTEGER NOT NULL,
    heart_rate INTEGER,
    systolic_bp INTEGER,
    diastolic_bp INTEGER,
    oxygen_sat REAL,
    temperature REAL,
    weight REAL,
    recorded_at TIMESTAMP,
    FOREIGN KEY (patient_id) REFERENCES patients(id)
);
```

### Symptoms
```sql
CREATE TABLE symptoms (
    id INTEGER PRIMARY KEY,
    patient_id INTEGER NOT NULL,
    symptom_text TEXT NOT NULL,
    severity INTEGER,
    onset_time TIMESTAMP,
    duration_hours INTEGER,
    reported_at TIMESTAMP,
    FOREIGN KEY (patient_id) REFERENCES patients(id)
);
```

### Assessments
```sql
CREATE TABLE assessments (
    id INTEGER PRIMARY KEY,
    patient_id INTEGER NOT NULL,
    risk_score REAL NOT NULL,
    risk_level TEXT,
    notes TEXT,
    created_at TIMESTAMP,
    FOREIGN KEY (patient_id) REFERENCES patients(id)
);
```

## Risk Scoring Algorithm

The system calculates risk using a simple evidence-based model:

```
VITALS SCORING:
- Abnormal heart rate (< 60 or > 100 bpm)     → +0.2
- Abnormal BP (> 140 or < 90 systolic)        → +0.2
- Low oxygen (< 95%)                          → +0.3
- Fever (> 38.5°C)                            → +0.2

SYMPTOM SCORING:
- Each symptom: (severity / 50)               → +0.02 to +0.2

RISK LEVELS:
- Score 0.0 - 0.39                            → LOW (green)
- Score 0.40 - 0.69                           → MEDIUM (yellow)
- Score 0.70 - 1.0                            → HIGH (red)
```

**Production Note:** This simple rule-based system would be replaced with a trained ML model in Vertex AI for more accurate predictions.

## Security Considerations

### Development
- ⚠️ Debug mode ON (only for development)
- Uses SQLite (not for production)
- Demo credentials hardcoded (for testing)

### Production (Cloud Deployment)
- ✅ Use service accounts with least-privilege IAM roles
- ✅ Credentials stored in Secret Manager
- ✅ Database connections via Cloud SQL Proxy
- ✅ Encryption in transit (HTTPS/TLS)
- ✅ Encryption at rest (Cloud Storage, Cloud SQL)
- ✅ No PHI in non-production environments
- ✅ Audit logging enabled
- ✅ Regular backups of Cloud SQL

## Deployment Options

### Local Development
```bash
python app.py
# Runs on http://localhost:5000
```

### Docker Deployment
```bash
# Create Dockerfile
docker build -t patient-triage:latest .
docker run -p 5000:5000 patient-triage:latest
```

### Google Cloud Run
```bash
gcloud builds submit --tag gcr.io/PROJECT_ID/patient-triage
gcloud run deploy patient-triage \
  --image gcr.io/PROJECT_ID/patient-triage \
  --platform managed \
  --region us-central1
```

## Testing

### Manual Testing
1. Register a test patient
2. Upload sample vital signs CSV
3. Report symptoms for the patient
4. Verify risk score calculation on dashboard

### Sample Test Data
- Patient: John Doe, DOB: 1980-05-15
- Vitals: HR 95, BP 135/82, O2 97%, Temp 37.0°C
- Symptoms: Mild cough (severity 4), Fatigue (severity 6)
- Expected Risk: MEDIUM (~0.45)

## Troubleshooting

### Port Already in Use
```bash
# Find process using port 5000
lsof -i :5000  # macOS/Linux
netstat -ano | findstr :5000  # Windows

# Kill process and restart
```

### Database Lock Issues
```bash
# Delete old database to start fresh
rm patient_triage.db
python app.py
```

### Module Import Errors
```bash
# Ensure virtual environment is activated
pip install -r requirements.txt --upgrade
```

## Future Enhancements

- [ ] Mobile app for patient self-reporting
- [ ] Real-time alerts via email/SMS
- [ ] Integration with EHR systems (HL7/FHIR)
- [ ] Advanced ML models in Vertex AI
- [ ] Telemedicine integration (Google Meet, Twilio)
- [ ] Multi-tenant support for clinic networks
- [ ] HIPAA/GDPR compliance audit trails
- [ ] BigQuery integration for population analytics
- [ ] Wearable device API integrations (Apple HealthKit, Fitbit, Garmin)

## Compliance & Privacy

**IMPORTANT:** This is a prototype for educational purposes. Do not use with real PHI without implementing:
- HIPAA compliance framework
- GDPR data handling procedures
- Encryption and key management
- Access control and audit logging
- Data retention policies
- Business Associate Agreements (BAAs)

## Course Mapping

| Assignment/Module | Demonstrated Concepts |
|-------------------|----------------------|
| **Assignment 2** | Flask web app, form handling, templating |
| **Assignment 3** | RESTful API design, serverless concepts |
| **Assignment 4** | Database management, service accounts, IAM |
| **Module 5** | Cloud Run deployment patterns |
| **Module 6** | Cloud Storage file uploads |
| **Module 7-8** | SQL database schema, queries |
| **Module 9** | ML integration, risk scoring model |

## Support

For issues or questions about:
- **Flask:** See [Flask Documentation](https://flask.palletsprojects.com/)
- **GCP Services:** See [Google Cloud Documentation](https://cloud.google.com/docs)
- **Database:** See [SQLite Documentation](https://www.sqlite.org/docs.html)

## License

This prototype is provided for educational purposes as part of HHA 504 coursework.

---

**Last Updated:** December 2024  
**Version:** 1.0 Prototype
