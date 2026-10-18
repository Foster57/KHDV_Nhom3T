# DATA DICTIONARY — E-COMMERCE CUSTOMER JOURNEY

## 1. Thông tin nguồn dữ liệu

- **Nguồn tham chiếu:** [eCommerce behavior data from multi category store — Kaggle](https://www.kaggle.com/datasets/mkechinov/ecommerce-behavior-data-from-multi-category-store), tác giả Michael Kechinov; dữ liệu được thu thập bởi dự án Open CDP, ghi nhận hành vi trên cửa hàng thương mại điện tử đa ngành hàng.
- **Đơn vị quan sát:** Một dòng CSV biểu diễn một sự kiện tương tác của người dùng với một sản phẩm tại một thời điểm.
- **Phạm vi công bố:** Bộ dữ liệu mô tả giai đoạn tháng 10/2019 đến tháng 4/2020; trang Kaggle chính hiển thị tệp tháng 10 và tháng 11/2019, các tháng còn lại được tác giả liên kết riêng. Phạm vi thực tế của dự án tùy các tệp nhóm tải về.
- **Định dạng:** CSV, gồm 9 cột dữ liệu gốc.
- **Lưu ý xác nhận:** Nhóm chưa cung cấp liên kết Kaggle cụ thể hoặc CSV đang dùng. Tài liệu này dựa trên bộ dữ liệu phù hợp nhất với 9 trường và 4 event_type đã mô tả; cần đối chiếu trước khi chốt báo cáo.

## 2. Từ điển dữ liệu gốc

| Trường | Kiểu dữ liệu đề xuất trong Python | Ý nghĩa | Ví dụ minh họa | Lưu ý xử lý |
|---|---|---|---|---|
| `event_time` | `datetime64[ns, UTC]` | Thời điểm sự kiện xảy ra, theo UTC. | `2019-11-01 00:00:14 UTC` | Chuyển sang datetime có múi giờ; sắp xếp theo phiên và thời gian. |
| `event_type` | `string` / `category` | Loại hành động mà người dùng thực hiện với sản phẩm. | `view`, `cart`, `remove_from_cart`, `purchase` | Chỉ giữ giá trị hợp lệ; dùng làm Activity. |
| `product_id` | `string` hoặc `Int64` | Mã định danh sản phẩm. | `1005014` | Là thuộc tính của sự kiện, không phải Case ID; tránh chuyển thành số thực. |
| `category_id` | `string` hoặc `Int64` | Mã định danh danh mục sản phẩm. | `2053013555631882655` | Giữ nguyên mã định danh, tránh mất độ chính xác. |
| `category_code` | `string` | Tên phân cấp danh mục, nếu có. | `electronics.smartphone` | Có thể thiếu; không mặc định xóa sự kiện. |
| `brand` | `string` | Thương hiệu sản phẩm, thường ở dạng chữ thường. | `samsung` | Có thể thiếu; không bắt buộc cho Process Discovery. |
| `price` | `float64` | Giá sản phẩm được ghi nhận tại sự kiện. | `503.09` | Kiểm tra giá trị không hợp lệ; không tự suy diễn doanh thu đơn hàng từ tổng mọi dòng. |
| `user_id` | `string` hoặc `Int64` | Mã định danh người dùng tương đối ổn định qua các phiên. | `533326659` | Dùng để phân tích người dùng nhiều phiên; không đồng nhất với Case ID. |
| `user_session` | `string` | Mã phiên truy cập; thay đổi khi người dùng trở lại sau một khoảng ngắt dài. | `b928be2b-2bce-4640-8296-0efdf2fda22a` | Dùng làm Case ID ở cấp phiên; kiểm tra null và tính duy nhất. |

**Quy ước:** Kiểu dữ liệu trên là kiểu *đề xuất sau khi nạp và chuẩn hóa*, không nhất thiết là kiểu CSV nguyên bản. Ví dụ chỉ để minh họa định dạng, không phải kết quả thống kê trên tập dữ liệu nhóm.

## 3. Giải thích chi tiết bốn giá trị `event_type`

| Giá trị | Diễn giải nghiệp vụ | Vai trò trong hành trình | Ý nghĩa phân tích |
|---|---|---|---|
| `view` | Người dùng xem thông tin một sản phẩm. | Điểm chạm khám phá / cân nhắc. | Đo lượt quan tâm, phát hiện xem lặp và rời phiên sau khi xem. |
| `cart` | Người dùng thêm một sản phẩm vào giỏ hàng. | Thể hiện ý định mua rõ hơn. | Đo chuyển đổi từ xem sang giỏ, xác định điểm rơi trước thanh toán. |
| `remove_from_cart` | Người dùng xóa một sản phẩm khỏi giỏ hàng. | Hành động điều chỉnh hoặc từ bỏ sản phẩm trong giỏ. | Phân tích luồng quay lại, khả năng do dự hoặc thay đổi lựa chọn; không mặc định là hủy toàn bộ đơn hàng. |
| `purchase` | Người dùng thực hiện mua sản phẩm. | Sự kiện chuyển đổi mua hàng được ghi nhận. | Đánh giá phiên có mua và đường đi tới mua; một phiên có thể có nhiều dòng purchase thuộc cùng đơn hàng. |

### 3.1. Luồng tham chiếu và biến thể

Luồng tuyến tính lý thuyết: `view → cart → purchase`.

Một số biến thể có thể quan sát được (minh họa, không khẳng định đã xuất hiện trong dữ liệu nhóm):

- `view → view → cart → purchase`: xem nhiều lần trước khi mua.
- `view → cart → remove_from_cart → cart → purchase`: điều chỉnh giỏ rồi mua.
- `view → cart`: phiên kết thúc sau khi thêm giỏ, chưa ghi nhận mua trong cửa sổ dữ liệu.
- `view`: phiên chỉ xem.

**Quan trọng:** `event_type` là tên *hoạt động/sự kiện*, không phải trạng thái bền vững của người dùng. Luồng trên là mô hình tham chiếu để so sánh với quy trình As-Is được khai phá, không phải quy tắc bắt buộc cho mọi phiên. Các hoạt động liên quan đến nhiều sản phẩm có thể xen kẽ trong cùng một phiên.

## 4. Ánh xạ sang Event Log cho PM4Py

| Khái niệm Process Mining | Cột dữ liệu | Tên chuẩn thường dùng trong PM4Py |
|---|---|---|
| Case ID | `user_session` | `case:concept:name` |
| Activity | `event_type` | `concept:name` |
| Timestamp | `event_time` | `time:timestamp` |
| Resource / bổ sung ngữ cảnh | `user_id`, `product_id`, `category_id`, `category_code`, `brand`, `price` | Giữ nguyên dưới dạng thuộc tính bổ sung |

**Quy tắc chuẩn hóa:**

1. Đọc các cột định danh ở dạng chuỗi hoặc kiểu số nguyên nullable; không chuyển ID dài thành `float`.
2. Parse `event_time` theo UTC; loại hoặc cách ly các dòng thiếu timestamp / event_type không hợp lệ.
3. Kiểm tra `user_session` rỗng; cách ly các sự kiện không xác định được Case ID hoặc xây dựng chính sách sessionization riêng và ghi rõ giả định.
4. Sắp xếp theo `user_session`, `event_time`; với sự kiện trùng thời điểm, dùng thứ tự dòng gốc làm quy tắc ổn định nhưng ghi nhận rằng thứ tự thực tế có thể không xác định.
5. Không tự động xóa phiên một sự kiện hay lặp `view` trước khi đánh giá tác động: đây có thể là hành vi hợp lệ và ảnh hưởng đến DFG, loops và drop-off.
6. Phân biệt phân tích theo **phiên** (`user_session`) với phân tích theo **sản phẩm trong phiên** (`user_session` + `product_id`). Mô hình chính dùng cấp phiên; mô hình cấp sản phẩm chỉ dùng khi cần phân tích hành vi với từng sản phẩm.
7. Ghi nhận phạm vi thời gian quan sát để tránh kết luận sai rằng phiên chưa có `purchase` là khách hàng đã bỏ mua vĩnh viễn.

### 4.1. Ví dụ log chuẩn hóa (giả lập)

| case:concept:name | concept:name | time:timestamp | product_id |
|---|---|---|---|
| `session_A` | `view` | `2019-11-01T09:00:00Z` | `1001` |
| `session_A` | `cart` | `2019-11-01T09:02:00Z` | `1001` |
| `session_A` | `purchase` | `2019-11-01T09:05:00Z` | `1001` |
| `session_B` | `view` | `2019-11-01T10:00:00Z` | `2002` |
| `session_B` | `cart` | `2019-11-01T10:03:00Z` | `2002` |
| `session_B` | `remove_from_cart` | `2019-11-01T10:04:00Z` | `2002` |

## 5. Liên hệ dữ liệu với chỉ số phân tích

| Chỉ số / kết quả | Trường sử dụng | Định nghĩa triển khai dự kiến |
|---|---|---|
| DFG (frequency) | `user_session`, `event_type`, `event_time` | Đếm số lần cặp hoạt động A → B xuất hiện liên tiếp trong các phiên. |
| DFG (performance) | `user_session`, `event_type`, `event_time` | Tổng hợp chênh lệch thời gian giữa các sự kiện liên tiếp, ví dụ trung vị theo cạnh A → B. |
| Tỷ lệ phiên có mua | `user_session`, `event_type` | Số phiên có ít nhất một `purchase` / tổng số phiên hợp lệ. |
| Drop-off sau bước | `user_session`, `event_type` | Cần xác định rõ mẫu số và quy tắc thứ tự: ví dụ tỷ lệ phiên đã có `cart` nhưng không có `purchase` sau đó trong khoảng quan sát. |
| Vòng lặp (loops) | `user_session`, `event_type`, `event_time` | Các cạnh lặp A → A hoặc vòng quay lại A → B → A trong chuỗi sự kiện. |
| Bottleneck | `user_session`, `event_type`, `event_time` | Cạnh có thời gian chuyển tiếp lớn theo chỉ số đã chọn; không mặc định đồng nghĩa độ trễ xử lý của hệ thống. |

## 6. Các rủi ro chất lượng dữ liệu

- **Thiếu dữ liệu:** `brand`, `category_code` có thể rỗng; cần thống kê null thực tế trước khi quyết định xử lý.
- **Dữ liệu lớn:** Nên thử nghiệm bằng mẫu có chọn theo phiên (lấy toàn bộ sự kiện của phiên được chọn), tránh lấy ngẫu nhiên từng dòng làm đứt chuỗi hành vi.
- **Trùng lặp:** Cần kiểm tra trùng dòng; nhiều sự kiện cùng loại trong một phiên không mặc nhiên là dữ liệu trùng lỗi.
- **Đa sản phẩm:** Một phiên có thể xem, thêm giỏ và mua nhiều sản phẩm; DFG cấp phiên phản ánh chuỗi hoạt động tổng thể, không nhất thiết là luồng của một sản phẩm.
- **Nhiều `purchase`:** Nguồn Kaggle ghi rõ một phiên có thể có nhiều sự kiện mua thuộc một đơn hàng; không xem mọi dòng purchase là một đơn hàng độc lập.
- **Giới hạn quan sát:** Log không nhất thiết chứa mọi hoạt động thanh toán, giao hàng, chăm sóc khách hàng hoặc lý do rời bỏ.

## 7. Nguồn tham khảo

1. Kechinov, M. *eCommerce behavior data from multi category store*. Kaggle. https://www.kaggle.com/datasets/mkechinov/ecommerce-behavior-data-from-multi-category-store
2. Kechinov, M. *eCommerce Data Overview*. Kaggle Notebook. https://www.kaggle.com/code/mkechinov/ecommerce-data-overview
3. PM4Py Documentation. https://processintelligence.solutions/static/api/2.7.11/index.html

> **Trạng thái tài liệu:** Bản khởi tạo dựa trên metadata công khai; cần xác nhận dataset chính thức và chạy kiểm tra schema trên CSV thực tế trước khi đánh dấu hoàn tất nghiệm thu.
