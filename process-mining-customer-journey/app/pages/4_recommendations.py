import sys
from pathlib import Path
import streamlit as st
import pandas as pd

# Đảm bảo app/ nằm trong sys.path để import utils
app_dir = Path(__file__).resolve().parent.parent
if str(app_dir) not in sys.path:
    sys.path.insert(0, str(app_dir))

from utils import get_data, transitions, sidebar_uploader

st.set_page_config(page_title="Recommendations", layout="wide")
st.title("💡 Khuyến nghị vận hành")
sidebar_uploader()

df = get_data()

ROOT = Path(__file__).resolve().parent.parent.parent
dt_img = ROOT / "image" / "decision_tree.png"
journey_img = ROOT / "image" / "theoretical_customer_journey.png"

# Hiển thị biểu đồ cây quyết định hoặc hành trình tham chiếu
st.subheader("Cây quyết định & Phân tích nguyên nhân gốc rễ (Root Cause Analysis)")

if dt_img.exists():
    st.image(str(dt_img), caption="Cây quyết định - Root Cause Analysis", use_container_width=True)
elif journey_img.exists():
    st.image(str(journey_img), caption="Hành trình khách hàng tham chiếu (Theoretical Customer Journey)", use_container_width=True)
    st.caption("*(Lưu ý: Để hiển thị cây quyết định chuyên sâu, lưu file ảnh vào thư mục `image/decision_tree.png`)*")
else:
    st.info("Chưa có ảnh sơ đồ cây quyết định trong thư mục `image/`.")

# Phân tích tự động từ dữ liệu hiện tại
st.subheader("Phát hiện tự động từ dữ liệu")
if not df.empty:
    t = transitions(df)
    if not t.empty:
        worst_bottleneck = (
            t.groupby(["activity", "next_activity"])["wait_h"]
            .mean()
            .sort_values(ascending=False)
            .head(1)
        )
        if not worst_bottleneck.empty:
            (act_from, act_to), avg_wait = worst_bottleneck.index[0], worst_bottleneck.values[0]
            st.warning(
                f"🚨 **Điểm nghẽn lớn nhất hiện tại:** Từ `{act_from}` sang `{act_to}` "
                f"với thời gian chờ trung bình **{avg_wait:.2f} giờ**."
            )

# Bảng quy tắc khuyến nghị
st.subheader("Quy tắc khuyến nghị hành động")
rules = pd.DataFrame([
    {
        "Điều kiện": "Thời gian chờ từ view → cart > 24h",
        "Khuyến nghị": "Gửi email/push notification nhắc nhở giỏ hàng, gợi ý mã giảm giá có hạn",
        "Ưu tiên": "Cao",
    },
    {
        "Điều kiện": "Khách hàng remove_from_cart nhiều lần",
        "Khuyến nghị": "Khảo sát nguyên nhân bỏ hàng (giá cả, phí ship), hiển thị gợi ý sản phẩm thay thế",
        "Ưu tiên": "Cao",
    },
    {
        "Điều kiện": "Số lượt view cao nhưng không thêm giỏ hàng (cart)",
        "Khuyến nghị": "Tối ưu trang chi tiết sản phẩm: cải thiện hình ảnh, đánh giá khách hàng và nút Call-to-Action",
        "Ưu tiên": "Trung bình",
    },
    {
        "Điều kiện": "Phiên mua hàng (purchase) thành công",
        "Khuyến nghị": "Gợi ý sản phẩm liên quan (cross-sell/up-sell) và tích điểm thành viên",
        "Ưu tiên": "Thấp",
    },
])

st.dataframe(rules, use_container_width=True, hide_index=True)
