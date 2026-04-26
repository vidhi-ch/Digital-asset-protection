# 🛡️ MediaShield AI

**AI-powered sports media rights protection platform** — detects unauthorized use of IPL cricket content across YouTube, Google, and the web using multi-layer fingerprinting and real-time monitoring.

---

## 🚀 What It Does

MediaShield AI helps sports organizations (like BCCI/IPL) automatically detect when their media content is being misused online — without manually searching the internet.

### Feature 1 — Continuous Monitoring
Organizations register their original media (images/videos) by uploading a file or pasting a URL. The system fingerprints the content using AI and then periodically scans YouTube, Google, and Reddit for unauthorized copies. Every match found is categorized as **Pending**, **Authorized**, or **Unauthorized** on a live dashboard.

### Feature 2 — Public Comparison Tool
Anyone can report suspected misuse by submitting a URL. The system compares it against all registered originals and automatically alerts the relevant organization if a match is found.

---

## 🏗️ Architecture

```
React Frontend (Chaitanya)
        ↓ HTTP calls
Node.js Backend (Chaitanya)
        ↓ forwards to
FastAPI ML Service (Vidhi) ← YOU ARE HERE
        ↓
┌──────────────────────────────────────┐
│         Google Cloud Stack           │
│                                      │
│  Vertex AI Multimodal Embeddings     │
│  CLIP (secondary verification)       │
│  Cloud Vision API                    │
│  Video Intelligence API              │
│  Gemini Vision                       │
│  Cloud Storage                       │
│  Firestore                           │
│  Pub/Sub                             │
│  Cloud Run                           │
│  Cloud Scheduler                     │
└──────────────────────────────────────┘
```

### Dual Verification Logic
- **Vertex AI Multimodal Embeddings** → primary similarity score
- **CLIP (OpenAI)** → secondary verification, activates only in borderline zone (0.50–0.80)
- **Gemini Vision** → contextual tampering analysis (logo removal, cropping, color filters)
- **Cloud Vision API** → logo and text detection on individual frames

---

## 📁 Project Structure

```
ml-service/
├── analysis/
│   ├── gemini.py           # Gemini Vision comparison & tampering detection
│   ├── video.py            # Video Intelligence API
│   └── vision.py           # Cloud Vision API (logos, text, labels)
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
```

---

## ⚙️ Tech Stack

| Layer | Technology |
|---|---|
| ML Framework | Vertex AI Multimodal Embeddings, CLIP (HuggingFace) |
| Smart Analysis | Gemini Vision (`gemini-1.5-pro`) |
| Image Analysis | Cloud Vision API |
| Video Analysis | Video Intelligence API |
| Vector Search | Vertex AI Vector Search |
| Database | Cloud Firestore |
| File Storage | Cloud Storage |
| Messaging | Cloud Pub/Sub |
| Deployment | Cloud Run |
| Scheduling | Cloud Scheduler |
| API Framework | FastAPI |
| Web Scraping | YouTube Data API v3, Google Custom Search, Reddit |

---

## 🔌 API Endpoints

### Registration
| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/register` | Register original media via file upload |
| `POST` | `/register-url` | Register original media via URL |

### Detection & Monitoring
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/detections/{media_id}` | Get all detections for a registered media, grouped by status |
| `POST` | `/detections/update` | Mark detection as authorized / unauthorized / ignored |
| `POST` | `/scan/trigger` | Manually trigger a scan across all platforms |

### Feature 2 — Public Tool
| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/analyze` | Compare two uploaded files |
| `POST` | `/analyze-urls` | Compare two media URLs |
| `POST` | `/report` | Report suspected misuse — alerts org if match found |

### Health
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/` | Health check |

Full interactive API docs available at `/docs` when running locally.

---

## 🛠️ Setup & Installation

### Prerequisites
- Python 3.11+
- Google Cloud account with billing enabled
- Google Cloud project with these APIs enabled:
  - Vertex AI API
  - Cloud Vision API
  - Video Intelligence API
  - Cloud Storage API
  - Cloud Firestore API
  - Cloud Pub/Sub API
  - Cloud Run API
  - Cloud Scheduler API
  - YouTube Data API v3

### Local Development

```bash
# Clone the repo
git clone https://github.com/YOUR_USERNAME/mediashield-ai.git
cd mediashield-ai/ml-service

# Create virtual environment
python -m venv venv
source venv/bin/activate        # Mac/Linux
# venv\Scripts\activate         # Windows

# Install dependencies
pip install -r requirements.txt
```

### Environment Variables

Create `ml-service/.env`:

```env
GOOGLE_APPLICATION_CREDENTIALS=./service-account.json
PROJECT_ID=your-gcp-project-id
LOCATION=us-central1
BUCKET_NAME=your-cloud-storage-bucket

YOUTUBE_API_KEY=your-youtube-data-api-key
GOOGLE_API_KEY=your-google-api-key
GOOGLE_CX=your-custom-search-engine-id
```

Place your GCP service account JSON file at `ml-service/service-account.json`.

### Run Locally

```bash
python main.py
```

API docs will be available at: `http://localhost:8000/docs`

---

## ☁️ Cloud Deployment (Google Cloud Run)

```bash
cd ml-service

gcloud run deploy mediashield-ml \
  --source . \
  --region us-central1 \
  --allow-unauthenticated \
  --project YOUR_PROJECT_ID \
  --set-env-vars PROJECT_ID=your-project,LOCATION=us-central1,BUCKET_NAME=your-bucket,YOUTUBE_API_KEY=your-key,GOOGLE_API_KEY=your-key,GOOGLE_CX=your-cx
```

After deployment you'll get a permanent URL:
```
https://mediashield-ml-xxxxxxxx-uc.a.run.app
```

---

## 🔄 How the Scan Pipeline Works

```
Cloud Scheduler (every 30 min)
        ↓ POST /scan/trigger
Fetch all registered media from Firestore
        ↓
Build search query from metadata (match name, teams, date)
        ↓
Search YouTube Data API + Google Custom Search + Reddit
        ↓
Download each result thumbnail/image
        ↓
Generate Vertex AI embedding
        ↓
Compare against original embedding (cosine similarity)
        ↓ if score 0.50–0.80 (borderline)
CLIP verification kicks in (weighted 60/40)
        ↓ if score ≥ 0.70
Store detection in Firestore
        ↓
Publish alert to Pub/Sub
        ↓
Dashboard updates in real time
```

---

## 🗄️ Firestore Schema

### `registered_media` collection
```json
{
  "media_id": "IPL_CSKvsMI_a3f9b2c1",
  "embedding": [0.23, -0.91, ...],
  "metadata": {
    "match_name": "CSK vs MI",
    "teams": "CSK, MI",
    "event_date": "2024-04-05",
    "organization": "IPL",
    "gcs_uri": "gs://bucket/originals/...",
    "vision_data": { ... }
  },
  "registered_at": "timestamp",
  "status": "active"
}
```

### `detections` collection
```json
{
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
```

---

## 🤝 Team

| Role | Person |
|---|---|
| ML Backend | Vidhi |
| Frontend & Node Backend | Chaitanya |

---

## 📝 License

This project was built for a hackathon. All rights reserved.
