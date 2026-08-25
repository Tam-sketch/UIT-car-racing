#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
auto_label_night.py
-------------------
Tự động gán nhãn YOLO Segmentation cho ảnh ban đêm từ V2_demo.

Chiến lược (không cần SAM / GPU):
  1. CLAHE tăng cường độ tương phản trên ảnh grayscale.
  2. Adaptive Threshold loại bỏ nền trời/tường/vật thể tối hơn đường.
  3. Flood-fill từ điểm seed bottom-center (xe luôn đứng trên đường)
     để trích vùng đường liên thông thực sự.
  4. Morphological cleaning (close, open) để lấp lỗ hổng nhỏ.
  5. Trích xuất contour lớn nhất -> normalize -> ghi file YOLO .txt

Kết quả:
  dataset/masks/night/     <- ảnh mặt nạ PNG (để đối chứng / debug)
  dataset/night_yolo/      <- dataset YOLO chuẩn (images + labels, đã chia train/val)
  dataset/night_yolo/night_road_seg.yaml  <- config cho Kaggle Notebook
"""

import os
import sys
import cv2
import numpy as np
import shutil
import argparse
import random

if sys.platform.startswith('win'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass
try:
    from tqdm import tqdm
except ImportError:
    def tqdm(iterable, desc="", ncols=70):
        total = len(iterable) if hasattr(iterable, '__len__') else None
        for i, item in enumerate(iterable):
            if total and i % 50 == 0:
                print(f"[{desc}] Tiến độ: {i}/{total} ({(i/total)*100:.1f}%)")
            yield item

DEFAULT_RAW_DIR = os.path.join(os.path.dirname(__file__), '..', '..', 'dataset', 'raw', 'night')
DEFAULT_MASK_DIR = os.path.join(os.path.dirname(__file__), '..', '..', 'dataset', 'masks', 'night')
DEFAULT_OUTPUT_DIR = os.path.join(os.path.dirname(__file__), '..', '..', 'dataset', 'night_yolo')

SEED_COLUMNS = [0.30, 0.40, 0.50, 0.60, 0.70]
MIN_ROAD_AREA = 300
POLY_EPSILON_RATIO = 0.003


def enhance_night_image(gray: np.ndarray) -> np.ndarray:
    clahe = cv2.createCLAHE(clipLimit=4.0, tileGridSize=(4, 4))
    return clahe.apply(gray)


def extract_road_mask(img: np.ndarray) -> np.ndarray:
    h, w = img.shape[:2]
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    enhanced = enhance_night_image(gray)

    ada = cv2.adaptiveThreshold(
        enhanced, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        blockSize=21, C=-5
    )

    ada = cv2.GaussianBlur(ada, (3, 3), 0)
    _, ada = cv2.threshold(ada, 127, 255, cv2.THRESH_BINARY)

    flood_mask = np.zeros((h + 2, w + 2), dtype=np.uint8)
    road_mask = np.zeros((h, w), dtype=np.uint8)
    seed_y = h - 3

    for ratio in SEED_COLUMNS:
        seed_x = int(w * ratio)
        if enhanced[seed_y, seed_x] < 15:
            continue

        tmp = ada.copy()
        flood_mask[:] = 0
        cv2.floodFill(
            tmp, flood_mask,
            seedPoint=(seed_x, seed_y),
            newVal=128,
            loDiff=20, upDiff=20,
            flags=cv2.FLOODFILL_MASK_ONLY | (128 << 8) | cv2.FLOODFILL_FIXED_RANGE
        )
        road_mask = cv2.bitwise_or(road_mask, (flood_mask[1:-1, 1:-1] > 0).astype(np.uint8) * 255)

    if road_mask.max() == 0:
        road_mask = ada.copy()

    kernel_close = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9))
    kernel_open = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    road_mask = cv2.morphologyEx(road_mask, cv2.MORPH_CLOSE, kernel_close, iterations=2)
    road_mask = cv2.morphologyEx(road_mask, cv2.MORPH_OPEN, kernel_open, iterations=1)

    num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(road_mask, connectivity=8)
    if num_labels > 1:
        largest = 1 + np.argmax(stats[1:, cv2.CC_STAT_AREA])
        road_mask = np.where(labels == largest, 255, 0).astype(np.uint8)

    return road_mask


def mask_to_yolo_polygon(mask: np.ndarray) -> list:
    h, w = mask.shape[:2]
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_TC89_KCOS)

    polygons = []
    for cnt in contours:
        if cv2.contourArea(cnt) < MIN_ROAD_AREA:
            continue
        epsilon = POLY_EPSILON_RATIO * cv2.arcLength(cnt, True)
        approx = cv2.approxPolyDP(cnt, epsilon, True)

        if len(approx) < 3:
            continue

        pts = []
        for pt in approx:
            x, y = pt[0]
            pts.append(f"{x / w:.6f} {y / h:.6f}")
        polygons.append(" ".join(pts))

    return polygons


def process_single(img_path: str, mask_save_path: str = None) -> list:
    img = cv2.imread(img_path)
    if img is None:
        return []

    mask = extract_road_mask(img)

    if mask_save_path:
        cv2.imwrite(mask_save_path, mask)

    return mask_to_yolo_polygon(mask)


def build_night_dataset(
    raw_dir: str,
    mask_dir: str,
    output_dir: str,
    val_ratio: float = 0.2,
    seed: int = 42,
    save_masks: bool = True,
    skip_empty: bool = False,
):
    raw_dir = os.path.abspath(raw_dir)
    mask_dir = os.path.abspath(mask_dir)
    output_dir = os.path.abspath(output_dir)

    if not os.path.isdir(raw_dir):
        print(f"[LỖI] Không tìm thấy thư mục ảnh gốc: {raw_dir}")
        return

    img_files = sorted([
        f for f in os.listdir(raw_dir)
        if f.lower().endswith(('.jpg', '.jpeg', '.png'))
    ])
    if not img_files:
        print("[LỖI] Không có ảnh nào trong thư mục raw!")
        return

    print(f"\n{'='*60}")
    print(f"  AUTO-LABEL ANH BAN DEM -> YOLO SEGMENTATION DATASET")
    print(f"{'='*60}")
    print(f"  Ảnh gốc     : {raw_dir}")
    print(f"  Mask output  : {mask_dir}")
    print(f"  YOLO dataset : {output_dir}")
    print(f"  Tổng ảnh     : {len(img_files)}")
    print(f"  Val ratio    : {val_ratio*100:.0f}%")
    print(f"{'='*60}\n")

    dirs = {
        'train_img': os.path.join(output_dir, 'images', 'train'),
        'val_img': os.path.join(output_dir, 'images', 'val'),
        'train_lbl': os.path.join(output_dir, 'labels', 'train'),
        'val_lbl': os.path.join(output_dir, 'labels', 'val'),
    }
    for d in dirs.values():
        os.makedirs(d, exist_ok=True)
    if save_masks:
        os.makedirs(mask_dir, exist_ok=True)

    records = []
    no_road = 0

    print("Đang phân tích & gán nhãn ảnh...")
    for img_file in tqdm(img_files, ncols=70):
        img_path = os.path.join(raw_dir, img_file)
        base_name = os.path.splitext(img_file)[0]
        mask_path = os.path.join(mask_dir, base_name + '.png') if save_masks else None

        polygons = process_single(img_path, mask_path)

        if not polygons:
            no_road += 1
            if skip_empty:
                continue

        records.append((img_file, polygons))

    print(f"\n  Gán nhãn xong: {len(records)} ảnh")
    print(f"  Không phát hiện đường: {no_road} ảnh (làm Empty Label)")

    random.seed(seed)
    random.shuffle(records)
    val_count = int(len(records) * val_ratio)
    train_count = len(records) - val_count
    val_records = records[:val_count]
    train_records = records[val_count:]

    print(f"\n  Train: {train_count} | Val: {val_count}")

    def write_split(split_records, split_name):
        img_dest = dirs[f'{split_name}_img']
        lbl_dest = dirs[f'{split_name}_lbl']

        for img_file, polygons in tqdm(split_records, desc=f"  Ghi {split_name:5s}", ncols=70):
            src_img = os.path.join(raw_dir, img_file)
            base_name = os.path.splitext(img_file)[0]

            shutil.copy(src_img, os.path.join(img_dest, img_file))

            lbl_path = os.path.join(lbl_dest, base_name + '.txt')
            with open(lbl_path, 'w', encoding='utf-8') as f:
                for poly in polygons:
                    f.write(f"0 {poly}\n")

    write_split(train_records, 'train')
    write_split(val_records, 'val')

    yaml_path = os.path.join(output_dir, 'night_road_seg.yaml')
    yaml_content = f"""# UIT-CAR-RACING | Night Road Segmentation Dataset
