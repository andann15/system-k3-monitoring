"""
app/backend.py – REST API Backend untuk Sistem Monitoring APD
Proyek Capstone: Deteksi APD Otomatis
Kelompok 04 – Universitas Brawijaya 2026

Endpoint sesuai desain LK-2:
  POST   /api/v1/violations           → Kirim data deteksi & upload gambar (Zidan/AI)
  GET    /api/v1/violations           → Ambil daftar semua pelanggaran (Aqilah/Dashboard)
  GET    /api/v1/violations/{id}      → Ambil detail satu pelanggaran (Aqilah/Dashboard)
  DELETE /api/v1/violations/{id}      → Hapus log pelanggaran (Admin)
  GET    /api/v1/stats/summary        → Ringkasan statistik kepatuhan (Aqilah/Dashboard)

Cara jalankan:
  pip install fastapi uvicorn python-multipart
  uvicorn app.backend:app --host 0.0.0.0 --port 8000 --reload
"""

import os
import json
import uuid
import datetime
import shutil
from pathlib import Path
from typing import List, Optional

from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

# ──────────────────────────────────────────────────────────────
# CONFIG
# ──────────────────────────────────────────────────────────────
CAPTURE_DIR  = Path(os.getenv("CAPTURE_DIR", "captures"))
LOG_PATH     = CAPTURE_DIR / "violation_log.json"
CAPTURE_DIR.mkdir(parents=True, exist_ok=True)

VIOLATION_CLASSES = {"no helmet", "no vest", "no boots"}

# ──────────────────────────────────────────────────────────────
# APP
# ──────────────────────────────────────────────────────────────
app = FastAPI(
    title       = "APD Monitor K3 – API",
    description = "REST API Sistem Monitoring Kepatuhan APD – PT Indonesia Epson Industry",
    version     = "1.0.0",
    docs_url    = "/docs",       # Swagger UI
    redoc_url   = "/redoc",
)

# CORS – izinkan dashboard mengakses API
app.add_middleware(
    CORSMiddleware,
    allow_origins  = ["*"],
    allow_methods  = ["*"],
    allow_headers  = ["*"],
)

# Static files untuk gambar capture
app.mount("/captures", StaticFiles(directory=str(CAPTURE_DIR)), name="captures")


# ──────────────────────────────────────────────────────────────
# MODELS (Pydantic)
# ──────────────────────────────────────────────────────────────
class ViolationRecord(BaseModel):
    id          : str
    timestamp   : str
    violations  : List[str]
    image_path  : Optional[str] = None
    image_url   : Optional[str] = None
    confidence  : Optional[float] = None
    area        : Optional[str] = "Area Tidak Diketahui"
    camera      : Optional[str] = "Kamera 1"

class ViolationCreate(BaseModel):
    violations  : List[str]
    confidence  : Optional[float] = None
    area        : Optional[str] = "Area Tidak Diketahui"
    camera      : Optional[str] = "Kamera 1"

class StatsSummary(BaseModel):
    total_violations    : int
    today_violations    : int
    no_helmet_count     : int
    no_vest_count       : int
    no_boots_count      : int
    compliance_rate     : float
    last_violation_time : Optional[str]


# ──────────────────────────────────────────────────────────────
# HELPERS
# ──────────────────────────────────────────────────────────────
def load_log() -> List[dict]:
    """Baca semua data pelanggaran dari JSON."""
    if not LOG_PATH.exists():
        return []
    try:
        return json.loads(LOG_PATH.read_text(encoding="utf-8"))
    except Exception:
        return []


