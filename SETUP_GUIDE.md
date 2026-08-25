# 📘 HƯỚNG DẪN CÀI ĐẶT & KHỞI CHẠY LẠI TỪ ĐẦU (A-Z SETUP GUIDE)
> **Dành cho dự án:** UIT-CAR-RACING  
> **Repository:** [https://github.com/Tam-sketch/UIT-car-racing](https://github.com/Tam-sketch/UIT-car-racing)

Tài liệu này hướng dẫn bạn dựng lại toàn bộ môi trường và chạy xe tự hành từ con số 0 sau khi đã xóa sạch Docker/WSL để giải phóng ổ cứng.

---

## 📑 Mục lục
1. [Yêu cầu tiên quyết](#1-yêu-cầu-tiên-quyết)
2. [Cài đặt Môi trường (Chỉ làm 1 lần khi cài mới)](#2-cài-đặt-môi-trường-chỉ-làm-1-lần-khi-cài-mới)
3. [Quy trình Khởi chạy Hàng ngày](#3-quy-trình-khởi-chạy-hàng-ngày)
4. [Quy trình Huấn luyện Mô hình mới (Kaggle GPU)](#4-quy-trình-huấn-luyện-mô-hình-mới-kaggle-gpu)
5. [Cẩm nang Khắc phục Lỗi Thường gặp](#5-cẩm-nang-khắc-phục-lỗi-thường-gặp)

---

## 1. Yêu cầu tiên quyết

- **Hệ điều hành:** Windows 11 (hoặc Windows 10 64-bit build 19041+).
- **GPU:** NVIDIA GPU (khuyến nghị VRAM ≥ 4GB) + đã cài NVIDIA Driver mới nhất.
- **Dung lượng trống:** ~15-20 GB ổ C/D.

---

## 2. Cài đặt Môi trường (Chỉ làm 1 lần khi cài mới)

### Bước 2.1: Clone mã nguồn từ GitHub
Mở **PowerShell** trên Windows và chạy:
```powershell
cd D:\
git clone https://github.com/Tam-sketch/UIT-car-racing.git
cd UIT-car-racing
```

---

### Bước 2.2: Cài đặt Docker Desktop
1. Tải và cài đặt [Docker Desktop for Windows](https://www.docker.com/products/docker-desktop/).
2. Trong lúc cài đặt, tích chọn **"Use WSL 2 instead of Hyper-V"**.
3. Mở Docker Desktop $\rightarrow$ vào **Settings** $\rightarrow$ **General** $\rightarrow$ đảm bảo bật **"Use the WSL 2 based engine"**.

---

### Bước 2.3: Tạo Docker Container `it-car`
Mở **PowerShell (Administrator)** tại thư mục dự án và chạy:
```powershell
# 1. Kéo image chuẩn của BTC
docker pull quocle28/it_car_2023:v1

# 2. Tạo container 'it-car' mount mã nguồn và mở cổng 11000
docker run --name it-car -it -p 11000:11000 -v ${PWD}:/workspace/UIT-CAR-RACING --shm-size=8G --gpus all quocle28/it_car_2023:v1 /bin/bash
```
*(Gõ `exit` để tạm thoát container)*.

---

### Bước 2.4: Cài đặt WSL2 (Chỉ cần nếu chạy Map Ban đêm `V2_demo` Linux)
1. Mở **PowerShell (Admin)**:
   ```powershell
   wsl --install -d Ubuntu-22.04
   ```
2. Khởi động lại máy tính nếu được yêu cầu.
3. Mở terminal WSL (gõ `wsl` trong PowerShell) và cài các thư viện đồ họa:
   ```bash
   sudo apt update && sudo apt install -y \
       libglu1-mesa libgles2-mesa mesa-utils \
       libasound2 libpulse0 libxcursor1 libxrandr2 libxi6
   ```

---

## 3. Quy trình Khởi chạy Hàng ngày

### 🚗 TRƯỜNG HỢP 1: Bản đồ Windows Ban ngày (`Demo 1.2`)
1. **Bật Game:** Vào thư mục `Demo 1.2` $\rightarrow$ nhấp đúp `UCR_Unity.exe` $\rightarrow$ nhấn **Play**.
2. **Bật Controller (PowerShell):**
   ```powershell
   docker start -ai it-car
   ```
   *Bên trong terminal Docker, dán cụm lệnh:*
   ```bash
   pkill -9 socat 2>/dev/null; fuser -k 11000/tcp 2>/dev/null; sleep 1
   socat TCP-LISTEN:11000,reuseaddr,fork TCP:host.docker.internal:11000 &
   cd /workspace/UIT-CAR-RACING
   python maycay.py
   ```
3. **Bắt đầu Lái:** Chuyển sang cửa sổ Unity $\rightarrow$ Click nút **`AV Mode`**.

---

### 🌙 TRƯỜNG HỢP 2: Bản đồ Linux Ban đêm (`V2_demo`)
1. **Terminal 1 (WSL):** Mở game Unity Linux:
   ```bash
   chmod +x /mnt/d/UIT-car-racing/V2_demo/UCRlinux.x86_64
   SDL_AUDIODRIVER=dummy /mnt/d/UIT-car-racing/V2_demo/UCRlinux.x86_64
   ```
2. **Terminal 2 (PowerShell):** Chạy Controller:
   ```powershell
   docker start -ai it-car
   ```
   *Bên trong Docker:*
   ```bash
   cd /workspace/UIT-CAR-RACING
   bash run_maycay.sh
   ```
3. **Bắt đầu Lái:** Chuyển sang cửa sổ Unity $\rightarrow$ Click nút **`AV Mode`**.

---

## 4. Quy trình Huấn luyện Mô hình mới (Kaggle GPU)

Khi bạn thu thập thêm dữ liệu mới và muốn train lại `best.pt`:

1. **Thu thập ảnh:**
   ```bash
   python collect_data.py --scene night --drive manual --max 1000
   ```
2. **Gán nhãn mặt nạ:**
   - Dùng [Roboflow](https://roboflow.com) (Smart Polygon) $\rightarrow$ Export **YOLOv8 Segmentation**.
3. **Huấn luyện trên Kaggle (Miễn phí GPU T4):**
   - Upload file zip dataset lên [Kaggle Datasets](https://www.kaggle.com/datasets).
   - Mở file `training/train_night_kaggle.ipynb` trên Kaggle Notebook $\rightarrow$ Bật GPU T4 $\rightarrow$ Nhấn **Run All**.
4. **Cập nhật Model về máy:**
   - Tải `best_night.pt` từ mục Output về máy.
   - Đổi tên và chép đè vào: `Road_Seg_Model/modelYolo/weights/best.pt`.

---

## 5. Cẩm nang Khắc phục Lỗi Thường gặp

| Triệu chứng | Nguyên nhân | Cách xử lý |
|---|---|---|
| **Xe đứng yên, log không chạy** | Unity ở giữa đường chưa sync Socket | Nhấn phím **`R`** trong Unity để reset xe về vạch xuất phát. |
| **`ConnectionRefusedError: [Errno 111]`** | Game Unity chưa bật hoặc socat chết | Bật game Unity trước, sau đó chạy lại lệnh socat trong Docker. |
| **`undefined symbol: _Py_CheckRecursionLimit`** | Chạy Python ngoài Windows/WSL | Phải chạy `python maycay.py` **bên trong Docker `it-car`** (nơi có Python 3.8 chuẩn). |
| **`Address already in use` 11000** | Cổng cũ chưa giải phóng | Chạy `fuser -k 11000/tcp` trong Docker trước khi bật socat. |
| **Muốn xem ảnh camera khi đang lái** | Xem trực tiếp không cần X11 | Mở file `live_view.jpg` trong VS Code, ảnh sẽ cập nhật liên tục theo thời gian thực. |
