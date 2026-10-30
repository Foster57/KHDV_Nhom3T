import streamlit as st
import plotly.graph_objects as go
from utils import get_data, transitions, sidebar_uploader

st.set_page_config(page_title="Customer Journey", layout="wide")
st.title("Hành trình khách hàng")
sidebar_uploader()
df = get_data()
t = transitions(df)

view = st.radio("Biểu đồ", ["Sankey", "Funnel"], horizontal=True)

if view == "Sankey":
    flows = t.groupby(["activity", "next_activity"]).size().reset_index(name="n")
    min_n = st.slider("Số lượt tối thiểu", 1, max(1, int(flows["n"].max())), 1)
    flows = flows[flows["n"] >= min_n]
    labels = sorted(set(flows["activity"]) | set(flows["next_activity"]))
    idx = {a: i for i, a in enumerate(labels)}
    fig = go.Figure(go.Sankey(
        node=dict(label=labels, pad=15),
        link=dict(source=flows["activity"].map(idx),
                  target=flows["next_activity"].map(idx),
                  value=flows["n"])))
else:
    d = df.copy()
    d["pos"] = d.groupby("case_id").cumcount()
    order = d.groupby("activity")["pos"].mean().sort_values().index
    cnt = d.groupby("activity")["case_id"].nunique().reindex(order)
    fig = go.Figure(go.Funnel(y=cnt.index, x=cnt.values,
                              textinfo="value+percent initial"))

st.plotly_chart(fig, use_container_width=True)

st.subheader("Trace variants")
var = (df.groupby("case_id")["activity"].apply(lambda s: " → ".join(s))
         .value_counts().reset_index())
var.columns = ["Biến thể", "Số case"]
var["Tỷ lệ %"] = (var["Số case"] / var["Số case"].sum() * 100).round(2)
st.caption(f"Tổng {len(var)} biến thể, hiển thị top 20")
st.dataframe(var.head(20), use_container_width=True, hide_index=True)