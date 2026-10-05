import os
import logging
import traceback
from datetime import datetime, timedelta
from app.core.database import SessionLocal
from app.models import Document, ExtractionJob, ExtractedField, LineItem, Page
from app.extraction.pipeline import run_extraction_pipeline

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def process_document(document_id: str, document_type: str = "auto"):
    db = SessionLocal()
    job = None
    try:
        doc = db.query(Document).filter(Document.id == document_id).first()
        if not doc:
            logger.error(f"Document {document_id} not found")
            return

        # ============ STEP 1: Create Job ============
        logger.info(f"[STEP 1] Creating ExtractionJob for {document_id}")
        job = ExtractionJob(
            document_id=doc.id,
            status="processing",
            started_at=datetime.utcnow()
        )
        db.add(job)
        db.commit()
        db.refresh(job)
        logger.info(f"[STEP 1 OK] job.id = {job.id}")

        # ============ STEP 2: Run Pipeline ============
        output_dir = f"./storage/processed/{document_id}"
        os.makedirs(output_dir, exist_ok=True)
        logger.info(f"[STEP 2] Running extraction pipeline...")
        result = run_extraction_pipeline(doc.storage_path, output_dir, document_type)
        logger.info(f"[STEP 2 OK] status = {result.get('status')}")

        # ============ STEP 3: Handle Failure ============
        if result.get("status") == "failed":
            job.status = "failed"
            job.error_message = str(result.get("error", "Unknown"))[:500]
            doc.status = "failed"
            db.commit()
            logger.error(f"[FAILED] Pipeline error: {result.get('error')}")
            return

        # ============ STEP 4: Save Pages ============
        try:
            count = result.get("page_count", 1)
            logger.info(f"[STEP 4] Saving {count} page(s)")
            for i in range(count):
                db.add(Page(
                    document_id=doc.id,
                    page_number=i + 1,
                    image_path=f"{output_dir}/page_{i + 1}.png"
                ))
            db.commit()
            logger.info("[STEP 4 OK] Pages saved")
        except Exception as e:
            logger.error(f"[STEP 4 FAILED] {e}")
            traceback.print_exc()
            db.rollback()

        # ============ STEP 5: Save Fields ============
        try:
            fields = result.get("fields", {}) or {}
            logger.info(f"[STEP 5] Saving {len(fields)} fields")
            for field_name, field_data in fields.items():
                db.add(ExtractedField(
                    document_id=doc.id,
                    field_name=str(field_name)[:100],
                    raw_value=str(field_data.get("value", ""))[:2000],
                    normalized_value=str(field_data.get("value", ""))[:2000],
                    confidence=field_data.get("confidence"),
                    source=field_data.get("source"),
                    requires_review=bool(field_data.get("requires_review", False))
                ))
            db.commit()
            logger.info("[STEP 5 OK] Fields saved")
        except Exception as e:
            logger.error(f"[STEP 5 FAILED] {e}")
            traceback.print_exc()
            db.rollback()

        # ============ STEP 6: Save Line Items ============
        try:
            items = result.get("line_items", []) or []
            logger.info(f"[STEP 6] Saving {len(items)} line items")
            for item in items:
                db.add(LineItem(
                    document_id=doc.id,
                    description=item.get("description"),
                    quantity=item.get("quantity"),
                    unit_price=item.get("unit_price"),
                    amount=item.get("amount")
                ))
            db.commit()
            logger.info("[STEP 6 OK] Line items saved")
        except Exception as e:
            logger.error(f"[STEP 6 FAILED] {e}")
            traceback.print_exc()
            db.rollback()

        # ============ STEP 7: Update Status ============
        try:
            logger.info("[STEP 7] Updating doc + job status")
            doc.document_type = result.get("document_type")
            doc.page_count = result.get("page_count", 1)
            doc.status = "needs_review" if result.get("requires_review") else "extracted"
            job.status = "completed"
            job.completed_at = datetime.utcnow()
            db.commit()
            logger.info(f"[STEP 7 OK] doc.status = {doc.status}")
        except Exception as e:
            logger.error(f"[STEP 7 FAILED] {e}")
            traceback.print_exc()
            db.rollback()

        logger.info(f"Document {document_id} FULLY PROCESSED")

    except Exception as e:
        logger.error(f"[FATAL] Worker error: {e}")
        traceback.print_exc()
        db.rollback()
        if job is not None:
            try:
                job.status = "failed"
                job.error_message = str(e)[:500]
                db.commit()
            except Exception:
                db.rollback()
    finally:
        db.close()


def cleanup_stuck_jobs():
    db = SessionLocal()
    try:
        cutoff = datetime.utcnow() - timedelta(minutes=10)
        stuck = db.query(ExtractionJob).filter(
            ExtractionJob.status == "processing",
            ExtractionJob.started_at < cutoff
        ).all()
        for j in stuck:
            j.status = "failed"
            j.error_message = "Timeout - worker did not complete"
            logger.warning(f"Marked stuck job {j.id} as failed")
        if stuck:
            db.commit()
    except Exception as e:
        logger.error(f"cleanup_stuck_jobs error: {e}")
        db.rollback()
    finally:
        db.close()


def worker_loop():
    from app.services.queue import dequeue_extraction_job
    import time

    logger.info("Worker started. Waiting for jobs...")
    while True:
        cleanup_stuck_jobs()
        job = dequeue_extraction_job()
        if job:
            process_document(job["document_id"], job.get("document_type", "auto"))
        else:
            time.sleep(1)


if __name__ == "__main__":
    worker_loop()