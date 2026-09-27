import os
import json
import logging
from datetime import datetime
from app.core.database import SessionLocal
from app.models import Document, ExtractionJob, ExtractedField, LineItem, Page
from app.extraction.pipeline import run_extraction_pipeline

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def process_document(document_id: str):
    """Main worker task."""
    db = SessionLocal()
    try:
        doc = db.query(Document).filter(Document.id == document_id).first()
        if not doc:
            logger.error(f"Document {document_id} not found")
            return

        # Create extraction job
        job = ExtractionJob(
            document_id=doc.id,
            status="processing",
            ocr_engine="paddleocr",
            vlm_model="gpt-4o",
            started_at=datetime.utcnow()
        )
        db.add(job)
        db.commit()
        db.refresh(job)

        # Prepare output directory
        output_dir = f"./storage/processed/{document_id}"
        os.makedirs(output_dir, exist_ok=True)

        # Run pipeline
        result = run_extraction_pipeline(doc.storage_path, output_dir)

        if result["status"] == "failed":
            job.status = "failed"
            job.error_message = result.get("error", "Unknown error")
            doc.status = "failed"
        else:
            # Save pages
            for i in range(result.get("page_count", 1)):
                page = Page(
                    document_id=doc.id,
                    page_number=i+1,
                    image_path=f"{output_dir}/page_{i+1}.png"
                )
                db.add(page)

            # Save extracted fields
            for field_name, field_data in result["fields"].items():
                field = ExtractedField(
                    document_id=doc.id,
                    job_id=job.id,
                    field_name=field_name,
                    raw_value=str(field_data["value"]),
                    normalized_value=str(field_data["value"]),
                    confidence=field_data["confidence"],
                    source=field_data["source"],
                    requires_review=field_data["requires_review"]
                )
                db.add(field)

            # Save line items
            for item in result.get("line_items", []):
                line_item = LineItem(
                    document_id=doc.id,
                    description=item.get("description"),
                    quantity=item.get("quantity"),
                    unit_price=item.get("unit_price"),
                    amount=item.get("amount")
                )
                db.add(line_item)

            # Update document
            doc.document_type = result["document_type"]
            doc.page_count = result.get("page_count", 1)
            doc.status = "needs_review" if result["requires_review"] else "extracted"

            job.status = "completed"
            job.completed_at = datetime.utcnow()

        db.commit()
        logger.info(f"Document {document_id} processed: {doc.status}")

    except Exception as e:
        logger.error(f"Worker error: {e}")
        db.rollback()
    finally:
        db.close()

def worker_loop():
    """Simple worker loop polling Redis."""
    from app.services.queue import dequeue_extraction_job
    import time

    logger.info("Worker started. Waiting for jobs...")
    while True:
        job = dequeue_extraction_job()
        if job:
            logger.info(f"Processing job: {job}")
            process_document(job["document_id"])
        else:
            time.sleep(1)

if __name__ == "__main__":
    worker_loop()