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
    "no helmet" : "Tanpa Helm",
    "no vest"   : "Tanpa Rompi",
    "no boots"  : "Tanpa Sepatu",
}

st.set_page_config(
    page_title = "APD Monitor K3 – Kelompok 04",
    page_icon  = "🦺",
    layout     = "wide",
)

# ──────────────────────────────────────────────────────────────
# LOGIN SYSTEM
# ──────────────────────────────────────────────────────────────
DASHBOARD_PASS = os.getenv("DASHBOARD_PASS", "admin123")

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.title("🔒 Login Sistem Monitoring K3")
    st.caption("Silakan masukkan kata sandi administrator untuk mengakses dashboard.")
    
    with st.form("login_form"):
        pwd = st.text_input("Password", type="password")
        submit = st.form_submit_button("Login")
        
        if submit:
            if pwd == DASHBOARD_PASS:
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("Password salah! Akses ditolak.")
    st.stop()


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
# Inject Custom CSS for Premium Look
st.markdown("""
<style>
    /* Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@400;600;700;800&family=Inter:wght@400;500;600;700&display=swap');
    
    /* Main App Background & Fonts */
    .stApp {
        font-family: 'Inter', sans-serif;
    }
    
    /* Minimize whitespace */
    .block-container {
        padding-top: 1.5rem !important;
        padding-bottom: 1rem !important;
        padding-left: 2rem !important;
        padding-right: 2rem !important;
    }
    div[data-testid="stVerticalBlock"] > div {
        padding-bottom: 0px !important;
    }
    
    /* Card Container */
    .k3-card {
        background: rgba(30, 41, 59, 0.45);
        backdrop-filter: blur(8px);
        -webkit-backdrop-filter: blur(8px);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 16px;
        padding: 20px;
        box-shadow: 0 4px 20px 0 rgba(0, 0, 0, 0.15);
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        margin-bottom: 15px;
    }
    .k3-card:hover {
        transform: translateY(-3px);
        border-color: rgba(239, 68, 68, 0.4);
        box-shadow: 0 8px 30px 0 rgba(239, 68, 68, 0.1);
    }
    
    /* Card Title */
    .k3-card-title {
        font-size: 13px;
        color: #9ca3af;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 6px;
    }
    
    /* Card Value */
    .k3-card-value {
        font-size: 32px;
        font-weight: 800;
        margin: 2px 0;
    }
    
    /* Card Desc */
    .k3-card-desc {
        font-size: 11px;
        color: #6b7280;
    }
    
    /* Badges */
    .badge {
        display: inline-block;
        padding: 4px 10px;
        font-size: 10px;
        font-weight: 700;
        border-radius: 12px;
        margin-right: 5px;
        text-transform: uppercase;
        letter-spacing: 0.03em;
    }
    .badge-viol {
        background-color: rgba(239, 68, 68, 0.15);
        color: #f87171;
        border: 1px solid rgba(239, 68, 68, 0.3);
    }
    
    /* Header Gradient */
    .header-banner {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
        border: 1px solid rgba(255, 255, 255, 0.08);
        padding: 16px 24px;
        border-radius: 16px;
        margin-bottom: 15px;
        box-shadow: 0 4px 20px 0 rgba(0, 0, 0, 0.2);
    }
    .header-banner h1 {
        font-size: 24px !important;
        margin-bottom: 2px !important;
    }

    /* Tabs Styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 40px;
        white-space: pre-wrap;
        background-color: rgba(30, 41, 59, 0.3);
        border-radius: 8px;
        color: #9ca3af;
        font-weight: 600;
        border: 1px solid rgba(255, 255, 255, 0.05);
        padding: 8px 16px;
        transition: all 0.2s ease;
    }
    .stTabs [data-baseweb="tab"]:hover {
        background-color: rgba(30, 41, 59, 0.6);
        color: #ffffff;
    }
    .stTabs [aria-selected="true"] {
        background-color: rgba(59, 130, 246, 0.2) !important;
        border-color: rgba(59, 130, 246, 0.5) !important;
        color: #3b82f6 !important;
    }
    
    /* Style the container borders to look like cards */
    div[data-testid="stVerticalBlockBorder"] {
        background: rgba(30, 41, 59, 0.45) !important;
        backdrop-filter: blur(8px) !important;
        -webkit-backdrop-filter: blur(8px) !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        border-radius: 16px !important;
        padding: 15px !important;
        box-shadow: 0 4px 20px 0 rgba(0, 0, 0, 0.15) !important;
        transition: all 0.3s ease !important;
    }
    div[data-testid="stVerticalBlockBorder"]:hover {
        border-color: rgba(239, 68, 68, 0.4) !important;
        box-shadow: 0 8px 30px 0 rgba(239, 68, 68, 0.1) !important;
        transform: translateY(-2px);
    }

    /* Sidebar Button Styling */
    div[data-testid="stSidebar"] button {
        background-color: transparent !important;
        border: none !important;
        border-radius: 10px !important;
        color: #9ca3af !important;
        font-family: 'Outfit', sans-serif !important;
        font-weight: 600 !important;
        font-size: 15px !important;
        padding: 12px 18px !important;
        height: 48px !important;
        text-align: left !important;
        justify-content: flex-start !important;
        transition: all 0.2s ease !important;
        margin-bottom: 8px !important;
        box-shadow: none !important;
    }
    div[data-testid="stSidebar"] button:hover {
        background-color: rgba(255, 255, 255, 0.05) !important;
        color: #ffffff !important;
        border: none !important;
    }
    div[data-testid="stSidebar"] button[kind="primary"] {
        background-color: rgba(59, 130, 246, 0.15) !important;
        color: #3b82f6 !important;
        border: none !important;
        box-shadow: none !important;
    }
    div[data-testid="stSidebar"] button[kind="primary"]:hover {
        background-color: rgba(59, 130, 246, 0.22) !important;
        color: #60a5fa !important;
        border: none !important;
    }
    
    /* Divider spacing */
    hr {
        margin-top: 10px !important;
        margin-bottom: 15px !important;
    }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="header-banner">
    <h1 style="color: white; margin: 0; font-size: 28px; font-weight: 800; font-family: 'Outfit', sans-serif;">Sistem Monitoring Kepatuhan APD</h1>
    <p style="color: #94a3b8; margin: 5px 0 0 0; font-size: 14px;">PT Indonesia Epson Industry (IEI) | Kelompok 04 – Universitas Brawijaya 2026</p>
</div>
""", unsafe_allow_html=True)