path: {output_dir}
train: images/train
val: images/val

nc: 1
names:
  0: road
"""
    with open(yaml_path, 'w', encoding='utf-8') as f:
        f.write(yaml_content)

    print(f"\n{'='*60}")
    print(f"  HOÀN TẤT BƯỚC 1 & 2!")
    print(f"  Dataset YOLO : {output_dir}")
    print(f"  Config YAML  : {yaml_path}")
    if save_masks:
        print(f"  Masks PNG    : {mask_dir}")
    print(f"{'='*60}\n")


def parse_args():
    p = argparse.ArgumentParser(
        description="Auto-label night images & build YOLO Segmentation dataset."
    )
    p.add_argument("--raw_dir", default=DEFAULT_RAW_DIR,
                   help="Thư mục ảnh gốc ban đêm")
    p.add_argument("--mask_dir", default=DEFAULT_MASK_DIR,
                   help="Thư mục lưu ảnh mask PNG để debug")
    p.add_argument("--output_dir", default=DEFAULT_OUTPUT_DIR,
                   help="Thư mục đầu ra YOLO dataset")
    p.add_argument("--val", type=float, default=0.2,
                   help="Tỉ lệ tập validation")
    p.add_argument("--seed", type=int, default=42,
                   help="Random seed")
    p.add_argument("--no_masks", action="store_true",
                   help="Không lưu ảnh mask PNG")
    p.add_argument("--skip_empty", action="store_true",
                   help="Bỏ qua ảnh không phát hiện được đường")
    return p.parse_args()


if __name__ == "__main__":
    args = parse_args()
    build_night_dataset(
        raw_dir=args.raw_dir,
        mask_dir=args.mask_dir,
        output_dir=args.output_dir,
        val_ratio=args.val,
        seed=args.seed,
        save_masks=not args.no_masks,
        skip_empty=args.skip_empty,
    )
