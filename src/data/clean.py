import os
import pandas as pd

def clean_and_sample_event_log(
        input_path: str, output_path: str, sample_size: int = 20000
):

    # 1. Trích xuất 3 cột cần thiết để tối ưu bộ nhớ
    use_cols = ["event_time", "event_type", "user_session"]
    df = pd.read_csv(input_path, usecols = use_cols)

    # 2. Xóa các dòng bị thiếu thông tin ở 1 trong 3 cột 
    df = df.dropna(subset=["event_time", "event_type", "user_session"])

    # 3. Chuẩn hóa cột event_time về dạng Ngày - Giờ 
    df["event_time"] = pd.to_datetime(df["event_time"])

    # 4. Khử nhiễu: Đếm số hành động của mỗi session và lọc bỏ các phiên chỉ có 1 hành động
    session_counts = df["user_session"].value_counts()
    valid_sessions = session_counts[session_counts > 1].index
    df_filtered = df[df["user_session"].isin(valid_sessions)]

    # 5. Cắt lấy dữ liệu mẫu để phục vụ test 
    df_sample = df_filtered.head(sample_size).copy()

    # 6. Sắp xếp hành trình theo từng phiên và theo thứ tự thời gian tăng dần
    df_sample = df_sample.sort_values(by=["user_session", "event_time"])

    # 7. Tự động tạo thư mục đích nếu chưa có và xuất ra file CSV sạch
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df_sample.to_csv(output_path, index=False)

if __name__== "__main__":
    RAW_DATA = "data/raw/2019-Oct.csv"
    PROCESSED_DATA = "data/processed/event_log_sample.csv"

    clean_and_sample_event_log(RAW_DATA, PROCESSED_DATA)
