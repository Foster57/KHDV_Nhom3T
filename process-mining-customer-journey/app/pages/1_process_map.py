"""
Trang Process Map (DFG)
Hiển thị sơ đồ Directly-Follows Graph (DFG) dựa trên dữ liệu hành trình khách hàng.
"""

import sys
from pathlib import Path
import streamlit as st
import pandas as pd
import graphviz

# Đảm bảo app/ nằm trong sys.path để import utils
app_dir = Path(__file__).resolve().parent.parent
if str(app_dir) not in sys.path:
    sys.path.insert(0, str(app_dir))

from utils import get_data, transitions, sidebar_uploader

st.set_page_config(page_title="Process Map (DFG)", layout="wide")
st.title("🗺️ Sơ đồ quy trình (Directly-Follows Graph)")

sidebar_uploader()
df = get_data()

if df.empty:
    st.warning("⚠️ Chưa có dữ liệu hoặc dữ liệu rỗng. Vui lòng kiểm tra lại file CSV.")
    st.stop()

st.caption(f"📊 Dữ liệu hiện tại: **{len(df):,}** sự kiện | **{df['case_id'].nunique():,}** case")

# Lấy dữ liệu transitions
t = transitions(df)

if t.empty:
    st.info("ℹ️ Không tìm thấy quan hệ chuyển tiếp (transitions) giữa các sự kiện trong cùng case.")
    st.stop()

col_mode, col_filter = st.columns([1, 2])
with col_mode:
    metric_type = st.radio("Chỉ số hiển thị trên cạnh:", ["Tần suất (Số lượt)", "Thời gian chờ TB (giờ)"], horizontal=True)

# Tính tổng hợp theo luồng
if metric_type == "Tần suất (Số lượt)":
    flows = t.groupby(["activity", "next_activity"]).size().reset_index(name="val")
    val_label = "lượt"
else:
    flows = t.groupby(["activity", "next_activity"])["wait_h"].mean().round(2).reset_index(name="val")
    val_label = "giờ"

# Đếm số lần mỗi activity xuất hiện
act_counts = df["activity"].value_counts()

# Bộ lọc cạnh tối thiểu
max_count = int(flows["val"].max()) if metric_type == "Tần suất (Số lượt)" and not flows.empty else 1
with col_filter:
    if metric_type == "Tần suất (Số lượt)" and max_count > 1:
        min_filter = st.slider("Lọc cạnh có số lượt tối thiểu:", 1, max_count, 1)
        flows_filtered = flows[flows["val"] >= min_filter]
    else:
        flows_filtered = flows
        st.write("")

# Vẽ DFG qua Graphviz
dot = graphviz.Digraph(format="svg")
dot.attr(rankdir="LR", bgcolor="transparent")

# Vẽ các node (hoạt động)
for act, count in act_counts.items():
    dot.node(
        str(act),
        f"{act}\n({count:,})",
        shape="box",
        style="rounded,filled",
        fillcolor="#E1F5FE",
        color="#0288D1",
        fontname="Arial",
        fontsize="11",
    )

# Vẽ các cạnh
for _, row in flows_filtered.iterrows():
    val_str = f"{row['val']:,} {val_label}" if metric_type == "Tần suất (Số lượt)" else f"{row['val']}h"
    dot.edge(
        str(row["activity"]),
        str(row["next_activity"]),
        label=val_str,
        fontname="Arial",
        fontsize="9",
        color="#546E7A",
    )

st.subheader("Sơ đồ Directly-Follows Graph")
st.graphviz_chart(dot, use_container_width=True)
