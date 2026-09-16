from __future__ import annotations

import streamlit as st

from ui.components import render_sidebar


st.set_page_config(page_title="DocuExtract AI", page_icon="📄")
render_sidebar()

st.title("DocuExtract AI")
st.write("Upload a document to start extraction, validation, and review workflows.")
