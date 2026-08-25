# 📚 KNOWLEDGE BASE - UIT-CAR-RACING
> **Comprehensive context document covering competition rules, system architecture, autonomous control algorithms, YOLO11 training pipeline, and troubleshooting history for AI Agents.**

---

## 📑 TABLE OF CONTENTS
1. Competition Context and Rules
2. System Architecture and Socket Protocol
3. Autonomous Steering Algorithms
4. YOLO11 Data and Training Pipeline
5. Technical Troubleshooting History
6. Complete Project Directory Structure

---

## 1. COMPETITION CONTEXT AND RULES

### 1.1. General Information
* **Competition Name**: UIT CAR RACING 2025 SEASON XIV - PROFESSIONAL LEAGUE.
* **Organizer**: Faculty of Computer Engineering, University of Information Technology, VNU-HCM.
* **Format**: Preliminary rounds take place on the Unity Simulator virtual environment. The Final round is an offline head-to-head race using physical miniature cars on a real-world track.

### 1.2. Scoring Mechanism
Each racing map contains 10 Checkpoints:
* **Using custom trained YOLO11n-seg AI**: Teams score 10 points per checkpoint, maxing out at 100 points.
* **Using default Segmentation images provided by Organizers**: Teams only score 5 points per checkpoint, maxing out at 50 points.

> 💡 **Strategy**: Training a custom YOLO model for road and traffic sign segmentation is an absolute prerequisite to double the maximum score and gain a massive advantage.

### 1.3. Expected Track Challenges
* Two-way roads with two lanes, one-way roads with one or two lanes.
* Winding curves and sharp steep turns.
* Dynamic lighting conditions and tree shadows causing visual noise.
* Nighttime maps and fog conditions with pitch-black road surfaces.
* Intersections and crossroads governed by traffic sign commands.

---

## 2. SYSTEM ARCHITECTURE AND SOCKET PROTOCOL

The system operates on a Client-Server architecture. The Unity Game acts as the Server listening on port 11000. The Docker environment acts as the Client.

### 2.1. Cyclic Data Flow
* Unity Game outputs RGB frames.
* The socat utility forwards TCP packets.
* The C-based client_lib.so library receives the data.
* The maycay.py script predicts the road mask using YOLO11n-seg.
* The AVControl command transmits speed and steering angle back to the Unity Game.

### 2.2. Mandatory Handshake Protocol
TO MAKE THE CAR MOVE, the control loop MUST call three functions in this exact sequence:
1. `GetStatus`: Initializes the handshake signal with Unity.
2. `GetRaw`: Fetches the RGB frame.
3. `AVControl`: Sends the speed and steering angle commands.

> [!WARNING]
> If the `GetStatus` function is skipped, the handshake will fail. The `AVControl` function will execute without throwing errors, but the Unity game will completely ignore the command and the car will remain permanently frozen.

---

## 3. AUTONOMOUS STEERING ALGORITHMS

The control logic in `maycay.py` utilizes a multi-layered adaptive algorithm rather than simple pathfinding.

### 3.1. Road Center Extraction Method
1. Scan individual pixel rows from the bottom of the image to the top.
2. Identify white pixel coordinates representing the road surface predicted by YOLO.
3. Calculate the midpoint of each row to form a sequence of center points.
4. Compute the weighted center of the road, assigning higher weights to points closer to the bottom of the image.

### 3.2. Near and Far Point Blending Technique
* **Near Error - E_near**: The deviation of the road center in the lower half of the image relative to the car axis. Highly reliable during sharp turns.
* **Far Error - E_far**: The deviation of the road center in the top third of the image. Helps the car anticipate upcoming curves.
* **Blended Error Formula**: E_blended = w_near * E_near + w_far * E_far
* The weight w_far increases linearly in proportion to the car velocity.

### 3.3. Lane Width Estimator
* The system continuously measures the horizontal width of the road surface.
* Upon detecting a sudden width increase, for example exceeding 20 percent, the system automatically zeroes out the Far Point weight. It relies solely on the Near Point to prevent the car from hallucinating a turn into the center of an intersection.

### 3.4. Curvature-Based Speed Control
* The system automatically brakes in direct proportion to the road curvature ahead.
* **Velocity Formula**: Speed = max[MinSpeed, MaxSpeed * [1 - 0.7 * CurveRatio]]

---

## 4. YOLO11 DATA AND TRAINING PIPELINE

