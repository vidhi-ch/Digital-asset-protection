from google.cloud import aiplatform
from config import PROJECT_ID, LOCATION, EMBEDDING_DIMENSION
import numpy as np

aiplatform.init(project=PROJECT_ID, location=LOCATION)

# You'll fill these after creating index in GCP Console
INDEX_ENDPOINT_ID = "your-index-endpoint-id"
DEPLOYED_INDEX_ID = "media_index"

def search_similar(
    query_embedding: list,
    top_k: int = 5
) -> list:
    """
    Search for similar vectors using Vertex Vector Search
    Returns top_k most similar media IDs
    """
    try:
        endpoint = aiplatform.MatchingEngineIndexEndpoint(
            index_endpoint_name=INDEX_ENDPOINT_ID
        )
        
        results = endpoint.find_neighbors(
            deployed_index_id=DEPLOYED_INDEX_ID,
            queries=[query_embedding],
            num_neighbors=top_k
        )
        
        matches = []
        for match in results[0]:
            matches.append({
                "media_id": match.id,
                "distance": match.distance,
                # Convert distance to similarity (0-1)
                "similarity_score": round(1 - match.distance, 4)
            })
        
        return matches
    
    except Exception as e:
        # Fallback to Firestore batch compare if Vector Search not set up
        print(f"Vector Search error: {e} — falling back to Firestore")
        return []