"""
train.py – YOLOv8 Training Script
Proyek Capstone: Deteksi APD Otomatis (Helm, Rompi, Sepatu Safety)
Kelompok 04 – Universitas Brawijaya 2026
"""

import os
import yaml
import argparse
from pathlib import Path
from ultralytics import YOLO

# ──────────────────────────────────────────────────────────────
# CONFIG
# ──────────────────────────────────────────────────────────────
DEFAULT_CONFIG = {
    "data_yaml"   : "dataset/data.yaml",      # path ke data.yaml
    "model"       : "yolov8n.pt",             # yolov8n / yolov8s / yolov8m
    "epochs"      : 50,
    "imgsz"       : 640,
    "batch"       : 16,
    "patience"    : 10,                       # early stopping
    "project"     : "runs/train",
    "name"        : "apd_kelompok04",
    "device"      : "0",                      # '0' = GPU, 'cpu' = CPU
    "workers"     : 4,
    "lr0"         : 0.01,
    "lrf"         : 0.01,
    "augment"     : True,
    "exist_ok"    : True,
}

CLASS_NAMES = ['boots', 'helmet', 'no boots', 'no helmet', 'no vest', 'person', 'vest']
VIOLATION_CLASSES = ['no boots', 'no helmet', 'no vest']   # kelas pelanggaran


def parse_args():
    parser = argparse.ArgumentParser(description="Train YOLOv8 untuk deteksi APD")
    parser.add_argument("--data",    default=DEFAULT_CONFIG["data_yaml"])
    parser.add_argument("--model",   default=DEFAULT_CONFIG["model"],
                        help="yolov8n.pt | yolov8s.pt | yolov8m.pt")
    parser.add_argument("--epochs",  type=int, default=DEFAULT_CONFIG["epochs"])
    parser.add_argument("--imgsz",   type=int, default=DEFAULT_CONFIG["imgsz"])
    parser.add_argument("--batch",   type=int, default=DEFAULT_CONFIG["batch"])
    parser.add_argument("--device",  default=DEFAULT_CONFIG["device"])
    parser.add_argument("--name",    default=DEFAULT_CONFIG["name"])
    return parser.parse_args()


def verify_dataset(data_yaml: str) -> bool:
    """Periksa apakah dataset tersedia dan valid."""
    p = Path(data_yaml)
    if not p.exists():
        print(f"[ERROR] data.yaml tidak ditemukan: {data_yaml}")
        return False
    with open(p) as f:
        cfg = yaml.safe_load(f)
    for split in ["train", "val"]:
        img_dir = Path(cfg[split])
        if not img_dir.exists():
            print(f"[ERROR] Direktori {split} tidak ditemukan: {img_dir}")
            return False
        n = len(list(img_dir.glob("*.jpg")) + list(img_dir.glob("*.png")))
        print(f"  [{split}] {n} gambar ditemukan")
    print(f"  [classes] {cfg['nc']} kelas: {cfg['names']}")
    return True


def train(args):
    print("\n" + "="*60)
    print("  TRAINING YOLOv8 – Deteksi APD K3")
    print("="*60)

    # Verifikasi dataset
    if not verify_dataset(args.data):
        return

    # Load model (pre-trained weights sebagai starting point)
    print(f"\n[INFO] Loading base model: {args.model}")
    model = YOLO(args.model)

    # Training
    print(f"[INFO] Mulai training {args.epochs} epoch ...\n")
    results = model.train(
        data       = args.data,
        epochs     = args.epochs,
        imgsz      = args.imgsz,
        batch      = args.batch,
        patience   = DEFAULT_CONFIG["patience"],
        device     = args.device,
        workers    = DEFAULT_CONFIG["workers"],
        lr0        = DEFAULT_CONFIG["lr0"],
        lrf        = DEFAULT_CONFIG["lrf"],
        augment    = DEFAULT_CONFIG["augment"],
        project    = DEFAULT_CONFIG["project"],
        name       = args.name,
        exist_ok   = DEFAULT_CONFIG["exist_ok"],

        # Augmentasi data khusus untuk kondisi pabrik
        hsv_h      = 0.015,   # variasi hue
        hsv_s      = 0.7,     # variasi saturasi
        hsv_v      = 0.4,     # variasi brightness (simulasi pencahayaan berbeda)
        flipud     = 0.0,     # jangan flip vertikal (kamera top-down)
        fliplr     = 0.5,     # flip horizontal ok
        mosaic     = 1.0,     # mosaic augmentation
        translate  = 0.1,
        scale      = 0.5,
        degrees    = 5.0,     # rotasi kecil
    )

    best_weights = Path(DEFAULT_CONFIG["project"]) / args.name / "weights" / "best.pt"
    print(f"\n[DONE] Training selesai!")
    print(f"[INFO] Best weights tersimpan di: {best_weights}")
    print(f"[INFO] Jalankan evaluasi dengan: python scripts/evaluate.py --weights {best_weights}")
    return results


if __name__ == "__main__":
    args = parse_args()
    train(args)
