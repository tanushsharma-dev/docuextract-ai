import streamlit as st
import requests

API_ROOT = "http://localhost:8000"
API_BASE = API_ROOT + "/api/v1"

st.set_page_config(page_title="DocuExtract AI - Review", page_icon="📄", layout="wide")

st.title("📄 DocuExtract AI — Human Review Console")


def find_upload_path():
    """API se khud upload endpoint ka path puchna."""
    try:
        spec = requests.get(f"{API_ROOT}/openapi.json", timeout=5).json()
        for path, methods in spec.get("paths", {}).items():
            if "post" in methods and ("document" in path or "upload" in path):
                return path
    except Exception:
        pass
    return None


# ---------- Sidebar: Upload + Pending ----------
with st.sidebar:
    st.header("📤 Upload Document")
    uploaded_file = st.file_uploader(
        "Invoice / Receipt choose karo",
        type=["png", "jpg", "jpeg", "webp", "tiff", "pdf"]
    )
    if uploaded_file is not None:
        if st.button("🚀 Upload & Process", type="primary"):
            upload_path = find_upload_path()
            if upload_path is None:
                st.error("❌ Upload endpoint API me nahi mila! Uvicorn RESTART karo (Ctrl+C karke dobara chalao)")
            else:
                with st.spinner(f"Processing via {upload_path} ... (30-60 sec)"):
                    files = {
                        "file": (
                            uploaded_file.name,
                            uploaded_file.getvalue(),
                            uploaded_file.type
                        )
                    }
                    try:
                        resp = requests.post(f"{API_ROOT}{upload_path}", files=files, timeout=180)
                        if resp.status_code == 200:
                            doc_id = resp.json()["document_id"]
                            st.success(f"✅ Processed! ID: {doc_id[:8]}...")
                            st.rerun()
                        else:
                            st.error(f"Upload failed: {resp.text}")
                    except Exception as e:
                        st.error(f"Error: {e}")

    st.markdown("---")
    st.header("📋 Pending Documents")
    if st.button("🔄 Refresh List"):
        st.rerun()

    selected_doc_id = None
    try:
        response = requests.get(f"{API_BASE}/review/pending", timeout=5)
        docs = response.json() if response.status_code == 200 else []
    except Exception:
        docs = []
        st.error("API not reachable - kya uvicorn chal raha hai?")

    if docs:
        options = {f"{d['filename']} ({d['document_id'][:8]}...)": d["document_id"] for d in docs}
        choice = st.selectbox("Select document", list(options.keys()))
        selected_doc_id = options[choice]
    else:
        st.info("No pending documents")

# ---------- Main Area ----------
if selected_doc_id:
    try:
        r = requests.get(f"{API_BASE}/review/{selected_doc_id}", timeout=10)
        data = r.json()

        st.subheader(f"Reviewing: {data['filename']}")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("### 📎 Document Preview")
            if data.get("storage_path"):
                try:
                    st.image(data["storage_path"], use_container_width=True)
                except Exception:
                    st.warning("Preview not available")

        with col2:
            st.markdown("### 📊 Extracted Fields")
            corrections = {}
            for field in data.get("fields", []):
                name = field["field_name"]
                value = str(field["value"] or "")
                conf = float(field.get("confidence") or 0)

                if conf >= 0.85:
                    badge = "✅"
                elif conf >= 0.60:
                    badge = "⚠️"
                else:
                    badge = "❌"

                st.markdown(f"**{name}** {badge} (confidence: {conf:.0%})")
                new_val = st.text_input(f"Edit {name}", value=value, key=f"edit_{name}")
                if new_val != value:
                    corrections[name] = new_val

        st.markdown("### ✅ Review Actions")
        c1, c2, c3 = st.columns(3)
        with c1:
            reviewer = st.text_input("Reviewer name", value="anonymous")
        with c2:
            status = st.selectbox("Status", ["approved", "rejected", "needs_more_info"])
        with c3:
            comments = st.text_input("Comments", value="")

        if st.button("✅ Submit Review", type="primary"):
            payload = {
                "corrections": corrections,
                "review_status": status,
                "reviewer_name": reviewer,
                "comments": comments,
            }
            sr = requests.post(f"{API_BASE}/review/{selected_doc_id}", json=payload, timeout=10)
            if sr.status_code == 200:
                st.success("Review submitted!")
                st.rerun()
            else:
                st.error(f"Failed: {sr.text}")

    except Exception as e:
        st.error(f"Error loading document: {e}")
else:
    st.info("👈 Sidebar se document upload karo ya select karo")