import sys
from pathlib import Path
import streamlit as st
import plotly.express as px

# Đảm bảo app/ nằm trong sys.path để import utils
app_dir = Path(__file__).resolve().parent.parent
if str(app_dir) not in sys.path:
    sys.path.insert(0, str(app_dir))

from utils import get_data, transitions, sidebar_uploader

st.set_page_config(page_title="Bottleneck Analysis", layout="wide")
st.title("⏱️ Phân tích điểm nghẽn thời gian")
sidebar_uploader()

df = get_data()
if df.empty:
    st.warning("⚠️ Chưa có dữ liệu hoặc dữ liệu rỗng. Vui lòng kiểm tra lại file CSV.")
    st.stop()

t = transitions(df)
if t.empty:
    st.info("ℹ️ Không tìm thấy quan hệ chuyển tiếp (transitions) giữa các bước.")
    st.stop()

# Xếp hạng điểm nghẽn
rank = (
    t.groupby(["activity", "next_activity"])["wait_h"]
    .agg(mean_h="mean", median_h="median", max_h="max", count="count")
    .reset_index()
    .sort_values("mean_h", ascending=False)
)
rank.insert(0, "Hạng", range(1, len(rank) + 1))
rank = rank.round(2)
rank = rank.rename(
    columns={
        "activity": "Thao tác hiện tại",
        "next_activity": "Thao tác kế tiếp",
        "mean_h": "Thời gian TB (giờ)",
        "median_h": "Trung vị (giờ)",
        "max_h": "Thời gian tối đa (giờ)",
        "count": "Số lượt",
    }
)

st.subheader("Bảng xếp hạng điểm nghẽn")
if len(rank) > 5:
    top_n = st.slider("Hiển thị top", min_value=5, max_value=min(30, max(5, len(rank))), value=min(10, len(rank)))
else:
    top_n = len(rank)

st.dataframe(rank.head(top_n), use_container_width=True, hide_index=True)

# Heatmap
st.subheader("Heatmap thời gian chờ trung bình (giờ)")
pv = t.pivot_table(index="activity", columns="next_activity", values="wait_h", aggfunc="mean")

if not pv.empty:
    fig = px.imshow(
        pv,
        text_auto=".2f",
        aspect="auto",
        color_continuous_scale="Reds",
        labels=dict(x="Thao tác kế tiếp", y="Thao tác hiện tại", color="Giờ"),
    )
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("Chưa đủ dữ liệu để vẽ heatmap.")
