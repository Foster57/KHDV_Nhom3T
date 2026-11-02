import sys
from pathlib import Path
import streamlit as st

# Đảm bảo app/ nằm trong sys.path để import utils
app_dir = Path(__file__).resolve().parent
if str(app_dir) not in sys.path:
    sys.path.insert(0, str(app_dir))

from utils import get_data, sidebar_uploader

st.set_page_config(page_title="Process Mining Dashboard", layout="wide")
st.title("Process Mining - Theo dõi khách hàng số")

sidebar_uploader()
df = get_data()

if df.empty:
    st.warning("⚠️ Chưa có dữ liệu hoặc file CSV rỗng.")
    st.stop()

case_column, log_column, activity_column = st.columns(3)
case_column.metric("Số case", f"{df['case_id'].nunique():,}")
log_column.metric("Số sự kiện", f"{len(df):,}")
activity_column.metric("Số hoạt động", f"{df['activity'].nunique():,}")
st.dataframe(df.head(50), use_container_width=True)
