#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
collect_data.py
---------------
Script thu thap anh tu Unity Simulator de lam dataset train YOLO.
"""

import os
import sys
import cv2
import time
import argparse
import numpy as np
from datetime import datetime

# Tat GUI neu khong co man hinh X11
if not os.environ.get('DISPLAY'):
    os.environ['QT_QPA_PLATFORM'] = 'offscreen'

# Tim client_lib
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.extend(["/workspace", SCRIPT_DIR])

from client_lib import GetStatus, GetRaw, AVControl, CloseSocket

# Duong dan model YOLO (chi can khi --drive av)
MODEL_PATHS = [
    os.path.join(SCRIPT_DIR, "Road_Seg_Model", "modelYolo", "weights", "best.pt"),
    "/workspace/UIT-CAR-RACING/Road_Seg_Model/modelYolo/weights/best.pt",
    "/workspace/Road_Seg_Model/modelYolo/weights/best.pt",
]


def get_steering_angle(model, raw_image):
    """Tinh goc lai tu anh camera dung YOLO segmentation."""
    try:
        results = model.predict(source=raw_image, verbose=False)
        if not results or results[0].masks is None:
            return 28.0, 0.0

        masks = results[0].masks.data.cpu().numpy()
        seg = (np.sum(masks, axis=0) > 0).astype(np.uint8) * 255

        height, width = seg.shape
        points = []
        for y in range(height - 1, -1, -1):
            cols = np.where(seg[y] > 0)[0]
            if len(cols) > 0:
                points.append(int(np.mean(cols)))

        if not points:
            return 28.0, 0.0

        near = points[:height // 2]
        far  = points[height * 2 // 3:]

        near_err = (int(np.mean(near)) - width // 2) if near else 0
        far_err  = (int(np.mean(far))  - width // 2) if far  else 0

        error = 0.6 * near_err + 0.4 * far_err
        angle = float(np.clip(error * 0.12, -25, 25))
        return 28.0, angle
    except Exception:
        return 28.0, 0.0


def print_progress(saved, total, last_file):
    bar_len = 30
    filled  = int(bar_len * saved / total) if total > 0 else 0
    bar     = "#" * filled + "-" * (bar_len - filled)
    pct     = saved / total * 100 if total > 0 else 0
    print(f"\r  [{bar}] {saved:4d}/{total} ({pct:.0f}%)  {last_file}", end="", flush=True)


def parse_args():
    p = argparse.ArgumentParser(description="Thu thap anh tu Unity Simulator")
    p.add_argument("--scene",    type=str,   default="night",
                   choices=["day", "night"],
                   help="day = ban ngay | night = ban dem")
    p.add_argument("--drive",    type=str,   default="manual",
                   choices=["manual", "av"],
                   help="manual = lai tay trong Unity | av = xe tu lai YOLO")
    p.add_argument("--interval", type=float, default=0.3,
                   help="Giay giua 2 anh lien tiep (mac dinh: 0.3)")
    p.add_argument("--max",      type=int,   default=1000,
                   help="So anh toi da (mac dinh: 1000)")
    return p.parse_args()


def main():
    args = parse_args()

    save_dir = os.path.join(SCRIPT_DIR, "dataset", "raw", args.scene)
    os.makedirs(save_dir, exist_ok=True)
    existing = len([f for f in os.listdir(save_dir) if f.endswith(".jpg")])

    model = None
    if args.drive == "av":
        from ultralytics import YOLO
        mp = next((p for p in MODEL_PATHS if os.path.exists(p)), None)
        if mp is None:
            print("[LOI] Khong tim thay best.pt! Dung --drive manual hoac kiem tra duong dan.")
            return
        print(f"[INFO] Nap YOLO model tu: {mp}")
        model = YOLO(mp)

    print("\n" + "=" * 60)
    print(f"  THU THAP DU LIEU TRAINING")
    print(f"  Canh       : {args.scene.upper()}")
    print(f"  Lai        : {'xe tu lai (YOLO AV)' if args.drive == 'av' else 'lai tay (Manual Mode)'}")
    print(f"  Luu vao    : {save_dir}")
    print(f"  Interval   : {args.interval}s / anh")
    print(f"  Muc tieu   : {args.max} anh  (da co san: {existing})")
    print("=" * 60)
    if args.drive == "manual":
        print("  > Hay chuyen Unity sang MANUAL MODE va bat dau lai!")
    else:
        print("  > Hay chuyen Unity sang AV MODE. Xe se tu chay.")
    print("  > Nhan Ctrl+C de dung bat cu luc nao.\n")

    saved_count  = 0
    last_save_time = 0.0
    start_time   = time.time()

    try:
        while saved_count < args.max:
            try:
                raw_image = GetRaw()
            except Exception:
                time.sleep(0.1)
                continue

            if raw_image is None or raw_image.size == 0:
                time.sleep(0.05)
                continue

            if args.drive == "av" and model is not None:
                speed, angle = get_steering_angle(model, raw_image)
                try:
                    AVControl(speed=speed, angle=angle)
                except Exception:
                    pass

            now = time.time()
            if now - last_save_time < args.interval:
                continue
            last_save_time = now

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
            filename  = f"{args.scene}_{timestamp}.jpg"
            filepath  = os.path.join(save_dir, filename)
            cv2.imwrite(filepath, raw_image, [cv2.IMWRITE_JPEG_QUALITY, 95])
            saved_count += 1
            print_progress(saved_count, args.max, filename)

    except KeyboardInterrupt:
        pass
    finally:
        elapsed = time.time() - start_time
        try:
            CloseSocket()
        except Exception:
            pass

    total_in_dir = len([f for f in os.listdir(save_dir) if f.endswith(".jpg")])
    print(f"\n\n{'=' * 60}")
    print(f"  HOAN TAT!")
    print(f"  Vua luu   : {saved_count} anh ({elapsed:.0f} giay)")
    print(f"  Tong cong : {total_in_dir} anh trong thu muc {args.scene}")
    print(f"  Duong dan : {save_dir}")
    print(f"{'=' * 60}\n")


if __name__ == "__main__":
    main()
