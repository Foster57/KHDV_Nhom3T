import sys
from pathlib import Path
import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# Đảm bảo app/ nằm trong sys.path để import utils
app_dir = Path(__file__).resolve().parent.parent
if str(app_dir) not in sys.path:
    sys.path.insert(0, str(app_dir))

from utils import get_data, transitions, sidebar_uploader

st.set_page_config(page_title="Customer Journey", layout="wide")
st.title("🛤️ Hành trình khách hàng")
sidebar_uploader()

df = get_data()
if df.empty:
    st.warning("⚠️ Chưa có dữ liệu hoặc dữ liệu rỗng. Vui lòng kiểm tra lại file CSV.")
    st.stop()

t = transitions(df)

view = st.radio("Chọn loại biểu đồ:", ["Sankey (Luồng chuyển tiếp)", "Funnel (Phễu chuyển đổi)"], horizontal=True)

if view == "Sankey (Luồng chuyển tiếp)":
    if t.empty:
        st.info("ℹ️ Không có dữ liệu chuyển tiếp để vẽ biểu đồ Sankey.")
    else:
        flows = t.groupby(["activity", "next_activity"]).size().reset_index(name="n")
        max_n = int(flows["n"].max()) if not flows.empty and pd.notna(flows["n"].max()) else 1

        if max_n > 1:
            min_n = st.slider("Số lượt tối thiểu", min_value=1, max_value=max_n, value=1)
        else:
            min_n = 1

        flows_filtered = flows[flows["n"] >= min_n]

        if flows_filtered.empty:
            st.info("Không có luồng chuyển tiếp nào đạt ngưỡng số lượt tối thiểu đã chọn.")
        else:
            labels = sorted(set(flows_filtered["activity"]) | set(flows_filtered["next_activity"]))
            idx = {a: i for i, a in enumerate(labels)}
            fig = go.Figure(
                go.Sankey(
                    node=dict(label=labels, pad=15, thickness=20),
                    link=dict(
                        source=flows_filtered["activity"].map(idx),
                        target=flows_filtered["next_activity"].map(idx),
                        value=flows_filtered["n"],
                    ),
                )
            )
            fig.update_layout(title_text="Biểu đồ luồng Sankey", font_size=12)
            st.plotly_chart(fig, use_container_width=True)
else:
    d = df.copy()
    d["pos"] = d.groupby("case_id").cumcount()
    order = d.groupby("activity")["pos"].mean().sort_values().index
    cnt = d.groupby("activity")["case_id"].nunique().reindex(order)

    if cnt.empty or cnt.sum() == 0:
        st.info("Chưa có đủ dữ liệu để vẽ phễu chuyển đổi.")
    else:
        fig = go.Figure(go.Funnel(y=cnt.index, x=cnt.values, textinfo="value+percent initial"))
        fig.update_layout(title_text="Phễu chuyển đổi hành trình (Funnel Chart)")
        st.plotly_chart(fig, use_container_width=True)

st.subheader("Trace variants (Các biến thể hành trình)")
var = (
    df.groupby("case_id")["activity"]
    .apply(lambda s: " → ".join(s))
    .value_counts()
    .reset_index()
)
var.columns = ["Biến thể", "Số case"]

if not var.empty and var["Số case"].sum() > 0:
    var["Tỷ lệ %"] = (var["Số case"] / var["Số case"].sum() * 100).round(2)
    st.caption(f"Tổng cộng **{len(var):,}** biến thể hành trình, hiển thị top 20")
    st.dataframe(var.head(20), use_container_width=True, hide_index=True)
else:
    st.info("Chưa có dữ liệu biến thể.")
