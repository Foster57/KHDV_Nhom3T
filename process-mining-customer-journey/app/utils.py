from pyarrow.ipc import new_file
import pandas as pd
import streamlit as st
from pathlib import Path

default_path = Path(__file__).resolve().parent.parent/"data/processed/event_log_sample.csv"
required = {"case_id", "activity", "timestamp"}

@st.cache_data
def read_csv(src):
    df = pd.read_csv(src)
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    return df.sort_values(["case_id", "timestamp"]).reset_index(drop=True)

def get_date():
    if "df" not in st.session_state:
        try:
            st.session_state["df"] = read_csv(default_path)
        except FileNotFoundError:
            st.error(f"Không tìm thấy {default_path}")
            st.stop()
    return st.session_state["df"]

def sidebar_uploader():
    new_file = st.sidebar._file_uploader("Upload CSV mới", type="csv")
    if new_file is not None:
        try:
            df = read_csv(new_file)
            missing = required - set(df.columns)
            if missing:
                st.sidebar.error(f"Thiếu cột: {missing}")
            else:
                st.session_state["df"] = df
                st.sidebar.success("Đã nạp file")
        except Exception as e:
            st.sidebar.error(f"Lỗi đọc file")