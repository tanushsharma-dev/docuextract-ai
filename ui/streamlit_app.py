import streamlit as st
import requests

API_BASE = "http://localhost:8000/api/v1"

st.set_page_config(
    page_title="DocuExtract AI - Review",
    page_icon="📄",
    layout="wide"
)

st.title("📄 DocuExtract AI - Human Review Console")

# Sidebar - document selection
with st.sidebar:
    st.header("📋 Pending Documents")

    if st.button("🔄 Refresh List"):
        st.rerun()

    selected_doc_id = None
    try:
        response = requests.get(f"{API_BASE}/review/pending")
        if response.status_code == 200:
            docs = response.json()
            if docs:
                doc_options = {
                    f"{d['document_id'][:8]}... - {d['filename']}": d['document_id']
                    for d in docs
                }
                selected_label = st.selectbox("Select Document", list(doc_options.keys()))
                selected_doc_id = doc_options[selected_label]
            else:
                st.info("No pending documents")
        else:
            st.error("Failed to fetch documents")
    except Exception as e:
        st.error(f"API not reachable: {str(e)}")

# Main content
if selected_doc_id:
    try:
        doc_response = requests.get(f"{API_BASE}/review/{selected_doc_id}")
        if doc_response.status_code == 200:
            doc_data = doc_response.json()

            col1, col2 = st.columns(2)

            with col1:
                st.markdown("### 📎 Document Preview")
                if doc_data.get("storage_path"):
                    st.image(doc_data["storage_path"], use_container_width=True)
                else:
                    st.warning("No preview available")

            with col2:
                st.markdown("### 📊 Extracted Fields")

                corrections = {}
                for field in doc_data.get("fields", []):
                    field_name = field["field_name"]
                    value = field["value"]
                    confidence = field["confidence"]

                    if confidence >= 0.85:
                        status = "✅"
                    elif confidence >= 0.60:
                        status = "⚠️"
                    else:
                        status = "❌"

                    st.markdown(f"**{field_name}** {status} (confidence: {confidence:.2f})")

                    new_value = st.text_input(
                        f"Edit {field_name}",
                        value=value if value else "",
                        key=f"edit_{field_name}"
                    )

                    if new_value != (value or ""):
                        corrections[field_name] = new_value

                    st.divider()

            st.markdown("### ✅ Review Actions")
            colA, colB = st.columns(2)
            with colA:
                reviewer_name = st.text_input("Reviewer Name", value="anonymous")
            with colB:
                review_status = st.selectbox(
                    "Status", ["approved", "rejected", "needs_more_info"]
                )

            if st.button("✅ Submit Review", type="primary"):
                payload = {
                    "corrections": corrections,
                    "review_status": review_status,
                    "reviewer_name": reviewer_name
                }
                submit_response = requests.post(
                    f"{API_BASE}/review/{selected_doc_id}", json=payload
                )
                if submit_response.status_code == 200:
                    st.success("✅ Review submitted!")
                    st.rerun()
                else:
