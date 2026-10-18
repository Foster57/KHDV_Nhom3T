"""
Trang chủ - Process Mining Customer Journey
Upload event log CSV và kiểm tra dữ liệu đầu vào.
"""

import streamlit as st
import pandas as pd

# --- Cấu hình trang ---
st.set_page_config(
    page_title="Process Mining - Customer Journey",
    layout="wide",
)

# --- Tiêu đề & mô tả ---
st.title("⛏️ Process Mining - Customer Journey")
st.markdown(
    "Ứng dụng phân tích hành trình khách hàng trên dữ liệu e-commerce "
    "bằng **Process Mining** (DFG, Heuristics Miner).  \n"
    "👉 Bắt đầu bằng cách upload file event log CSV ở bên dưới."
)

# 3 cột bắt buộc trong event log
REQUIRED_COLUMNS = [
    "case:concept:name",
    "concept:name",
    "time:timestamp",
]

st.divider()

# --- Upload file ---
uploaded_file = st.file_uploader(
    "📂 Chọn file event log (.csv) từ thư mục data/processed/",
    type=["csv"],
)

if uploaded_file is not None:
    # Đọc CSV, bọc try/except
    try:
        df = pd.read_csv(uploaded_file)
    except Exception as e:
        st.error(f"❌ Không thể đọc file CSV: {e}")
        st.stop()

    # Kiểm tra đủ 3 cột bắt buộc
    missing = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing:
        st.error(
            f"❌ File thiếu các cột bắt buộc: **{', '.join(missing)}**. "
            f"Cần đủ 3 cột: {', '.join(REQUIRED_COLUMNS)}"
        )
        st.stop()

    # Ép cột timestamp sang datetime
    df["time:timestamp"] = pd.to_datetime(
        df["time:timestamp"], errors="coerce"
    )

    # Lưu vào session_state để các trang khác dùng
    st.session_state["event_log"] = df

    # Thống kê nhanh
    num_rows = len(df)
    num_sessions = df["case:concept:name"].nunique()

    st.success(
        f"✅ Upload thành công! **{num_rows}** dòng, "
        f"**{num_sessions}** session duy nhất."
    )

    # Hiển thị 10 dòng đầu
    st.subheader("🔍 Xem trước dữ liệu (10 dòng đầu)")
    st.dataframe(df.head(10))
