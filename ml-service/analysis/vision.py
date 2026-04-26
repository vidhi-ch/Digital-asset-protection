from google.cloud import vision

client = vision.ImageAnnotatorClient()

def analyze_image(image_path: str) -> dict:
    """
    Detect logos, text, labels in image
    """
    with open(image_path, "rb") as f:
        content = f.read()
    
    image = vision.Image(content=content)
    
    logos = client.logo_detection(image=image).logo_annotations
    texts = client.text_detection(image=image).text_annotations
    labels = client.label_detection(image=image).label_annotations
    
    return {
        "logos": [l.description for l in logos],
        "text": texts[0].description.split("\n") if texts else [],
        "labels": [l.description for l in labels],
        "has_logo": len(logos) > 0
    }

def analyze_image_gcs(gcs_uri: str) -> dict:
    """
    Same but from GCS URI
    """
    image = vision.Image()
    image.source.image_uri = gcs_uri
    
    logos = client.logo_detection(image=image).logo_annotations
    texts = client.text_detection(image=image).text_annotations
    
    return {
        "logos": [l.description for l in logos],
        "text": texts[0].description.split("\n") if texts else [],
        "has_logo": len(logos) > 0
    }