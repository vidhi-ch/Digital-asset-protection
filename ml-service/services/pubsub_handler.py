from google.cloud import pubsub_v1
from config import PROJECT_ID
import json

publisher = pubsub_v1.PublisherClient()
subscriber = pubsub_v1.SubscriberClient()

DETECTION_TOPIC = "new-detection"
SCAN_TOPIC = "trigger-scan"

def publish_new_detection(detection_data: dict):
    topic_path = publisher.topic_path(PROJECT_ID, DETECTION_TOPIC)
    
    # Convert datetime objects to string before JSON serializing
    serializable = {}
    for key, value in detection_data.items():
        if hasattr(value, 'isoformat'):  # catches datetime objects
            serializable[key] = str(value)
        else:
            serializable[key] = value
    
    data = json.dumps(serializable).encode("utf-8")
    future = publisher.publish(topic_path, data)
    print(f"Published detection alert: {future.result()}")

def publish_scan_trigger(media_id: str):
    """
    Trigger periodic scan for a specific media
    """
    topic_path = publisher.topic_path(PROJECT_ID, SCAN_TOPIC)
    
    data = json.dumps({"media_id": media_id}).encode("utf-8")
    publisher.publish(topic_path, data)

def create_topics_if_not_exist():
    """
    Run once during setup to create Pub/Sub topics
    """
    for topic_name in [DETECTION_TOPIC, SCAN_TOPIC]:
        topic_path = publisher.topic_path(PROJECT_ID, topic_name)
        try:
            publisher.create_topic(request={"name": topic_path})
            print(f"Created topic: {topic_name}")
        except Exception as e:
            print(f"Topic {topic_name} already exists or error: {e}")