# UIT-CAR-RACING AUTONOMOUS DRIVING SYSTEM KNOWLEDGE BASE

> [!IMPORTANT]
> Comprehensive Master Knowledge Base for UIT Car Racing 2025 -- Professional League.
> This document provides complete contest rules, architecture, algorithms, data pipelines, operating procedures, and technical diagnostics for all AI agents and developers.

---

## TABLE OF CONTENTS
* 1. Contest Background and Official Competition Rules
* 2. End-to-End System Architecture and Dataflow
* 3. Autonomous Steering and Speed Adaptive Control Algorithms
* 4. Dataset Engineering and YOLO11 Model Training Toolkit
* 5. Execution and Operating Procedures on Windows 11 and WSL2
* 6. Complete Technical Diagnostic and Troubleshooting Matrix
* 7. Directory Tree and Workspace Layout

---

## 1. CONTEST BACKGROUND AND OFFICIAL COMPETITION RULES

### 1.1 Tournament Overview
* Competition Name: UIT CAR RACING 2025 SEASON XIV -- PROFESSIONAL LEAGUE
* Organizing Institution: Faculty of Computer Engineering -- University of Information Technology -- Vietnam National University HCMC
* Phase 1 -- Online Simulation Rounds: Virtual racing on Unity 3D simulator instances. Teams submit fully containerized Docker images.
* Phase 2 -- Physical Offline Finals: Live physical races on custom scaled autonomous vehicles across physical tracks built at University of Information Technology campus.

### 1.2 Scoring Matrix and Point Distribution
Each race track contains 10 Checkpoints:
* Custom Autonomous AI Model Inference -- YOLO11n-seg: Awards 10 Points per checkpoint -- Maximum 100 Points per run.
* Default Simulator Semantic Segmentation Mask: Awards 5 Points per checkpoint -- Maximum 50 Points per run.
* Tie-breaking Criterion: In case of equal points, total lap completion time determines final standings.

> [!TIP]
> Training and deploying a dedicated YOLO segmentation model is the single most critical factor to double total score and secure podium qualification.

### 1.3 Track Challenges and Obstacles
* Dual-lane two-way roadways with center dash lines and outer solid boundary lines.
* Single-lane one-way segments and complex s-curves.
* Tree shadows, dynamic sunlight shifts, and visual lighting variations that disrupt naive color thresholding.
* Low-light nighttime tracks with localized street lamps and deep dark zones such as the V2_demo map.
* Intersections with traffic signs, traffic light color states, and designated parking maneuvers.

### 1.4 Official Submission Requirements
Submissions consist of two artifacts:
* Compressed Docker Image Archive: Named `uit_car_racing_submission.tar` containing all dependencies, code, and model weights.
* Startup Instruction Note: A plain text file named `instruction.txt` specifying the entrypoint command: `python /workspace/UIT-CAR-RACING/maycay.py`.

---

## 2. END-TO-END SYSTEM ARCHITECTURE AND DATAFLOW

### 2.1 Communication Topology
* Unity 3D Simulator: Runs on host environment, renders physical simulation and vehicle dynamics, and transmits raw camera streams over TCP Socket port 11000 or port 11001.
* Socat Network Bridge: Bridges TCP packets between container internal loopback and host network endpoints.
* CEEC Docker Container: Image tag `quocle28/it_car_2023:v1` built upon Ubuntu 18.04 with CPython 3.8 runtime.
* Python Central Controller: File `maycay.py` receives RGB frames, runs neural inference, computes adaptive steering, and transmits motion commands back to Unity at approximately 30 frames per second.

```
[Unity 3D Simulator Host]
       │
       ▼ Raw RGB Frame & Telemetry over TCP Port 11000
[Socat Port Forwarding Bridge]
       │
       ▼ Local Loopback Forwarding
[client_lib C-Extension CPython 3.8]
       │
       ▼ GetRaw Function
[maycay.py: YOLO11n-seg Predictor]
       │
       ▼ Binary Segmentation Mask
[Adaptive Multi-Layer Steering & Speed Engine]
       │
       ▼ AVControl: Speed & Steering Angle
[client_lib -> Socat -> Unity Simulator]
```

