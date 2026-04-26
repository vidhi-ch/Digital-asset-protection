from google.cloud import firestore
from datetime import datetime
from google.cloud.firestore_v1.base_query import FieldFilter
db = firestore.Client()

def register_media(media_id: str, metadata: dict, embedding: list):
    db.collection("registered_media").document(media_id).set({
        "media_id": media_id,
        "embedding": embedding,
        "metadata": metadata,
        "registered_at": datetime.utcnow(),
        "status": "active"
    })
from google.cloud.firestore_v1.base_query import FieldFilter

def get_media_by_user(user_id: str) -> list:
    docs = db.collection("registered_media")\
        .where(filter=FieldFilter("metadata.user_id", "==", user_id))\
        .stream()
    result = []
    for doc in docs:
        d = doc.to_dict()
        d["id"] = doc.id
        # remove embedding from response (too large, frontend doesn't need it)
        d.pop("embedding", None)
        for key in ["registered_at"]:
            if key in d and d[key]:
                d[key] = str(d[key])
        result.append(d)
    return result

def get_detection_counts_by_user(user_id: str) -> dict:
    """
    Returns counts of authorized, unauthorized, pending
    for all media belonging to this user
    """
    # First get all media_ids for this user
    media_docs = db.collection("registered_media")\
        .where(filter=FieldFilter("metadata.user_id", "==", user_id))\
        .stream()
    
    user_media_ids = [doc.to_dict().get("media_id") for doc in media_docs]
    
    if not user_media_ids:
        return {"authorized": 0, "unauthorized": 0, "pending": 0, "total_uploads": 0}
    
    # Count detections per status for those media_ids
    # Firestore doesn't support OR queries across IDs natively,
    # so we fetch per media_id and aggregate
    authorized = 0
    unauthorized = 0
    pending = 0
    
    for media_id in user_media_ids:
        dets = db.collection("detections")\
            .where(filter=FieldFilter("original_media_id", "==", media_id))\
            .stream()
        for det in dets:
            status = det.to_dict().get("status", "pending")
            if status == "authorized":
                authorized += 1
            elif status == "unauthorized":
                unauthorized += 1
            else:
                pending += 1
    
    return {
        "total_uploads": len(user_media_ids),
        "authorized": authorized,
        "unauthorized": unauthorized,
        "pending": pending
    }

def store_detection(detection: dict) -> str:
    detection["detected_at"] = datetime.utcnow()
    detection["reviewed"] = False
    detection["status"] = "pending"
    ref = db.collection("detections").document()
    ref.set(detection)
    return ref.id

def get_all_registered_media() -> list:
    docs = db.collection("registered_media").stream()
    return [doc.to_dict() for doc in docs]

def is_already_detected(original_id: str, source_url: str) -> bool:
    existing = db.collection("detections")\
        .where(filter=FieldFilter("original_media_id", "==", original_id))\
        .where(filter=FieldFilter("source_url", "==", source_url))\
        .get()
    return len(existing) > 0

def update_detection_status(
    detection_id: str,
    status: str,
    updated_by: str
):
    db.collection("detections").document(detection_id).update({
        "status": status,
        "reviewed": True,
        "reviewed_by": updated_by,
        "reviewed_at": datetime.utcnow()
    })

def get_detections(organization=None, status=None):
    query = db.collection("detections")
    
    if organization:
        query = query.where(filter=FieldFilter("organization", "==", organization))
    if status:
        query = query.where(filter=FieldFilter("status", "==", status))
    
    results = []
    for doc in query.stream():
        d = doc.to_dict()
        d["id"] = doc.id
        for key in ["detected_at", "reviewed_at"]:
            if key in d and d[key]:
                d[key] = str(d[key])
        results.append(d)
    
    return results

def get_org_stats(organization: str) -> dict:
    """
    Returns stats for one organization:
    total uploads, detections breakdown by status
    """
    # Count registered media
    media_docs = db.collection("registered_media")\
        .where("metadata.organization", "==", organization)\
        .stream()
    
    media_list = []
    media_ids = []
    for doc in media_docs:
        d = doc.to_dict()
        media_list.append({
            "media_id": d.get("media_id"),
            "match_name": d.get("metadata", {}).get("match_name"),
            "teams": d.get("metadata", {}).get("teams"),
            "event_date": d.get("metadata", {}).get("event_date"),
            "registered_at": str(d.get("registered_at", ""))
        })
        media_ids.append(d.get("media_id"))

    # Count detections per status
    authorized = 0
    unauthorized = 0
    pending = 0
    total_detections = 0

    detection_docs = db.collection("detections")\
        .where("organization", "==", organization)\
        .stream()

    for doc in detection_docs:
        d = doc.to_dict()
        status = d.get("status", "pending")
        total_detections += 1
        if status == "authorized":
            authorized += 1
        elif status == "unauthorized":
            unauthorized += 1
        else:
            pending += 1

    return {
        "organization": organization,
        "total_uploads": len(media_list),
        "uploads": media_list,
        "detections": {
            "total": total_detections,
            "authorized": authorized,
            "unauthorized": unauthorized,
            "pending": pending
        }
    }

def delete_detection(detection_id: str):
    db.collection("detections").document(detection_id).delete()

def get_media_by_user(user_id: str) -> list:
    docs = db.collection("registered_media")\
        .where(filter=FieldFilter("metadata.user_id", "==", user_id))\
        .stream()
    return [doc.to_dict() for doc in docs]