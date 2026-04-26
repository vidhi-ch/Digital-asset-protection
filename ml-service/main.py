from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
import tempfile, os, uuid
from dotenv import load_dotenv
from datetime import datetime
from google.cloud.firestore_v1.base_query import FieldFilter
from config import BUCKET_NAME
from core.embeddings import get_image_embedding, get_video_embedding
from core.similarity import compare_embeddings, batch_compare, cosine_similarity
from core.vector_search import search_similar
from analysis.vision import analyze_image
from analysis.video import analyze_video
from analysis.gemini import compare_images, explain_result, check_tampering_only
from services.firestore_handler import (
    register_media,
    get_all_registered_media,
    store_detection,
    get_detections,
    update_detection_status,
    is_already_detected

)
from services.pubsub_handler import publish_new_detection
from utils.preprocessing import preprocess_image, validate_file, is_video
from utils.media_utils import download_from_url, upload_to_gcs, cleanup_temp_files
from core.clip_embeddings import get_clip_embedding, clip_cosine_similarity
from core.similarity import dual_verify, batch_compare
from services.scraper import search_all_platforms
from services.scheduler import run_periodic_scan
from utils.preprocessing import is_video
load_dotenv()

app = FastAPI(title="MediaShield AI", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {"status": "MediaShield AI running", "version": "1.0"}


@app.post("/register")
async def register_original(
    file: UploadFile = File(...),
    match_name: str = Form(...),
    teams: str = Form(...),
    event_date: str = Form(...),
    organization: str = Form(...),
    user_id: str = Form(...)
):
    validation = validate_file(file.filename)
    if not validation["valid"]:
        return {"error": validation["error"]}
    
    ext = os.path.splitext(file.filename)[1]
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=ext)
    tmp.write(await file.read())
    tmp.close()
    
    try:
        media_id = f"{organization}_{match_name}_{str(uuid.uuid4())[:8]}"
        gcs_uri = upload_to_gcs(tmp.name, f"originals/{media_id}{ext}")
        
        if is_video(file.filename):
            embedding = get_video_embedding(gcs_uri)
            vision_data = analyze_video(gcs_uri)
        else:
            processed = preprocess_image(tmp.name)
            embedding = get_image_embedding(processed)
            vision_data = analyze_image(processed)
            cleanup_temp_files(processed)
        
        metadata = {
            "match_name": match_name,
            "teams": teams,
            "event_date": event_date,
            "organization": organization,
            "user_id": user_id,
            "gcs_uri": gcs_uri,
            "filename": file.filename,
            "vision_data": vision_data,
            "registered_at": str(datetime.utcnow())
        }
        
        register_media(media_id, metadata, embedding)

        # Trigger background scan immediately after registration
        import threading
        def run_scan_background():
            from services.scheduler import scan_one_media
            scan_one_media({
                "media_id": media_id,
                "embedding": embedding,
                "metadata": metadata
            })
        thread = threading.Thread(target=run_scan_background)
        thread.daemon = True
        thread.start()
        
        return {
            "success": True,
            "media_id": media_id,
            "message": "Registered and scan started automatically",
            "vision_analysis": vision_data
        }
    
    finally:
        cleanup_temp_files(tmp.name)

# UPDATE /registered-media endpoint
@app.get("/registered-media")
def get_registered_media(user_id: str = None):
    from google.cloud import firestore as fs
    from google.cloud.firestore_v1.base_query import FieldFilter
    db_client = fs.Client()
    
    query = db_client.collection("registered_media")
    if user_id:
        query = query.where(filter=FieldFilter("metadata.user_id", "==", user_id))
    
    docs = query.stream()
    result = []
    for doc in docs:
        d = doc.to_dict()
        d["id"] = doc.id
        d.pop("embedding", None)  # don't send huge vectors to frontend
        if "registered_at" in d and d["registered_at"]:
            d["registered_at"] = str(d["registered_at"])
        result.append(d)
    
    return {"media": result, "total": len(result)}


# ADD this new endpoint for dashboard summary counts
@app.get("/dashboard-summary")
def get_dashboard_summary(user_id: str):
    """
    Returns all 4 numbers the dashboard needs in one call:
    total_uploads, authorized, unauthorized, pending
    """
    from services.firestore_handler import get_detection_counts_by_user
    counts = get_detection_counts_by_user(user_id)
    return counts

