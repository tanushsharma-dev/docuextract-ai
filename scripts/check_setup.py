import sys, os, inspect
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

print("=== DocuExtract Setup Check ===\n")

try:
    from app.core.config import settings
    print("1 ✅ config.py | DB:", settings.DATABASE_URL[:30], "| VLM:", settings.VLM_MODEL)
except Exception as e:
    print("1 ❌ config.py FAIL:", e)

try:
    from app.core.database import engine, Base
    print("2 ✅ database.py OK")
except Exception as e:
    print("2 ❌ database.py FAIL:", e)

try:
    from app.models import Document, ExtractedField, LineItem
    print("3 ✅ models OK")
except Exception as e:
    print("3 ❌ models FAIL:", e)

try:
    from app.extraction.vlm import extract_with_vlm, SUPPORTED_TYPES
    print("4 ✅ vlm.py OK | types:", SUPPORTED_TYPES)
except Exception as e:
    print("4 ❌ vlm.py FAIL:", e)

try:
    from app.extraction.pipeline import run_extraction_pipeline
    print("5 ✅ pipeline.py | sig:", inspect.signature(run_extraction_pipeline))
except Exception as e:
    print("5 ❌ pipeline.py FAIL:", e)

try:
    from app.services.queue import enqueue_extraction_job
    print("6 ✅ queue.py | sig:", inspect.signature(enqueue_extraction_job))
except Exception as e:
    print("6 ❌ queue.py FAIL:", e)

try:
    from worker.tasks import process_document
    print("7 ✅ tasks.py | sig:", inspect.signature(process_document))
except Exception as e:
    print("7 ❌ tasks.py FAIL:", e)

try:
    from app.api.routes import documents, review, evaluation
    print("8 ✅ routes OK")
except Exception as e:
    print("8 ❌ routes FAIL:", e)

try:
    from app.main import app
    print("9 ✅ main.py OK | total routes:", len(app.routes))
except Exception as e:
    print("9 ❌ main.py FAIL:", e)

print("\n=== Check Complete ===")