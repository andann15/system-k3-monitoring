# 🦺 Sistem Monitoring APD K3 – Panduan Menjalankan Sistem
**Kelompok 04 – Universitas Brawijaya 2026**

Sistem ini digunakan untuk mendeteksi kepatuhan penggunaan Alat Pelindung Diri (APD) pada lingkungan kerja secara *real-time* berbasis Computer Vision (YOLOv8) dengan fitur dashboard pelaporan, keamanan API, pemantauan performa CPU, dan notifikasi Telegram.

---

## 📥 Langkah 0: Download File Wajib (Tidak Ada di GitHub)

Karena alasan keamanan dan batas ukuran file, ada dua file penting yang **tidak diupload** ke GitHub. Sebelum memulai, Anda dan rekan satu tim Anda **wajib** mendownload kedua file ini melalui tautan Google Drive berikut:

🔗 **[Download File .env dan best.pt di Sini](https://drive.google.com/drive/folders/1EM0kmI7ZeDi3g0FbFihSYOfm3cgGAKq0?usp=sharing)**

Setelah berhasil didownload, **pindahkan kedua file tersebut (`.env` dan `best.pt`) tepat di dalam folder root `apd_project`** Anda.

---

## 🛠️ Prasyarat

Pastikan semua persyaratan berikut sudah terpenuhi sebelum menjalankan sistem:

- ✅ Python 3.10+ sudah terinstall.
- ✅ File `best.pt` dan `.env` sudah didownload dan diletakkan di folder proyek (Lihat Langkah 0).
- ✅ Webcam tersambung dan berfungsi di laptop/PC.
- ✅ Virtual environment (`.venv`) sudah dibuat dan semua dependensi terinstall.
  *Jika belum: Jalankan `pip install -r requirements.txt` di dalam virtual environment.*

---

## 📂 Struktur Folder Proyek

```text
apd_project/
├── .venv/                        ← Virtual environment Python (Dependensi lokal)
├── app/
│   ├── backend.py                ← REST API (FastAPI) terproteksi API Key untuk database
│   └── dashboard.py              ← Dashboard interaktif (Streamlit) dengan sistem Login
├── captures/                     ← Folder otomatis tempat hasil foto pelanggaran disimpan
├── dataset/                      ← Folder dataset YOLOv8
├── runs/                         ← Folder log dari proses evaluasi & training YOLOv8
├── scripts/
│   ├── detect_realtime.py        ← Script inferensi & deteksi kamera real-time (dengan CPU Monitoring)
│   ├── evaluate.py               ← Script evaluasi performa model
│   └── train.py                  ← Script untuk melatih ulang model YOLO
├── utils/
│   ├── ai_integration_client.py  ← Mengirim data pelanggaran dari kamera ke backend (terenkripsi API Key)
│   ├── notifier.py               ← Mengirim notifikasi pelanggaran via Telegram
│   └── violation_handler.py      ← Mengambil foto bukti (auto-capture) pelanggaran
├── .env                          ← File konfigurasi rahasia (Token, API Key, Password)
├── .gitignore                    ← Konfigurasi file yang diabaikan oleh Git
├── Dockerfile                    ← Script untuk membungkus Dashboard menjadi Docker image
├── README.md                     ← Panduan ini
├── best.pt                       ← Model AI YOLOv8 yang sudah dilatih (Weights)
├── docker-compose.yml            ← Konfigurasi Docker (PostgreSQL & Dashboard Opsional)
└── requirements.txt              ← Daftar library yang dibutuhkan
```

---

## 🚀 Langkah Menjalankan Sistem

Untuk menjalankan sistem ini secara penuh, Anda harus **membuka 3 Terminal terpisah** (bisa menggunakan fitur *Split Terminal* di VSCode). **Penting:** Pastikan Virtual Environment aktif di ketiga terminal tersebut sebelum menjalankan perintah!

### 🔹 Tahap Persiapan: Aktifkan Virtual Environment
Jalankan perintah ini di **setiap** terminal yang baru dibuka:
```powershell
# Untuk Windows (PowerShell)
cd d:\apd_project_kelompok04\apd_project
.\.venv\Scripts\Activate.ps1
```
*(Pastikan muncul tulisan `(.venv)` di awal baris terminal)*

### 🔹 Terminal 1: Jalankan Backend API (Wajib Dijalankan Pertama)
Backend memiliki proteksi **API Key**. Pastikan file `.env` sudah ada.
```bash
uvicorn app.backend:app --host 0.0.0.0 --port 8000 --reload
```
✅ **Verifikasi:** Buka browser dan akses `http://localhost:8000/docs`. Jika muncul halaman Swagger UI, backend telah berjalan dengan sukses.

### 🔹 Terminal 2: Jalankan Deteksi Kamera Real-Time
Script kamera ini akan otomatis memantau pelanggaran, memantau *CPU Usage*, dan mengirim data ke Backend secara aman.
```bash
# Menggunakan webcam bawaan laptop (Source 0)
python scripts/detect_realtime.py --weights best.pt

# Jika ingin menggunakan kamera eksternal (Source 1)
python scripts/detect_realtime.py --weights best.pt --source 1
```
✅ **Verifikasi:** Jendela kamera akan terbuka dengan info FPS dan CPU Usage di pojok kiri atas. Kotak hijau menandakan patuh, kotak merah menandakan pelanggaran. Foto pelanggaran otomatis tersimpan di `captures/`.
*(Tekan tombol `Q` pada keyboard untuk menghentikan kamera).*

### 🔹 Terminal 3: Jalankan Dashboard Monitor
Dashboard sekarang dilengkapi dengan **Sistem Login** untuk keamanan.
```bash
streamlit run app/dashboard.py
```
✅ **Verifikasi:** Browser otomatis terbuka di `http://localhost:8501`. 
🔒 **Login:** Masukkan kata sandi administrator (default: `admin123`) untuk bisa melihat grafik laporan kepatuhan, foto bukti, dan riwayat pelanggaran.

---

## 🗄️ (Opsional) Setup Database PostgreSQL

Secara default, data ditampung dalam file log JSON (sesuai tahap development). Jika Anda membutuhkan penyimpanan permanen menggunakan PostgreSQL via Docker:

1. Pastikan Docker Desktop berjalan.
2. Jalankan perintah:
   ```bash
   docker-compose up -d db
   ```
3. Pastikan konfigurasi database di file `.env` sudah benar.

---

## 🔧 Troubleshooting Umum

* **Camera Error / Could not open camera:** Ganti `--source 0` menjadi `--source 1` atau pastikan kamera tidak sedang dipakai aplikasi lain (seperti Zoom/Meet).
* **ModuleNotFoundError:** Anda lupa mengaktifkan `.venv`. Kembali lakukan Tahap Persiapan.
* **ImportError (utils tidak ditemukan):** Set PYTHONPATH dengan perintah: `$env:PYTHONPATH = "d:\apd_project_kelompok04\apd_project"`.
* **Program Tiba-Tiba "Freeze" Saat Loading AI:** Saat pertama kali dijalankan, PyTorch membutuhkan waktu memuat file `.dll`. **Jangan menekan `Ctrl+C`**, cukup tunggu 15-30 detik hingga jendela kamera terbuka!
* **Data Pelanggaran Tidak Muncul di Dashboard:** Pastikan Terminal 1 (Backend API) sudah menyala dan berjalan **SEBELUM** Anda menjalankan kamera di Terminal 2.