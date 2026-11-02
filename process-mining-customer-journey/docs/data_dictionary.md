# Từ điển dữ liệu (Data Dictionary)

## 1. Thông tin nguồn dữ liệu

- **Tên bộ dữ liệu tham chiếu:** eCommerce behavior data from multi category store.
- **Tác giả đăng tải:** Michael Kechinov.
- **Nguồn:** [Kaggle](https://www.kaggle.com/datasets/mkechinov/ecommerce-behavior-data-from-multi-category-store).
- **Nguồn thu thập được tác giả công bố:** dự án Open CDP; trang dữ liệu ghi nhận REES46 Marketing Platform.
- **Phạm vi được mô tả:** các sự kiện hành vi trên cửa hàng trực tuyến đa ngành hàng, từ tháng 10/2019 đến tháng 4/2020. Trang Kaggle cung cấp trực tiếp tệp tháng 10 và tháng 11/2019; các tháng khác được tác giả dẫn sang kho bổ sung. Phạm vi thực tế của dự án phụ thuộc vào những tệp CSV nhóm tải và sử dụng.
- **Đơn vị bản ghi:** một sự kiện liên quan đến một sản phẩm và một người dùng tại một thời điểm.

Tài liệu này mô tả **lược đồ được công bố trên Kaggle**, chưa phải báo cáo kiểm định chất lượng toàn bộ tệp CSV mà nhóm đã tải. Các quy tắc tiền xử lý ở phần 4 là đề xuất triển khai cho dự án Process Mining.

## 2. Danh mục trường dữ liệu

| Trường | Kiểu dữ liệu đề xuất khi xử lý bằng Python | Ý nghĩa theo nguồn Kaggle | Vai trò trong dự án |
| --- | --- | --- | --- |
| `event_time` | `datetime64[ns, UTC]` | Thời điểm xảy ra sự kiện, theo múi giờ UTC. | Sắp xếp các sự kiện và đo khoảng thời gian chuyển tiếp. |
| `event_type` | `string` / `category` | Loại tương tác với sản phẩm; thuộc một trong bốn giá trị ở mục 3. | Hoạt động (`concept:name`) trong Event Log. |
| `product_id` | `string` hoặc số nguyên có khả năng chứa giá trị lớn | Mã định danh sản phẩm. | Phân tích hành trình theo sản phẩm; kiểm tra hành động thêm/xóa/mua. |
| `category_id` | `string` hoặc số nguyên có khả năng chứa giá trị lớn | Mã định danh danh mục sản phẩm. | Phân nhóm theo danh mục. |
| `category_code` | `string`, có thể thiếu | Tên phân cấp danh mục nếu được gán; một số loại sản phẩm không có giá trị này. | Phân tích theo nhóm hàng. |
| `brand` | `string`, có thể thiếu | Tên thương hiệu viết chữ thường, có thể không được ghi nhận. | Phân tích theo thương hiệu. |
| `price` | `float64` hoặc `Decimal` khi cần phép tính tiền tệ chính xác | Giá của sản phẩm tại sự kiện. | Phân tích giá và phân khúc sản phẩm; không tự coi là tổng giá trị đơn hàng. |
| `user_id` | `string` hoặc số nguyên có khả năng chứa giá trị lớn | Mã định danh người dùng có tính ổn định qua các phiên. | Phân tích theo người dùng, phân biệt với phiên truy cập. |
| `user_session` | `string` | Mã phiên tạm thời, dùng chung cho các sự kiện thuộc một phiên; có thể thay đổi khi người dùng quay lại sau khoảng nghỉ dài. | Đề xuất làm Case ID (`case:concept:name`) để dựng trace theo phiên. |

**Lưu ý về kiểu dữ liệu:** Kaggle mô tả ý nghĩa trường chứ không quy định bắt buộc các kiểu `pandas` trong bảng. Việc giữ mã định danh dưới dạng chuỗi giúp tránh làm mất giá trị hoặc vô tình thực hiện phép toán trên ID. Không tự thay giá trị thiếu của `category_code` hoặc `brand` bằng một danh mục/thương hiệu có thật.

## 3. Định nghĩa bốn loại sự kiện `event_type`

`event_type` là **loại sự kiện**, không phải trạng thái tồn tại liên tục của khách hàng. Một phiên có thể xuất hiện nhiều sự kiện cùng loại và không nhất thiết đi theo thứ tự tuyến tính.

| Giá trị | Định nghĩa theo Kaggle | Cách diễn giải trong hành trình khách hàng | Điều không thể kết luận chỉ từ sự kiện |
| --- | --- | --- | --- |
| `view` | Người dùng xem một sản phẩm. | Ghi nhận một lần xem sản phẩm; có thể xuất hiện lặp lại trong cùng phiên. | Chưa chứng minh người dùng có ý định mua hoặc đã đọc hết thông tin sản phẩm. |
| `cart` | Người dùng thêm một sản phẩm vào giỏ hàng. | Ghi nhận hành động thêm giỏ, có thể xảy ra nhiều lần hoặc với nhiều sản phẩm. | Không đồng nghĩa đơn hàng đã được tạo hay thanh toán. |
| `remove_from_cart` | Người dùng loại một sản phẩm khỏi giỏ hàng. | Ghi nhận thao tác bỏ sản phẩm khỏi giỏ; có thể theo sau bằng một lần thêm giỏ khác. | Không đủ căn cứ khẳng định người dùng từ bỏ toàn bộ phiên mua sắm. |
| `purchase` | Người dùng mua một sản phẩm. | Ghi nhận sự kiện mua liên quan đến sản phẩm. | Không mặc định mỗi dòng `purchase` là một đơn hàng riêng biệt. |

Trang Kaggle nêu rõ **một phiên có thể có nhiều sự kiện `purchase` nhưng vẫn thuộc cùng một đơn hàng**. Vì vậy, không được dùng số dòng `purchase` làm số đơn hàng nếu chưa có quy tắc nhận diện đơn hàng được kiểm chứng.

### 3.1. Ví dụ trace minh họa

Các chuỗi dưới đây được tạo để giải thích phương pháp, **không phải mẫu dữ liệu đã trích xuất từ Kaggle**:

| Case | Trace | Diễn giải |
| --- | --- | --- |
| S1 | `view → cart → purchase` | Luồng tham chiếu tuyến tính. |
| S2 | `view → cart → remove_from_cart → cart → purchase` | Người dùng thay đổi giỏ rồi tiếp tục mua. |
| S3 | `view → view` | Xem lặp lại, chưa ghi nhận thêm giỏ hay mua trong trace. |
| S4 | `view → cart` | Có thêm giỏ nhưng chưa quan sát được sự kiện mua tiếp theo. |

Trace S4 không chứng minh người dùng đã từ bỏ mua hàng vĩnh viễn: phiên có thể bị cắt tại ranh giới thời gian thu thập dữ liệu.

## 4. Quy tắc chuyển đổi sang Event Log cho PM4Py

### 4.1. Ánh xạ thuộc tính

| Thành phần Process Mining | Trường CSV | Tên thuộc tính chuẩn thường dùng trong Event Log |
| --- | --- | --- |
| Case ID | `user_session` | `case:concept:name` |
| Activity | `event_type` | `concept:name` |
| Timestamp | `event_time` | `time:timestamp` |
| Event attributes | `user_id`, `product_id`, `category_id`, `category_code`, `brand`, `price` | Giữ nguyên tên cột khi cần phân tích bổ sung. |

**Đơn vị phân tích mặc định:** một phiên truy cập (`user_session`) tương ứng một case. Do một phiên có thể chứa tương tác với nhiều sản phẩm, DFG theo phiên phản ánh chuỗi tương tác tổng hợp, không nhất thiết là hành trình của một sản phẩm riêng lẻ. Với bài toán theo sản phẩm, có thể khảo sát khóa ghép (`user_session`, `product_id`) nhưng cần định nghĩa và kiểm thử riêng.

### 4.2. Kiểm tra và làm sạch dữ liệu

1. **Kiểm tra lược đồ:** xác nhận đủ 9 cột, nhận diện định dạng và ký tự phân cách CSV trước khi xử lý.
2. **Chuẩn hóa thời gian:** phân tích `event_time` theo UTC; kiểm tra giá trị không đọc được và sắp xếp tăng dần trong mỗi case. Nếu nhiều sự kiện cùng timestamp, phải công bố quy tắc xử lý thứ tự (ví dụ giữ thứ tự dòng gốc); không tự nhận rằng thứ tự đó phản ánh thời gian thực chính xác hơn.
3. **Kiểm tra hoạt động:** chỉ chấp nhận bốn giá trị được nguồn công bố; báo cáo riêng các giá trị lạ hoặc thiếu.
4. **Kiểm tra Case ID:** thống kê `user_session` thiếu/rỗng trước khi tạo Event Log. Không tự ghép tất cả dòng thiếu session thành một case.
5. **Kiểm tra thuộc tính bổ sung:** thống kê giá trị thiếu ở `brand` và `category_code`; không xóa toàn bộ bản ghi chỉ vì thiếu hai trường này khi vẫn có đủ ba thuộc tính cốt lõi.
6. **Kiểm tra trùng lặp:** thống kê dòng giống hệt nhau trước khi quyết định loại bỏ. Những lần tương tác thực tế có thể có cùng thuộc tính; xóa trùng thiếu kiểm chứng có thể làm sai tần suất DFG.
7. **Kiểm tra giá:** nhận diện giá không hợp lệ, giá âm và giá bằng 0 để đánh giá riêng. Không mặc định `price` là doanh thu đã thanh toán.
8. **Lưu vết xử lý:** lưu số dòng đầu vào, số dòng loại bỏ theo từng nguyên nhân, khoảng thời gian dữ liệu và tham số lọc. Giữ bản gốc trong `data/raw/`, ghi dữ liệu đã chuẩn hóa vào `data/processed/`.

Việc lọc phiên chỉ có một sự kiện là **lựa chọn phân tích**, không phải quy tắc bắt buộc. Các phiên này không tạo cạnh trực tiếp trong DFG nhưng vẫn có thể quan trọng khi tính tỷ lệ phiên chưa chuyển đổi.

## 5. Sử dụng dữ liệu cho các chỉ số của đề tài

| Chỉ số | Định nghĩa vận hành đề xuất | Giới hạn diễn giải |
| --- | --- | --- |
| Tần suất cạnh DFG `a → b` | Đếm số lần `a` đứng ngay trước `b` trong cùng trace sau khi sắp xếp sự kiện. | Một case có thể đóng góp nhiều lần cho cùng cạnh. |
| Chuyển đổi `view → cart` theo phiên | Số phiên có ít nhất một `cart` xảy ra sau một `view`, chia cho số phiên có `view`. | Đây là chuyển đổi theo thứ tự trong phiên, không phải số cạnh DFG trực tiếp. |
| Chuyển đổi `cart → purchase` theo phiên | Số phiên có `purchase` sau ít nhất một `cart`, chia cho số phiên có `cart`. | Cần xác định rõ có yêu cầu cùng `product_id` hay không. |
| Drop-off sau `cart` | Số phiên có `cart` nhưng không quan sát thấy `purchase` sau đó, chia cho số phiên có `cart`. | Chỉ phản ánh cửa sổ quan sát và cách chọn case. |
| Loops | Đếm chuyển tiếp lặp như `view → view` hoặc chuỗi quay lại như `cart → remove_from_cart → cart`. | Không mặc định vòng lặp là lỗi hoặc trải nghiệm xấu. |
| Thời gian chuyển tiếp | Hiệu `event_time` giữa hai sự kiện liên tiếp trong cùng case; tổng hợp theo cạnh bằng trung vị hoặc trung bình. | Không thể mặc định toàn bộ thời gian là độ trễ hệ thống. |

Các công thức KPI ở phần này là **quy ước phân tích đề xuất cho nhóm**, không phải chỉ số được Kaggle công bố hay đầu ra duy nhất của PM4Py. Cần ghi rõ mẫu số, cửa sổ thời gian, bộ lọc và đơn vị case khi công bố kết quả.

## 6. Phạm vi xác minh và những điểm cần đối chiếu với CSV thực tế

- Đã đối chiếu trên trang Kaggle: tên bộ dữ liệu, 9 trường, ý nghĩa bốn sự kiện, thời gian UTC, tính chất của `user_session` và khả năng có nhiều `purchase` trong một phiên.
- Chưa kiểm tra trực tiếp các tệp CSV nhóm sử dụng: tỷ lệ thiếu, số bản ghi, phân phối hoạt động, tính duy nhất của ID, tỷ lệ trùng, giá trị ngoại lệ và thời gian chuyển tiếp.
- Cần ghi lại tên tệp và phạm vi tháng thực tế trong `data/raw/` trước khi chạy phân tích. Không dùng thống kê của toàn bộ bộ dữ liệu để mô tả một tập con chưa kiểm tra.

## 7. Tài liệu tham khảo

[1] Kechinov, M. *eCommerce behavior data from multi category store*. Kaggle. https://www.kaggle.com/datasets/mkechinov/ecommerce-behavior-data-from-multi-category-store

[2] PM4Py, *Documentation*. https://pm4py-source.readthedocs.io/

Nguồn [1] được sử dụng để xác định cấu trúc và ngữ nghĩa dữ liệu. Nguồn [2] là tài liệu kỹ thuật tham khảo cho bước chuyển đổi và xử lý Event Log bằng PM4Py; các lựa chọn tiền xử lý cụ thể là thiết kế của nhóm.
