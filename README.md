<div align="center">

# 🏁 UIT-CAR-RACING
### Autonomous Navigation and Vision-Based Road Segmentation with YOLO11

<a href="https://www.python.org/"><img src="https://img.shields.io/badge/Python-3.8-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python Version"></a>
<a href="https://docs.ultralytics.com/"><img src="https://img.shields.io/badge/YOLO11-Ultralytics-00FFFF?style=for-the-badge&logo=yolo&logoColor=black" alt="Ultralytics YOLO"></a>
<a href="https://pytorch.org/"><img src="https://img.shields.io/badge/PyTorch-EE4C2C?style=for-the-badge&logo=pytorch&logoColor=white" alt="PyTorch"></a>
<a href="https://unity.com/"><img src="https://img.shields.io/badge/Unity_3D-Simulator-000000?style=for-the-badge&logo=unity&logoColor=white" alt="Unity 3D"></a>
<a href="https://www.docker.com/"><img src="https://img.shields.io/badge/Docker-Containerized-2496ED?style=for-the-badge&logo=docker&logoColor=white" alt="Docker"></a>
<a href="https://learn.microsoft.com/en-us/windows/wsl/"><img src="https://img.shields.io/badge/Platform-Windows_11_%7C_WSL2-0078D6?style=for-the-badge&logo=windows&logoColor=white" alt="Platform"></a>

<p align="center">
  <b>Real-time autonomous driving system integrating Unity 3D simulator, deep learning road segmentation with YOLO11, and adaptive steering control.</b><br>
  <i>Developed for UIT CAR RACING 2025 Season XIV - Professional League by Faculty of Computer Engineering, University of Information Technology, VNU-HCM.</i>
</p>

</div>

---

## ⚡ 1. One-Time Environment Setup

Open **VS Code Terminal** or **PowerShell as Administrator**:

```powershell
# 1. Clone project repository
git clone https://github.com/Tam-sketch/UIT-car-racing.git
cd UIT-car-racing

# 2. Pull official competition Docker image
docker pull quocle28/it_car_2023:v1

# 3. Create container it-car with GPU and mounted workspace
docker run --name it-car -it -p 11000:11000 -v ${PWD}:/workspace/UIT-CAR-RACING --shm-size=8G --gpus all quocle28/it_car_2023:v1 /bin/bash
```

> [!NOTE]
> If running the Linux Night Map V2_demo, install WSL2 via `wsl --install` then install graphics libraries inside WSL:
> `sudo apt update && sudo apt install -y libglu1-mesa libgles2-mesa mesa-utils libasound2`

---

## 🚀 2. Daily Workflow in VS Code

> [!TIP]
> All controller execution, Docker management, and live camera monitoring happen directly inside **VS Code Terminal**.

---

### 🚗 Case A: Windows Daytime Map - Demo 1.2

1. **Launch Game Simulator:**
   Open directory `Demo 1.2` $\rightarrow$ double-click `UCR_Unity.exe` $\rightarrow$ click **Play**.

2. **Start Controller inside VS Code Terminal:**
   ```powershell
   docker start -ai it-car
   ```
   Paste the following commands into the Docker session:
   ```bash
   pkill -9 socat 2>/dev/null; fuser -k 11000/tcp 2>/dev/null; sleep 1
   socat TCP-LISTEN:11000,reuseaddr,fork TCP:host.docker.internal:11000 &
   cd /workspace/UIT-CAR-RACING
   python maycay.py
   ```

3. **Engage Autonomous Mode:**
   Switch to Unity window $\rightarrow$ click button **AV Mode**.

---

### 🌙 Case B: Linux Night Map - V2_demo

1. **External PowerShell Window - Start Unity in WSL2:**
   ```bash
   wsl chmod +x /mnt/d/UIT-car-racing/V2_demo/UCRlinux.x86_64
   wsl SDL_AUDIODRIVER=dummy /mnt/d/UIT-car-racing/V2_demo/UCRlinux.x86_64
   ```

2. **VS Code Terminal - Start Controller:**
   ```powershell
   docker start -ai it-car
   ```
   Run the launcher script inside Docker:
   ```bash
   cd /workspace/UIT-CAR-RACING
   bash run_maycay.sh
   ```

3. **Engage Autonomous Mode:**
   Switch to Unity window $\rightarrow$ click button **AV Mode**.

