import pandas as pd
import streamlit as st
from pathlib import Path

default_path = Path(__file__).resolve().parent.parent / "data/processed/event_log_sample.csv"
required = {"case_id", "activity", "timestamp"}

# Ánh xạ tên cột từ các định dạng CSV khác nhau về chuẩn nội bộ
COLUMN_ALIASES = {
    # event_log_sample.csv (Kaggle eCommerce)
    "event_time": "timestamp",
    "event_type": "activity",
    "user_session": "case_id",
    # sample.csv (PM4Py naming)
    "case:concept:name": "case_id",
    "concept:name": "activity",
    "time:timestamp": "timestamp",
}


@st.cache_data
def read_csv(src):
    df = pd.read_csv(src)
    # Chuẩn hóa tên cột
    df = df.rename(columns={c: COLUMN_ALIASES[c] for c in df.columns if c in COLUMN_ALIASES})
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    return df.sort_values(["case_id", "timestamp"]).reset_index(drop=True)


def get_data():
    if "df" not in st.session_state:
        try:
            st.session_state["df"] = read_csv(default_path)
        except FileNotFoundError:
            st.error(f"Không tìm thấy {default_path}")
            st.stop()
    return st.session_state["df"]


def sidebar_uploader():
    new_file = st.sidebar.file_uploader("Upload CSV mới", type="csv")
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
            st.sidebar.error(f"Lỗi đọc file: {e}")


@st.cache_data
def transitions(df):
    d = df.copy()
    g = d.groupby("case_id")
    d["next_activity"] = g["activity"].shift(-1)
    d["next_timestamp"] = g["timestamp"].shift(-1)
    d["wait_h"] = (d["next_timestamp"] - d["timestamp"]).dt.total_seconds() / 3600
    return d.dropna(subset=["next_activity"]).reset_index(drop=True)
