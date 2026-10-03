import importlib
import logging
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, RedirectResponse

from app.api.routes import documents, review

logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
logger = logging.getLogger(__name__)

app = FastAPI(
    title="DocuExtract AI",
    description="Multimodal Document Intelligence — FastAPI + Groq/Gemini + Neon PostgreSQL",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(documents.router, prefix="/api/v1/documents", tags=["documents"])
app.include_router(review.router, prefix="/api/v1/reviews", tags=["review"])

# Optional routers — agar project me exist karte hai to auto-include, warna skip
for _mod, _prefix in [("queue", "/api/v1/queue"),]:
    try:
        _m = importlib.import_module(f"app.api.routes.{_mod}")
        if hasattr(_m, "router"):
            app.include_router(_m.router, prefix=_prefix, tags=[_mod])
    except Exception:
        pass

for _d in ["storage/uploads", "storage/processed", "storage/samples"]:
    os.makedirs(_d, exist_ok=True)

app.mount("/storage", StaticFiles(directory="storage"), name="storage")


@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse(url="/ui/")


@app.get("/ui/", include_in_schema=False)
def ui_home():
    return FileResponse("ui/web/index.html")


@app.get("/ui/dashboard", include_in_schema=False)
def ui_dashboard():
    return FileResponse("ui/web/documents.html")


@app.get("/health", tags=["health"])
def health():
    return {"status": "ok", "service": "DocuExtract AI"}