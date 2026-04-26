import numpy as np
from typing import List, Optional
from config import SIMILARITY_THRESHOLD, REVIEW_THRESHOLD

# Borderline zone — triggers CLIP verification
BORDERLINE_LOW = 0.60
BORDERLINE_HIGH = 0.80

def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    v1, v2 = np.array(vec1), np.array(vec2)
    dot = np.dot(v1, v2)
    norm = np.linalg.norm(v1) * np.linalg.norm(v2)
    if norm == 0:
        return 0.0
    return float(np.clip(dot / norm, 0, 1))

def get_label(score: float) -> str:
    if score >= 0.90:
        return "Very High — Likely Same Content"
    elif score >= 0.75:
        return "High — Probable Match"
    elif score >= 0.60:
        return "Medium — Possible Match"
    else:
        return "Low — Likely Different"

def dual_verify(
    vertex_score: float,
    image1_path: str,
    image2_path: str
) -> dict:
    """
    If Vertex AI score is borderline, use CLIP to confirm.
    Vertex AI is primary. CLIP only activates in borderline zone.
    
    Zones:
    >= 0.80  → Match confirmed by Vertex AI alone
    0.60-0.80 → Borderline → CLIP decides
    < 0.60   → No match, CLIP not needed
    """
    is_borderline = BORDERLINE_LOW <= vertex_score < BORDERLINE_HIGH
    clip_score = None
    final_score = vertex_score
    verification_method = "vertex_ai_only"

    if is_borderline:
        try:
            from core.clip_embeddings import (
                get_clip_embedding,
                clip_cosine_similarity
            )
            clip_emb1 = get_clip_embedding(image1_path)
            clip_emb2 = get_clip_embedding(image2_path)
            clip_score = clip_cosine_similarity(clip_emb1, clip_emb2)

            # CLIP confirms or denies borderline case
            # Weighted: Vertex 60% + CLIP 40% in borderline zone
            final_score = (0.60 * vertex_score) + (0.40 * clip_score)
            verification_method = "dual_verified"

        except Exception as e:
            print(f"CLIP verification failed: {e} — using Vertex score only")

    is_match = final_score >= SIMILARITY_THRESHOLD
    requires_review = BORDERLINE_LOW <= final_score < SIMILARITY_THRESHOLD

    return {
        "vertex_score": round(vertex_score, 4),
        "clip_score": round(clip_score, 4) if clip_score else None,
        "final_score": round(final_score, 4),
        "similarity_percentage": f"{round(final_score * 100, 2)}%",
        "label": get_label(final_score),
        "is_match": is_match,
        "requires_review": requires_review,
        "borderline": is_borderline,
        "verification_method": verification_method
    }

def compare_embeddings(emb1: List[float], emb2: List[float]) -> dict:
    """
    Basic comparison without file paths
    Used when images not available locally (URL-based flows)
    """
    score = cosine_similarity(emb1, emb2)
    return {
        "vertex_score": round(score, 4),
        "clip_score": None,
        "final_score": round(score, 4),
        "similarity_percentage": f"{round(score * 100, 2)}%",
        "label": get_label(score),
        "is_match": score >= SIMILARITY_THRESHOLD,
        "requires_review": BORDERLINE_LOW <= score < SIMILARITY_THRESHOLD,
        "verification_method": "vertex_ai_only"
    }

def batch_compare(
    query_embedding: List[float],
    candidates: list
) -> list:
    """
    Compare one embedding against all registered media
    Returns sorted matches above review threshold
    """
    results = []
    for candidate in candidates:
        score = cosine_similarity(
            query_embedding,
            candidate["embedding"]
        )
        if score >= REVIEW_THRESHOLD:
            results.append({
                "media_id": candidate["media_id"],
                "organization": candidate.get(
                    "metadata", {}
                ).get("organization"),
                "match_name": candidate.get(
                    "metadata", {}
                ).get("match_name"),
                "vertex_score": round(score, 4),
                "final_score": round(score, 4),
                "similarity_percentage": f"{round(score * 100, 2)}%",
                "label": get_label(score),
                "is_match": score >= SIMILARITY_THRESHOLD,
                "requires_review": BORDERLINE_LOW <= score < SIMILARITY_THRESHOLD
            })

    return sorted(
        results,
        key=lambda x: x["final_score"],
        reverse=True
    )