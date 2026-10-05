import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy import text
from app.core.database import engine, Base
from app.models import User, Document, ExtractedField, LineItem, HumanReview, Page, ExtractionJob

Base.metadata.create_all(bind=engine)

STATEMENTS = [
    "ALTER TABLE users ADD COLUMN IF NOT EXISTS username VARCHAR(100)",
    "ALTER TABLE users ADD COLUMN IF NOT EXISTS email VARCHAR(255)",
    "ALTER TABLE users ADD COLUMN IF NOT EXISTS full_name VARCHAR(200)",
    "ALTER TABLE users ADD COLUMN IF NOT EXISTS hashed_password VARCHAR(255)",
    "ALTER TABLE users ADD COLUMN IF NOT EXISTS auth_provider VARCHAR(20) DEFAULT 'local'",
    "ALTER TABLE users ADD COLUMN IF NOT EXISTS google_id VARCHAR(255)",
    "ALTER TABLE users ADD COLUMN IF NOT EXISTS is_verified BOOLEAN DEFAULT FALSE",
    "ALTER TABLE users ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE",
    "ALTER TABLE users ADD COLUMN IF NOT EXISTS otp_code VARCHAR(10)",
    "ALTER TABLE users ADD COLUMN IF NOT EXISTS otp_expires TIMESTAMP",
    # Purane NOT NULL columns ko nullable banao (signup crash fix)
    "ALTER TABLE users ALTER COLUMN username DROP NOT NULL",
    "ALTER TABLE users ALTER COLUMN password DROP NOT NULL",
    "ALTER TABLE users ALTER COLUMN hashed_password DROP NOT NULL",
    "ALTER TABLE users ALTER COLUMN password_hash DROP NOT NULL",
    "ALTER TABLE users ALTER COLUMN email DROP NOT NULL",
    "ALTER TABLE users ALTER COLUMN role DROP NOT NULL",
    "ALTER TABLE documents ADD COLUMN IF NOT EXISTS user_id UUID",
    "ALTER TABLE extracted_fields ADD COLUMN IF NOT EXISTS raw_value TEXT",
    "ALTER TABLE human_reviews ADD COLUMN IF NOT EXISTS field_id UUID",
    "ALTER TABLE human_reviews ADD COLUMN IF NOT EXISTS field_name VARCHAR(100)",
    "ALTER TABLE human_reviews ADD COLUMN IF NOT EXISTS original_value TEXT",
    "ALTER TABLE human_reviews ADD COLUMN IF NOT EXISTS corrected_value TEXT",
    "ALTER TABLE human_reviews ADD COLUMN IF NOT EXISTS reviewer VARCHAR(200)",
    "ALTER TABLE human_reviews ADD COLUMN IF NOT EXISTS reviewer_name VARCHAR(200)",
    "ALTER TABLE human_reviews ADD COLUMN IF NOT EXISTS status VARCHAR(50) DEFAULT 'pending'",
    "ALTER TABLE human_reviews ADD COLUMN IF NOT EXISTS approved BOOLEAN",
    "ALTER TABLE human_reviews ADD COLUMN IF NOT EXISTS comments TEXT",
    "ALTER TABLE human_reviews ADD COLUMN IF NOT EXISTS notes TEXT",
    "ALTER TABLE human_reviews ADD COLUMN IF NOT EXISTS reviewed_at TIMESTAMP",
    "ALTER TABLE pages ADD COLUMN IF NOT EXISTS storage_path VARCHAR(1000)",
    "ALTER TABLE pages ADD COLUMN IF NOT EXISTS text TEXT",
    "ALTER TABLE extraction_jobs ADD COLUMN IF NOT EXISTS document_type VARCHAR(50)",
    "ALTER TABLE extraction_jobs ADD COLUMN IF NOT EXISTS priority INTEGER DEFAULT 0",
    "ALTER TABLE extraction_jobs ADD COLUMN IF NOT EXISTS worker_id VARCHAR(100)",
    "ALTER TABLE extraction_jobs ADD COLUMN IF NOT EXISTS result_json TEXT",
]

print("Running migrations...")
with engine.connect() as conn:
    for sql in STATEMENTS:
        try:
            conn.execute(text(sql))
            conn.commit()
            print("OK  :", sql[:70])
        except Exception as e:
            print("SKIP:", sql[:50], "->", str(e)[:60])

print("\nMigration complete!")