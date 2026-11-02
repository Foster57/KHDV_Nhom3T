# 🔍 Process Mining — Customer Journey Analysis

Ứng dụng **Process Mining** phân tích hành trình khách hàng trên nền tảng thương mại điện tử, xây dựng bằng Python và Streamlit.

![Hành trình khách hàng lý thuyết](image/theoretical_customer_journey.png)

## 📋 Mô tả dự án

Dự án áp dụng kỹ thuật Process Mining để khai phá và trực quan hóa hành vi khách hàng từ dữ liệu event log e-commerce. Thông qua dashboard tương tác, người dùng có thể:

- **Khám phá quy trình thực tế (As-Is)** thay vì chỉ dựa vào giả định
- **Phát hiện điểm nghẽn (bottleneck)** giữa các bước trong hành trình
- **Phân tích các biến thể hành trình** (trace variants) của khách hàng
- **Đưa ra khuyến nghị vận hành** dựa trên kết quả phân tích

## 📁 Cấu trúc thư mục

```
process-mining-customer-journey/
├── app/
│   ├── app.py                          # Trang chủ dashboard
│   ├── utils.py                        # Hàm tiện ích: đọc dữ liệu, tính transition
│   └── pages/
│       ├── 1_process_map.py            # Sơ đồ DFG (Directly-Follows Graph)
│       ├── 2_bottleneck.py             # Phân tích điểm nghẽn thời gian
│       ├── 3_customer_journey.py       # Sankey, Funnel, Trace variants
│       └── 4_recommendations.py        # Khuyến nghị vận hành
├── data/
│   └── processed/
│       ├── event_log_sample.csv        # Dữ liệu event log (20.000 dòng)
│       └── sample.csv                  # Dữ liệu mẫu nhỏ để test
├── docs/
│   └── data_dictionary.md             # Từ điển dữ liệu
├── image/                             # Hình ảnh minh họa
├── reports/                           # Báo cáo
├── requirements.txt                   # Thư viện Python cần cài
└── README.md
```

## 🗂️ Nguồn dữ liệu

Dữ liệu được lấy từ bộ [eCommerce behavior data from multi category store](https://www.kaggle.com/datasets/mkechinov/ecommerce-behavior-data-from-multi-category-store) trên Kaggle (tác giả: Michael Kechinov), ghi nhận hành vi người dùng trên cửa hàng thương mại điện tử đa ngành hàng giai đoạn 10/2019 – 04/2020.

**Bốn loại sự kiện (event_type):**

| Sự kiện | Ý nghĩa |
|---------|---------|
| `view` | Xem sản phẩm |
| `cart` | Thêm vào giỏ hàng |
| `remove_from_cart` | Xóa khỏi giỏ hàng |
| `purchase` | Mua hàng |

> Chi tiết đầy đủ xem tại [docs/data_dictionary.md](docs/data_dictionary.md)

## 🚀 Cách chạy

### Yêu cầu

- Python 3.9+

### Cài đặt và chạy

```bash
# 1. Clone hoặc tải project
cd process-mining-customer-journey

# 2. Tạo virtual environment (nếu chưa có)
python -m venv venv

# 3. Kích hoạt virtual environment
# Windows:
.\venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# 4. Cài thư viện
pip install -r requirements.txt

# 5. Chạy ứng dụng
streamlit run app/app.py
```

Trình duyệt sẽ tự động mở tại **http://localhost:8501**.

## 📊 Các trang Dashboard

| Trang | Mô tả |
|-------|-------|
| **🏠 Home** | Tổng quan: số case, số sự kiện, số hoạt động; xem trước dữ liệu |
| **🗺️ Process Map** | Sơ đồ Directly-Follows Graph (DFG) — trực quan hóa luồng quy trình |
| **⏱️ Bottleneck** | Bảng xếp hạng điểm nghẽn + heatmap thời gian chờ trung bình giữa các bước |
| **🛤️ Customer Journey** | Biểu đồ Sankey / Funnel + bảng trace variants (top 20 biến thể hành trình) |
| **💡 Recommendations** | Cây quyết định (Root Cause Analysis) + bảng quy tắc khuyến nghị vận hành |

Trên mỗi trang có thể **upload CSV mới** qua sidebar để phân tích dữ liệu tùy chọn.

## 📄 Định dạng CSV đầu vào

Ứng dụng hỗ trợ nhiều định dạng cột. Chỉ cần CSV có **3 cột** tương ứng:

| Vai trò | Tên cột được chấp nhận |
|---------|----------------------|
| Case ID | `case_id`, `user_session`, `case:concept:name` |
| Activity | `activity`, `event_type`, `concept:name` |
| Timestamp | `timestamp`, `event_time`, `time:timestamp` |

## 🛠️ Công nghệ sử dụng

- **[Streamlit](https://streamlit.io/)** — Framework xây dựng dashboard tương tác
- **[Pandas](https://pandas.pydata.org/)** — Xử lý và phân tích dữ liệu
- **[Plotly](https://plotly.com/python/)** — Trực quan hóa (Sankey, Funnel, Heatmap)
- **[PM4Py](https://pm4py.fit.fraunhofer.de/)** — Thư viện Process Mining
- **[scikit-learn](https://scikit-learn.org/)** — Mô hình Decision Tree cho Root Cause Analysis
- **[Graphviz](https://graphviz.org/)** — Vẽ sơ đồ quy trình

