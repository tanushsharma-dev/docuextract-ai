import json
import logging
import redis
from app.core.config import settings

logger = logging.getLogger(__name__)

_redis_client = None
_redis_checked = False

def get_redis():
    global _redis_client, _redis_checked
    if not _redis_checked:
        _redis_checked = True
        try:
            client = redis.from_url(settings.REDIS_URL, decode_responses=True, socket_connect_timeout=2)
            client.ping()
            _redis_client = client
            logger.info("Redis connected - async mode")
        except Exception:
            logger.warning("Redis not available - sync mode")
    return _redis_client

def enqueue_extraction_job(document_id: str, document_type: str = "auto"):
    job = {"document_id": document_id, "task": "extract_document", "document_type": document_type}
    r = get_redis()
    if r is not None:
        r.lpush("extraction_queue", json.dumps(job))
        return {"mode": "queued"}
    from worker.tasks import process_document
    process_document(document_id, document_type)
    return {"mode": "sync"}

def dequeue_extraction_job():
    r = get_redis()
    if r is None:
        return None
    result = r.brpop("extraction_queue", timeout=5)
    if result:
        _, job_data = result
        return json.loads(job_data)
    return None

def get_queue_length():
    r = get_redis()
    return r.llen("extraction_queue") if r else 0