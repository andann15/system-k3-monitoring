"""
utils/violation_handler.py
Menangani auto-capture gambar pelanggaran
Log ke DB/JSON sekarang ditangani oleh backend API
"""

import os
import json
import time
import datetime
import cv2
from pathlib import Path

try:
    import psycopg2
    HAS_DB = True
except ImportError:
    HAS_DB = False

VIOLATION_CLASSES = {'no boots', 'no helmet', 'no vest'}


class ViolationHandler:
    # Cooldown antar capture (detik) — hindari duplikasi
    CAPTURE_COOLDOWN = 3.0

    def __init__(
        self,
        capture_dir : str  = "captures",
        db_host     : str  = "localhost",
        db_port     : int  = 5432,
        db_name     : str  = "apd_monitor",
        db_user     : str  = "postgres",
        db_pass     : str  = "postgres",
        use_db      : bool = False,   # default False — pakai JSON fallback
    ):
        self.capture_dir   = Path(capture_dir)
        self.capture_dir.mkdir(parents=True, exist_ok=True)
        self._last_capture = 0.0
        self._log_path     = self.capture_dir / "violation_log.json"
        self._db_conn      = None
        self._use_db       = use_db

        if not self._log_path.exists():
            self._log_path.write_text("[]")

        if use_db and HAS_DB:
            try:
                self._db_conn = psycopg2.connect(
                    host=db_host, port=db_port,
                    dbname=db_name, user=db_user, password=db_pass,
                )
                self._ensure_table()
                print("[DB] Koneksi PostgreSQL berhasil.")
            except Exception as e:
                print(f"[DB] Tidak dapat terhubung: {e}")
                self._db_conn = None

    # ─────────────────────────────────────────────────────────
    def capture_only(self, frame) -> str | None:
        """
        Hanya simpan gambar bukti ke disk.
        TIDAK menyimpan log ke JSON/DB — tugas backend API.
        Dipanggil oleh detect_realtime.py sebelum kirim ke API.
        """
        now = time.time()
        if now - self._last_capture < self.CAPTURE_COOLDOWN:
            return None

        self._last_capture = now
        ts    = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:19]
        fname = f"violation_{ts}.jpg"
        path  = self.capture_dir / fname
        cv2.imwrite(str(path), frame, [cv2.IMWRITE_JPEG_QUALITY, 90])
        print(f"[CAPTURE] Gambar disimpan: {fname}")
        return str(path)

    # ─────────────────────────────────────────────────────────
    def handle(self, frame, detections: list) -> str | None:
        """
        Capture gambar + log ke JSON/DB (mode lama).
        Masih bisa dipakai jika tidak ada backend API.
        """
        now = time.time()
        if now - self._last_capture < self.CAPTURE_COOLDOWN:
            return None

        violations = [d for d in detections if d["class"] in VIOLATION_CLASSES]
        if not violations:
            return None

        self._last_capture = now
        ts     = datetime.datetime.now()
        ts_str = ts.strftime("%Y%m%d_%H%M%S_%f")[:19]
        fname  = f"violation_{ts_str}.jpg"
        path   = self.capture_dir / fname
        cv2.imwrite(str(path), frame, [cv2.IMWRITE_JPEG_QUALITY, 90])

        viol_types = list({v["class"] for v in violations})
        record = {
            "timestamp"  : ts.isoformat(),
            "violations" : viol_types,
            "image_path" : str(path),
            "detections" : len(detections),
        }

        if self._db_conn:
            self._log_to_db(record)
        else:
            self._log_to_json(record)

        print(f"[CAPTURE] {ts.strftime('%H:%M:%S')} – {', '.join(viol_types)} → {fname}")
        return str(path)

    # ─────────────────────────────────────────────────────────
    def _ensure_table(self):
        with self._db_conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS violations (
                    id          SERIAL PRIMARY KEY,
                    timestamp   TIMESTAMP NOT NULL,
                    violations  TEXT[],
                    image_path  TEXT,
                    detections  INTEGER,
                    created_at  TIMESTAMP DEFAULT NOW()
                );
            """)
            self._db_conn.commit()

    def _log_to_db(self, record: dict):
        try:
            with self._db_conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO violations (timestamp, violations, image_path, detections) "
                    "VALUES (%s, %s, %s, %s)",
                    (record["timestamp"], record["violations"],
                     record["image_path"], record["detections"]),
                )
                self._db_conn.commit()
        except Exception as e:
            print(f"[DB][ERROR] {e}")
            self._log_to_json(record)

    def _log_to_json(self, record: dict):
        try:
            logs = json.loads(self._log_path.read_text())
            logs.append(record)
            self._log_path.write_text(
                json.dumps(logs, indent=2, ensure_ascii=False)
            )
        except Exception as e:
            print(f"[LOG][ERROR] {e}")

    def get_recent(self, n: int = 50) -> list:
        try:
            logs = json.loads(self._log_path.read_text())
            return logs[-n:][::-1]
        except Exception:
            return []

    def capture_only(self, frame):
        """Hanya simpan gambar bukti tanpa log ke JSON/DB."""
        import time as _time
        now = _time.time()
        if now - self._last_capture < self.CAPTURE_COOLDOWN:
            return None
        self._last_capture = now
        import datetime as _dt
        ts    = _dt.datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:19]
        fname = f"violation_{ts}.jpg"
        path  = self.capture_dir / fname
        import cv2 as _cv2
        _cv2.imwrite(str(path), frame, [_cv2.IMWRITE_JPEG_QUALITY, 90])
        print(f"[CAPTURE] {fname}")
        return str(path)