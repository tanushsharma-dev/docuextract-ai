import redis
import json
from app.core.config import settings

redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)

def enqueue_extraction_job(document_id: str):
    """Push extraction job to Redis queue."""
    job = {
        "document_id": document_id,
        "task": "extract_document"
    }
    redis_client.lpush("extraction_queue", json.dumps(job))
    return job

def dequeue_extraction_job():
    """Pop next job from queue (blocking)."""
    result = redis_client.brpop("extraction_queue", timeout=5)
    if result:
        _, job_data = result
        return json.loads(job_data)
    return None

def get_queue_length():
    return redis_client.llen("extraction_queue")