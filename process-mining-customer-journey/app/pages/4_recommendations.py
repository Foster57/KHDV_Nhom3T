import streamlit as st
import pandas as pd
from pathlib import Path

st.set_page_config(page_title="Recommendations", layout="wide")
st.title("Khuyến nghị vận hành")

ROOT = Path(__file__).resolve().parent.parent.parent
img = ROOT / "image" / "decision_tree.png"   # đổi theo thư mục ảnh thật của bạn

if img.exists():
    st.image(str(img), caption="Cây quyết định - Root Cause Analysis",
             use_container_width=True)
else:
    st.warning(f"Chưa có ảnh: {img}")

st.subheader("Quy tắc khuyến nghị")
rules = pd.DataFrame([
    {"Điều kiện": "Thời gian chờ bước A→B > 24h", "Khuyến nghị": "Tự động nhắc/gửi thông báo", "Ưu tiên": "Cao"},
    {"Điều kiện": "Cụm 2 và bỏ giỏ hàng", "Khuyến nghị": "Gửi ưu đãi kéo lại", "Ưu tiên": "Trung bình"},
])  # thay bằng quy tắc thật rút ra từ các nhánh của cây
st.dataframe(rules, use_container_width=True, hide_index=True)