# Initialize page state
if "current_page" not in st.session_state:
    st.session_state.current_page = "Dashboard Utama"

# ──────────────────────────────────────────────────────────────
# SIDEBAR
# ──────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style="text-align: center; margin-top: -15px; margin-bottom: 15px;">
        <h3 style="margin: 0; color: #ffffff; font-family: 'Outfit', sans-serif; font-size: 14px; letter-spacing: 0.05em;">MENU NAVIGASI</h3>
    </div>
    """, unsafe_allow_html=True)
    
    if st.session_state.current_page == "Dashboard Utama":
        btn1_type = "primary"
        btn2_type = "secondary"
    else:
        btn1_type = "secondary"
        btn2_type = "primary"
        
    if st.button("Dashboard Utama", type=btn1_type, use_container_width=True):
        st.session_state.current_page = "Dashboard Utama"
        st.rerun()
        
    if st.button("Riwayat Pelanggaran", type=btn2_type, use_container_width=True):
        st.session_state.current_page = "Riwayat Pelanggaran"
        st.rerun()
    
    st.divider()
    
    st.header("Filter & Pengaturan")
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
    st.info("Gambar bukti disimpan di:\n`" + CAPTURE_DIR + "/`")

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
# MAIN NAVIGATION ROUTING
# ──────────────────────────────────────────────────────────────
if st.session_state.current_page == "Dashboard Utama":
    # ──────────────────────────────────────────────────────────────
    # KPI CARDS
    # ──────────────────────────────────────────────────────────────
    total_viol = len(df)
    today_viol = len(df[df["date"] == datetime.date.today()])

    helm_cnt  = df["violations"].apply(lambda v: "no helmet" in v if isinstance(v, list) else False).sum()
    vest_cnt  = df["violations"].apply(lambda v: "no vest"   in v if isinstance(v, list) else False).sum()
    boots_cnt = df["violations"].apply(lambda v: "no boots"  in v if isinstance(v, list) else False).sum()

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f'<div class="k3-card"><div class="k3-card-title">📊 Total Pelanggaran</div><div class="k3-card-value" style="color: #f87171;">{total_viol}</div></div>', unsafe_allow_html=True)
    with col2:
        st.markdown(f'<div class="k3-card"><div class="k3-card-title">📅 Hari Ini</div><div class="k3-card-value" style="color: #fb923c;">{today_viol}</div></div>', unsafe_allow_html=True)
    with col3:
        st.markdown(f'<div class="k3-card"><div class="k3-card-title">⛑️ Tanpa Helm</div><div class="k3-card-value" style="color: #facc15;">{int(helm_cnt)}</div></div>', unsafe_allow_html=True)
    with col4:
        st.markdown(f'<div class="k3-card"><div class="k3-card-title">🦺 Tanpa Rompi / Sepatu</div><div class="k3-card-value" style="color: #c084fc;">{int(vest_cnt + boots_cnt)}</div></div>', unsafe_allow_html=True)

    # ──────────────────────────────────────────────────────────────
    # CHARTS & VISUAL TABS
    # ──────────────────────────────────────────────────────────────
    tab1, tab2, tab3 = st.tabs(["Tren Waktu", "Analisis APD", "Bukti Visual"])

    with tab1:
        daily = df.groupby("date").size().reset_index(name="jumlah")
        if not daily.empty:
            chart_col1, chart_col2 = st.columns(2)
            with chart_col1:
                with st.container(border=True):
                    fig = px.bar(daily, x="date", y="jumlah", color="jumlah", color_continuous_scale="Reds")
                    fig.update_layout(
                        showlegend=False,
                        coloraxis_showscale=False,
                        height=360,
                        margin=dict(l=15, r=15, t=55, b=15),
                        paper_bgcolor="rgba(0,0,0,0)",
                        plot_bgcolor="rgba(0,0,0,0)",
                        font=dict(family="'Inter', sans-serif", color="#9ca3af"),
                        title=dict(
                            text="Pelanggaran per Hari",
                            font=dict(family="'Outfit', sans-serif", size=16, color="#ffffff"),
                            x=0.0,
                            y=0.95
                        ),
                        xaxis=dict(showgrid=False, color="#9ca3af"),
                        yaxis=dict(gridcolor="rgba(255,255,255,0.05)", color="#9ca3af")
                    )
                    st.plotly_chart(fig, use_container_width=True)
            with chart_col2:
                with st.container(border=True):
                    hourly = df.groupby("hour").size().reset_index(name="jumlah")
                    fig2 = px.line(hourly, x="hour", y="jumlah", markers=True)
                    fig2.update_traces(line_color="#e74c3c")
                    fig2.update_layout(
                        height=360,
                        margin=dict(l=15, r=15, t=55, b=15),
                        paper_bgcolor="rgba(0,0,0,0)",
                        plot_bgcolor="rgba(0,0,0,0)",
                        font=dict(family="'Inter', sans-serif", color="#9ca3af"),
                        title=dict(
                            text="Pelanggaran per Jam",
                            font=dict(family="'Outfit', sans-serif", size=16, color="#ffffff"),
                            x=0.0,
                            y=0.95
                        ),
                        xaxis=dict(showgrid=False, color="#9ca3af"),
                        yaxis=dict(gridcolor="rgba(255,255,255,0.05)", color="#9ca3af")
                    )
                    st.plotly_chart(fig2, use_container_width=True)
        else:
            st.info("Tidak ada data tersedia.")

    with tab2:
        with st.container(border=True):
            counts = {"Tanpa Helm": int(helm_cnt), "Tanpa Rompi": int(vest_cnt), "Tanpa Sepatu": int(boots_cnt)}
            pie_df = pd.DataFrame(list(counts.items()), columns=["APD", "Jumlah"])
            pie_df = pie_df[pie_df["Jumlah"] > 0]
            if not pie_df.empty:
                fig = px.pie(pie_df, names="APD", values="Jumlah", hole=0.4, color_discrete_sequence=["#e74c3c", "#e67e22", "#f1c40f"])
                fig.update_layout(
                    height=360,
                    margin=dict(l=15, r=15, t=55, b=15),
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    font=dict(family="'Inter', sans-serif", color="#9ca3af"),
                    title=dict(
                        text="Proporsi Jenis Pelanggaran",
                        font=dict(family="'Outfit', sans-serif", size=16, color="#ffffff"),
                        x=0.0,
                        y=0.95
                    ),
                    legend=dict(
                        font=dict(color="#9ca3af"),
                        orientation="h",
                        yanchor="bottom",
                        y=-0.2,
                        xanchor="center",
                        x=0.5
                    )
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Belum ada data.")

    with tab3:
        st.subheader("Bukti Visual Pelanggaran Terbaru")
        recent = df.tail(12).iloc[::-1] # Ambil 12 data terakhir untuk galeri
        if not recent.empty:
            cols = st.columns(3)
            for idx, (_, row) in enumerate(recent.iterrows()):
                col_target = cols[idx % 3]
                img_path = row.get("image_path", "")
                viol_list = row["violations"]
                ts_str   = row["timestamp"].strftime("%Y-%m-%d %H:%M:%S")
                area     = row.get("area", "Area Kerja")
                camera   = row.get("camera", "Kamera 1")
                conf     = row.get("confidence", 0.0)
                
                with col_target:
                    with st.container(border=True):
                        if img_path and Path(img_path).exists():
                            st.image(img_path, use_container_width=True)
                        else:
                            st.markdown("""
                            <div style="background-color: rgba(30, 41, 59, 0.5); height: 180px; display: flex; align-items: center; justify-content: center; border-radius: 8px; border: 1px dashed rgba(255,255,255,0.1); margin-bottom: 10px;">
                                <span style="color: #6b7280; font-size: 14px;">📷 Gambar tidak tersedia</span>
                            </div>
                            """, unsafe_allow_html=True)
                        
                        badges_html = "".join([f'<span class="badge badge-viol">{v}</span>' for v in viol_list])
                        
                        st.markdown(f"""
                        <div style="margin-top: 5px;">
                            <div style="font-size: 11px; color: #9ca3af; font-weight: 500;">
                                {area} &bull; {camera}
                            </div>
                            <div style="font-size: 13px; font-weight: 700; color: #ffffff; margin: 4px 0;">
                                {ts_str}
                            </div>
                            <div style="margin: 6px 0;">
                                {badges_html}
                            </div>
                            <div style="font-size: 12px; color: #f87171; font-weight: 600;">
                                Skor Akurasi: {conf*100:.1f}%
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
        else:
            st.info("Belum ada bukti visual pelanggaran.")

else:
    # Riwayat Pelanggaran Page
    st.subheader("Riwayat Pelanggaran Lengkap")
    
    with st.container(border=True):
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
        
        st.dataframe(display_df.iloc[::-1].reset_index(drop=True), use_container_width=True, height=400)
        
        # Download CSV
        csv = display_df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label     = "Download Laporan CSV",
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