def save_log(data: List[dict]):
    """Simpan semua data ke JSON."""
    LOG_PATH.write_text(
        json.dumps(data, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )


def record_to_model(r: dict, base_url: str = "") -> ViolationRecord:
    """Konversi dict ke ViolationRecord, tambahkan URL gambar."""
    img_path = r.get("image_path", "")
    img_url  = None
    if img_path and Path(img_path).exists():
        fname   = Path(img_path).name
        img_url = f"{base_url}/captures/{fname}"

    return ViolationRecord(
        id         = r.get("id", str(uuid.uuid4())),
        timestamp  = r.get("timestamp", ""),
        violations = r.get("violations", []),
        image_path = img_path,
        image_url  = img_url,
        confidence = r.get("confidence"),
        area       = r.get("area", "Area Tidak Diketahui"),
        camera     = r.get("camera", "Kamera 1"),
    )


# ──────────────────────────────────────────────────────────────
# ROOT
# ──────────────────────────────────────────────────────────────
@app.get("/", tags=["Info"])
def root():
    return {
        "service" : "APD Monitor K3 API",
        "version" : "1.0.0",
        "docs"    : "/docs",
        "status"  : "online",
    }


# ──────────────────────────────────────────────────────────────
# POST /api/v1/violations
# Pengguna: Zidan (AI Detection Engine)
# Menerima data deteksi + upload gambar bukti
# ──────────────────────────────────────────────────────────────
@app.post("/api/v1/violations", tags=["Violations"], status_code=201)
async def create_violation(
    violations : str        = Form(..., description="JSON array jenis pelanggaran, contoh: '[\"no helmet\"]'"),
    confidence : float      = Form(None, description="Confidence score model"),
    area       : str        = Form("Area Tidak Diketahui"),
    camera     : str        = Form("Kamera 1"),
    image      : UploadFile = File(None, description="Gambar bukti pelanggaran (opsional)"),
):
    """
    **Kirim data deteksi pelanggaran dari AI engine.**

    Dipanggil oleh `detect_realtime.py` setiap kali pelanggaran terdeteksi.
    """
    # Parse violations JSON string
    try:
        viol_list = json.loads(violations)
        if not isinstance(viol_list, list):
            raise ValueError
    except Exception:
        raise HTTPException(status_code=422, detail="Format violations harus JSON array, contoh: '[\"no helmet\"]'")

    # Validasi kelas pelanggaran
    invalid = [v for v in viol_list if v not in VIOLATION_CLASSES]
    if invalid:
        raise HTTPException(
            status_code=422,
            detail=f"Kelas tidak valid: {invalid}. Pilihan: {list(VIOLATION_CLASSES)}"
        )

    # Simpan gambar
    image_path = None
    if image and image.filename:
        ts_str     = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:19]
        ext        = Path(image.filename).suffix or ".jpg"
        fname      = f"violation_{ts_str}{ext}"
        image_path = str(CAPTURE_DIR / fname)
        with open(image_path, "wb") as f:
            shutil.copyfileobj(image.file, f)

    # Buat record
    record = {
        "id"         : str(uuid.uuid4()),
        "timestamp"  : datetime.datetime.now().isoformat(),
        "violations" : viol_list,
        "image_path" : image_path,
        "confidence" : confidence,
        "area"       : area,
        "camera"     : camera,
    }

    # Simpan ke log
    data = load_log()
    data.append(record)
    save_log(data)

    return {
        "status"  : "created",
        "id"      : record["id"],
        "message" : f"Pelanggaran {viol_list} berhasil dicatat.",
    }


# ──────────────────────────────────────────────────────────────
# GET /api/v1/violations
# Pengguna: Aqilah (Dashboard)
# Ambil daftar semua pelanggaran dengan filter opsional
# ──────────────────────────────────────────────────────────────
@app.get("/api/v1/violations", tags=["Violations"], response_model=List[ViolationRecord])
def get_violations(
    limit      : int           = Query(50,   description="Jumlah data maksimal"),
    offset     : int           = Query(0,    description="Offset untuk pagination"),
    type_filter: Optional[str] = Query(None, description="Filter jenis: no helmet / no vest / no boots"),
    date_from  : Optional[str] = Query(None, description="Filter tanggal mulai (YYYY-MM-DD)"),
    date_to    : Optional[str] = Query(None, description="Filter tanggal akhir (YYYY-MM-DD)"),
):
    """
    **Ambil daftar semua pelanggaran.**

    Mendukung filter berdasarkan jenis APD dan rentang tanggal.
    """
    data = load_log()

    # Filter jenis
    if type_filter:
        data = [r for r in data if type_filter in r.get("violations", [])]

    # Filter tanggal
    if date_from:
        data = [r for r in data if r.get("timestamp", "") >= date_from]
    if date_to:
        data = [r for r in data if r.get("timestamp", "") <= date_to + "T23:59:59"]

    # Urutkan terbaru dulu
    data = sorted(data, key=lambda r: r.get("timestamp", ""), reverse=True)

    # Pagination
    data = data[offset : offset + limit]

    return [record_to_model(r) for r in data]