### 2.2 Client Library Interface Specifications
The binary module `client_lib.so` provides four primary functions:
* `GetRaw`: Returns the current camera frame as an OpenCV BGR numpy array.
* `GetStatus`: Returns telemetry strings and vehicle speed feedback.
* `AVControl`: Sends float target speed and float steering angle clamped between -25 degrees and +25 degrees.
* `CloseSocket`: Gracefully terminates network socket connections and releases system descriptors.

---

## 3. AUTONOMOUS STEERING AND SPEED ADAPTIVE CONTROL ALGORITHMS

The core controller `maycay.py` utilizes a multi-layered adaptive control engine designed for high-speed tracking and sharp turn stabilization.

### 3.1 Centerline Feature Extraction
* Bottom-up Row Scanner: Scans image rows from bottom to top, identifying white mask pixels predicted by YOLO.
* Mean Center Points: Computes midpoint of each valid road row to establish a smooth green line centerline array.
* Distance-weighted Center: Assigns higher weight coefficients to rows closest to the vehicle bumper.

### 3.2 Near and Far Point Blending
* Near Point Error: Computed from lower half of the image. Represents immediate lateral displacement from vehicle center.
* Far Point Error: Computed from upper third of the image. Represents preview horizon curve lookahead.
* Blending Equation:
  `Blended_Error = w_near * Near_Error + w_far * Far_Error`
  Where `w_far` increases dynamically with vehicle velocity to allow earlier steering initiation on straights.

### 3.3 Dynamic Lane Width Estimator
* Class `LaneWidthEstimator`: Continuously samples road width across multiple vertical scanlines.
* Intersection Detection: When measured width expands by over 20 percent compared to base width -- indicating junctions or split lanes -- the estimator forces `w_far = 0`. This isolates steering to immediate near points and prevents the car from swerving toward the center of intersections.

### 3.4 Curvature-Adaptive Velocity Governor
* Curvature Ratio: Computed from horizontal deviation between topmost and bottommost centerline points normalized by half image width.
* Speed Equation:
  `Speed = max[Min_Speed, Max_Speed * [1.0 - 0.7 * Curve_Ratio]]`
  The vehicle automatically slows down during sharp bends and accelerates to maximum speed on open straights.

### 3.5 Progressive Multi-Stage Steering Mapping
* Small errors below 15 pixels: Proportional steering with speed and aggressive scaling factors.
* Moderate errors between 15 and 25 pixels: Scaled steering between 10 and 20 degrees.
* High errors between 25 and 35 pixels: Scaled steering between 18 and 30 degrees.
* Severe errors above 35 pixels: Full lock steering clamped at 25 degrees.
* Angle Smoothing: Two-step rolling history queue with max delta limit of 15 degrees per frame prevents jerky steering.

---

## 4. DATASET ENGINEERING AND YOLO11 MODEL TRAINING TOOLKIT

### 4.1 Automated Data Collection Tool -- `collect_data.py`
* Supports Manual Driving Mode with argument `--drive manual` for human keyboard driving in Unity.
* Supports Autonomous Driving Mode with argument `--drive av` for autonomous data harvesting with an existing model.
* Configurable capture interval with default 0.3 seconds per image.
* Stores images inside `dataset/raw/day/` and `dataset/raw/night/`.
* Includes built-in socket error handling and automatic retry loops to prevent crashes during simulator pauses.

### 4.2 Road Mask Polygon Conversion -- `convert_mask_to_yolo.py`
* Converts binary or color segmentation masks into YOLO polygon annotation text files.
* Color filtering with adjustable tolerance to extract road pixels.
* Morphological closing to seal mask gaps.
* Douglas-Peucker polygon approximation via `cv2.approxPolyDP` to optimize vertex count.
* Normalizes coordinates to range 0.0 to 1.0 with a minimum of 3 vertices per polygon.
* Splits dataset into training and validation sets with configurable ratio.

