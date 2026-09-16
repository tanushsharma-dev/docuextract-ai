from __future__ import annotations


class QueueClient:
    def __init__(self, redis_url: str | None = None):
        self.redis_url = redis_url

    def enqueue(self, task_name: str, payload: dict) -> dict:
        return {
            "task": task_name,
            "payload": payload,
            "status": "queued",
        }


def enqueue_document_job(document_id: int, redis_url: str | None = None) -> dict:
    client = QueueClient(redis_url=redis_url)
    return client.enqueue("process_document", {"document_id": document_id})
