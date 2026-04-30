# 🦺 Sistem Monitoring APD K3 – Panduan Menjalankan Sistem
**Kelompok 04 – Universitas Brawijaya 2026**

---

## Prasyarat

Pastikan semua sudah tersedia sebelum menjalankan sistem:

- ✅ Python 3.10+ terinstall
- ✅ File `best.pt` ada di folder `apd_project`
- ✅ Semua library terinstall (`pip install -r requirements.txt`)
- ✅ Webcam tersambung ke laptop
- ✅ Virtual environment sudah dibuat

---

## Struktur Folder

```
apd_project/
├── app/
│   ├── backend.py          ← REST API FastAPI
│   ├── dashboard.py        ← Dashboard Streamlit
│   └── dashboard.html      ← Dashboard HTML (tanpa server)
├── scripts/
│   ├── detect_realtime.py  ← Deteksi real-time webcam
│   ├── evaluate.py         ← Evaluasi model
│   └── train.py            ← Training model
├── utils/
│   ├── ai_integration_client.py  ← Kirim data ke backend
│   ├── dashboard_client.py       ← Ambil data dari backend
│   ├── violation_handler.py      ← Auto-capture pelanggaran
│   └── notifier.py               ← Notifikasi email/Telegram
├── captures/               ← Hasil auto-capture (dibuat otomatis)
├── dataset/                ← Dataset YOLOv8
├── best.pt                 ← Model hasil training
├── requirements.txt
└── docker-compose.yml
```

---

## Langkah 0 — Aktifkan Virtual Environment

Buka terminal VSCode, jalankan setiap kali sebelum memulai:

```bash
# Windows
cd C:\apd_project_kelompok04\apd_project
.\.venv\Scripts\Activate.ps1

# Harus muncul:
# (.venv) PS C:\apd_project_kelompok04\apd_project>
```

---

## Langkah 1 — Jalankan Backend API

**Buka Terminal 1**, jalankan:

```bash
pip install fastapi uvicorn python-multipart
uvicorn app.backend:app --host 0.0.0.0 --port 8000 --reload
```

**Verifikasi berhasil:**
- Buka browser → `http://localhost:8000/docs`
- Swagger UI harus muncul dengan semua endpoint

**Endpoint yang tersedia:**
```
POST   /api/v1/violations         → Kirim data pelanggaran
GET    /api/v1/violations         → Ambil semua pelanggaran
GET    /api/v1/violations/{id}    → Detail satu pelanggaran
DELETE /api/v1/violations/{id}    → Hapus pelanggaran
GET    /api/v1/stats/summary      → Statistik kepatuhan
GET    /api/v1/stats/per-type     → Tren per jenis APD
```

---

## Langkah 2 — Jalankan Deteksi Real-Time

**Buka Terminal 2 baru**, jalankan:

```bash
# Webcam default (kamera bawaan laptop)
python scripts/detect_realtime.py --weights best.pt

# Kamera eksternal
python scripts/detect_realtime.py --weights best.pt --source 1

# IP Camera / RTSP
python scripts/detect_realtime.py --weights best.pt --source rtsp://192.168.1.x/stream

# Dengan area dan kamera spesifik
python scripts/detect_realtime.py --weights best.pt --area "Area A" --camera "Kamera 1"
```

**Verifikasi berhasil:**
- Jendela kamera terbuka
- Bounding box hijau = patuh, merah = pelanggaran
- Di Terminal 1 (backend) muncul: `POST /api/v1/violations → 201`
- Di Terminal 2 muncul: `✅ Berhasil: ['no helmet'] | ID: xxxx`

**Kontrol:**
- Tekan `Q` untuk berhenti

---

## Langkah 3 — Jalankan Dashboard

**Buka Terminal 3 baru**, pilih salah satu:

### Opsi A — Streamlit (lengkap, butuh server)
```bash
streamlit run app/dashboard.py
```
Buka browser → `http://localhost:8501`

