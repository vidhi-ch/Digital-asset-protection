import os
from dotenv import load_dotenv
load_dotenv()

print("Testing setup...\n")

# Test 1: Credentials file exists
creds_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
if os.path.exists(creds_path):
    print("✅ Service account JSON found")
else:
    print("❌ Service account JSON NOT found — check path")

# Test 2: Firestore
try:
    from google.cloud import firestore
    db = firestore.Client()
    db.collection("registered_media").limit(1).get()
    print("✅ Firestore connected")
except Exception as e:
    print(f"❌ Firestore error: {e}")

# Test 3: Cloud Storage
try:
    from google.cloud import storage
    client = storage.Client()
    bucket = client.bucket(os.getenv("BUCKET_NAME"))
    bucket.reload()
    print("✅ Cloud Storage connected")
except Exception as e:
    print(f"❌ Storage error: {e}")

# Test 4: Vertex AI
try:
    import vertexai
    vertexai.init(
        project=os.getenv("PROJECT_ID"),
        location=os.getenv("LOCATION")
    )
    print("✅ Vertex AI connected")
except Exception as e:
    print(f"❌ Vertex AI error: {e}")

# Test 5: Pub/Sub
try:
    from google.cloud import pubsub_v1
    publisher = pubsub_v1.PublisherClient()
    project_path = f"projects/{os.getenv('PROJECT_ID')}"
    publisher.list_topics(request={"project": project_path})
    print("✅ Pub/Sub connected")
except Exception as e:
    print(f"❌ Pub/Sub error: {e}")

print("\nSetup test complete!")