### 4.1. Night Map V2_demo Detection Failure
* **Root Cause Analysis**: While navigating the night map, the car continuously returned a Steering Angle of +0.00. The reason was that the automated grayscale adaptive thresholding labeling script completely failed. In the night map, the road surface is significantly darker than the grass and sky. The flood-fill algorithm failed because the seed pixel was located in a pitch-black region, generating 100 percent solid white masks across all images.
* **Mandatory Solution**: Never use automated grayscale thresholding scripts for night images. Night dataset images must be uploaded to Roboflow, manually annotated using the Smart Polygon tool, and exported in the YOLOv8 Segmentation format.

### 4.2. Traffic Sign Preprocessing
* Utilizes Meta Segment Anything Model combined with a circularity filtering algorithm.
* **Circularity Formula**: Circularity = [4 * Pi * Area] / [Perimeter * Perimeter]
* A Circularity threshold greater than or equal to 0.8 is required to classify an object as a traffic sign.
* **Empty Labels Technique**: Automatically generate zero-byte text files for landscape images containing no traffic signs to completely eliminate false positive detections during inference.

### 4.3. Critical Training Configurations
Training on the Kaggle GPU T4 requires specific optimized parameters:
* Disable horizontal image flipping using the flag `fliplr=0.0`. This is a matter of life and death to ensure the car does not confuse left-turn and right-turn signs.
* Enable brightness augmentation `hsv_v=0.4` to help the model adapt exceptionally well to low-light night environments.
* Prevent Docker RAM overflow errors by setting `workers=0` and `cache='disk'`.

---

## 5. TECHNICAL TROUBLESHOOTING HISTORY

| Error Symptom | Root Cause | Solution |
| :--- | :--- | :--- |
| **ConnectionRefusedError Errno 111** | Unity Socket server has not started or crashed. | Start the 3D scene in the game first. Re-run the socat command. |
| **Address already in use port 11000** | Windows OS retains the old connection in a TIME_WAIT state. | Run the command `fuser -k 11000/tcp` to kill background processes, and always append the `reuseaddr` flag to the socat command. |
| **undefined symbol _Py_CheckRecursionLimit** | The client_lib.so library uses deprecated CPython functions. | Never use higher Python versions on the Host. Run the code strictly inside the Docker Python 3.8 environment. |
| **Qt plugin offscreen not found error** | The Docker container lacks headless graphics plugins. | Remove the QT_QPA_PLATFORM environment variable from the script and delete all cv2.imshow function calls. View the camera feed via the live_view.jpg file. |
| **Linux Game crashes abruptly after 1 second** | WSL2 is missing OpenGL graphics rendering libraries. | Install the libglu1-mesa package and launch the game with the SDL_AUDIODRIVER=dummy environment prefix. |

---

## 6. COMPLETE PROJECT DIRECTORY STRUCTURE

```text
UIT-CAR-RACING/
├── dataset/                                # Image data collection directory
│   └── raw/
│       ├── day/                            # Daytime raw images
│       └── night/                          # Nighttime raw images
├── Demo 1.2/                               # Windows simulation map
├── V2_demo/                                # Linux simulation map
├── Road_Seg_Model/                         # Road models and weights
│   ├── modelYolo/                          # Trained YOLO checkpoints
│   │   ├── weights/
│   │   │   ├── best.pt                     # Most optimal weights
│   │   │   └── last.pt                     # Final epoch weights
│   │   └── results.png                     # mAP evaluation graph
├── training/                               # Independent YOLO training toolkit
│   ├── configs/                            # YAML configuration files
│   │   ├── road_seg.yaml                   # Road dataset configuration
│   │   └── traffic_sign_seg.yaml           # Traffic sign dataset configuration
│   ├── utils/                              # Preprocessing and labeling tools
│   │   ├── convert_mask_to_yolo.py         # Extract contours to Polygons
│   │   └── prepare_sign_dataset.py         # Assign sign labels using SAM
│   ├── train_road.py                       # Road training script
│   └── train_night_kaggle.ipynb            # Kaggle training notebook
├── client_lib.so                           # Socket communication library for Unity
├── collect_data.py                         # Automated image collection tool
├── maycay.py                               # Core autonomous vehicle control code
└── KNOWLEDGE_BASE.md                       # Comprehensive knowledge base document
```

---
<div align="center">
  <sub>Document copyright belongs to the UIT-CAR-RACING Team • Autonomous Car Racing Competition 2025</sub>
</div>
