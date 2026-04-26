import os

# Works both locally (from .env) and on Cloud Run (from env vars)
from dotenv import load_dotenv
load_dotenv()

PROJECT_ID = os.getenv("PROJECT_ID")
LOCATION = os.getenv("LOCATION", "us-central1")
BUCKET_NAME = os.getenv("BUCKET_NAME")
SIMILARITY_THRESHOLD = 0.70
REVIEW_THRESHOLD = 0.50
EMBEDDING_DIMENSION = 1408

YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GOOGLE_CX = os.getenv("GOOGLE_CX")