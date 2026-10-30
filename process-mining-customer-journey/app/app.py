import streamlit as st
from utils import get_data, sidebar_uploader

st.set_page_config(page_title="Process Mining Dashboard", layout="wide")
st.title("Process Mining - Theo dõi khách hàng số")

sidebar_uploader()
df = get_data()

case_column, log_column, activity_column = st.columns(3)
case_column.metric("Số case", df["case_id"].nunique())
log_column.metric("Số sự kiện", len(df))
activity_column.metric("Số hoạt động", df["activity"].nunique())
st.dataframe(df.head(50), use_container_width=True)
