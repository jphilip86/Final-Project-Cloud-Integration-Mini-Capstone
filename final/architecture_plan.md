# Architecture & Implementation Plan: Remote Patient Triage System

## 1. Service Mapping

| Layer                    | Service (Cloud)                         | Role in Solution                                         | Related Assignment/Module                               |
| ------------------------ | --------------------------------------- | -------------------------------------------------------- | ------------------------------------------------------- |
| **Frontend**       | Flask Web App + HTML/CSS                | Patient intake forms, clinician dashboard, vital uploads | Assignment 2 (Basic Flask app)                          |
| **API/Compute**    | Cloud Run (or local Flask for dev)      | RESTful API endpoints for data submission and retrieval  | Assignment 3 (Cloud Functions)                          |
| **Storage**        | Google Cloud Storage (GCS)              | Store uploaded wearable data files (CSV), backups        | Module 6 (Cloud Storage)                                |
| **Database**       | Cloud SQL (PostgreSQL)                  | Store patient records, vitals, symptoms, assessments     | Assignment 4 (Managed Services), Module 7-8 (Databases) |
| **Analytics/AI**   | Vertex AI (Pre-trained Models)          | Risk scoring, optional severity prediction from symptoms | Module 9 (ML)                                           |
| **Authentication** | Service Account + Environment Variables | Secure credential management for cloud services          | Assignment 4 (IAM & Security)                           |

---

## 2. Data Flow Narrative

### End-to-End Flow:

**Step 1: Patient Registration & Intake**

- Patient accesses Flask app at `/` (home page)
- Fills out intake form with demographics, medical history
- Form POST request goes to `/api/patient/register`
- Flask validates data and inserts into Cloud SQL database

**Step 2: Wearable Data Upload**

- Patient or clinic staff uploads vital signs CSV file via `/upload`
- Flask receives file, stores it in GCS bucket (`patient-vitals/`)
- File is parsed and individual vital records inserted into Cloud SQL
- Timestamp and patient ID are recorded for correlation

**Step 3: Symptom Reporting**

- Patient submits symptoms via mobile form or web UI (`/api/symptoms/report`)
- Data includes: symptoms, severity (1-10), onset time, duration
- Stored in Cloud SQL with timestamp

**Step 4: Automated Risk Assessment**

- Flask combines latest vitals + symptom data for the patient
- Optional: Calls Vertex AI API with patient features to predict triage risk
- Calculates simple risk score: abnormal vitals + high-severity symptoms = higher risk
- Stores assessment result in Cloud SQL with timestamp

**Step 5: Clinician Dashboard**

- Clinician logs in and accesses `/dashboard`
- Flask queries Cloud SQL to fetch all patients with risk scores
- Dashboard displays patients color-coded by risk (green = low, yellow = medium, red = high)
- Clinician clicks on patient to view detailed history (vitals chart, symptoms, notes)

**Step 6: Data Export & Audit**

- System can export patient cohorts to CSV and upload to GCS for backup
- Optional: BigQuery integration for large-scale analytics on aggregate patient data

## 3. Security, Identity & Governance

### Credential Management

- All sensitive credentials (database password, API keys, storage bucket names) are stored in **environment variables**
- `.env` file is kept **local only** and never committed to version control (`.gitignore`)
- When deployed to Cloud Run, credentials are managed via **Google Service Account** with principle of least privilege
- Each service account has only the permissions it needs (e.g., Cloud SQL client role, Storage Object Viewer/Creator)

### Access Control & RBAC

- **Patient Data Access:** Only authenticated clinicians can view patient dashboards (user session token validation)
- **Database Access:** Cloud SQL only allows connections from authorized Cloud Run instances via private IP or Cloud SQL Proxy
- **File Access:** GCS bucket policies restrict uploads/downloads to authenticated service accounts only
- **API Endpoints:** Critical endpoints (`/api/patient/register`, `/api/assessment`) validate API keys or JWT tokens

### PHI & Data Privacy

- **No Real PHI in Development:** Prototype uses mock/fake patient data and vitals for demonstration
- **Encryption in Transit:** All communications use HTTPS/TLS
- **Encryption at Rest:** GCS buckets and Cloud SQL enable encryption at rest by default
- **Data Retention:** Old vital sign files can be automatically deleted after 90 days (GCS lifecycle policies)
- **Audit Logging:** Cloud SQL and GCS enable query/access logging for compliance audits

---

## 4. Cost & Operational Considerations

### Cost Breakdown

