# Use Case: Remote Patient Triage & Monitoring System

## Problem Statement

Healthcare clinics and remote care centers struggle with efficiently triaging patient intake and monitoring vital signs from remote patients. Current workflows are fragmented: patient intake forms are paper-based or stored in disconnected systems, vital sign data from wearable devices is not automatically integrated, and clinicians spend excessive time manually reviewing and categorizing patient data.

**Users:**
- Clinicians and nurses who need quick access to patient status
- Administrative staff managing intake and data entry
- Remote patients who submit vitals and symptoms via mobile app
- Clinic managers monitoring patient outcomes and system usage

---

## Data Sources

1. **Patient Intake Data**
   - Demographics, medical history, insurance information (initial form submission)
   - Format: JSON or form data from web interface
   - Source: Patient self-entry or staff data entry

2. **Vital Signs & Wearable Data**
   - Heart rate, blood pressure, oxygen saturation, temperature, weight
   - Format: JSON streams or CSV batch uploads from wearable devices (e.g., Fitbit, Apple Watch, medical-grade devices)
   - Source: Automated device APIs or manual uploads

3. **Symptom Reports**
   - Patient-reported symptoms, severity ratings, onset times
   - Format: JSON from mobile app
   - Source: Patient mobile application

4. **Clinical Assessment Data**
   - Clinician notes and triage decisions
   - Format: Text/JSON entered during patient consultation
   - Source: Clinician input via web portal

---

## Basic Workflow

1. **Patient Registration**
   - Patient visits clinic portal and completes intake form
   - Data is submitted to Flask API (`/api/patient/register`)
   - Form data is validated and stored in Cloud SQL database

2. **Vital Sign Upload**
   - Wearable device automatically exports vitals or patient manually uploads CSV
   - File is sent to Flask API (`/api/vitals/upload`)
   - Flask processes and stores raw data in Cloud Storage (GCS bucket)
   - Data is parsed and inserted into Cloud SQL for querying

3. **Symptom Reporting**
   - Patient submits symptoms via mobile form (`/api/symptoms/report`)
   - Symptoms are stored in database with timestamp
   - Flask combines vital signs + symptoms and calls Google AI API (Vertex AI) for risk assessment

4. **Triage Assessment & Risk Scoring**
   - System calculates risk score based on vitals + symptom data
   - Optional: Calls pre-trained ML model (Vertex AI) for severity prediction
   - Stores assessment in database

5. **Clinician Dashboard**
   - Clinician accesses `/dashboard` to view all patients
   - Data is fetched from Cloud SQL and displayed with color-coded risk levels
   - Clinician can click on patient to view full history and notes

6. **Data Export & Analytics**
   - System exports aggregated patient data to Cloud Storage
   - Optional: BigQuery integration for advanced analytics and reporting

---

## Benefits of Cloud Architecture

- **Scalability:** Handle multiple concurrent patient uploads and data streams
- **Reliability:** Managed databases ensure data persistence and availability
- **Security:** Cloud Storage with encryption, Cloud SQL with access controls, environment-based credential management
- **Cost Efficiency:** Pay-per-use model for storage and compute; serverless components for sporadic workloads
- **Interoperability:** RESTful APIs enable integration with external devices and EHR systems
