import gradio as gr
import requests
import json
from pathlib import Path

API_BASE = "http://localhost:8000/api/v1"

def list_pending_documents():
    try:
        r = requests.get(f"{API_BASE}/review/pending")
        if r.status_code == 200:
            docs = r.json()
            return "\n".join([f"{d['document_id']} - {d['filename']}" for d in docs])
    except Exception as e:
        return f"Error: {e}"
    return "No pending documents"

def load_document(doc_id: str):
    try:
        r = requests.get(f"{API_BASE}/review/{doc_id}")
        if r.status_code == 200:
            data = r.json()
            fields_text = "\n".join([
                f"{f['field_name']}: {f['value']} (conf: {f['confidence']:.2f}) {'⚠️' if f['requires_review'] else '✅'}"
                for f in data["fields"]
            ])
            image_path = data.get("storage_path")
            return image_path, fields_text, doc_id
    except Exception as e:
        return None, f"Error: {e}", ""
    return None, "Not found", ""

def submit_corrections(doc_id: str, corrections_text: str, reviewer: str):
    try:
        corrections = {}
        for line in corrections_text.strip().split("\n"):
            if ":" in line:
                key, val = line.split(":", 1)
                corrections[key.strip()] = val.strip()

        payload = {
            "corrections": corrections,
            "review_status": "approved",
            "reviewer_name": reviewer or "anonymous"
        }
        r = requests.post(f"{API_BASE}/review/{doc_id}", json=payload)
        if r.status_code == 200:
            return "✅ Review submitted successfully!"
        return f"❌ Error: {r.text}"
    except Exception as e:
        return f"❌ Error: {e}"

with gr.Blocks(title="DocuExtract Review") as demo:
    gr.Markdown("# 📄 DocuExtract AI — Human Review Console")

    with gr.Row():
        with gr.Column(scale=1):
            refresh_btn = gr.Button("🔄 Refresh Pending")
            pending_list = gr.Textbox(label="Pending Documents", lines=10, interactive=False)
            doc_id_input = gr.Textbox(label="Document ID")
            load_btn = gr.Button("📂 Load Document")

        with gr.Column(scale=2):
            doc_image = gr.Image(label="Document Preview", type="filepath")
            fields_display = gr.Textbox(label="Extracted Fields", lines=10, interactive=False)

        with gr.Column(scale=1):
            corrections_input = gr.Textbox(
                label="Corrections (field: value per line)",
                lines=10,
                placeholder="total_amount: 2360\ninvoice_date: 2026-01-15"
            )
            reviewer_input = gr.Textbox(label="Your Name", value="reviewer")
            submit_btn = gr.Button("✅ Submit Review")
            status_output = gr.Textbox(label="Status", interactive=False)

    refresh_btn.click(list_pending_documents, outputs=pending_list)
    load_btn.click(load_document, inputs=doc_id_input, outputs=[doc_image, fields_display, doc_id_input])
    submit_btn.click(submit_corrections, inputs=[doc_id_input, corrections_input, reviewer_input], outputs=status_output)

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860)