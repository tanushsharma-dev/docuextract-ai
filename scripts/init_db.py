from app.core.database import engine, Base
from app.models import Document, Page, ExtractionJob, ExtractedField, LineItem, HumanReview

def init():
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("✅ Tables created successfully!")

if __name__ == "__main__":
    init()