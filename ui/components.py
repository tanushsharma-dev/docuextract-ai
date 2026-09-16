from __future__ import annotations

import streamlit as st


def render_sidebar() -> None:
    with st.sidebar:
        st.header("DocuExtract")
        st.button("Refresh")
        st.caption("Invoice and receipt extraction workspace")