### 4.3 Traffic Sign Dataset Preparation -- `prepare_sign_dataset.py`
* Employs Meta Segment Anything Model or OpenCV fallback filter to generate precise circular masks.
* Circularity Detection Formula:
  `Circularity = 4.0 * PI * Area / [Perimeter * Perimeter] >= 0.8`
* Maps index ranges to 5 sign classes:
  * Class 0: `di_thang` -- Straight Ahead
  * Class 1: `re_trai` -- Turn Left
  * Class 2: `re_phai` -- Turn Right
  * Class 3: `cam_re_trai` -- No Left Turn
  * Class 4: `cam_re_phai` -- No Right Turn
* Background Suppression: Creates empty label text files for landscape frames without signs to eliminate false positives.

### 4.4 Model Training Configurations

#### Road Segmentation Training -- `train_road.py`
* Model: `yolo11n-seg.pt`
* Epochs: 50
* Input Size: 640 by 640 pixels
* Batch Size: 2
* Data Loader Workers: 0 -- Essential to eliminate Docker multiprocessing crashes
* Cache: `disk` -- Prevents shared memory overflow
* Optimizer: `AdamW` with initial learning rate 0.001

#### Traffic Sign Training -- `train_yolo_signs.py`
* Model: `yolo11n-seg.pt`
* Epochs: 100
* Input Size: 320 by 320 pixels for fast sign detection
* Batch Size: 4
* Horizontal Flip `fliplr`: 0.0 -- CRITICAL -- Must be disabled to preserve directional meaning of turn signs
* Vertical Flip `flipud`: 0.0
* Mosaic Augmentation: 0.3
* Copy-Paste Augmentation: 0.1

---

## 5. EXECUTION AND OPERATING PROCEDURES ON WINDOWS 11 AND WSL2

### 5.1 Scenario A: Running Windows Simulator -- `Demo 1.2/UCR_Unity.exe`

Step 1: Launch Unity Simulator
* Double-click `Demo 1.2/UCR_Unity.exe` on Windows.
* Select resolution, click Play, and check port number displayed in top right corner -- typically 11000 or 11001.

Step 2: Launch Docker and Controller
* Open Windows PowerShell:
  `docker start -ai it-car`
* Inside Docker terminal, execute:
  `pkill -9 socat 2>/dev/null; fuser -k 11000/tcp 2>/dev/null; sleep 1`
  `socat TCP-LISTEN:11000,reuseaddr,fork TCP:host.docker.internal:11000 &`
  `cd /workspace/UIT-CAR-RACING`
  `python maycay.py`

Step 3: Engage Autonomous Mode
* Switch to Unity window and click `AV Mode`.

---

### 5.2 Scenario B: Running Linux Night Simulator -- `V2_demo/UCRlinux.x86_64`

Step 1: Launch Unity Simulator in WSL2
* Open WSL2 terminal:
  `chmod +x /mnt/d/UIT-CAR-RACING/V2_demo/UCRlinux.x86_64`
  `SDL_AUDIODRIVER=dummy /mnt/d/UIT-CAR-RACING/V2_demo/UCRlinux.x86_64`

Step 2: Launch Docker Controller in Second Terminal
* Open Windows PowerShell:
  `docker start -ai it-car`
* Inside Docker terminal, execute:
  `pkill -9 socat 2>/dev/null; fuser -k 11000/tcp 2>/dev/null; sleep 1`
  `socat TCP-LISTEN:11000,reuseaddr,fork TCP:host.docker.internal:11000 &`
  `cd /workspace/UIT-CAR-RACING`

Step 3: Execute Data Collection or Autonomous Drive
* To collect night dataset:
  `python collect_data.py --scene night --drive manual --max 1000 --interval 0.3`
