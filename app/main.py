import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.routes import documents, review, evaluation

app = FastAPI(
    title="DocuExtract AI",
    description="Multimodal Document Intelligence System",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(documents.router, prefix="/api/v1/documents", tags=["Documents"])
app.include_router(review.router, prefix="/api/v1/review", tags=["Review"])
app.include_router(evaluation.router, prefix="/api/v1/evaluation", tags=["Evaluation"])


@app.on_event("startup")
def on_startup():
    """Deploy pe tables automatically create ho"""
    from app.core.database import engine, Base
    from app.models import Document, Page, ExtractionJob, ExtractedField, LineItem, HumanReview
    Base.metadata.create_all(bind=engine)


@app.get("/")
def root():
    return {"service": "DocuExtract AI", "status": "running", "version": "1.0.0"}


@app.get("/health")
def health():
    return {"status": "healthy"}


os.makedirs("storage", exist_ok=True)
os.makedirs("storage/samples", exist_ok=True)
os.makedirs("storage/processed", exist_ok=True)
os.makedirs("ui/web", exist_ok=True)

app.mount("/storage", StaticFiles(directory="storage"), name="storage")
app.mount("/ui", StaticFiles(directory="ui/web", html=True), name="ui")