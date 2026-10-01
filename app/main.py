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

# CORS - frontend ko API se baat karne ke liye
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Routes
app.include_router(documents.router, prefix="/api/v1/documents", tags=["Documents"])
app.include_router(review.router, prefix="/api/v1/review", tags=["Review"])
app.include_router(evaluation.router, prefix="/api/v1/evaluation", tags=["Evaluation"])


@app.get("/")
def root():
    return {"service": "DocuExtract AI", "status": "running", "version": "1.0.0"}


@app.get("/health")
def health():
    return {"status": "healthy"}


# ============================================================
# Static File Serving
# ============================================================

# Processed document images ko browser me serve karna
# (Isse frontend pe document preview dikhta hai: /storage/processed/{id}/page_1.png)
os.makedirs("storage", exist_ok=True)
os.makedirs("storage/samples", exist_ok=True)
os.makedirs("storage/processed", exist_ok=True)
os.makedirs("ui/web", exist_ok=True)

app.mount("/storage", StaticFiles(directory="storage"), name="storage")

# UI ko FastAPI se hi serve karo (Live Server ki zaroorat nahi - no reload trap!)
# Access: http://127.0.0.1:8000/ui/
app.mount("/ui", StaticFiles(directory="ui/web", html=True), name="ui")