* To run autonomous driving:
  `python maycay.py`

---

## 6. COMPLETE TECHNICAL DIAGNOSTIC AND TROUBLESHOOTING MATRIX

| Error Signature | Root Cause | Definitive Technical Resolution |
| :--- | :--- | :--- |
| `ConnectionRefusedError: [Errno 111]` | Unity scene has not finished loading or socat forwarder is inactive. | Ensure Unity 3D scene is active, then restart socat bridge pointing to `host.docker.internal:11000`. |
| `Address already in use on port 11000` | Port remains trapped in kernel TIME_WAIT state after termination. | Kill lingering processes with `fuser -k 11000/tcp` and attach `reuseaddr` flag to socat commands. |
| `undefined symbol: _Py_CheckRecursionLimit` | Binary `client_lib.so` executed on Python 3.10 or higher where CPython recursion symbol was removed. | Run all controller and collection scripts inside Docker container `it-car` which provides CPython 3.8. |
| `VS Code Server Missing GLIBC >= 2.28` | VS Code version 1.86 and above discontinued Dev Container attachment on Ubuntu 18.04 images. | Edit code on host Windows VS Code via mounted volume `-v` and execute commands through standard terminal. |
| `qt.qpa.xcb: could not connect to display` | OpenCV attempted to spawn GUI windows in headless Docker environment. | Auto-configured `QT_QPA_PLATFORM = offscreen` in code; GUI calls isolated via `show_image_safe`. |
| `Unity Linux .x86_64 terminates after 1s` | Missing Mesa OpenGL graphic libraries or pulse audio backend failures. | Install `libglu1-mesa`, `libgles2-mesa`, `libasound2` in WSL and prepend `SDL_AUDIODRIVER=dummy`. |

---

## 7. DIRECTORY TREE AND WORKSPACE LAYOUT

```text
UIT-CAR-RACING/
├── dataset/                                # Dataset storage root
│   └── raw/
│       ├── day/                            # Raw daytime frames
│       └── night/                          # Raw nighttime frames from V2_demo
├── Demo 1.2/                               # Windows Unity simulator build
│   └── UCR_Unity.exe                       # Windows binary executable
├── V2_demo/                                # Linux Unity simulator build
│   ├── UCRlinux.x86_64                     # Linux x86_64 binary executable
│   ├── UnityPlayer.so                      # Unity engine graphic library
│   └── UCRlinux_Data/                      # Scene and asset bundle data
├── Road_Seg_Model/                         # Pretrained model weights and metrics
│   ├── modelYolo/                          # YOLO training outputs
│   │   ├── weights/
│   │   │   ├── best.pt                     # Best model checkpoint
│   │   │   └── last.pt                     # Last epoch checkpoint
│   │   └── results.png                     # Validation metric curves
│   └── yolo_model                          # Auxiliary checkpoints
├── training/                               # Standalone YOLO training toolkit
│   ├── configs/                            # YAML dataset manifests
│   │   ├── road_seg.yaml                   # Road segmentation config
│   │   └── traffic_sign_seg.yaml           # Traffic sign config
│   ├── utils/                              # Data preparation scripts
│   │   ├── __init__.py                     # Package declaration
│   │   ├── convert_mask_to_yolo.py         # Mask to YOLO polygon converter
│   │   └── prepare_sign_dataset.py         # SAM and circular sign builder
│   ├── train_road.py                       # Road segmentation training script
│   └── train_yolo_signs.py                 # Traffic sign training script
├── client_lib.so                           # Socket client library for Python 3.8
├── collect_data.py                         # Camera frame harvester
├── maycay.py                               # Autonomous driving real-time brain
├── README.md                               # GitHub repository documentation
└── KNOWLEDGE_BASE.md                       # Master knowledge base document
```

---
UIT-CAR-RACING Master Documentation -- Professional League Autonomous System
