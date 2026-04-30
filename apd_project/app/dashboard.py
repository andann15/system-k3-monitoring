"""
app/dashboard.py – Dashboard Monitoring APD K3
Jalankan: streamlit run app/dashboard.py

Proyek Capstone: Deteksi APD Otomatis
Kelompok 04 – Universitas Brawijaya 2026
"""

import os
import sys
import json
import datetime
import time
from pathlib import Path

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Tambahkan root project ke sys.path agar bisa import utils
sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.violation_handler import ViolationHandler

# ──────────────────────────────────────────────────────────────
# KONFIGURASI
# ──────────────────────────────────────────────────────────────
CAPTURE_DIR   = os.getenv("CAPTURE_DIR", "captures")
VIOLATION_CLS = ["no helmet", "no vest", "no boots"]
APD_LABELS    = {
    "no helmet" : "🔴 Helm",
    "no vest"   : "🔴 Rompi",
    "no boots"  : "🔴 Sepatu Safety",
}

st.set_page_config(
    page_title = "APD Monitor K3 – Kelompok 04",
    page_icon  = "🦺",
    layout     = "wide",
)


# ──────────────────────────────────────────────────────────────
# LOAD DATA
# ──────────────────────────────────────────────────────────────
@st.cache_data(ttl=10)
def load_violations():
    log_path = Path(CAPTURE_DIR) / "violation_log.json"
    if not log_path.exists():
        return pd.DataFrame()
    try:
        data = json.loads(log_path.read_text())
        if not data:
            return pd.DataFrame()
        df = pd.DataFrame(data)
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        df["date"]      = df["timestamp"].dt.date
        df["hour"]      = df["timestamp"].dt.hour
        return df
    except Exception:
        return pd.DataFrame()


# ──────────────────────────────────────────────────────────────
# HEADER
# ──────────────────────────────────────────────────────────────
st.title("🦺 Sistem Monitoring Kepatuhan APD – K3 Real-Time")
st.caption("PT Indonesia Epson Industry (IEI) | Kelompok 04 – Universitas Brawijaya 2026")

st.divider()

# ──────────────────────────────────────────────────────────────
# SIDEBAR FILTER
# ──────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("⚙️ Filter & Pengaturan")
    auto_refresh = st.toggle("Auto Refresh (10 detik)", value=True)
    st.divider()

    date_range = st.date_input(
        "Rentang Tanggal",
        value=(datetime.date.today() - datetime.timedelta(days=7), datetime.date.today()),
    )
    st.divider()

    viol_filter = st.multiselect(
        "Jenis Pelanggaran",
        options=VIOLATION_CLS,
        default=VIOLATION_CLS,
        format_func=lambda x: APD_LABELS.get(x, x),
    )
    st.divider()
    st.info("📁 Gambar bukti disimpan di:\n`" + CAPTURE_DIR + "/`")

# ──────────────────────────────────────────────────────────────
# LOAD & FILTER DATA
# ──────────────────────────────────────────────────────────────
df_all = load_violations()

if df_all.empty:
    st.warning("⚠️ Belum ada data pelanggaran. Jalankan deteksi terlebih dahulu.")
    st.code("python scripts/detect_realtime.py --weights best.pt")
    st.stop()

# Terapkan filter tanggal
if len(date_range) == 2:
    start, end = date_range
    df = df_all[(df_all["date"] >= start) & (df_all["date"] <= end)].copy()
else:
    df = df_all.copy()

# Filter jenis pelanggaran
if viol_filter:
    mask = df["violations"].apply(
        lambda v: any(vt in viol_filter for vt in v) if isinstance(v, list) else False
    )
    df = df[mask]


# ──────────────────────────────────────────────────────────────
# KPI CARDS
# ──────────────────────────────────────────────────────────────
col1, col2, col3, col4 = st.columns(4)

total_viol = len(df)
today_viol = len(df[df["date"] == datetime.date.today()])

# Hitung per jenis
helm_cnt  = df["violations"].apply(lambda v: "no helmet" in v if isinstance(v, list) else False).sum()
vest_cnt  = df["violations"].apply(lambda v: "no vest"   in v if isinstance(v, list) else False).sum()
boots_cnt = df["violations"].apply(lambda v: "no boots"  in v if isinstance(v, list) else False).sum()