@app.post("/analyze")
async def analyze_two_files(
    original: UploadFile = File(...),
    suspected: UploadFile = File(...)
):
    """
    Feature 2 — Anyone compares two files
    Uses dual verification (Vertex AI + CLIP if borderline)
    """
    tmp1 = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg")
    tmp2 = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg")
    tmp1.write(await original.read())
    tmp2.write(await suspected.read())
    tmp1.close()
    tmp2.close()

    try:
        # Vertex AI embeddings
        emb1 = get_image_embedding(tmp1.name)
        emb2 = get_image_embedding(tmp2.name)
        vertex_score = cosine_similarity(emb1, emb2)

        # Dual verify (CLIP activates if borderline)
        similarity = dual_verify(vertex_score, tmp1.name, tmp2.name)

        # Gemini smart analysis
        gemini = compare_images(tmp1.name, tmp2.name)

        # Vision API on suspected image
        vision = analyze_image(tmp2.name)

        # Explanation
        explanation = explain_result({**similarity, **gemini})

        return {
            "similarity": similarity,
            "gemini_analysis": gemini,
            "vision_analysis": vision,
            "explanation": explanation
        }

    finally:
        cleanup_temp_files(tmp1.name, tmp2.name)


@app.post("/analyze-urls")
async def analyze_two_urls(
    original_url: str = Form(...),
    suspected_url: str = Form(...)
):
    """
    Feature 2 alternate — Compare via URLs
    """
    path1 = download_from_url(original_url)
    path2 = download_from_url(suspected_url)

    try:
        emb1 = get_image_embedding(path1)
        emb2 = get_image_embedding(path2)
        vertex_score = cosine_similarity(emb1, emb2)

        similarity = dual_verify(vertex_score, path1, path2)
        gemini = compare_images(path1, path2)
        explanation = explain_result({**similarity, **gemini})

        return {
            "similarity": similarity,
            "gemini_analysis": gemini,
            "explanation": explanation
        }

    finally:
        cleanup_temp_files(path1, path2)


@app.post("/report")
async def public_report(
    suspected_url: str = Form(...),
    reported_by: str = Form(...),
    notes: str = Form(default="")
):
    """
    Feature 2 — Anyone reports a suspected copy
    We search our database for matching originals
    If found → alert the organization
    """
    path = None
    try:
        # Download suspected media
        path = download_from_url(suspected_url)
        suspected_emb = get_image_embedding(path)

        # Compare against ALL registered originals
        all_media = get_all_registered_media()
        matches = batch_compare(suspected_emb, all_media)

        new_alerts = []
        for match in matches:
            if not is_already_detected(
                match["media_id"], suspected_url
            ):
                detection = {
                    "original_media_id": match["media_id"],
                    "organization": match.get("organization"),
                    "match_name": match.get("match_name"),
                    "source_url": suspected_url,
                    "similarity_score": match["final_score"],
                    "similarity_percentage": match["similarity_percentage"],
                    "label": match["label"],
                    "is_match": match["is_match"],
                    "requires_review": match["requires_review"],
                    "reported_by": reported_by,
                    "notes": notes,
                    "type": "public_report",
                    "status": "pending"
                }
                detection_id = store_detection(detection)
                publish_new_detection(detection)
                new_alerts.append(detection_id)

        return {
            "message": "Report submitted",
            "matches_found": len(matches),
            "new_alerts_sent": len(new_alerts),
            "top_matches": matches[:3]
        }

    finally:
        cleanup_temp_files(path)


@app.get("/detections")
def get_all_detections(
    organization: str = None,
    status: str = None
):
    return {"detections": get_detections(organization, status)}


@app.post("/detections/update")
async def update_status(
    detection_id: str = Form(...),
    status: str = Form(...),
    updated_by: str = Form(...)
):
    update_detection_status(detection_id, status, updated_by)
    return {"success": True}

@app.post("/register-url")
async def register_from_url(
    media_url: str = Form(...),
    match_name: str = Form(...),
    teams: str = Form(...),
    event_date: str = Form(...),
    organization: str = Form(...),
    user_id: str = Form(...)
):
    path = None
    try:
        path = download_from_url(media_url)

        media_id = f"{organization}_{match_name}_{str(uuid.uuid4())[:8]}"
        ext = os.path.splitext(path)[1] or ".jpg"
        gcs_uri = upload_to_gcs(path, f"originals/{media_id}{ext}")

        processed = preprocess_image(path)
        embedding = get_image_embedding(processed)
        vision_data = analyze_image(processed)
        cleanup_temp_files(processed)

        metadata = {
            "match_name": match_name,
            "teams": teams,
            "event_date": event_date,
            "organization": organization,
            "user_id": user_id,
            "original_url": media_url,
            "gcs_uri": gcs_uri,
            "vision_data": vision_data,
            "note": "Registered via URL — thumbnail used for YouTube/Instagram links"
        }

        register_media(media_id, metadata, embedding)

        return {
            "success": True,
            "media_id": media_id,
            "message": "Media registered successfully. Note: For YouTube/Instagram, thumbnail was used as fingerprint.",
            "vision_analysis": vision_data
        }

    except ValueError as e:
        return {
            "success": False,
            "error": str(e),
            "suggestion": "For Instagram/YouTube content, please download the file and use the /register file upload endpoint instead."
        }

    finally:
        cleanup_temp_files(path)

