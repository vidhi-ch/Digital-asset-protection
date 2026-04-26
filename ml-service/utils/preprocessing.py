from PIL import Image
import os
import tempfile

ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}
ALLOWED_VIDEO_EXTENSIONS = {".mp4", ".avi", ".mov", ".mkv"}

def is_image(filename: str) -> bool:
    ext = os.path.splitext(filename)[1].lower()
    return ext in ALLOWED_IMAGE_EXTENSIONS

def is_video(filename: str) -> bool:
    ext = os.path.splitext(filename)[1].lower()
    return ext in ALLOWED_VIDEO_EXTENSIONS

def preprocess_image(image_path: str) -> str:
    """
    Resize and normalize image for consistent processing
    Returns path to processed image
    """
    img = Image.open(image_path).convert("RGB")
    
    # Resize if too large (keeps aspect ratio)
    max_size = 1024
    if max(img.size) > max_size:
        img.thumbnail((max_size, max_size), Image.LANCZOS)
    
    # Save processed version to temp file
    tmp = tempfile.NamedTemporaryFile(
        delete=False, suffix=".jpg"
    )
    img.save(tmp.name, "JPEG", quality=95)
    return tmp.name

def validate_file(filename: str, max_size_mb: int = 50) -> dict:
    """
    Validate file type and size
    """
    ext = os.path.splitext(filename)[1].lower()
    
    if ext not in ALLOWED_IMAGE_EXTENSIONS | ALLOWED_VIDEO_EXTENSIONS:
        return {
            "valid": False,
            "error": f"Unsupported file type: {ext}"
        }
    
    return {"valid": True, "type": "image" if is_image(filename) else "video"}