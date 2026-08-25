# 📚 KNOWLEDGE BASE - UIT-CAR-RACING
> **Tài liệu tổng hợp toàn diện từ A-Z về thể lệ cuộc thi, kiến trúc hệ thống, thuật toán điều khiển tự hành, quy trình huấn luyện YOLO11 và cẩm nang xử lý sự cố kỹ thuật.**

---

## 📑 MỤC LỤC
1. Bối cảnh Cuộc thi và Thể lệ Thi đấu
2. Kiến trúc Hệ thống và Giao thức Socket
3. Thuật toán Điều khiển Xe Tự hành
4. Bộ Công cụ Dữ liệu và Huấn luyện YOLO11
5. Lịch sử Khắc phục Sự cố Kỹ thuật
6. Cấu trúc Thư mục Toàn dự án

---

## 1. BỐI CẢNH CUỘC THI VÀ THỂ LỆ THI ĐẤU

### 1.1. Thông tin Chung
* **Tên cuộc thi**: UIT CAR RACING 2025 MÙA XIV - BẢNG CHUYÊN NGHIỆP.
* **Đơn vị tổ chức**: Khoa Kỹ thuật Máy tính – Trường Đại học Công nghệ Thông tin, ĐHQG-HCM.
* **Hình thức thi đấu**: Vòng Sơ loại thi đấu trên phần mềm giả lập Unity Simulator. Vòng Chung kết thi đấu offline đối kháng trên sa bàn vật lý thực tế.

### 1.2. Cơ chế Tính điểm
Mỗi sa hình bản đồ thi đấu có 10 Checkpoints:
* **Sử dụng AI tự huấn luyện YOLO11n-seg**: Đạt 10 điểm / 1 checkpoint, tổng tối đa 100 điểm.
* **Sử dụng ảnh Phân đoạn do BTC cung cấp**: Chỉ đạt 5 điểm / 1 checkpoint, tổng tối đa 50 điểm.

> 💡 **Chiến lược**: Việc tự huấn luyện mô hình YOLO phân đoạn đường và biển báo là điều kiện tiên quyết để nhân đôi điểm số.

### 1.3. Thử thách Sa hình Dự kiến
* Đường 2 chiều có 2 làn đường, đường 1 chiều 1 làn hoặc 2 làn.
* Khúc cua quanh co, dốc cua gấp.
* Đổi loại đường, điều kiện ánh sáng thay đổi, có bóng cây che khuất.
* Bản đồ ban đêm, sương mù với bề mặt đường tối đen.
* Ngã ba, ngã tư đi theo hiệu lệnh biển báo.

---

## 2. KIẾN TRÚC HỆ THỐNG VÀ GIAO THỨC SOCKET

Hệ thống hoạt động theo mô hình Client-Server. Game Unity đóng vai trò Server lắng nghe ở cổng 11000. Môi trường Docker đóng vai trò Client.

### 2.1. Sơ đồ Luồng Tuần Hoàn
* Game Unity xuất khung hình RGB
* Tiện ích socat chuyển tiếp gói tin TCP
* Thư viện client_lib.so viết bằng C nhận dữ liệu
* Script maycay.py dự đoán làn đường bằng YOLO11n-seg
* Lệnh AVControl truyền tốc độ và góc lái ngược lại game Unity

### 2.2. Giao thức Bắt tay Bắt buộc
ĐỂ XE CÓ THỂ DI CHUYỂN, vòng lặp điều khiển BẮT BUỘC phải gọi đúng thứ tự 3 hàm:
1. `GetStatus`: Khởi tạo tín hiệu bắt tay với Unity
2. `GetRaw`: Lấy khung hình RGB
3. `AVControl`: Gửi lệnh tốc độ và góc lái

> [!WARNING]
> Nếu bỏ qua hàm `GetStatus`, quá trình bắt tay sẽ thất bại. Hàm `AVControl` vẫn chạy không báo lỗi nhưng game Unity sẽ phớt lờ lệnh và xe đứng im vĩnh viễn.

