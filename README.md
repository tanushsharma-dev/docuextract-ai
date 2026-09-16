# DocuExtract AI

DocuExtract AI is a document extraction and validation platform for invoices, receipts, and other structured business documents. The project combines preprocessing, OCR, layout analysis, validation, and human review workflows in a single modular service.

## Structure

- `app/` – FastAPI application, extraction pipeline, schemas, and business logic.
- `worker/` – background task workers.
- `ui/` – Streamlit interface.
- `evaluation/` – evaluation tooling and reference datasets.
- `tests/` – automated tests.
- `scripts/` – data and database utilities.

## Getting started

1. Create a virtual environment.
2. Install dependencies from `requirements.txt`.
3. Copy `.env.example` to `.env` and adjust settings.
4. Run the API with `uvicorn app.main:app --reload`.

## Docker

```bash
docker compose up --build
```
