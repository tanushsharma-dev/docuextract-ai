from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
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

@app.get("/")
def root():
    return {"service": "DocuExtract AI", "status": "running", "version": "1.0.0"}

@app.get("/health")
def health():
    return {"status": "healthy"}