@app.post("/scan/trigger")
async def trigger_scan_manually():
    """
    Manually trigger a scan (useful for demo)
    In production this runs automatically via Cloud Scheduler
    """
    result = run_periodic_scan()
    return result
@app.get("/detections/grouped")
def get_detections_grouped(user_id: str = None, status: str = None):
    """
    For when user clicks a card on dashboard.
    Returns detections filtered by user and optionally by status.
    """
    from google.cloud import firestore as fs
    from google.cloud.firestore_v1.base_query import FieldFilter
    db_client = fs.Client()

    # Get this user's media_ids first
    media_query = db_client.collection("registered_media")
    if user_id:
        media_query = media_query.where(
            filter=FieldFilter("metadata.user_id", "==", user_id)
        )
    user_media_ids = [doc.to_dict().get("media_id") for doc in media_query.stream()]

    if not user_media_ids:
        return {"detections": [], "total": 0}

    # Fetch detections for those media_ids
    all_detections = []
    for media_id in user_media_ids:
        det_query = db_client.collection("detections")\
            .where(filter=FieldFilter("original_media_id", "==", media_id))
        if status:
            det_query = det_query.where(filter=FieldFilter("status", "==", status))
        for doc in det_query.stream():
            d = doc.to_dict()
            d["id"] = doc.id
            for key in ["detected_at", "reviewed_at"]:
                if key in d and d[key]:
                    d[key] = str(d[key])
            all_detections.append(d)

    return {"detections": all_detections, "total": len(all_detections)}
@app.get("/detections/{media_id}")
def get_detections_for_media(media_id: str):
    """
    Get all detections for one registered media
    Categorized by status
    """
    from google.cloud import firestore
    db = firestore.Client()

    docs = db.collection("detections")\
          .where(filter=FieldFilter("original_media_id", "==", media_id))\
          .stream()

    authorized = []
    unauthorized = []
    pending = []

    for doc in docs:
        d = doc.to_dict()
        d["id"] = doc.id
        for key in ["detected_at", "reviewed_at"]:
            if key in d and d[key]:
                d[key] = str(d[key])

        status = d.get("status", "pending")
        if status == "authorized":
            authorized.append(d)
        elif status == "unauthorized":
            unauthorized.append(d)
        else:
            pending.append(d)

    return {
        "media_id": media_id,
        "authorized": authorized,
        "unauthorized": unauthorized,
        "pending": pending,
        "total": len(authorized) + len(unauthorized) + len(pending)
    }

@app.get("/org/{organization}/stats")
def get_organization_stats(organization: str):
    """
    Get full stats for one organization:
    - total original uploads
    - detections breakdown (authorized/unauthorized/pending)
    """
    from services.firestore_handler import get_org_stats
    return get_org_stats(organization)


@app.get("/org/{organization}/media")
def get_organization_media(organization: str):
    """
    Get all registered media for one organization
    with their detection counts
    """
    from google.cloud import firestore
    db = firestore.Client()

    media_docs = db.collection("registered_media")\
        .where("metadata.organization", "==", organization)\
        .stream()

    result = []
    for doc in media_docs:
        d = doc.to_dict()
        media_id = d.get("media_id")

        # Count detections for this specific media
        det_docs = db.collection("detections")\
            .where("original_media_id", "==", media_id)\
            .stream()

        auth = unauth = pend = 0
        for det in det_docs:
            s = det.to_dict().get("status", "pending")
            if s == "authorized": auth += 1
            elif s == "unauthorized": unauth += 1
            else: pend += 1

        result.append({
            "media_id": media_id,
            "match_name": d.get("metadata", {}).get("match_name"),
            "teams": d.get("metadata", {}).get("teams"),
            "event_date": d.get("metadata", {}).get("event_date"),
            "registered_at": str(d.get("registered_at", "")),
            "gcs_uri": d.get("metadata", {}).get("gcs_uri"),
            "detections": {
                "authorized": auth,
                "unauthorized": unauth,
                "pending": pend,
                "total": auth + unauth + pend
            }
        })

    return {
        "organization": organization,
        "total_uploads": len(result),
        "media": result
    }
@app.delete("/detections/{detection_id}")
async def delete_detection(detection_id: str):
    """
    User marks a detection as incorrect — deletes it entirely
    """
    from google.cloud import firestore as fs
    db_client = fs.Client()
    db_client.collection("detections").document(detection_id).delete()
    return {"success": True, "deleted_id": detection_id}

@app.get("/my-media")
def get_my_media(user_id: str):
    """
    Get all media registered by this user
    """
    from services.firestore_handler import get_media_by_user
    media = get_media_by_user(user_id)
    return {"media": media, "total": len(media)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
