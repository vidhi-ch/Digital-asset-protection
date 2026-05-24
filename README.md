🛡️ MediaShield AI
AI-Powered Digital Media Rights Protection

Built for the Google Solution Challenge 2026 — Team CodeStorm Duo

MediaShield AI is a platform where any individual or organization can register their original media, automatically monitor the internet for unauthorized copies, and take action — powered entirely by Google Cloud AI.

Note: Current prototype is designed for sports media (IPL/cricket) as a primary use case, with architecture built for extension to any content type.


🚨 The Problem
[ DIGITAL ASSET PROTECTION ] — Content creators, sports organizations, and media companies lose billions annually to unauthorized redistribution of their digital assets. Edited or re-uploaded content makes it nearly impossible to track the origin and ownership across platforms.

🚀 Our Solution
How It Works
1. User uploads media or provides a YouTube / Instagram link
        ↓
2. Vertex AI Fingerprinting + CLIP Verification
        ↓
3. Ranked results with similarity scores & source links shown in dashboard
        ↓
4. User verifies, flags, or reports unauthorized content

✨ Features
Multi-Layer Fingerprinting
Upload media or paste a YouTube/Instagram URL. Vertex AI generates an AI fingerprint, stored instantly in Firestore + Cloud Storage.
Automated Detections
Cloud Scheduler triggers every 2 days. Searches YouTube Data API, SerpAPI, RapidAPI, and Reddit simultaneously.
Gemini Vision Analysis
Detects tampering evidence on matched content — identifies logo removal, watermark erasure, and color filters. Returns structured reasoning, not just a score.
Live Detection Dashboard
Live categorization: Pending / Authorized / Unauthorized. One-click Authorize or Reject controls with real-time updates via Firestore.
Fully Cloud Deployed
Google Cloud Run with Firestore, Pub/Sub alerts, and Cloud Scheduler. Auto-scales without infrastructure management.
Manual Comparison (Future Addition)
Upload or paste two URLs to compare directly. Returns similarity score + Gemini explanation.

💡 How Is It Different?
vs. Existing SolutionsMediaShield AI AdvantageYouTube Content IDWorks across all platforms (YouTube, Instagram, Google, Reddit)Exact-match only toolsDetects cropped, filtered & re-watermarked copiesSingle-API solutions11 Google Cloud tools in one unified pipelineManual monitoringRegister once — system monitors automatically

🏗️ Architecture
Frontend (React.js)
        ↓ HTTP calls
Node.js + Express Backend
        ↓ forwards to
FastAPI ML Service (Python)
        ↓
┌──────────────────────────────────────────┐
│           Google Cloud Stack             │
│                                          │
│  Vertex AI Multimodal Embeddings         │
│  Gemini Vision (gemini-1.5-pro)          │
│  CLIP (OpenAI — secondary verification) │
│  Cloud Storage                           │
│  Cloud Firestore                         │
│  Cloud Pub/Sub                           │
│  Cloud Run                               │
│  Cloud Scheduler                         │
└──────────────────────────────────────────┘
Dual Verification Logic

Vertex AI Multimodal Embeddings → primary similarity score (cosine similarity)
CLIP (OpenAI) → secondary verification, activates only in borderline zone (0.50–0.80), weighted 60/40
Gemini Vision → contextual tampering analysis (logo removal, cropping, color filters)


🔄 Process Flow
Organisation/User Original Media Detection
User Logins & Uploads Original Media
        ↓
AI Fingerprinting & Stored in Cloud + Firestore
        ↓
Scan Triggered → YouTube, Instagram, Google, Reddit searched
        ↓
Compare Embeddings → If similarity > 50%, store detection
        ↓
Dashboard shows result → User reviews and takes actions
Manual Comparison (Backend ready, frontend in next sprint)
User Uploads Two Media / URLs for comparison
        ↓
Backend downloads both → Vertex AI creates Embeddings
        ↓
Cosine Similarity calculated → if needed, CLIP Verification
        ↓
Gemini does Vision Analysis
        ↓
Result returned with score + explanation

⚙️ Tech Stack
CategoryTechnologyGoogle AI & MLVertex AI Multimodal Embeddings, Gemini Vision (gemini-1.5-pro), CLIP (OpenAI — secondary)InfrastructureCloud Run, Cloud Scheduler, Cloud Pub/Sub, Cloud Firestore, Cloud StorageSearch / ScrapingYouTube Data API v3, RapidAPI (Google Images), SerpAPI (Instagram), Reddit Public APIFrontendReact.js, Firebase Hosting, Firebase AuthenticationBackendFastAPI + Python (ML service), Node.js + Express

