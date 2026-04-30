# 🦺 Sistem Monitoring APD K3 – Panduan Menjalankan Sistem
**Kelompok 04 – Universitas Brawijaya 2026**

Sistem ini digunakan untuk mendeteksi kepatuhan penggunaan Alat Pelindung Diri (APD) pada lingkungan kerja secara *real-time* berbasis Computer Vision (YOLOv8) dengan fitur dashboard pelaporan dan notifikasi Telegram.

---

## 🛠️ Prasyarat

Pastikan semua persyaratan berikut sudah terpenuhi sebelum menjalankan sistem:

- ✅ Python 3.10+ sudah terinstall.
- ✅ File `best.pt` (model YOLO) sudah ada di dalam folder root `apd_project`.
- ✅ Webcam tersambung dan berfungsi di laptop/PC.
- ✅ Virtual environment (`.venv`) sudah dibuat dan semua dependensi terinstall.
  *Jika belum: Jalankan `pip install -r requirements.txt` di dalam virtual environment.*

---

## 📂 Struktur Folder Proyek

```text
apd_project/
├── .venv/                        ← Virtual environment Python (Dependensi lokal)
├── app/
│   ├── backend.py                ← REST API (FastAPI) untuk menangani database & data
│   └── dashboard.py              ← Dashboard interaktif (Streamlit)
├── captures/                     ← Folder otomatis tempat hasil foto pelanggaran disimpan
├── dataset/                      ← Folder dataset YOLOv8
├── runs/                         ← Folder log dari proses evaluasi & training YOLOv8
├── scripts/
│   ├── detect_realtime.py        ← Script inferensi & deteksi kamera real-time
│   ├── evaluate.py               ← Script evaluasi performa model
│   └── train.py                  ← Script untuk melatih ulang model YOLO
├── utils/
│   ├── ai_integration_client.py  ← Mengirim data pelanggaran dari kamera ke backend
│   ├── notifier.py               ← Mengirim notifikasi pelanggaran via Telegram
│   └── violation_handler.py      ← Mengambil foto bukti (auto-capture) pelanggaran
├── .env                          ← File konfigurasi environment variables (Tokens, DB config)
├── .gitignore                    ← Konfigurasi file yang diabaikan oleh Git
├── Dockerfile                    ← Script untuk membungkus Dashboard menjadi Docker image
├── README.md                     ← Panduan ini
├── best.pt                       ← Model AI YOLOv8 yang sudah dilatih (Weights)
├── docker-compose.yml            ← Konfigurasi Docker (PostgreSQL & Dashboard Opsional)
└── requirements.txt              ← Daftar library yang dibutuhkan
```

*(Catatan: File duplikat yang tidak terpakai seperti `dashboard.html` dan `dashboard_client.py` telah dihapus agar proyek lebih bersih).*

---

## 🚀 Langkah Menjalankan Sistem

Untuk menjalankan sistem ini secara penuh, Anda harus **membuka 3 Terminal terpisah** (bisa menggunakan fitur *Split Terminal* di VSCode). **Penting:** Pastikan Virtual Environment aktif di ketiga terminal tersebut sebelum menjalankan perintah!

### 🔹 Langkah 0: Aktifkan Virtual Environment
Jalankan perintah ini di **setiap** terminal yang baru dibuka:
```powershell
# Untuk Windows (PowerShell)
cd d:\apd_project_kelompok04\apd_project
.\.venv\Scripts\Activate.ps1
```
*(Pastikan muncul tulisan `(.venv)` di awal baris terminal)*

### 🔹 Langkah 1: Jalankan Backend API
**Di Terminal 1**, jalankan server backend untuk menerima data dari kamera:
```bash
uvicorn app.backend:app --host 0.0.0.0 --port 8000 --reload
```
✅ **Verifikasi:** Buka browser dan akses `http://localhost:8000/docs`. Jika muncul halaman Swagger UI, backend telah berjalan dengan sukses.

### 🔹 Langkah 2: Jalankan Deteksi Kamera Real-Time
**Di Terminal 2**, jalankan script AI untuk mulai mendeteksi dari kamera:
```bash
# Menggunakan webcam bawaan laptop (Source 0)
python scripts/detect_realtime.py --weights best.pt

# Jika ingin menggunakan kamera eksternal (Source 1)
python scripts/detect_realtime.py --weights best.pt --source 1
```
✅ **Verifikasi:** Jendela kamera akan terbuka. Kotak hijau menandakan patuh, kotak merah menandakan pelanggaran. Foto pelanggaran akan otomatis tersimpan di folder `captures/`.
*(Tekan tombol `Q` pada keyboard untuk menghentikan kamera).*

### 🔹 Langkah 3: Jalankan Dashboard Monitor
**Di Terminal 3**, jalankan visualisasi dashboard berbasis web:
```bash
streamlit run app/dashboard.py
```
✅ **Verifikasi:** Browser akan otomatis terbuka menuju `http://localhost:8501` yang menampilkan grafik laporan kepatuhan, foto bukti, dan riwayat pelanggaran.

---

## 🔔 (Opsional) Setup Notifikasi Telegram

Sistem dapat mengirim alert beserta foto otomatis ke grup/chat Telegram Anda saat terdeteksi pelanggaran.

1. **Buat Bot:** Cari `@BotFather` di Telegram, ketik `/newbot`, ikuti instruksinya, dan simpan **Token** bot Anda.
2. **Dapatkan Chat ID:** Start bot Anda, kirim pesan apa saja. Lalu buka browser: `https://api.telegram.org/bot<TOKEN_ANDA>/getUpdates`. Cari angka `id` di bagian `chat`.
3. **Set Environment Variables:** Sebelum menjalankan *Langkah 2 (Deteksi Kamera)*, jalankan perintah ini di Terminal 2:
   ```powershell
   $env:TELEGRAM_TOKEN = "Masukkan_Token_Bot_Disini"
   $env:TELEGRAM_CHAT_ID = "Masukkan_Chat_ID_Disini"
   ```

---

## 🗄️ (Opsional) Setup Database PostgreSQL

Secara default, data ditampung dalam memori aplikasi. Jika Anda membutuhkan penyimpanan permanen menggunakan PostgreSQL via Docker:

1. Pastikan Docker Desktop berjalan.
2. Jalankan perintah:
   ```bash
   docker-compose up -d db
   ```
3. Set variabel environment database di Terminal 1 (sebelum menjalankan backend):
   ```powershell
   $env:DB_HOST = "localhost"
   $env:DB_PORT = "5432"
   $env:DB_NAME = "apd_monitor"
   $env:DB_USER = "postgres"
   $env:DB_PASS = "postgres"
   ```

---

## 🔧 Troubleshooting Umum

* **Camera Error / Could not open camera:** Ganti `--source 0` menjadi `--source 1` atau pastikan kamera tidak sedang dipakai aplikasi lain (seperti Zoom/Meet).
* **ModuleNotFoundError:** Anda lupa mengaktifkan `.venv`. Kembali lakukan Langkah 0.
* **ImportError (utils tidak ditemukan):** Set PYTHONPATH dengan menjalankan perintah: `$env:PYTHONPATH = "d:\apd_project_kelompok04\apd_project"`.
* **Program Tiba-Tiba "Freeze" Saat Loading AI:** Saat pertama kali dijalankan, PyTorch membutuhkan waktu beberapa detik memuat file `.dll`. Jangan menekan `Ctrl+C`, cukup tunggu hingga jendela kamera terbuka.