| Component                        | Estimated Monthly Cost                                                                       | Notes                                                     |
| -------------------------------- | -------------------------------------------------------------------------------------------- | --------------------------------------------------------- |
| **Cloud SQL (PostgreSQL)** | $15-50                                                                                       | Depends on storage and compute; shared instance for dev   |
| **Cloud Storage (GCS)**    | $0.5-2                                                                                       | Minimal for low-volume clinic data; ~100 GB uploads/month |
| **Cloud Run (Compute)**    | $0-20 | Pay-per-request; ~$0.40 per 1M requests; free tier covers small deployments          |                                                           |
| **Vertex AI Calls**        | $0-10 | Pre-trained models are cheaper; custom training would be $$$. Free tier available. |                                                           |
| **BigQuery (Optional)**    | $0-5                                                                                         | Per-query pricing; free tier includes 1 TB/month          |
| **Total (Student Budget)** | **$15-87/month**                                                                       | Entire stack stays within free tier + minimal paid tier   |

### Operational Efficiency

**Serverless First:**

- Flask deployed on **Cloud Run** for automatic scaling; no running VMs
- Scheduled Cloud Functions (optional) could run nightly data cleanup and exports instead of always-on jobs
- Only pay for compute when requests arrive

**Data Storage Strategy:**

- Store raw wearable CSV uploads in GCS for 30 days, then archive to Coldline (cheaper)
- Keep recent vitals (7-14 days) in Cloud SQL for fast queries; older data archived to BigQuery

**Budget Optimization:**

- Use **GCP Free Tier:** Cloud SQL (750 hrs/month), Cloud Run (2M invocations/month), GCS (5 GB storage)
- Prototype stays within free tier for development/testing
- Scale payment components only when in production with real patients

---

## 5. Deployment Architecture

### Local Development

```
Patient/Staff → Flask Dev Server (localhost:5000)
             → Local SQLite or Cloud SQL Proxy
             → Mock GCS (local file storage)
             → Mock Vertex AI (hardcoded risk scores)
```

### Production on Google Cloud

```
Patient/Staff → Load Balancer
             → Cloud Run (Flask Container)
             → Cloud SQL (Managed PostgreSQL)
             → Cloud Storage (GCS)
             → Vertex AI API
```

### Deployment Steps

1. Create GCP project and enable APIs (Cloud SQL, Cloud Run, Cloud Storage, Vertex AI)
2. Set up Cloud SQL PostgreSQL instance (shared tier for cost savings)
3. Create GCS bucket for vital file uploads
4. Create Service Account with appropriate roles
5. Build Flask container image and push to Artifact Registry
6. Deploy Flask container to Cloud Run with service account and environment variables
7. Configure Cloud SQL Proxy or Cloud SQL connectors for database access
8. Test endpoints and clinician dashboard

---

## 6. Mapping to Prior Coursework

| Assignment/Module                                    | How It's Used                                                            |
| ---------------------------------------------------- | ------------------------------------------------------------------------ |
| **Assignment 2:** Basic Flask App              | Foundation for patient intake forms and clinician dashboard              |
| **Assignment 3:** Cloud Functions              | Serverless approach; potential for event-driven data processing          |
| **Assignment 4:** Managed Services & Databases | Cloud SQL PostgreSQL; IAM roles and service accounts                     |
| **Module 5:** Serverless                       | Cloud Run deployment instead of VMs                                      |
| **Module 6:** Cloud Storage                    | GCS for storing wearable CSV uploads and backups                         |
| **Module 7-8:** Databases                      | Cloud SQL schema design for patients, vitals, symptoms, assessments      |
| **Module 9:** ML & Analytics                   | Vertex AI for risk prediction; optional BigQuery for aggregate analytics |

---

## 7. Future Enhancements (4-8 Weeks, Unlimited Budget)

1. **Mobile App:** Native iOS/Android app for patient self-reporting instead of web forms
2. **Real-time Alerts:** Pub/Sub messaging to trigger alerts when risk score exceeds threshold
3. **Advanced Analytics:** BigQuery + Looker dashboards for population health insights
4. **ML Model Training:** Custom Vertex AI model trained on clinic's historical triage data
5. **Electronic Health Record (EHR) Integration:** HL7/FHIR APIs to sync with hospital EHR systems
6. **Multi-tenant Support:** RBAC for multiple clinic networks sharing the platform
7. **Compliance & Auditing:** Full HIPAA/GDPR audit logging; de-identification pipelines
8. **Telemedicine Integration:** Video consultation hooks via Twilio or Google Meet APIs
