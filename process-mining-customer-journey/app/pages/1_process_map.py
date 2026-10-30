"""
Trang Process Map (DFG)
Hiển thị placeholder cho sơ đồ Directly-Follows Graph.
Logic DFG sẽ được bổ sung ở tuần sau.
"""

import streamlit as st
from utils import get_data, sidebar_uploader

st.set_page_config(page_title="Process Map", layout="wide")
st.title("🗺️ Process Map (DFG)")

sidebar_uploader()
df = get_data()

# Hiển thị caption số dòng hiện tại
st.caption(f"📊 Dữ liệu hiện tại: **{len(df)}** dòng")

# --- Placeholder cho sơ đồ DFG ---
dfg_container = st.container(border=True)
with dfg_container:
    st.info("ℹ️ Sơ đồ DFG sẽ hiển thị tại đây sau khi hoàn thành module Process Mining.")
    # Tuần sau: dùng dfg_placeholder.graphviz_chart(...) để render sơ đồ DFG
    dfg_placeholder = st.empty()
