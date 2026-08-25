<div align="center">

# 🏁 UIT-CAR-RACING
### Autonomous Navigation & Vision-Based Road Segmentation with YOLO11

[![Python Version](https://img.shields.io/badge/Python-3.8-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Ultralytics YOLO](https://img.shields.io/badge/YOLO11-Ultralytics-00FFFF?style=for-the-badge&logo=yolo&logoColor=black)](https://docs.ultralytics.com/)
[![PyTorch](https://img.shields.io/badge/PyTorch-EE4C2C?style=for-the-badge&logo=pytorch&logoColor=white)](https://pytorch.org/)
[![Unity 3D](https://img.shields.io/badge/Unity_3D-Simulator-000000?style=for-the-badge&logo=unity&logoColor=white)](https://unity.com/)
[![Docker](https://img.shields.io/badge/Docker-Containerized-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://www.docker.com/)
[![Platform](https://img.shields.io/badge/Platform-Windows_11_%7C_WSL2-0078D6?style=for-the-badge&logo=windows&logoColor=white)](https://learn.microsoft.com/en-us/windows/wsl/)

<p align="center">
  <b>Hệ thống lái xe tự hành thời gian thực kết hợp giữa mô phỏng Unity 3D, nhận diện làn đường bằng mô hình học sâu YOLO11 phân đoạn (Segmentation) và thuật toán điều khiển lái thích ứng.</b><br>
  <i>Dự án phục vụ cuộc thi "UIT CAR RACING 2025 - BẢNG CHUYÊN NGHIỆP" (ĐH Công nghệ Thông tin - ĐHQG-HCM).</i>
</p>

</div>

---

## ⚡ 1. Cài đặt Môi trường từ Đầu (Chỉ làm 1 lần)

Mở **Terminal trong VS Code (`Ctrl + ~`)** hoặc PowerShell:

```powershell
# 1. Kéo mã nguồn dự án
git clone https://github.com/Tam-sketch/UIT-car-racing.git
cd UIT-car-racing

# 2. Kéo Docker Image chính thức của Ban tổ chức
docker pull quocle28/it_car_2023:v1

# 3. Tạo Container 'it-car' gắn mã nguồn và kích hoạt GPU
docker run --name it-car -it -p 11000:11000 -v ${PWD}:/workspace/UIT-CAR-RACING --shm-size=8G --gpus all quocle28/it_car_2023:v1 /bin/bash
```

*(Nếu dùng bản đồ Ban đêm `V2_demo`, cài WSL2 bằng cách mở PowerShell gõ `wsl --install` và cài thư viện đồ họa: `sudo apt update && sudo apt install -y libglu1-mesa libgles2-mesa mesa-utils libasound2`)*.

---

## 🚀 2. Hướng dẫn Khởi chạy Hàng ngày (Ngay trong VS Code)

> 💡 **Mẹo:** Bạn chỉ cần mở VS Code, toàn bộ quá trình điều khiển xe, xem camera và chạy Docker đều thực hiện trong **Terminal VS Code (`Ctrl + ~`)**.

---

### 🚗 TRƯỜNG HỢP A: Bản đồ Windows Ban ngày (`Demo 1.2` `.exe`)

1. **Khởi động Game:** Mở thư mục `Demo 1.2` $\rightarrow$ nhấp đúp `UCR_Unity.exe` $\rightarrow$ bấm **Play**.
2. **Khởi động Controller (Trong Terminal VS Code):**
   ```powershell
   docker start -ai it-car
   ```
   *Bên trong Docker, dán cụm lệnh:*
   ```bash
   pkill -9 socat 2>/dev/null; fuser -k 11000/tcp 2>/dev/null; sleep 1
   socat TCP-LISTEN:11000,reuseaddr,fork TCP:host.docker.internal:11000 &
   cd /workspace/UIT-CAR-RACING
   python maycay.py
   ```
3. **Bắt đầu Lái:** Chuyển sang cửa sổ Unity $\rightarrow$ Click nút **`AV Mode`**.

---

### 🌙 TRƯỜNG HỢP B: Bản đồ Linux Ban đêm (`V2_demo` `.x86_64`)

1. **Cửa sổ PowerShell ngoài (Bật game Unity WSL2):**
   ```bash
   wsl chmod +x /mnt/d/UIT-car-racing/V2_demo/UCRlinux.x86_64
   wsl SDL_AUDIODRIVER=dummy /mnt/d/UIT-car-racing/V2_demo/UCRlinux.x86_64
   ```
2. **Terminal trong VS Code (Khởi động Controller):**
   ```powershell
   docker start -ai it-car
   ```
   *Bên trong Docker chạy:*
   ```bash
   cd /workspace/UIT-CAR-RACING
   bash run_maycay.sh
   ```
3. **Bắt đầu Lái:** Chuyển sang cửa sổ Unity $\rightarrow$ Click nút **`AV Mode`**.

> [!TIP]
> **Xem trực tiếp Camera & YOLO trong VS Code:** Mở file [`live_view.jpg`](file:///d:/UIT-CAR-RACING/live_view.jpg) ngay trên thanh Explorer của VS Code. Ảnh sẽ tự cập nhật liên tục thời gian thực mà không cần cài đặt XLaunch/GUI phức tạp.

---

## 📂 3. Cấu trúc Dự án

```text
UIT-CAR-RACING/
├── dataset/                                # Dữ liệu hình ảnh thu thập
│   └── raw/
│       ├── day/                            # Ảnh thô ban ngày
│       └── night/                          # Ảnh thô ban đêm (1061 ảnh)
├── Demo 1.2/                               # Bản đồ giả lập Windows (.exe)
├── V2_demo/                                # Bản đồ giả lập Linux (.x86_64)
├── Road_Seg_Model/                         # Trọng số & kết quả mô hình YOLO
│   └── modelYolo/weights/
│       ├── best.pt                         # Trọng số tốt nhất đang triển khai
│       └── last.pt
├── training/                               # Bộ công cụ huấn luyện
│   ├── configs/                            # Cấu hình dataset (.yaml)
│   ├── utils/
│   │   ├── convert_mask_to_yolo.py         # Chuyển đổi Mask sang Polygon YOLO
│   │   └── prepare_sign_dataset.py         # Gán nhãn biển báo (SAM + lọc tròn)
│   ├── train_road.py                       # Huấn luyện làn đường nội bộ
│   └── train_night_kaggle.ipynb            # Notebook huấn luyện Kaggle GPU T4
├── client_lib.so                           # Socket Client CPython 3.8 giao tiếp Unity
├── collect_data.py                         # Công cụ chụp ảnh dataset tự động
├── maycay.py                               # Mã nguồn điều khiển xe tự hành chính
├── run_maycay.sh                           # Script chạy nhanh tự động bắt IP WSL2
├── KNOWLEDGE_BASE.md                       # Báo cáo kỹ thuật chi tiết toàn diện
└── README.md                               # Tài liệu hướng dẫn này
```

---

## 🚂 4. Quy trình Huấn luyện Mô hình mới (Kaggle GPU)

1. **Thu thập dữ liệu (Trong Terminal VS Code Docker):**
   ```bash
   python collect_data.py --scene night [day] --drive manual --max 1000 --interval 0.3
   ```
2. **Gán nhãn mặt nạ:**
   - Dùng [Roboflow](https://roboflow.com) (Smart Polygon) gán nhãn lớp `road` $\rightarrow$ Export định dạng **YOLOv8 Segmentation**.
3. **Huấn luyện trên Kaggle (GPU T4 Miễn phí):**
   - Upload file zip dataset lên [Kaggle Datasets](https://www.kaggle.com/datasets).
   - Mở file `training/train_night_kaggle.ipynb` trên Kaggle $\rightarrow$ Chọn Accelerator **GPU T4** $\rightarrow$ Bấm **Run All**.
4. **Triển khai Model:**
   - Tải `best_night.pt` từ tab Output về máy.
   - Đổi tên và chép đè vào: `Road_Seg_Model/modelYolo/weights/best.pt`.

---

## 📦 5. Đóng gói Nộp bài Thi đấu

```powershell
# 1. Tại Terminal VS Code (PowerShell), lưu container thành Image mới:
docker commit it-car uit_car_racing_submission:v1.0

# 2. Xuất Image ra tệp nén .tar vật lý:
docker save -o uit_car_racing_submission.tar uit_car_racing_submission:v1.0

# 3. Chuẩn bị file instruction.txt ghi chú lệnh chạy:
#    "python /workspace/UIT-CAR-RACING/maycay.py"
```

---

## ⚠️ 6. Cẩm nang Khắc phục Sự cố

| Vấn đề | Nguyên nhân | Cách khắc phục |
| :--- | :--- | :--- |
| **Xe đứng yên, log không chạy** | Unity ở giữa đường chưa bắt tay Socket | Nhấn phím **`R`** trong game Unity để reset về vạch xuất phát. |
| **`ConnectionRefusedError: [Errno 111]`** | Unity chưa bật hoặc socat chưa chạy | Mở game Unity trước $\rightarrow$ chạy lại lệnh `socat ...` trong Docker. |
| **`undefined symbol: _Py_CheckRecursionLimit`** | Chạy Python 3.10+ ngoài WSL/Host | Bắt buộc chạy `python maycay.py` **trong Docker Container `it-car`** (Python 3.8). |
| **`Address already in use` 11000** | Cổng cũ còn lưu trạng thái TIME_WAIT | Chạy `fuser -k 11000/tcp` trong Docker trước khi bật socat. |
| **`Angle: +0.00`, `Error: +0.0` liên tục** | Model YOLO không nhận diện được đường | Kiểm tra chất lượng trọng số `best.pt` hoặc gán nhãn lại dataset ban đêm. |

---

## 🧹 7. Dọn dẹp & Giải phóng 15 – 25 GB Ổ cứng khi không dùng

Khi kết thúc đợt thực hành và muốn lấy lại dung lượng trống cho máy tính:

```powershell
# 1. Xóa Docker container và image giải phóng ~12 GB
docker rm -f it-car
docker system prune -a --volumes -f

# 2. Xóa máy ảo WSL2 giải phóng ~5 - 10 GB
wsl --shutdown
wsl --unregister Ubuntu
wsl --unregister docker-desktop
wsl --unregister docker-desktop-data
```
*(Toàn bộ mã nguồn, model và tài liệu đã được lưu trữ an toàn trên GitHub, bạn có thể tái tạo lại môi trường theo [Mục 1](#-1-cài-đặt-môi-trường-từ-đầu-chỉ-làm-1-lần) trong vòng 5 phút).*

---

<div align="center">
  <sub>UIT-CAR-RACING • Developed with ❤️ for UIT Autonomous Car Racing 2025</sub>
</div>
