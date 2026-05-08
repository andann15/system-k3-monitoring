"""
detect_realtime.py – Deteksi APD Real-Time via Webcam / IP Camera
Proyek Capstone: Deteksi APD Otomatis
Kelompok 04 – Universitas Brawijaya 2026

Cara pakai:
  python scripts/detect_realtime.py --weights runs/train/apd_kelompok04/weights/best.pt
  python scripts/detect_realtime.py --weights best.pt --source rtsp://192.168.1.x/stream
"""

import argparse
import time
import datetime
import os
import sys
import cv2
import numpy as np
from pathlib import Path
import psutil

# Fix ModuleNotFoundError by adding the parent directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from ultralytics import YOLO
from utils.violation_handler import ViolationHandler
from utils.notifier import send_notification
from utils.ai_integration_client import K3IntegrationClient

client = K3IntegrationClient()

# ──────────────────────────────────────────────────────────────
# CONFIG
# ──────────────────────────────────────────────────────────────
CLASS_NAMES   = ['boots', 'helmet', 'no boots', 'no helmet', 'no vest', 'person', 'vest']
VIOLATION_CLS = {'no boots', 'no helmet', 'no vest'}

COLORS = {
    'boots'     : (0, 200, 0),
    'helmet'    : (0, 200, 0),
    'vest'      : (0, 200, 0),
    'no boots'  : (0, 0, 255),
    'no helmet' : (0, 0, 255),
    'no vest'   : (0, 0, 255),
    'person'    : (255, 165, 0),
}


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--weights",     required=True)
    parser.add_argument("--source",      default="0")
    parser.add_argument("--conf",        type=float, default=0.60)
    parser.add_argument("--iou",         type=float, default=0.45)
    parser.add_argument("--imgsz",       type=int,   default=640)
    parser.add_argument("--capture_dir", default="captures")
    parser.add_argument("--show",        action="store_true", default=True)
    parser.add_argument("--no_notify",   action="store_true")
    parser.add_argument("--area",        default="Area A")
    parser.add_argument("--camera",      default="Kamera 1")
    return parser.parse_args()


def draw_overlay(frame, detections, fps: float, cpu_usage: float, violation_count: int):
    h, w = frame.shape[:2]

    for det in detections:
        cls_name = det["class"]
        if cls_name == "person":
            continue

        x1, y1, x2, y2 = det["bbox"]
        conf     = det["conf"]
        color    = COLORS.get(cls_name, (200, 200, 200))
        is_viol  = cls_name in VIOLATION_CLS

        thickness = 3 if is_viol else 2
        cv2.rectangle(frame, (x1, y1), (x2, y2), color, thickness)

        label = f"{cls_name} {conf:.2f}"
        (lw, lh), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.55, 1)
        cv2.rectangle(frame, (x1, y1 - lh - 6), (x1 + lw, y1), color, -1)
        cv2.putText(frame, label, (x1, y1 - 4),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 1)

        if is_viol:
            cv2.putText(frame, "PELANGGARAN", (x1, y2 + 20),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)

    cv2.rectangle(frame, (0, 0), (w, 36), (30, 30, 30), -1)
    ts   = datetime.datetime.now().strftime("%Y-%m-%d  %H:%M:%S")
    info = f"APD Monitor K3  |  FPS: {fps:.1f}  |  CPU: {cpu_usage:.1f}%  |  Pelanggaran: {violation_count}  |  {ts}"
    cv2.putText(frame, info, (10, 24),
                cv2.FONT_HERSHEY_SIMPLEX, 0.55, (200, 200, 200), 1)

    return frame


def run(args):
    print("\n" + "="*60)
    print("  SISTEM MONITORING APD – REAL-TIME")
    print("="*60)

    os.makedirs(args.capture_dir, exist_ok=True)

    print(f"[INFO] Loading model: {args.weights}")
    model   = YOLO(args.weights)
    handler = ViolationHandler(capture_dir=args.capture_dir)

    src = int(args.source) if args.source.isdigit() else args.source
    print(f"[INFO] Membuka sumber video: {src}")
    cap = cv2.VideoCapture(src)

    if not cap.isOpened():
        print("[ERROR] Tidak dapat membuka sumber video!")
        return

    width  = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps_in = cap.get(cv2.CAP_PROP_FPS) or 30
    print(f"[INFO] Resolusi input: {width}x{height} @ {fps_in:.0f} FPS")
    print("[INFO] Tekan 'q' untuk keluar\n")

    fps_calc        = 0.0
    prev_time       = time.time()
    violation_total = 0
    notified_track_ids = set()

    while True:
        ret, frame = cap.read()
        if not ret:
            print("[WARN] Frame tidak terbaca, mencoba lagi...")
            time.sleep(0.1)
            continue

        # ── Inferensi ─────────────────────────────────────────
        results = model.track(
            source  = frame,
            conf    = args.conf,
            iou     = args.iou,
            imgsz   = args.imgsz,
            persist = True,
            verbose = False,
        )[0]

        # ── Parse deteksi ─────────────────────────────────────
        detections    = []
        has_new_violation = False

        for box in results.boxes:
            cls_id   = int(box.cls[0])
            conf     = float(box.conf[0])
            cls_name = CLASS_NAMES[cls_id] if cls_id < len(CLASS_NAMES) else "unknown"
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            track_id = int(box.id[0]) if box.id is not None else None

            detections.append({
                "class"    : cls_name,
                "conf"     : conf,
                "bbox"     : (x1, y1, x2, y2),
                "track_id" : track_id
            })

            # Tandai pelanggaran baru jika track_id belum pernah diberi notifikasi
            if cls_name in VIOLATION_CLS:
                if track_id is not None and track_id not in notified_track_ids:
                    has_new_violation = True

        # ── Tampilan & Anotasi Frame ──────────────────────────
        cpu_perc  = psutil.cpu_percent()
        curr_time = time.time()
        fps_calc  = 0.9 * fps_calc + 0.1 * (1.0 / max(curr_time - prev_time, 1e-6))
        prev_time = curr_time

        annotated = draw_overlay(frame.copy(), detections, fps_calc, cpu_perc, violation_total + (1 if has_new_violation else 0))

        # ── Tangani pelanggaran ───────────────────────────────
        if has_new_violation:
            # Cari track ID pelanggar baru di frame ini
            new_violator_ids = [d["track_id"] for d in detections 
                                if d["class"] in VIOLATION_CLS and d["track_id"] is not None and d["track_id"] not in notified_track_ids]
            
            # Daftarkan ke set agar tidak dikirim ulang
            for tid in new_violator_ids:
                notified_track_ids.add(tid)
                violation_total += 1

            # Pass the annotated frame so the saved image has bounding boxes
            capture_path = handler.capture_only(annotated)

            # Kirim ke backend API
            viol_types = [d["class"] for d in detections if d["class"] in VIOLATION_CLS]
            conf_max   = max(d["conf"] for d in detections if d["class"] in VIOLATION_CLS)
            client.send_violation(
                violation_types = viol_types,
                confidence      = conf_max,
                image_path      = capture_path or "",
                area            = args.area,
                camera          = args.camera,
            )

            # Kirim notifikasi
            if not args.no_notify and capture_path:
                send_notification(viol_types, capture_path)

        # ── Tampilkan frame di Layar ──────────────────────────
        if args.show:
            cv2.imshow("APD Monitor K3 – Kelompok 04", annotated)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    cap.release()
    cv2.destroyAllWindows()
    print(f"\n[DONE] Sesi monitoring selesai. Total pelanggaran: {violation_total}")


if __name__ == "__main__":
    args = parse_args()
    run(args)