📁 Project Structure
ml-service/
├── analysis/
│   └── gemini.py           # Gemini Vision comparison & tampering detection
├── core/
│   ├── clip_embeddings.py  # CLIP secondary verification layer
│   ├── embeddings.py       # Vertex AI Multimodal Embeddings
│   ├── similarity.py       # Dual verification + cosine similarity
│   └── vector_search.py    # Vertex AI Vector Search
├── services/
│   ├── firestore_handler.py # Firestore read/write operations
│   ├── pubsub_handler.py    # Pub/Sub alerts
│   └── scheduler.py         # Periodic scan pipeline
├── utils/
│   ├── media_utils.py       # Cloud Storage upload/download
│   └── preprocessing.py     # Image validation & resizing
├── config.py
├── main.py                  # FastAPI app & all endpoints
├── Dockerfile
└── requirements.txt

🔌 API Endpoints
Registration
MethodEndpointDescriptionPOST/registerRegister original media via file uploadPOST/register-urlRegister original media via URL
Detection & Monitoring
MethodEndpointDescriptionGET/detections/{media_id}Get all detections for a registered media, grouped by statusPOST/detections/updateMark detection as authorized / unauthorized / ignoredPOST/scan/triggerManually trigger a scan across all platforms
Public Tool
MethodEndpointDescriptionPOST/analyzeCompare two uploaded filesPOST/analyze-urlsCompare two media URLsPOST/reportReport suspected misuse — alerts org if match found
Health
MethodEndpointDescriptionGET/Health check
Full interactive API docs available at /docs when running locally.

🗄️ Firestore Schema
registered_media collection
json{
  "media_id": "IPL_CSKvsMI_a3f9b2c1",
  "embedding": [0.23, -0.91, "..."],
  "metadata": {
    "match_name": "CSK vs MI",
    "teams": "CSK, MI",
    "event_date": "2024-04-05",
    "organization": "IPL",
    "gcs_uri": "gs://bucket/originals/...",
    "vision_data": {}
  },
  "registered_at": "timestamp",
  "status": "active"
}
detections collection
json{
  "original_media_id": "IPL_CSKvsMI_a3f9b2c1",
  "source_url": "https://youtube.com/watch?v=...",
  "platform": "youtube",
  "similarity_score": 0.89,
  "similarity_percentage": "89.0%",
  "label": "High — Probable Match",
  "status": "pending",
  "is_match": true,
  "verification_method": "dual_verified",
  "detected_at": "timestamp",
  "type": "periodic_scan",
  "reviewed": false
}

🛠️ Setup & Installation
Prerequisites

Python 3.11+
Google Cloud account with billing enabled
Google Cloud project with the following APIs enabled:

Vertex AI API
Cloud Storage API
Cloud Firestore API
Cloud Pub/Sub API
Cloud Run API
Cloud Scheduler API
YouTube Data API v3

Local Development
bash# Clone the repo
git clone https://github.com/YOUR_USERNAME/mediashield-ai.git
cd mediashield-ai/ml-service

# Create virtual environment
python -m venv venv
source venv/bin/activate        # Mac/Linux
# venv\Scripts\activate         # Windows

# Install dependencies
pip install -r requirements.txt
Environment Variables
Create ml-service/.env:
envGOOGLE_APPLICATION_CREDENTIALS=./service-account.json
PROJECT_ID=your-gcp-project-id
LOCATION=us-central1
BUCKET_NAME=your-cloud-storage-bucket

YOUTUBE_API_KEY=your-youtube-data-api-key
GOOGLE_API_KEY=your-google-api-key
GOOGLE_CX=your-custom-search-engine-id
Place your GCP service account JSON at ml-service/service-account.json.
Run Locally
bashpython main.py
API docs: http://localhost:8000/docs

☁️ Cloud Deployment (Google Cloud Run)
bashcd ml-service

gcloud run deploy mediashield-ml \
  --source . \
  --region us-central1 \
  --allow-unauthenticated \
  --project YOUR_PROJECT_ID \
  --set-env-vars PROJECT_ID=your-project,LOCATION=us-central1,BUCKET_NAME=your-bucket,YOUTUBE_API_KEY=your-key,GOOGLE_API_KEY=your-key,GOOGLE_CX=your-cx
After deployment you'll get a permanent URL:
https://mediashield-ml-xxxxxxxx-uc.a.run.app

🔮 Future Development

Manual Comparison Tool — Upload or input multiple media files/links and directly compare similarity scores for quick verification and validation.
Real-time Monitoring System — Continuously scan online platforms and detect unauthorized media usage instantly instead of only on user input.
Automated Alert & Notification System — Notify users when similar or unauthorized content is detected, enabling quicker action without manual checking.
Expanded Search Coverage — Search across a wider range of platforms and domains for more comprehensive detection of duplicated or redistributed content.

🤝 Team — CodeStorm Duo
RolePersonTeam Leader & ML BackendVidhi ChandakFrontend & Node BackendChaitanya

📝 License
Built for Google Solution Challenge 2026. All rights reserved.
