from google.cloud import videointelligence

def analyze_video(gcs_uri: str) -> dict:
    """
    Full video analysis using Video Intelligence API
    """
    client = videointelligence.VideoIntelligenceServiceClient()
    
    features = [
        videointelligence.Feature.LABEL_DETECTION,
        videointelligence.Feature.SHOT_CHANGE_DETECTION,
        videointelligence.Feature.LOGO_RECOGNITION,
        videointelligence.Feature.TEXT_DETECTION,
    ]
    
    operation = client.annotate_video(
        request={"features": features, "input_uri": gcs_uri}
    )
    
    print("Analyzing video... (may take a few minutes)")
    result = operation.result(timeout=300)
    annotations = result.annotation_results[0]
    
    shots = [
        {
            "start": s.start_time_offset.seconds,
            "end": s.end_time_offset.seconds
        }
        for s in annotations.shot_annotations
    ]
    
    logos = [
        l.entity.description 
        for l in annotations.logo_recognition_annotations
    ]
    
    labels = [
        l.entity.description 
        for l in annotations.segment_label_annotations
    ]
    
    texts = [t.text for t in annotations.text_annotations]
    
    return {
        "total_shots": len(shots),
        "shot_boundaries": shots,
        "logos": logos,
        "labels": labels,
        "texts": texts,
        "has_logo": len(logos) > 0
    }