# ──────────────────────────────────────────────────────────────
# GET /api/v1/violations/{id}
# Pengguna: Aqilah (Dashboard)
# Ambil detail satu pelanggaran spesifik
# ──────────────────────────────────────────────────────────────
@app.get("/api/v1/violations/{violation_id}", tags=["Violations"], response_model=ViolationRecord)
def get_violation_by_id(violation_id: str):
    """
    **Ambil detail satu pelanggaran berdasarkan ID.**
    """
    data   = load_log()
    record = next((r for r in data if r.get("id") == violation_id), None)

    if not record:
        raise HTTPException(status_code=404, detail=f"Pelanggaran dengan ID '{violation_id}' tidak ditemukan.")

    return record_to_model(record)


# ──────────────────────────────────────────────────────────────
# DELETE /api/v1/violations/{id}
# Pengguna: Admin (Internal)
# Hapus log pelanggaran jika salah deteksi
# ──────────────────────────────────────────────────────────────
@app.delete("/api/v1/violations/{violation_id}", tags=["Violations"])
def delete_violation(violation_id: str):
    """
    **Hapus log pelanggaran berdasarkan ID.**

    Digunakan admin jika terjadi false positive (salah deteksi).
    """
    data   = load_log()
    record = next((r for r in data if r.get("id") == violation_id), None)

    if not record:
        raise HTTPException(status_code=404, detail=f"Pelanggaran dengan ID '{violation_id}' tidak ditemukan.")

    # Hapus gambar bukti jika ada
    img_path = record.get("image_path")
    if img_path and Path(img_path).exists():
        Path(img_path).unlink()

    # Hapus dari log
    data = [r for r in data if r.get("id") != violation_id]
    save_log(data)

    return {"status": "deleted", "id": violation_id}


# ──────────────────────────────────────────────────────────────
# GET /api/v1/stats/summary
# Pengguna: Aqilah (Dashboard)
# Ringkasan statistik kepatuhan APD
# ──────────────────────────────────────────────────────────────
@app.get("/api/v1/stats/summary", tags=["Statistics"], response_model=StatsSummary)
def get_stats_summary():
    """
    **Ambil ringkasan statistik kepatuhan APD hari ini.**

    Meliputi: total pelanggaran, per jenis APD, dan tingkat kepatuhan.
    """
    data  = load_log()
    today = datetime.date.today().isoformat()

    today_data = [
        r for r in data
        if r.get("timestamp", "").startswith(today)
    ]

    total      = len(data)
    today_tot  = len(today_data)

    no_helmet  = sum(1 for r in data if "no helmet" in r.get("violations", []))
    no_vest    = sum(1 for r in data if "no vest"   in r.get("violations", []))
    no_boots   = sum(1 for r in data if "no boots"  in r.get("violations", []))

    # Tingkat kepatuhan sederhana (asumsi 100 pengamatan per hari)
    base       = max(today_tot + 10, 10)
    compliance = round((1 - today_tot / base) * 100, 1)
    compliance = max(0.0, min(100.0, compliance))

    last_time  = None
    if data:
        sorted_data = sorted(data, key=lambda r: r.get("timestamp", ""), reverse=True)
        last_time   = sorted_data[0].get("timestamp")

    return StatsSummary(
        total_violations    = total,
        today_violations    = today_tot,
        no_helmet_count     = no_helmet,
        no_vest_count       = no_vest,
        no_boots_count      = no_boots,
        compliance_rate     = compliance,
        last_violation_time = last_time,
    )


# ──────────────────────────────────────────────────────────────
# GET /api/v1/stats/per-type
# Tambahan: breakdown per jenis per hari (untuk chart)
# ──────────────────────────────────────────────────────────────
@app.get("/api/v1/stats/per-type", tags=["Statistics"])
def get_stats_per_type(days: int = Query(7, description="Jumlah hari ke belakang")):
    """
    **Statistik pelanggaran per jenis per hari.**

    Digunakan untuk bar chart tren di dashboard.
    """
    data     = load_log()
    cutoff   = (datetime.date.today() - datetime.timedelta(days=days)).isoformat()
    filtered = [r for r in data if r.get("timestamp", "") >= cutoff]

    result = {}
    for r in filtered:
        date = r.get("timestamp", "")[:10]
        if date not in result:
            result[date] = {"no helmet": 0, "no vest": 0, "no boots": 0}
        for v in r.get("violations", []):
            if v in result[date]:
                result[date][v] += 1

    return {"data": result, "days": days}


# ──────────────────────────────────────────────────────────────
# RUN
# ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.backend:app", host="0.0.0.0", port=8000, reload=True)
