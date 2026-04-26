from google import genai
from google.genai import types
import json
import re
import os
from dotenv import load_dotenv

load_dotenv()

def _get_client():
    """
    Create genai client - works both locally and on Cloud Run.
    Uses automatic credentials (no file needed on Cloud Run).
    """
    import google.auth
    import google.auth.transport.requests

    credentials, project = google.auth.default(
        scopes=["https://www.googleapis.com/auth/cloud-platform"]
    )
    auth_req = google.auth.transport.requests.Request()
    credentials.refresh(auth_req)

    return genai.Client(
        project=os.getenv("PROJECT_ID"),
        location="us-central1",
        vertexai=True,
        credentials=credentials
    )

MODEL = "gemini-2.0-flash"

def _load_image_bytes(image_path: str) -> bytes:
    with open(image_path, "rb") as f:
        return f.read()

def _get_mime_type(image_path: str) -> str:
    ext = os.path.splitext(image_path)[1].lower()
    return {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".webp": "image/webp",
        ".gif": "image/gif"
    }.get(ext, "image/jpeg")


def compare_images(image1_path: str, image2_path: str) -> dict:
    client = _get_client()
    img1_bytes = _load_image_bytes(image1_path)
    img2_bytes = _load_image_bytes(image2_path)

    prompt = """
    You are a sports media copyright detection system.
    Compare these two images carefully.
    Return ONLY valid JSON, no markdown, no extra text:
    {
        "same_event": true/false,
        "same_teams": true/false,
        "tampering_detected": true/false,
        "tampering_details": "description or none",
        "logo_removed": true/false,
        "watermark_removed": true/false,
        "cropped": true/false,
        "color_adjusted": true/false,
        "overall_assessment": "Authorized/Suspicious/Unauthorized",
        "reasoning": "brief explanation"
    }
    """

    response = client.models.generate_content(
        model=MODEL,
        contents=[
            types.Part.from_bytes(
                data=img1_bytes,
                mime_type=_get_mime_type(image1_path)
            ),
            types.Part.from_bytes(
                data=img2_bytes,
                mime_type=_get_mime_type(image2_path)
            ),
            prompt
        ]
    )

    try:
        return json.loads(response.text)
    except json.JSONDecodeError:
        match = re.search(r'\{.*\}', response.text, re.DOTALL)
        if match:
            return json.loads(match.group())
        return {"error": "Could not parse response", "raw": response.text}


def explain_result(result: dict) -> str:
    client = _get_client()
    prompt = f"""
    A sports media copyright system found this:
    {json.dumps(result, indent=2)}

    Write a 2-3 sentence professional explanation for a sports
    organization. Tell them what was found and recommended action.
    """
    response = client.models.generate_content(
        model=MODEL,
        contents=[prompt]
    )
    return response.text


def check_tampering_only(image_path: str) -> dict:
    client = _get_client()
    img_bytes = _load_image_bytes(image_path)

    prompt = """
    Analyze this sports media image for signs of tampering.
    Return ONLY valid JSON:
    {
        "watermark_present": true/false,
        "logo_present": true/false,
        "appears_cropped": true/false,
        "color_filter_applied": true/false,
        "tampering_confidence": "High/Medium/Low",
        "notes": "brief observation"
    }
    """

    response = client.models.generate_content(
        model=MODEL,
        contents=[
            types.Part.from_bytes(
                data=img_bytes,
                mime_type=_get_mime_type(image_path)
            ),
            prompt
        ]
    )

    try:
        return json.loads(response.text)
    except json.JSONDecodeError:
        match = re.search(r'\{.*\}', response.text, re.DOTALL)
        return json.loads(match.group()) if match else {}