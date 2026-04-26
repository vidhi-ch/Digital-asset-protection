"""
Periodic monitoring scheduler
Triggered by Cloud Scheduler every 30 minutes
Searches all platforms for copies of registered media
"""
from services.scraper import search_all_platforms
from services.firestore_handler import (
    get_all_registered_media,
    store_detection,
    is_already_detected
)
from services.pubsub_handler import publish_new_detection
from core.embeddings import get_image_embedding
from core.similarity import compare_embeddings
from utils.media_utils import download_from_url, cleanup_temp_files
from config import SIMILARITY_THRESHOLD, REVIEW_THRESHOLD


def build_search_query(media_metadata: dict) -> str:
    """
    Build search query from media metadata
    """
    parts = []
    if media_metadata.get("match_name"):
        parts.append(media_metadata["match_name"])
    if media_metadata.get("teams"):
        parts.append(media_metadata["teams"])
    if media_metadata.get("event_date"):
        parts.append(media_metadata["event_date"])

    # Fallback query
    if not parts:
        return "IPL cricket match highlights"

    return " ".join(parts)


def process_candidate(
    candidate_result: dict,
    original_embedding: list,
    original_media: dict
) -> dict | None:
    """
    Download candidate image and compare with original
    Returns detection dict if match found, else None
    """
    image_url = candidate_result.get("image_url")
    if not image_url:
        return None

    local_path = None
    try:
        # Download candidate image
        local_path = download_from_url(image_url)

        # Get embedding
        candidate_embedding = get_image_embedding(local_path)

        # Compare
        result = compare_embeddings(
            original_embedding,
            candidate_embedding
        )

        source_url = candidate_result.get("url") or image_url

        # Only process if above review threshold
        if result["final_score"] < REVIEW_THRESHOLD:
            return None

        # Skip if already detected
        if is_already_detected(original_media["media_id"], source_url):
            return None

        return {
            "original_media_id": original_media["media_id"],
            "organization": original_media.get(
                "metadata", {}
            ).get("organization"),
            "match_name": original_media.get(
                "metadata", {}
            ).get("match_name"),
            "source_url": source_url,
            "image_url": image_url,
            "platform": candidate_result.get("platform"),
            "similarity_score": result["final_score"],
            "similarity_percentage": result["similarity_percentage"],
            "label": result["label"],
            "is_match": result["is_match"],
            "requires_review": result["requires_review"],
            "verification_method": result["verification_method"],
            "status": "pending"
        }

    except Exception as e:
        print(f"Error processing candidate {image_url}: {e}")
        return None

    finally:
        cleanup_temp_files(local_path)


def scan_one_media(original_media: dict) -> list:
    """
    Scan all platforms for one registered media
    Returns list of new detection IDs
    """
    metadata = original_media.get("metadata", {})
    original_embedding = original_media.get("embedding")

    if not original_embedding:
        print(f"No embedding for {original_media['media_id']}")
        return []

    query = build_search_query(metadata)
    print(f"Scanning for: {query}")

    # Search all platforms
    candidates = search_all_platforms(query, max_per_platform=10)

    new_detection_ids = []

    for candidate in candidates:
        detection = process_candidate(
            candidate,
            original_embedding,
            original_media
        )

        if detection:
            detection_id = store_detection(detection)
            publish_new_detection(detection)
            new_detection_ids.append(detection_id)
            print(
                f"New detection: {detection['platform']} "
                f"| Score: {detection['similarity_percentage']}"
            )

    return new_detection_ids


def run_periodic_scan(event=None, context=None):
    """
    Entry point for Cloud Function / Cloud Scheduler
    Runs every 30 minutes
    """
    all_media = get_all_registered_media()
    print(f"Starting scan for {len(all_media)} registered media items")

    total = 0
    for media in all_media:
        ids = scan_one_media(media)
        total += len(ids)

    print(f"Scan complete — {total} new detections")
    return {"new_detections": total}