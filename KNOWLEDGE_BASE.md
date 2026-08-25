# 📚 KNOWLEDGE BASE - UIT-CAR-RACING
> **Tài liệu cung cấp ngữ cảnh toàn diện về kiến trúc hệ thống, thuật toán và lịch sử khắc phục sự cố dành cho các AI Agents tham gia dự án.**

---

## 📑 MỤC LỤC
1. Kiến trúc Hệ thống và Giao thức Socket
2. Cấu trúc Môi trường Docker và WSL2
3. Thuật toán Điều khiển Xe Tự hành
4. Sự cố Mô hình Nhận diện Ban đêm
5. Quy trình Gán nhãn và Huấn luyện Tối ưu
6. Lịch sử Khắc phục Sự cố Kỹ thuật

---

## 1. KIẾN TRÚC HỆ THỐNG VÀ GIAO THỨC SOCKET

Hệ thống hoạt động theo mô hình Client-Server. Game Unity đóng vai trò Server lắng nghe ở cổng 11000. Code Python trong Docker đóng vai trò Client.

### 1.1. Luồng Dữ liệu Tuần hoàn
* Game Unity xuất khung hình RGB
* Tiện ích socat chuyển tiếp gói tin TCP
* Thư viện client_lib.so viết bằng C nhận dữ liệu
* Script maycay.py dự đoán làn đường bằng YOLO11n-seg
* Script maycay.py tính toán góc lái và vận tốc
* Lệnh AVControl truyền ngược lại game Unity

### 1.2. Giao thức Bắt tay Bắt buộc
ĐỂ XE CÓ THỂ DI CHUYỂN, vòng lặp điều khiển BẮT BUỘC phải gọi đúng thứ tự 3 hàm từ client_lib:
1. `GetStatus`: Khởi tạo tín hiệu bắt tay với Unity
2. `GetRaw`: Lấy khung hình RGB
3. `AVControl`: Gửi lệnh tốc độ và góc lái

> [!WARNING]
> Nếu bỏ qua hàm `GetStatus`, quá trình bắt tay sẽ thất bại. Hàm `AVControl` vẫn chạy không báo lỗi nhưng game Unity sẽ phớt lờ lệnh và xe đứng im vĩnh viễn.

---

## 2. CẤU TRÚC MÔI TRƯỜNG DOCKER VÀ WSL2

Ban tổ chức cung cấp Docker Image `quocle28/it_car_2023:v1` chạy Ubuntu 18.04 và Python 3.8. Mọi đoạn code Python bắt buộc chạy bên trong vùng chứa này vì thư viện `client_lib.so` được biên dịch riêng cho Python 3.8.

### 2.1. Cầu nối Mạng socat
Docker không tự nhìn thấy cổng 11000 của Host Windows. Cần chạy socat chạy nền để chuyển tiếp TCP:
* Khi chơi bản đồ Demo 1.2 trên Windows: Trỏ socat về `host.docker.internal:11000`
* Khi chơi bản đồ V2_demo trên WSL2: Trỏ socat về địa chỉ IP mạng ảo của WSL2. Script `run_maycay.sh` tự động dò tìm IP này.

### 2.2. Xử lý Lỗi Đồ họa Headless
Vùng chứa Docker không có máy chủ hiển thị X11.
Không được đặt biến môi trường `QT_QPA_PLATFORM=offscreen` vì phiên bản OpenCV trong vùng chứa này thiếu plugin offscreen, dẫn đến sập chương trình ngay lập tức.
Giải pháp hiển thị: Code lưu khung hình hòa trộn ra file `live_view.jpg` liên tục. Người dùng mở file này trong VS Code để xem luồng video thời gian thực.

---

## 3. THUẬT TOÁN ĐIỀU KHIỂN XE TỰ HÀNH

Hệ thống lái sử dụng phương pháp Phối hợp Điểm Gần và Điểm Xa kết hợp bộ Ước lượng Độ Rộng Làn.

* **Trích xuất Tâm đường**: Tìm tọa độ pixel làn đường theo từng dòng từ dưới lên trên.
* **Sai số Điểm gần**: Chênh lệch tâm đường ở nửa dưới ảnh so với trục xe. Đảm bảo xe bám sát quỹ đạo.
* **Sai số Điểm xa**: Chênh lệch tâm đường ở một phần ba phía trên ảnh. Giúp xe đón đầu khúc cua.
* **Trọng số Động**: Ở vận tốc cao, xe tin tưởng Điểm xa nhiều hơn. Ở giao lộ rộng, xe loại bỏ hoàn toàn Điểm xa để tránh bẻ lái nhầm.
* **Kiểm soát Vận tốc**: Tự động hãm tốc tỷ lệ thuận với độ cong của đường phía trước.

