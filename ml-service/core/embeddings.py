import os
import base64
import requests as req
import tempfile
from dotenv import load_dotenv
import warnings
warnings.filterwarnings("ignore", category=UserWarning)

load_dotenv()

PROJECT_ID = os.getenv("PROJECT_ID")
LOCATION = os.getenv("LOCATION", "us-central1")
BUCKET_NAME = os.getenv("BUCKET_NAME")
EMBEDDING_DIMENSION = 1408

# ─────────────────────────────────────────
# Auth — explicitly use service account
# ─────────────────────────────────────────
def _get_access_token() -> str:
    """
    Get access token - works both locally (service account file)
    and on Cloud Run (automatic credentials).
    """
    import time
    import google.auth
    import google.auth.transport.requests

    last_error = None
    for attempt in range(4):
        try:
            # Try automatic credentials first (works on Cloud Run)
            # Falls back to service account file locally
            creds, project = google.auth.default(
                scopes=["https://www.googleapis.com/auth/cloud-platform"]
            )
            auth_req = google.auth.transport.requests.Request()
            creds.refresh(auth_req)
            return creds.token

        except Exception as e:
            last_error = e
            wait = 2 ** attempt
            print(f"Token attempt {attempt + 1}/4 failed, retrying in {wait}s: {e}")
            time.sleep(wait)
            continue

    raise Exception(f"Failed to get access token after 4 attempts: {last_error}")


# ─────────────────────────────────────────
# Image Embedding
# ─────────────────────────────────────────
def get_image_embedding(image_path: str) -> list:
    """
    Generate embedding for an image using Vertex AI REST API.
    Includes retry logic for SSL errors.
    """
    with open(image_path, "rb") as f:
        image_b64 = base64.b64encode(f.read()).decode("utf-8")

    ext = os.path.splitext(image_path)[1].lower()
    mime_map = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".webp": "image/webp",
        ".gif": "image/gif",
        ".bmp": "image/bmp"
    }
    mime_type = mime_map.get(ext, "image/jpeg")

    token = _get_access_token()

    url = (
        f"https://{LOCATION}-aiplatform.googleapis.com/v1/projects/"
        f"{PROJECT_ID}/locations/{LOCATION}/publishers/google/"
        f"models/multimodalembedding@001:predict"
    )

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    payload = {
        "instances": [
            {
                "image": {
                    "bytesBase64Encoded": image_b64,
                    "mimeType": mime_type
                }
            }
        ],
        "parameters": {"dimension": EMBEDDING_DIMENSION}
    }

    # Retry up to 3 times for SSL errors
    import time
    last_error = None
    for attempt in range(3):
        try:
            session = req.Session()
            # Configure retry adapter
            from requests.adapters import HTTPAdapter
            from urllib3.util.retry import Retry
            retry_strategy = Retry(
                total=2,
                backoff_factor=1,
                status_forcelist=[429, 500, 502, 503, 504]
            )
            adapter = HTTPAdapter(max_retries=retry_strategy)
            session.mount("https://", adapter)

            response = session.post(
                url,
                headers=headers,
                json=payload,
                timeout=60,  # increased from 30
                verify=True
            )
            response.raise_for_status()
            result = response.json()
            return result["predictions"][0]["imageEmbedding"]

        except req.exceptions.SSLError as e:
            last_error = e
            print(f"SSL error on attempt {attempt + 1}/3, retrying in {2 ** attempt}s...")
            time.sleep(2 ** attempt)  # exponential backoff: 1s, 2s, 4s
            # Refresh token on retry
            token = _get_access_token()
            headers["Authorization"] = f"Bearer {token}"
            continue

        except Exception as e:
            raise e

    raise Exception(f"Failed after 3 SSL retries: {last_error}")


# ─────────────────────────────────────────
# Video Embedding
# ─────────────────────────────────────────
def get_video_embedding(gcs_uri: str) -> list:
    """
    Generate embedding for a video stored in GCS.
    Returns averaged vector across all segments.
    """
    import time
    from requests.adapters import HTTPAdapter
    from urllib3.util.retry import Retry

    token = _get_access_token()

    url = (
        f"https://{LOCATION}-aiplatform.googleapis.com/v1/projects/"
        f"{PROJECT_ID}/locations/{LOCATION}/publishers/google/"
        f"models/multimodalembedding@001:predict"
    )

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    payload = {
        "instances": [
            {
                "video": {
                    "gcsUri": gcs_uri
                }
            }
        ],
        "parameters": {"dimension": EMBEDDING_DIMENSION}
    }

    last_error = None
    for attempt in range(3):
        try:
            session = req.Session()
            retry_strategy = Retry(total=2, backoff_factor=1)
            adapter = HTTPAdapter(max_retries=retry_strategy)
            session.mount("https://", adapter)

            response = session.post(
                url, headers=headers, json=payload, timeout=120
            )
            response.raise_for_status()
            result = response.json()

            segments = result["predictions"][0].get("videoEmbeddings", [])
            if not segments:
                return None

            all_vecs = [seg["embedding"] for seg in segments]
            avg = [sum(x) / len(x) for x in zip(*all_vecs)]
            return avg

        except req.exceptions.SSLError as e:
            last_error = e
            print(f"SSL error on attempt {attempt + 1}/3, retrying...")
            time.sleep(2 ** attempt)
            token = _get_access_token()
            headers["Authorization"] = f"Bearer {token}"
            continue

        except Exception as e:
            raise e

    raise Exception(f"Failed after 3 SSL retries: {last_error}")


# ─────────────────────────────────────────
# Embedding from URL
# ─────────────────────────────────────────
def get_embedding_from_url(url: str) -> list:
    """
    Generate embedding from a public URL.
    Downloads first, then generates embedding.
    """
    from utils.media_utils import download_from_url, cleanup_temp_files
    from utils.preprocessing import is_image, is_video

    local_path = download_from_url(url)
    try:
        if is_image(local_path):
            return get_image_embedding(local_path)
        else:
            from utils.media_utils import upload_to_gcs
            import uuid
            gcs_uri = upload_to_gcs(
                local_path, f"temp/{uuid.uuid4()}.mp4"
            )
            return get_video_embedding(gcs_uri)
    finally:
        cleanup_temp_files(local_path)


# ─────────────────────────────────────────
# Cloud Storage Upload
# ─────────────────────────────────────────
def upload_to_gcs(local_path: str, filename: str) -> str:
    from google.cloud import storage
    client = storage.Client()
    bucket = client.bucket(BUCKET_NAME)
    blob = bucket.blob(filename)
    blob.upload_from_filename(local_path)
    return f"gs://{BUCKET_NAME}/{filename}"