"""
evaluate.py – Evaluasi model YOLOv8 pada test set
Proyek Capstone: Deteksi APD Otomatis
Kelompok 04 – Universitas Brawijaya 2026
"""

import argparse
import json
from pathlib import Path
import numpy as np
from ultralytics import YOLO

CLASS_NAMES    = ['boots', 'helmet', 'no boots', 'no helmet', 'no vest', 'person', 'vest']
VIOLATION_CLS  = ['no boots', 'no helmet', 'no vest']
COMPLIANT_CLS  = ['boots', 'helmet', 'vest']


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--weights", required=True, help="Path ke best.pt")
    parser.add_argument("--data",    default="dataset/data.yaml")
    parser.add_argument("--imgsz",   type=int, default=640)
    parser.add_argument("--conf",    type=float, default=0.001)
    parser.add_argument("--iou",     type=float, default=0.6)
    parser.add_argument("--split",   default="test", choices=["val", "test"])
    parser.add_argument("--save_json", action="store_true")
    return parser.parse_args()


def evaluate(args):
    print("\n" + "="*60)
    print("  EVALUASI MODEL – Deteksi APD K3")
    print("="*60)

    model = YOLO(args.weights)

    print(f"\n[INFO] Mengevaluasi pada split: {args.split}")
    metrics = model.val(
        data    = args.data,
        imgsz   = args.imgsz,
        conf    = args.conf,
        iou     = args.iou,
        split   = args.split,
    )

    # ── Ringkasan Metrik ──────────────────────────────────────
    print("\n" + "─"*50)
    print("  HASIL EVALUASI")
    print("─"*50)

    map50    = metrics.box.map50
    map5095  = metrics.box.map
    precision = metrics.box.mp
    recall    = metrics.box.mr

    print(f"  mAP@0.5       : {map50:.4f}  ({'✅ LULUS' if map50 >= 0.80 else '❌ BELUM LULUS'} target ≥ 0.80)")
    print(f"  mAP@0.5:0.95  : {map5095:.4f}")
    print(f"  Precision     : {precision:.4f}")
    print(f"  Recall        : {recall:.4f}")
    print(f"  F1-Score      : {2 * precision * recall / (precision + recall + 1e-9):.4f}")

    # ── Per-class ─────────────────────────────────────────────
    print("\n  Per-Kelas AP@0.5:")
    print(f"  {'Kelas':<15} {'AP@0.5':>8}  {'Tipe'}")
    print("  " + "-"*40)

    ap_per_class = metrics.box.ap50           # array per kelas
    for i, cls_name in enumerate(CLASS_NAMES):
        if i < len(ap_per_class):
            ap = ap_per_class[i]
            tipe = "🔴 PELANGGARAN" if cls_name in VIOLATION_CLS else (
                   "🟢 KEPATUHAN"  if cls_name in COMPLIANT_CLS else "⚪ LAINNYA")
            print(f"  {cls_name:<15} {ap:>8.4f}  {tipe}")

    # ── Simpan JSON ───────────────────────────────────────────
    if args.save_json:
        result_dict = {
            "mAP50"     : float(map50),
            "mAP50_95"  : float(map5095),
            "precision" : float(precision),
            "recall"    : float(recall),
            "f1"        : float(2 * precision * recall / (precision + recall + 1e-9)),
            "per_class" : {CLASS_NAMES[i]: float(ap_per_class[i])
                           for i in range(min(len(CLASS_NAMES), len(ap_per_class)))},
        }
        out = Path("runs/eval_results.json")
        out.parent.mkdir(exist_ok=True)
        out.write_text(json.dumps(result_dict, indent=2))
        print(f"\n[INFO] Hasil JSON disimpan ke: {out}")

    # ── Confusion Matrix ──────────────────────────────────────
    save_dir = getattr(metrics, 'save_dir', None)
    if save_dir:
        cm_path = Path(save_dir) / "confusion_matrix.png"
        if cm_path.exists():
            print(f"\n[INFO] Confusion Matrix (Matriks Kebingungan) berhasil digenerate.")
            print(f"       Silakan cek file: {cm_path.absolute()}")
        else:
            print(f"\n[INFO] Direktori evaluasi: {save_dir}")

    print("\n[DONE] Evaluasi selesai.\n")
    return metrics


if __name__ == "__main__":
    args = parse_args()
    evaluate(args)
