import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.database import SessionLocal
from app.models import Document, ExtractedField

db = SessionLocal()

docs = db.query(Document).all()
print(f"\n📄 Total documents: {len(docs)}")
for d in docs:
    print(f"  - {str(d.id)[:8]} | {d.filename} | status: {d.status} | type: {d.document_type}")

fields = db.query(ExtractedField).all()
print(f"\n📊 Total extracted fields: {len(fields)}")
for f in fields[:20]:
    print(f"  - {f.field_name}: {f.normalized_value} (confidence: {f.confidence})")

db.close()
print("\n✅ Database check complete!")