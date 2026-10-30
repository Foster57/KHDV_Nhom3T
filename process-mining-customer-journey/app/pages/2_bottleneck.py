import streamlit as st
import plotly.express as px
from utils import get_data, transitions, sidebar_uploader

st.set_page_config(page_title="Bottleneck", layout="wide")
st.title("Điểm nghẽn thời gian")
sidebar_uploader()
t = transitions(get_data())

rank = (t.groupby(["activity", "next_activity"])["wait_h"]
          .agg(mean_h="mean", median_h="median", max_h="max", count="count")
          .reset_index().sort_values("mean_h", ascending=False))
rank.insert(0, "Hạng", range(1, len(rank) + 1))
rank = rank.round(2)

st.subheader("Bảng xếp hạng điểm nghẽn")
top_n = st.slider("Hiển thị top", 5, 30, 10)
st.dataframe(rank.head(top_n), use_container_width=True, hide_index=True)

st.subheader("Heatmap thời gian chờ trung bình (giờ)")
pv = t.pivot_table(index="activity", columns="next_activity",
                   values="wait_h", aggfunc="mean")
fig = px.imshow(pv, text_auto=".1f", aspect="auto", color_continuous_scale="Reds",
                labels=dict(x="Thao tác kế tiếp", y="Thao tác", color="Giờ"))
st.plotly_chart(fig, use_container_width=True)