### Opsi B — HTML (langsung, tanpa server)
```bash
# Windows — buka langsung di browser
start app/dashboard.html
```
Atau klik 2x file `app/dashboard.html` di File Explorer.

---

## Langkah 4 — Setup Notifikasi Telegram (Opsional)

**Buat bot Telegram:**
1. Buka Telegram → cari `@BotFather`
2. Ketik `/newbot` → ikuti instruksi
3. Simpan token yang diberikan

**Dapatkan Chat ID:**
1. Start bot kamu di Telegram
2. Buka: `https://api.telegram.org/bot<TOKEN>/getUpdates`
3. Catat angka `chat.id`

**Set environment variable sebelum jalankan deteksi:**
```bash
# Windows PowerShell
$env:TELEGRAM_TOKEN   = "token_dari_botfather"
$env:TELEGRAM_CHAT_ID = "chat_id_kamu"
```

---

## Langkah 5 — Setup Database PostgreSQL (Opsional)

Jalankan PostgreSQL via Docker:

```bash
docker-compose up -d db
```

Verifikasi:
```bash
docker ps
# Harus muncul container apd_postgres running
```

Set environment variable:
```bash
$env:DB_HOST = "localhost"
$env:DB_PORT = "5432"
$env:DB_NAME = "apd_monitor"
$env:DB_USER = "postgres"
$env:DB_PASS = "postgres"
```

---

## Ringkasan — Jalankan Semua Sekaligus

Buka **3 terminal terpisah** di VSCode, jalankan berurutan:

```
Terminal 1 — Backend API:
  uvicorn app.backend:app --host 0.0.0.0 --port 8000 --reload

Terminal 2 — Deteksi Kamera:
  python scripts/detect_realtime.py --weights best.pt

Terminal 3 — Dashboard:
  streamlit run app/dashboard.py
```

---

## Cek Status Sistem

| Komponen | URL / Cara Cek |
|---|---|
| Backend API | `http://localhost:8000/docs` |
| Dashboard Streamlit | `http://localhost:8501` |
| Data pelanggaran | `http://localhost:8000/api/v1/violations` |
| Statistik hari ini | `http://localhost:8000/api/v1/stats/summary` |
| Log JSON | `captures/violation_log.json` |
| Gambar bukti | folder `captures/` |

---

## Troubleshooting

**Error: `No module named 'utils'`**
```bash
$env:PYTHONPATH = "C:\apd_project_kelompok04\apd_project"
```

**Error: `streamlit not found`**
```bash
python -m streamlit run app/dashboard.py
```

**Error: `Could not open camera`**
```bash
# Coba source 0 atau 1
python scripts/detect_realtime.py --weights best.pt --source 1
```

**Error: `Invalid CUDA device=0`**
```bash
# Tidak ada GPU, pakai CPU
python scripts/detect_realtime.py --weights best.pt --device cpu
```

**Backend tidak bisa diakses dari terminal deteksi:**
- Pastikan Terminal 1 (backend) sudah jalan dulu
- Cek `http://localhost:8000` bisa dibuka di browser

---

## Evaluasi Model

Jalankan untuk mendapatkan mAP, precision, recall:

```bash
python scripts/evaluate.py --weights best.pt --split test --save_json
```

Hasil tersimpan di `runs/eval_results.json`.

---

## Tim Pengembang

| Nama | NIM | Peran |
|---|---|---|
| Elvin Darrels Markho | 235150201111011 | Sistem & Bisnis |
| Rafly Januar Raharjo | 235150401111050 | AI Logic & Algoritma |
| Muhamad Fazri Supani | 235150701111019 | Backend & Deployment |
| Zidan Kusuma Putra W. | 235150307111002 | Computer Vision Engineer |
| Andan Riski Mustari | 235150301111002 | Video & Camera Engineer |
| Aqilah Akma | 235150301111017 | System Integrator |

---

*Universitas Brawijaya – Fakultas Ilmu Komputer – 2026*