# DocuExtract AI — Multimodal Document Intelligence

DocuExtract AI is a production-grade document extraction and validation platform for invoices, receipts, bank statements, ID cards and forms. It combines preprocessing, OCR, AI-powered (VLM) extraction, rule-based cross-validation, confidence scoring and a human review workflow in a single modular service.

> Built by **Tanush Sharma** — AI / Full-Stack Developer
> GitHub: https://github.com/tanushsharma-dev · LinkedIn: https://www.linkedin.com/in/tanush-sharma-8b1807280/ · Email: tanushsharma052@gmail.com

## ✨ Features

- 📄 **Multi-modal extraction** — PDF & image (JPEG/PNG/WebP/TIFF) support with in-browser PDF preview
- 🧠 **5 document types** — invoice, receipt, bank statement, ID card, form
- 🤖 **Multi-provider AI engine** — Groq (Qwen3.8-27B vision) primary with automatic Google Gemini fallback & model rotation
- 🎯 **Confidence scoring** — per-field confidence with auto-approval (≥85%) and review routing
- 👁️ **Human review console** — edit fields, approve documents, full audit trail (`HumanReview` table)
- 📊 **Document dashboard** — live stats, history table, view / review / export actions
- 📤 **CSV export** — one-click export of extracted fields + line items
- ☁️ **Neon PostgreSQL** — serverless cloud database
- ⚡ **Premium web UI** — FastAPI + Tailwind CSS with client-side caching

## 🏗️ Architecture