---

## 3. THUẬT TOÁN ĐIỀU KHIỂN XE TỰ HÀNH

Hệ thống điều khiển trong `maycay.py` không dùng thuật toán dò đường đơn giản mà sử dụng thuật toán thích ứng đa tầng.

### 3.1. Phương pháp Quét Tâm Làn Đường
1. Quét từng dòng pixel từ đáy ảnh lên trên.
2. Xác định các tọa độ pixel trắng đại diện cho mặt đường dự đoán bởi YOLO.
3. Tính trung điểm của từng dòng để tạo thành chuỗi điểm tim đường.
4. Tính tâm đường có trọng số khoảng cách với điểm đáy ảnh được gán trọng số lớn hơn.

### 3.2. Kỹ thuật Phối hợp Điểm Gần và Điểm Xa
* **Sai số Điểm gần - E_near**: Chênh lệch tâm đường ở nửa dưới ảnh so với trục xe. Tin cậy tuyệt đối khi vào cua gắt.
* **Sai số Điểm xa - E_far**: Chênh lệch tâm đường ở một phần ba phía trên ảnh. Giúp xe đón đầu khúc cua.
* **Sai số tổng hợp**: E_blended = w_near * E_near + w_far * E_far
* Trọng số w_far sẽ tăng tuyến tính theo vận tốc của xe.

### 3.3. Bộ Ước lượng Độ Rộng Làn
* Hệ thống liên tục đo bề ngang mặt đường.
* Khi phát hiện độ rộng tăng đột biến, ví dụ lớn hơn 20%, hệ thống tự động loại bỏ hoàn toàn Điểm xa, chỉ tin cậy Điểm gần để giữ xe không bị bẻ lái ảo ra giữa ngã ba.

### 3.4. Kiểm soát Vận tốc theo Độ Cong
* Tự động hãm tốc tỷ lệ thuận với độ cong của đường phía trước.
* Công thức tính Vận tốc: Speed = max[MinSpeed, MaxSpeed * [1 - 0.7 * CurveRatio]]

---

## 4. BỘ CÔNG CỤ DỮ LIỆU VÀ HUẤN LUYỆN YOLO11

### 4.1. Sự cố Mô hình Nhận diện Ban đêm V2_demo
* **Phân tích Nguyên nhân**: Khi chạy xe trong bản đồ đêm, xe liên tục trả về Góc lái +0.00. Lý do là script gán nhãn tự động bằng Adaptive Thresholding hoạt động sai hoàn toàn. Trong bản đồ đêm, mặt đường tối hơn cả cỏ và bầu trời. Thuật toán loang màu thất bại do hạt giống xuất phát nằm ở vùng tối đen, sinh ra mặt nạ trắng xóa toàn ảnh.
* **Giải pháp Bắt buộc**: Tuyệt đối không dùng script đo mức xám tự động cho ảnh ban đêm. Dữ liệu ban đêm cần tải lên Roboflow, sử dụng công cụ Smart Polygon để khoanh vùng thủ công, xuất định dạng YOLOv8 Segmentation.

### 4.2. Tiền xử lý Biển báo Giao thông
* Ứng dụng Segment Anything Model của Meta kết hợp thuật toán lọc độ tròn.
* Công thức tính độ tròn: Circularity = [4 * Pi * Area] / [Perimeter * Perimeter]
* Yêu cầu Circularity lớn hơn hoặc bằng 0.8 để được xem là biển báo.
* Kỹ thuật Nhãn Rỗng: Tự động tạo các file text dung lượng 0 byte cho ảnh phong cảnh không có biển báo để triệt tiêu hiện tượng báo động giả.

### 4.3. Cấu hình Huấn luyện Sống còn
Huấn luyện trên Kaggle GPU T4 yêu cầu các tham số tối ưu:
* Tắt lật ngang hình ảnh bằng cờ `fliplr=0.0`. Điều này sống còn để xe không nhầm lẫn biển báo rẽ trái và rẽ phải.
* Kích hoạt tăng cường độ sáng `hsv_v=0.4` giúp mô hình thích nghi tốt với môi trường đêm thiếu sáng.
* Chống lỗi tràn bộ nhớ RAM Docker bằng cách cài đặt `workers=0` và `cache='disk'`.

