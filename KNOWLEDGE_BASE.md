# 📚 BÁO CÁO TỔNG HỢP KIẾN THỨC & KỸ THUẬT DỰ ÁN UIT-CAR-RACING
> **Tài liệu tổng hợp toàn diện từ A-Z về thể lệ cuộc thi, kiến trúc hệ thống, thuật toán điều khiển tự hành, quy trình huấn luyện thị giác máy tính YOLO11 và cẩm nang xử lý sự cố kỹ thuật.**

---

## 📑 MỤC LỤC
1. [Bối cảnh Cuộc thi & Thể lệ Thi đấu](#1-bối-cảnh-cuộc-thi--thể-lệ-thi-đấu)
2. [Kiến trúc Hệ thống & Luồng Dữ liệu](#2-kiến-trúc-hệ-thống--luồng-dữ-liệu)
3. [Thuật toán Điều khiển Xe Tự hành (Steering & Speed Logic)](#3-thuật-toán-điều-khiển-xe-tự-hành-steering--speed-logic)
4. [Bộ Công cụ Dữ liệu & Huấn luyện YOLO11 (Data & Training Pipeline)](#4-bộ-công-cụ-dữ-liệu--huấn-luyện-yolo11-data--training-pipeline)
5. [Cẩm nang Vận hành trên Windows 11 & WSL2](#5-cẩm-nang-vận-hành-trên-windows-11--wsl2)
6. [Tổng hợp Sự cố Kỹ thuật & Giải pháp Đã Triển khai (Troubleshooting Matrix)](#6-tổng-hợp-sự-cố-kỹ-thuật--giải-pháp-đã-triển-khai-troubleshooting-matrix)
7. [Cấu trúc Thư mục Toàn dự án](#7-cấu-trúc-thư-mục-toàn-dự-án)

---

## 1. BỐI CẢNH CUỘC THI & THỂ LỆ THI ĐẤU

### 1.1. Thông tin Chung
* **Tên cuộc thi**: UIT CAR RACING 2025 MÙA XIV - BẢNG CHUYÊN NGHIỆP.
* **Đơn vị tổ chức**: Khoa Kỹ thuật Máy tính – Trường Đại học Công nghệ Thông tin, ĐHQG-HCM.
* **Hình thức thi đấu qua các vòng**:
  1. **Vòng Sơ loại & Khởi động (Mô phỏng trực tuyến)**: Thi đấu trên phần mềm giả lập Unity Simulator máy chủ BTC. Bài thi được nộp dưới dạng gói Docker Image nén (`.tar`).
  2. **Vòng Chung kết (Sa hình vật lý thực tế)**: Thi đấu offline đối kháng trên **mô hình xe thật và sa bàn thực tế** tại khuôn viên trường ĐH Công nghệ Thông tin.

### 1.2. Cơ chế Tính điểm (Tối quan trọng)
Mỗi sa hình bản đồ thi đấu có **10 Checkpoints**:
* **Sử dụng Model AI tự xử lý nhận diện (YOLO11n-seg tự huấn luyện)**: Đạt **10 điểm / 1 checkpoint** (Tối đa **100 điểm/vòng**).
* **Sử dụng ảnh Phân đoạn (Segment) mặc định do BTC cung cấp**: Chỉ đạt **5 điểm / 1 checkpoint** (Tối đa **50 điểm/vòng**).
* *(Trường hợp bằng điểm: Đội nào có tổng thời gian hoàn thành vòng đua sớm hơn sẽ giành chiến thắng)*.

> 💡 **Kết luận chiến lược**: Việc tự huấn luyện mô hình YOLO phân đoạn đường và biển báo của riêng đội là điều kiện tiên quyết để **nhân đôi điểm số tối đa** và giành lợi thế vượt trội.

### 1.3. Thử thách Sa hình Dự kiến
* Đường 2 chiều có 2 làn đường, đường 1 chiều 1 làn / 2 làn.
* Khúc cua quanh co, dốc cua gấp.
* **Đổi loại đường, điều kiện ánh sáng thay đổi, có bóng cây che khuất** (Gây nhiễu thị giác).
* **Bản đồ ban đêm / sương mù** (Độ tương phản thấp, mặt đường tối đen).
* Ngã ba, ngã tư đi theo hiệu lệnh biển báo, thử thách đèn giao thông và đỗ xe.

### 1.4. Quy cách Nộp bài
* Bài thi nộp qua form BTC gồm 2 thành phần:
  1. **Tệp nén Docker Image**: `uit_car_racing_submission.tar` (đóng gói toàn bộ môi trường và mã nguồn).
  2. **Tệp ghi chú `instruction.txt`**: Ghi rõ lệnh khởi chạy (ví dụ `python /workspace/UIT-CAR-RACING/maycay.py`).

---

## 2. KIẾN TRÚC HỆ THỐNG & LUỒNG DỮ LIỆU

### 2.1. Sơ đồ Luồng Tuần Hoàn
```
[Unity Simulator (Host)]
       │
       ▼ (Gửi khung hình RGB & Trạng thái xe qua TCP Socket)
[socat Network Forwarder (Port 11000)]
       │
       ▼ (Chuyển tiếp nội bộ)
[client_lib (Socket Interface CPython 3.8)]
       │
       ▼ (GetRaw RGB Frame)
[maycay.py: YOLO11n-seg Predict]
       │
       ▼ (Binary Mask mặt đường)
[Thuật toán Tính Góc Lái & Vận Tốc Thích Ứng]
       │
       ▼ (AVControl: Speed, Angle)
[client_lib -> socat -> Unity Simulator]
```

### 2.2. Chi tiết các Thành phần Cốt lõi
* **Unity Simulator**: Ứng dụng đóng gói nhị phân (mã nguồn đóng), render vật lý xe và camera hành trình ảo, lắng nghe lệnh điều khiển tại Socket Port `11000` (hoặc `11001`).
* **CEEC Docker Container (`quocle28/it_car_2023:v1`)**: Môi trường Linux Ubuntu 18.04 với Python 3.8, chứa thư viện `client_lib.so` để giao tiếp với game.
* **Mã nguồn Điều khiển (`maycay.py`)**: Đóng vai trò bộ não, xử lý hình ảnh qua YOLO và điều chỉnh góc lái theo chu kỳ ~30 FPS.

---

## 3. THUẬT TOÁN ĐIỀU KHIỂN XE TỰ HÀNH (STEERING & SPEED LOGIC)

Hệ thống điều khiển trong `maycay.py` không dùng PID cứng nhắc đơn thuần mà sử dụng **thuật toán thích ứng đa tầng (Multi-layered Adaptive Control)**:

### 3.1. Phương pháp Quét Tâm Làn Đường (Center Points Extraction)
1. Quét từng dòng pixel từ đáy ảnh lên trên (từ gần đến xa).
2. Xác định các tọa độ pixel trắng (`> 0`) đại diện cho mặt đường dự đoán bởi YOLO.
3. Tính trung điểm của từng dòng để tạo thành chuỗi điểm tim đường (`green_line_points`).
4. Tính tâm đường có trọng số khoảng cách (điểm đáy ảnh được gán trọng số lớn hơn điểm trên cao).

### 3.2. Kỹ thuật Phối hợp Điểm Gần & Điểm Xa (Near/Far Point Blending)
* **Near Error ($E_{near}$)**: Sai số giữa tâm đường ở nửa dưới ảnh với trục giữa xe. Tin cậy tuyệt đối khi vào cua gắt hoặc khi đường bị mở rộng bất thường.
* **Far Error ($E_{far}$)**: Sai số ở 1/3 trên ảnh. Giúp xe đón đầu khúc cua phía trước khi chạy tốc độ cao trên đường thẳng.
* **Sai số tổng hợp (Blended Error)**:
  $$E_{blended} = w_{near} \cdot E_{near} + w_{far} \cdot E_{far}$$
  Trong đó trọng số $w_{far}$ tăng tuyến tính theo vận tốc của xe.

### 3.3. Bộ Ước lượng Độ Rộng Làn (Lane Width Estimator)
* Liên tục đo bề ngang mặt đường tại nhiều dòng pixel.
* Khi phát hiện độ rộng tăng đột biến $> 20\%$ (giao lộ, ngã ba, đường phình to), hệ thống tự động **loại bỏ hoàn toàn điểm Far ($w_{far} = 0$)**, chỉ tin cậy điểm Near để giữ xe không bị bẻ lái ảo ra giữa ngã ba.

### 3.4. Kiểm soát Vận Tốc Tự Động theo Độ Cong (Curvature-based Speed Control)
* Tính hệ số cong của đường: $CurveRatio = \frac{|TopRowCX - BottomRowCX|}{Width / 2}$.
* Tự động hãm tốc khi vào cua gắt và tăng tốc tối đa trên đường thẳng:
  $$Speed = \max(MinSpeed, MaxSpeed \cdot (1 - 0.7 \cdot CurveRatio))$$

---

## 4. BỘ CÔNG CỤ DỮ LIỆU & HUẤN LUYỆN YOLO11 (DATA & TRAINING PIPELINE)

### 4.1. Công cụ Thu thập Dữ liệu (`collect_data.py`)
* Hỗ trợ 2 chế độ: Lái tay bằng bàn phím (`--drive manual`) và Xe tự lái bằng model cũ (`--drive av`).
* Chụp ảnh theo khoảng thời gian tùy chỉnh (ví dụ `0.3s/ảnh`), tự động phân loại thư mục `dataset/raw/day/` hoặc `dataset/raw/night/`.
* Tích hợp cơ chế tự động chờ khung hình và bọc ngoại lệ chống đứt kết nối Socket.

### 4.2. Tiền xử lý & Tạo Nhãn Tự động
* **Phân đoạn Làn đường (`convert_mask_to_yolo.py`)**: Trích xuất đường bao Contours bằng OpenCV từ ảnh mặt nạ, chuẩn hóa tọa độ sang định dạng đa giác **Polygon YOLO `.txt`** (tối thiểu 3 đỉnh, tức $\ge 6$ tọa độ).
* **Phân đoạn Biển báo (`prepare_sign_dataset.py`)**:
  * Ứng dụng **Segment Anything Model (SAM)** của Meta kết hợp thuật toán lọc độ tròn Circularity:
    $$Circularity = \frac{4\pi \cdot Area}{Perimeter^2} \ge 0.8$$
  * Tự động gán 5 lớp biển báo: `di_thang` (0), `re_trai` (1), `re_phai` (2), `cam_re_trai` (3), `cam_re_phai` (4).
* **Kỹ thuật Nhãn Rỗng (Empty Labels)**: Tự động tạo các file `.txt` dung lượng 0 byte cho các ảnh nền phong cảnh không có biển báo, giúp mô hình triệt tiêu hoàn toàn hiện tượng báo động giả (False Positives).

### 4.3. Cấu hình Huấn luyện Tối ưu An toàn (Chống Crash)
* **Huấn luyện Làn đường (`train_road.py`)**: Đặt `workers=0` và `cache='disk'`, `batch=2` để ngăn triệt để lỗi tràn bộ nhớ dùng chung `/dev/shm` trong Docker.
* **Huấn luyện Biển báo (`train_yolo_signs.py`)**: BẮT BUỘC đặt `fliplr=0.0` (tắt lật ngang) để giữ nguyên ý nghĩa hướng rẽ của biển báo; giảm `imgsz=320` và `mosaic=0.3`.

---

## 5. CẨM NANG VẬN HÀNH TRÊN WINDOWS 11 & WSL2

### 5.1. Bản đồ Windows (`Demo 1.2` - `.exe`)
```powershell
# 1. Bật game Unity Demo 1.2/UCR_Unity.exe trên Windows -> Bấm Play
# 2. Mở PowerShell khởi động Docker:
docker start -ai it-car

# 3. Trong Docker: Chuyển tiếp cổng và chạy xe:
pkill -9 socat 2>/dev/null; fuser -k 11000/tcp 2>/dev/null; sleep 1
socat TCP-LISTEN:11000,reuseaddr,fork TCP:host.docker.internal:11000 &
cd /workspace/UIT-CAR-RACING
python maycay.py
```

### 5.2. Bản đồ Linux Ban đêm (`V2_demo` - `.x86_64`)
```bash
# Terminal 1: Mở game Unity Linux trong WSL2:
chmod +x /mnt/d/UIT-CAR-RACING/V2_demo/UCRlinux.x86_64
SDL_AUDIODRIVER=dummy /mnt/d/UIT-CAR-RACING/V2_demo/UCRlinux.x86_64

# Terminal 2: Mở PowerShell kết nối Docker và chạy thu thập ảnh / điều khiển:
docker start -ai it-car

# Trong Docker:
pkill -9 socat 2>/dev/null; fuser -k 11000/tcp 2>/dev/null; sleep 1
socat TCP-LISTEN:11000,reuseaddr,fork TCP:host.docker.internal:11000 &
cd /workspace/UIT-CAR-RACING

# Thu thập ảnh ban đêm:
python collect_data.py --scene night --drive manual --max 1000

# Hoặc chạy xe tự hành:
python maycay.py
```

---

## 6. TỔNG HỢP SỰ CỐ KỸ THUẬT & GIẢI PHÁP ĐÃ TRIỂN KHAI (TROUBLESHOOTING MATRIX)

| Sự cố / Lỗi gặp phải | Nguyên nhân Gốc rễ | Giải pháp Triệt để Đã Áp dụng |
| :--- | :--- | :--- |
| **`ConnectionRefusedError: [Errno 111]`** | Unity chưa kịp khởi động Socket Server hoặc Docker không thấy cổng ngoài Windows. | 1. Đảm bảo Unity đã load xong cảnh 3D trước khi chạy Python.<br>2. Sử dụng `socat` tạo cầu nối chuyển tiếp từ cổng `11000` nội bộ Docker ra `host.docker.internal:11000`. |
| **`Address already in use` trên cổng 11000** | Socket vừa đóng bị giữ lại trong hàng đợi `TIME_WAIT` của hệ điều hành. | 1. Dùng lệnh `fuser -k 11000/tcp` giải phóng cổng.<br>2. Bổ sung cờ `reuseaddr` vào lệnh socat. |
| **`undefined symbol: _Py_CheckRecursionLimit`** | Chạy file C-extension `client_lib.so` bằng Python 3.10+ ngoài WSL (do symbol này bị xóa từ Python 3.10). | Bắt buộc chạy mã nguồn Python bên trong **Docker container `it-car`** (nơi có môi trường Conda Python 3.8 chuẩn). |
| **`VS Code Missing GLIBC >= 2.28`** | VS Code từ bản 1.86 ngừng hỗ trợ Dev Container trên nền Ubuntu 18.04 cũ. | Không cần Attach VS Code vào container. Mở và chỉnh sửa file trực tiếp trên VS Code Windows (nhờ cơ chế mount volume `-v`), chỉ dùng Terminal để tương tác với Docker. |
| **`qt.qpa.xcb: could not connect to display`** | OpenCV gọi `cv2.imshow` trong Docker khi không có màn hình đồ họa X11. | Đã cấu hình tự động `QT_QPA_PLATFORM = 'offscreen'` và bọc hàm hiển thị an toàn `show_image_safe()`. |
| **`Unity Linux .x86_64 hiện 1s rồi tắt`** | Thiếu thư viện đồ họa OpenGL/Mesa và lỗi driver âm thanh trên WSL. | Cài đặt các gói `libglu1-mesa`, `libgles2-mesa`, `libasound2` và chạy kèm tiền tố `SDL_AUDIODRIVER=dummy`. |

---

## 7. CẤU TRÚC THƯ MỤC TOÀN DỰ ÁN

```text
UIT-CAR-RACING/
├── dataset/                                # Thư mục chứa dữ liệu hình ảnh
│   └── raw/
│       ├── day/                            # Ảnh thu thập ban ngày
│       └── night/                          # Ảnh thu thập ban đêm (V2_demo)
├── Demo 1.2/                               # Bản đồ mô phỏng Windows (.exe)
│   └── UCR_Unity.exe                       # Game thực thi trên Windows
├── V2_demo/                                # Bản đồ mô phỏng Linux (.x86_64)
│   ├── UCRlinux.x86_64                     # Game thực thi trên WSL2
│   ├── UnityPlayer.so                      # Thư viện đồ họa Unity
│   └── UCRlinux_Data/                      # Dữ liệu game 3D
├── Road_Seg_Model/                         # Mô hình & trọng số làn đường
│   ├── modelYolo/                          # Checkpoint YOLO đã huấn luyện
│   │   ├── weights/
│   │   │   ├── best.pt                     # Trọng số tối ưu nhất
│   │   │   └── last.pt                     # Trọng số epoch cuối
│   │   └── results.png                     # Đồ thị đánh giá mAP
│   └── yolo_model                          # Checkpoint dự phòng
├── training/                               # Bộ công cụ huấn luyện YOLO độc lập
│   ├── configs/                            # File cấu hình YAML
│   │   ├── road_seg.yaml                   # Cấu hình tập dữ liệu Làn đường
│   │   └── traffic_sign_seg.yaml           # Cấu hình tập dữ liệu Biển báo
│   ├── utils/                              # Công cụ tiền xử lý & gán nhãn
│   │   ├── __init__.py                     # File khai báo package Python
│   │   ├── convert_mask_to_yolo.py         # Trích xuất contour sang Polygon YOLO
│   │   └── prepare_sign_dataset.py         # Tự động gán nhãn biển báo (SAM + lọc tròn)
│   ├── train_road.py                       # Huấn luyện mô hình làn đường (an toàn Docker)
│   └── train_yolo_signs.py                 # Huấn luyện biển báo (tắt lật ngang fliplr=0.0)
├── client_lib.so                           # Thư viện giao tiếp Socket với Unity (Python 3.8)
├── collect_data.py                         # Công cụ thu thập ảnh tự động
├── maycay.py                               # Mã nguồn điều khiển xe tự hành chính
├── README.md                               # Hướng dẫn dự án chuẩn GitHub Repository
└── KNOWLEDGE_BASE.md                       # [TÀI LIỆU NÀY] Báo cáo tổng hợp toàn bộ kiến thức dự án
```

---
<div align="center">
  <sub>Bản quyền tài liệu thuộc về Đội thi UIT-CAR-RACING • Cuộc thi Lập trình Xe tự hành 2025</sub>
</div>