---

## 4. SỰ CỐ MÔ HÌNH NHẬN DIỆN BAN ĐÊM

### 4.1. Phân tích Nguyên nhân Cốt lõi
Khi chạy xe trong bản đồ đêm V2_demo, xe liên tục trả về Góc lái +0.00 và Lỗi +0.0.
Lý do: Script gán nhãn tự động bằng thuật toán Adaptive Thresholding hoạt động sai hoàn toàn. Trong bản đồ đêm, mặt đường tối hơn cả cỏ và bầu trời. Thuật toán loang màu Flood-fill thất bại do hạt giống xuất phát nằm ở vùng tối đen.
Hệ quả: Sinh ra hàng loạt mặt nạ trắng xóa 100% toàn ảnh. Mô hình YOLO học sai kiến thức nên không phát hiện được bất kỳ làn đường nào trong thực tế.

### 4.2. Giải pháp Áp dụng
Tuyệt đối không dùng các script gán nhãn tự động dựa trên mức xám cho ảnh chụp ban đêm.
Dữ liệu ban đêm cần tải lên Roboflow, sử dụng công cụ Smart Polygon để khoanh vùng thủ công bề mặt đường, sau đó xuất ra định dạng YOLOv8 Segmentation chuẩn.

---

## 5. QUY TRÌNH GÁN NHÃN VÀ HUẤN LUYỆN TỐI ƯU

### 5.1. Thu thập và Gán nhãn
* **Bản đồ ngày Demo 1.2**: Trò chơi xuất sẵn mặt nạ màu song song với ảnh RGB. Dùng script `convert_mask_to_yolo.py` để trích xuất đa giác tọa độ tự động.
* **Bản đồ đêm V2_demo**: Chụp ảnh thô bằng `collect_data.py`. Gán nhãn thủ công qua Roboflow.
* **Biển báo Giao thông**: Dùng script `prepare_sign_dataset.py` tích hợp Segment Anything Model kết hợp thuật toán tính độ tròn để tự động khoanh vùng biển báo.

### 5.2. Tham số Huấn luyện Kaggle
Huấn luyện trên sổ tay Kaggle GPU T4. Tham số tối ưu cho mô hình YOLO11n-seg:
* Tắt lật ngang hình ảnh bằng cờ `fliplr=0.0`. Điều này sống còn để xe không nhầm lẫn biển báo rẽ trái và rẽ phải.
* Kích hoạt tăng cường độ sáng `hsv_v=0.4` giúp mô hình thích nghi tốt với môi trường đêm thiếu sáng.
* Sử dụng `imgsz=640` và `epochs=60`.

---

## 6. LỊCH SỬ KHẮC PHỤC SỰ CỐ KỸ THUẬT

| Dấu hiệu Lỗi | Nguyên nhân Gốc rễ | Giải pháp |
| :--- | :--- | :--- |
| Trục trặc kết nối báo Errno 111 | Máy chủ Socket của Unity chưa mở hoặc sập. | Khởi động cảnh 3D trong game trước. Chạy lại lệnh socat. |
| Port 11000 Address already in use | Hệ điều hành Windows giữ kết nối cũ ở trạng thái TIME_WAIT. | Chạy lệnh `fuser -k 11000/tcp` để diệt tiến trình ngầm, luôn thêm cờ `reuseaddr` vào lệnh socat. |
| Sập Python báo thiếu symbol | Thư viện client_lib.so dùng hàm cũ của CPython. | Tuyệt đối không dùng Python đời cao ở Host. Chạy code trong Docker Python 3.8. |
| Lỗi Qt plugin offscreen not found | Vùng chứa Docker của Ban tổ chức biên dịch thiếu plugin đồ họa ngầm. | Gỡ bỏ biến môi trường QT_QPA_PLATFORM khỏi script và xóa mọi hàm cv2.imshow. |
| Game Linux tắt đột ngột sau 1 giây | WSL2 thiếu thư viện kết xuất đồ họa OpenGL. | Cài đặt libglu1-mesa và chạy game kèm tiền tố môi trường SDL_AUDIODRIVER=dummy. |
| Xe im lìm dù log camera vẫn chạy | Bỏ quên hàm GetStatus trong vòng lặp điều khiển chính. | Đảm bảo chuỗi gọi hàm GetStatus tiếp nối GetRaw tiếp nối AVControl. |
