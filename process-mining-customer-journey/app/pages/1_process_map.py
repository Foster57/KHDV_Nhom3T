"""
Trang Process Map (DFG)
Hiển thị placeholder cho sơ đồ Directly-Follows Graph.
Logic DFG sẽ được bổ sung ở tuần sau.
"""

import streamlit as st

st.title("🗺️ Process Map (DFG)")

# Lấy dữ liệu từ session_state (đã upload ở trang chủ)
df = st.session_state.get("event_log")

if df is None:
    st.warning(
        "⚠️ Chưa có dữ liệu! Vui lòng quay lại **trang chủ** để upload file CSV."
    )
    st.stop()

# Hiển thị caption số dòng hiện tại
st.caption(f"📊 Dữ liệu hiện tại: **{len(df)}** dòng")

# --- Placeholder cho sơ đồ DFG ---
dfg_container = st.container(border=True)
with dfg_container:
    st.info("ℹ️ Sơ đồ DFG sẽ hiển thị tại đây sau khi hoàn thành module Process Mining.")
    # Tuần sau: dùng dfg_placeholder.graphviz_chart(...) để render sơ đồ DFG
    dfg_placeholder = st.empty()