> [!TIP]
> **Real-Time Visual Monitoring:** Open `live_view.jpg` in VS Code Explorer. The composite view updates automatically without requiring X11 or XLaunch servers.

---

## 📂 3. Project Structure

```text
UIT-CAR-RACING/
├── dataset/                                # Raw training datasets
│   └── raw/
│       ├── day/                            # Daytime raw frames
│       └── night/                          # Night raw frames
├── Demo 1.2/                               # Windows Unity Simulator
├── V2_demo/                                # Linux Unity Simulator
├── Road_Seg_Model/                         # Model weights and training results
│   └── modelYolo/weights/
│       ├── best.pt                         # Active production weight
│       └── last.pt                         # Last epoch checkpoint
├── training/                               # Training pipeline and utilities
│   ├── configs/                            # Dataset YAML definitions
│   ├── utils/
│   │   ├── convert_mask_to_yolo.py         # Mask to YOLO polygon converter
│   │   └── prepare_sign_dataset.py         # Traffic sign auto-labeler
│   ├── train_road.py                       # Local road training script
│   └── train_night_kaggle.ipynb            # Kaggle GPU T4 training notebook
├── client_lib.so                           # Socket client interface for Python 3.8
├── collect_data.py                         # Automated frame capture utility
├── maycay.py                               # Core autonomous driving controller
├── run_maycay.sh                           # Fast launcher for WSL2 network bridge
├── KNOWLEDGE_BASE.md                       # Comprehensive engineering report
└── README.md                               # Project guide
```

---

## 🚂 4. Retraining Pipeline on Kaggle GPU

1. **Collect Images in VS Code Docker Terminal:**
   ```bash
   python collect_data.py --scene night --drive manual --max 1000 --interval 0.3
   ```

2. **Annotate Ground Truth Masks:**
   Import frames into Roboflow Smart Polygon with class `road` $\rightarrow$ Export as **YOLOv8 Segmentation**.

3. **Train on Kaggle with Free GPU T4:**
   Upload zipped dataset to Kaggle Datasets $\rightarrow$ Open `training/train_night_kaggle.ipynb` $\rightarrow$ Select **GPU T4** $\rightarrow$ Click **Run All**.

4. **Deploy Weights:**
   Download `best_night.pt` from Kaggle Output $\rightarrow$ Rename and replace `Road_Seg_Model/modelYolo/weights/best.pt`.

---

## 📦 5. Competition Submission Packaging

```powershell
# 1. Commit container state to a new submission image:
docker commit it-car uit_car_racing_submission:v1.0

# 2. Export image to compressed tarball:
docker save -o uit_car_racing_submission.tar uit_car_racing_submission:v1.0

# 3. Create instruction.txt specifying startup command:
#    python /workspace/UIT-CAR-RACING/maycay.py
```

---

## ⚠️ 6. Troubleshooting Matrix

| Issue | Root Cause | Solution |
| :--- | :--- | :--- |
| **Car idle, no log flow** | Unity socket session out of sync | Press **R** in Unity to reset car to starting line. |
| **ConnectionRefusedError 111** | Unity not running or socat bridge dead | Open Unity game first, then re-execute socat in Docker. |
| **undefined symbol _Py_CheckRecursionLimit** | Running outside Python 3.8 environment | Run `python maycay.py` strictly inside **it-car Docker container**. |
| **Address already in use 11000** | Port occupied by dangling socket | Run `fuser -k 11000/tcp` inside Docker before launching socat. |
| **Angle +0.00 and Error +0.0 constantly** | Model fails to detect road surface | Retrain model with high quality annotations from Roboflow. |

---

## 🧹 7. Reclaiming Disk Space

When pausing development and freeing 15 to 25 GB of disk space:

```powershell
# 1. Purge Docker container and images to reclaim 12 GB
docker rm -f it-car
docker system prune -a --volumes -f

# 2. Remove WSL2 virtual disk to reclaim 5 to 10 GB
wsl --shutdown
wsl --unregister Ubuntu
wsl --unregister docker-desktop
wsl --unregister docker-desktop-data
```

> [!IMPORTANT]
> All code, model weights, and guides are securely preserved in GitHub. The complete workspace can be restored at any time within 5 minutes.

---

<div align="center">
  <sub>UIT-CAR-RACING • Developed with passion for UIT Autonomous Car Racing 2025</sub>
</div>
