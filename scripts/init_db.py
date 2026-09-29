import sys
from pathlib import Path

# Project root ko sys.path me add karo (yahi fix hai)
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from app.core.database import engine, Base
from app.models import Document, Page, ExtractionJob, ExtractedField, LineItem, HumanReview

def init():
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("✅ Tables created successfully!")

if __name__ == "__main__":
    init()