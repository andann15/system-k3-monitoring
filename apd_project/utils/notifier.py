"""
utils/notifier.py
Notifikasi pelanggaran APD – Email / Desktop / Webhook (Slack/Teams)
"""

import os
import smtplib
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from pathlib import Path

# ── Konfigurasi (bisa override via environment variable) ──────
SMTP_HOST     = os.getenv("SMTP_HOST",     "smtp.gmail.com")
SMTP_PORT     = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER     = os.getenv("SMTP_USER",     "your_email@gmail.com")
SMTP_PASS     = os.getenv("SMTP_PASS",     "your_app_password")
NOTIFY_TARGET = os.getenv("NOTIFY_TO",     "supervisor@company.com")
WEBHOOK_URL   = os.getenv("WEBHOOK_URL",   "")   # Slack/Teams webhook
TELEGRAM_TOKEN= os.getenv("TELEGRAM_TOKEN", "")
TELEGRAM_CHAT = os.getenv("TELEGRAM_CHAT_ID", "")


def send_notification(violation_types: list, image_path: str = None) -> bool:
    """
    Kirim notifikasi pelanggaran.
    Mencoba email → webhook → desktop (berurutan).
    Mengembalikan True jika berhasil via salah satu metode.
    """
    ts      = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    types_str = ", ".join(violation_types)
    subject = f"[APD ALERT] Pelanggaran K3 – {types_str} – {ts}"
    body    = (
        f"⚠️  PELANGGARAN APD TERDETEKSI\n\n"
        f"Waktu      : {ts}\n"
        f"Jenis APD  : {types_str}\n"
        f"Gambar bukti: {image_path or 'N/A'}\n\n"
        f"Harap segera tindaklanjuti.\n"
        f"— Sistem Monitoring K3 Otomatis, PT IEI"
    )

    sent = False
    sent = sent or _send_telegram(subject, body, image_path)
    sent = sent or _send_email(subject, body, image_path)
    sent = sent or _send_webhook(subject, body)
    _desktop_notify(types_str)   # selalu tampilkan di terminal
    return sent


# ─────────────────────────────────────────────────────────────
def _send_telegram(subject: str, body: str, image_path: str = None) -> bool:
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT:
        return False
    try:
        import requests
        message = f"<b>{subject}</b>\n\n{body}"
        if image_path and Path(image_path).exists():
            url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"
            with open(image_path, "rb") as f:
                res = requests.post(
                    url, 
                    data={"chat_id": TELEGRAM_CHAT, "caption": message, "parse_mode": "HTML"},
                    files={"photo": f},
                    timeout=10
                )
        else:
            url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
            res = requests.post(
                url, 
                data={"chat_id": TELEGRAM_CHAT, "text": message, "parse_mode": "HTML"},
                timeout=10
            )
        if res.status_code == 200:
            print("[NOTIF] Telegram terkirim.")
            return True
        else:
            print(f"[NOTIF][WARN] Telegram gagal: {res.text}")
            return False
    except Exception as e:
        print(f"[NOTIF][WARN] Telegram error: {e}")
        return False

def _send_email(subject: str, body: str, image_path: str = None) -> bool:
    if not SMTP_USER or SMTP_USER == "your_email@gmail.com":
        return False   # belum dikonfigurasi

    try:
        msg = MIMEMultipart()
        msg["From"]    = SMTP_USER
        msg["To"]      = NOTIFY_TARGET
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))

        # Lampirkan gambar bukti jika tersedia
        if image_path and Path(image_path).exists():
            with open(image_path, "rb") as f:
                img = MIMEImage(f.read())
                img.add_header("Content-Disposition", "attachment",
                               filename=Path(image_path).name)
                msg.attach(img)

        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=5) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASS)
            server.sendmail(SMTP_USER, NOTIFY_TARGET, msg.as_string())

        print(f"[NOTIF] Email terkirim ke {NOTIFY_TARGET}")
        return True

    except Exception as e:
        print(f"[NOTIF][WARN] Email gagal: {e}")
        return False


def _send_webhook(subject: str, body: str) -> bool:
    """Kirim ke Slack/MS Teams via Incoming Webhook."""
    if not WEBHOOK_URL:
        return False
    try:
        import urllib.request, json as _json
        payload = _json.dumps({"text": f"*{subject}*\n```{body}```"}).encode()
        req = urllib.request.Request(
            WEBHOOK_URL, data=payload,
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=5):
            pass
        print("[NOTIF] Webhook terkirim.")
        return True
    except Exception as e:
        print(f"[NOTIF][WARN] Webhook gagal: {e}")
        return False


def _desktop_notify(types_str: str):
    """Print alert ke terminal – selalu berhasil."""
    bar = "!" * 55
    print(f"\n{bar}")
    print(f"  ⚠  PELANGGARAN APD: {types_str}")
    print(f"{bar}\n")