col1.metric("📊 Total Pelanggaran", total_viol)
col2.metric("📅 Hari Ini",          today_viol)
col3.metric("⛑️ Tanpa Helm",        int(helm_cnt))
col4.metric("🦺 Tanpa Rompi/Sepatu", int(vest_cnt + boots_cnt))

st.divider()

# ──────────────────────────────────────────────────────────────
# CHARTS
# ──────────────────────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs(["📈 Tren Waktu", "🍕 Distribusi APD", "🖼️ Bukti Visual"])

with tab1:
    daily = df.groupby("date").size().reset_index(name="jumlah")
    if not daily.empty:
        fig = px.bar(
            daily, x="date", y="jumlah",
            title="Jumlah Pelanggaran per Hari",
            labels={"date": "Tanggal", "jumlah": "Jumlah Pelanggaran"},
            color="jumlah",
            color_continuous_scale="Reds",
        )
        fig.update_layout(showlegend=False, coloraxis_showscale=False)
        st.plotly_chart(fig, use_container_width=True)

        # Tren per jam
        hourly = df.groupby("hour").size().reset_index(name="jumlah")
        fig2 = px.line(
            hourly, x="hour", y="jumlah",
            title="Distribusi Pelanggaran per Jam",
            labels={"hour": "Jam", "jumlah": "Jumlah"},
            markers=True,
        )
        fig2.update_traces(line_color="#e74c3c")
        st.plotly_chart(fig2, use_container_width=True)
    else:
        st.info("Tidak ada data di rentang tanggal yang dipilih.")

with tab2:
    counts = {
        "Tanpa Helm"  : int(helm_cnt),
        "Tanpa Rompi" : int(vest_cnt),
        "Tanpa Sepatu": int(boots_cnt),
    }
    pie_df = pd.DataFrame(list(counts.items()), columns=["APD", "Jumlah"])
    pie_df = pie_df[pie_df["Jumlah"] > 0]
    if not pie_df.empty:
        fig = px.pie(
            pie_df, names="APD", values="Jumlah",
            title="Proporsi Jenis Pelanggaran APD",
            color_discrete_sequence=["#e74c3c", "#e67e22", "#f1c40f"],
            hole=0.4,
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Belum ada data distribusi.")

with tab3:
    st.subheader("Bukti Visual Pelanggaran Terbaru")
    recent = df.tail(20).iloc[::-1]
    for _, row in recent.iterrows():
        img_path = row.get("image_path", "")
        if img_path and Path(img_path).exists():
            viol_str = ", ".join(row["violations"]) if isinstance(row["violations"], list) else "-"
            ts_str   = row["timestamp"].strftime("%Y-%m-%d %H:%M:%S")
            with st.expander(f"🔴 {ts_str}  –  {viol_str}"):
                st.image(img_path, caption=viol_str, use_container_width=True)

# ──────────────────────────────────────────────────────────────
# TABEL RIWAYAT
# ──────────────────────────────────────────────────────────────
st.divider()
st.subheader("📋 Riwayat Pelanggaran")

display_df = df[["timestamp", "violations", "image_path"]].copy()
display_df["timestamp"]  = display_df["timestamp"].dt.strftime("%Y-%m-%d %H:%M:%S")
display_df["violations"] = display_df["violations"].apply(
    lambda v: ", ".join(v) if isinstance(v, list) else str(v)
)
display_df = display_df.rename(columns={
    "timestamp"  : "Waktu Kejadian",
    "violations" : "Jenis Pelanggaran",
    "image_path" : "Path Bukti",
})

st.dataframe(display_df.iloc[::-1].reset_index(drop=True), use_container_width=True)

# Download CSV
csv = display_df.to_csv(index=False).encode("utf-8")
st.download_button(
    label     = "⬇️ Download Laporan CSV",
    data      = csv,
    file_name = f"laporan_apd_{datetime.date.today()}.csv",
    mime      = "text/csv",
)

# ──────────────────────────────────────────────────────────────
# AUTO REFRESH
# ──────────────────────────────────────────────────────────────
if auto_refresh:
    time.sleep(10)
    st.rerun()
