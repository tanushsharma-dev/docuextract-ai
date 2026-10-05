import os
import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from app.api.routes import documents, review, evaluation, analytics, auth

logger = logging.getLogger(__name__)

app = FastAPI(
    title="DocuExtract AI",
    description="Multimodal Document Intelligence System",
    version="2.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ===== GLOBAL ERROR HANDLER =====
# Ab kabhi bhi plain "Internal Server Error" nahi dikhega — asli reason JSON me aayega
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"UNHANDLED ERROR on {request.url.path}: {type(exc).__name__}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": f"{type(exc).__name__}: {str(exc)[:300]}"}
    )


# ===== API ROUTES =====
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Auth"])
app.include_router(documents.router, prefix="/api/v1/documents", tags=["Documents"])
app.include_router(review.router, prefix="/api/v1/review", tags=["Review"])
app.include_router(evaluation.router, prefix="/api/v1/evaluation", tags=["Evaluation"])
app.include_router(analytics.router, prefix="/api/v1/analytics", tags=["Analytics"])


@app.get("/")
def root():
    return {"service": "DocuExtract AI", "status": "running", "version": "2.1.0"}


@app.get("/health")
def health():
    return {"status": "healthy"}


# ===== CLEAN URLs =====
@app.get("/ui/login")
def ui_login():
    return RedirectResponse("/ui/login.html")


@app.get("/ui/signup")
def ui_signup():
    return RedirectResponse("/ui/login.html")


@app.get("/ui/dashboard")
def ui_dashboard():
    return RedirectResponse("/ui/dashboard.html")


@app.get("/ui/documents")
def ui_documents():
    return RedirectResponse("/ui/documents.html")


@app.get("/ui/analytics")
def ui_analytics():
    return RedirectResponse("/ui/analytics.html")


# Static files
os.makedirs("storage", exist_ok=True)
os.makedirs("storage/samples", exist_ok=True)
os.makedirs("storage/processed", exist_ok=True)
os.makedirs("storage/uploads", exist_ok=True)
os.makedirs("ui/web", exist_ok=True)

app.mount("/storage", StaticFiles(directory="storage"), name="storage")
app.mount("/ui", StaticFiles(directory="ui/web", html=True), name="ui")