---

## 5. LỊCH SỬ KHẮC PHỤC SỰ CỐ KỸ THUẬT

| Dấu hiệu Lỗi | Nguyên nhân | Giải pháp |
| :--- | :--- | :--- |
| **ConnectionRefusedError Errno 111** | Máy chủ Socket của Unity chưa mở hoặc sập. | Khởi động cảnh 3D trong game trước. Chạy lại lệnh socat. |
| **Address already in use cổng 11000** | Hệ điều hành Windows giữ kết nối cũ ở trạng thái TIME_WAIT. | Chạy lệnh `fuser -k 11000/tcp` để diệt tiến trình ngầm, luôn thêm cờ `reuseaddr` vào lệnh socat. |
| **undefined symbol _Py_CheckRecursionLimit** | Thư viện client_lib.so dùng hàm cũ của CPython. | Tuyệt đối không dùng Python đời cao ở máy chủ. Chạy code trong Docker Python 3.8. |
| **Lỗi Qt plugin offscreen not found** | Vùng chứa Docker biên dịch thiếu plugin đồ họa ngầm. | Xóa bỏ biến môi trường QT_QPA_PLATFORM khỏi script và xóa mọi hàm cv2.imshow. Xem ảnh qua file live_view.jpg. |
| **Game Linux tắt đột ngột sau 1 giây** | WSL2 thiếu thư viện kết xuất đồ họa OpenGL. | Cài đặt libglu1-mesa và chạy game kèm tiền tố môi trường SDL_AUDIODRIVER=dummy. |

---

## 6. CẤU TRÚC THƯ MỤC TOÀN DỰ ÁN

```text
UIT-CAR-RACING/
├── dataset/                                # Dữ liệu hình ảnh thu thập
│   └── raw/
│       ├── day/                            # Ảnh thô ban ngày
│       └── night/                          # Ảnh thô ban đêm
├── Demo 1.2/                               # Bản đồ mô phỏng Windows
├── V2_demo/                                # Bản đồ mô phỏng Linux
├── Road_Seg_Model/                         # Mô hình và trọng số làn đường
│   ├── modelYolo/                          # Checkpoint YOLO đã huấn luyện
│   │   ├── weights/
│   │   │   ├── best.pt                     # Trọng số tối ưu nhất
│   │   │   └── last.pt                     # Trọng số epoch cuối
│   │   └── results.png                     # Đồ thị đánh giá mAP
├── training/                               # Bộ công cụ huấn luyện YOLO
│   ├── configs/                            # File cấu hình YAML
│   │   ├── road_seg.yaml                   # Cấu hình tập dữ liệu Làn đường
│   │   └── traffic_sign_seg.yaml           # Cấu hình tập dữ liệu Biển báo
│   ├── utils/                              # Công cụ tiền xử lý và gán nhãn
│   │   ├── convert_mask_to_yolo.py         # Trích xuất contour sang Polygon
│   │   └── prepare_sign_dataset.py         # Gán nhãn biển báo bằng SAM
│   ├── train_road.py                       # Script huấn luyện làn đường
│   └── train_night_kaggle.ipynb            # Sổ tay huấn luyện trên Kaggle
├── client_lib.so                           # Thư viện giao tiếp Socket với Unity
├── collect_data.py                         # Công cụ thu thập ảnh tự động
├── maycay.py                               # Mã nguồn điều khiển xe tự hành chính
└── KNOWLEDGE_BASE.md                       # Tài liệu tổng hợp kiến thức
```

---
<div align="center">
  <sub>Bản quyền tài liệu thuộc về Đội thi UIT-CAR-RACING • Cuộc thi Lập trình Xe tự hành 2025</sub>
</div>
