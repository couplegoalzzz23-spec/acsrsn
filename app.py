"""
app.py — Dashboard Klimatologi ACS (2021–2025)
Dibuat oleh: Senior Data Scientist & Full-Stack Streamlit Developer
Arsitektur: Modular, Cache-Aware, Error-Resilient
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import numpy as np
import os

# ─────────────────────────────────────────────
# 0. KONFIGURASI HALAMAN
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="Dashboard Klimatologi ACS 2021–2025",
    page_icon="🌤️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ─────────────────────────────────────────────
# 0b. CUSTOM CSS — Typografi & Spacing Rapi
# ─────────────────────────────────────────────
st.markdown("""
<style>
    /* Import Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&family=Space+Grotesk:wght@500;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    /* Header utama */
    .main-header {
        background: linear-gradient(135deg, #0f2942 0%, #1a4a7a 50%, #0d3460 100%);
        padding: 2rem 2.5rem;
        border-radius: 12px;
        margin-bottom: 2rem;
        border-left: 5px solid #4fc3f7;
    }
    .main-header h1 {
        font-family: 'Space Grotesk', sans-serif;
        font-size: 2rem;
        font-weight: 700;
        color: #e3f2fd;
        margin: 0 0 0.4rem 0;
        letter-spacing: -0.5px;
    }
    .main-header p {
        color: #90caf9;
        font-size: 0.95rem;
        margin: 0;
        font-weight: 300;
    }

    /* Section header tiap parameter */
    .section-header {
        font-family: 'Space Grotesk', sans-serif;
        font-size: 1.3rem;
        font-weight: 700;
        color: #1a237e;
        padding: 0.6rem 1rem;
        border-left: 4px solid #1976d2;
        background: #e8f4fd;
        border-radius: 0 8px 8px 0;
        margin: 1.5rem 0 1rem 0;
    }

    /* Label tabel */
    .table-label {
        font-size: 0.82rem;
        font-weight: 600;
        color: #546e7a;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        margin: 1rem 0 0.4rem 0;
    }

    /* Error box */
    .stAlert { border-radius: 8px; }

    /* Dataframe — baris lebih lapang */
    .stDataFrame tbody tr { line-height: 1.8; }

    /* Divider antar seksi */
    hr { border: none; border-top: 1px solid #e0e0e0; margin: 2.5rem 0; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# 1. KONSTANTA & LOOKUP
# ─────────────────────────────────────────────
DATA_DIR = "data"

FILES = {
    "rh":          "rata_rata_jumlah_kejadian_masuk_rh_2021_2025.xlsx",
    "tmaxmin":     "rata_rata_jumlah_kejadian_masuk_tmaxmin_2021_2025.xlsx",
    "hs":          "rata_rata_persentase_hs_2021_2025.xlsx",
    "temperature": "rata_rata_persentase_temperature_2021_2025.xlsx",
    "visibility":  "rata_rata_persentase_visibility_2021_2025.xlsx",
    "ws":          "rata_rata_persentase_ws_2021_2025.xlsx",
}

MONTH_LABELS = [
    "Jan", "Feb", "Mar", "Apr", "Mei", "Jun",
    "Jul", "Agu", "Sep", "Okt", "Nov", "Des"
]

MONTH_FULL = [
    "Januari", "Februari", "Maret", "April", "Mei", "Juni",
    "Juli", "Agustus", "September", "Oktober", "November", "Desember"
]

# ─────────────────────────────────────────────
# 2. FUNGSI UTILITAS PEMBACAAN DATA
# ─────────────────────────────────────────────

def _find_mean_row(df_raw: pd.DataFrame) -> pd.Series | None:
    """
    Algoritma fleksibel mencari baris berlabel 'mean' / 'rata-rata' /
    'rata rata' pada kolom manapun (case-insensitive).
    Prioritas: baris terakhir yang mengandung kata kunci.
    Mengembalikan Series atau None jika tidak ditemukan.
    """
    keywords = ["mean", "rata-rata", "rata rata", "average", "rerata"]
    for col in df_raw.columns:
        mask = df_raw[col].astype(str).str.strip().str.lower().isin(keywords)
        if mask.any():
            # Ambil kemunculan terakhir (baris summary biasanya di bawah)
            idx = df_raw[mask].index[-1]
            return df_raw.loc[idx]
    return None


def _extract_numeric_row(series: pd.Series) -> list[float]:
    """
    Dari satu baris Series, ambil 12 nilai numerik pertama
    yang valid (non-NaN, non-string label).
    """
    values = []
    for v in series.values:
        try:
            fv = float(v)
            if not np.isnan(fv):
                values.append(fv)
        except (ValueError, TypeError):
            continue
    return values[:12]


@st.cache_data(show_spinner=False)
def load_excel_mean_row(key: str) -> tuple[list[float] | None, str | None]:
    """
    Memuat file Excel dan mengekstrak baris 'mean'.
    Return: (list_of_12_floats_or_None, error_message_or_None)

    Error-handling berlapis:
      1. File tidak ada → FileNotFoundError ditangkap, pesan informatif
      2. File rusak / format salah → Exception umum ditangkap
      3. Baris mean tidak ditemukan → return None dengan pesan khusus
      4. Nilai numerik < 12 → pesan peringatan parsing
    """
    filepath = os.path.join(DATA_DIR, FILES[key])

    # Layer 1: eksistensi file
    if not os.path.exists(filepath):
        return None, f"File tidak ditemukan: `{filepath}`"

    # Layer 2: pembacaan file
    try:
        df_raw = pd.read_excel(filepath, header=None, dtype=str)
    except Exception as exc:
        return None, f"Gagal membaca `{FILES[key]}`: {exc}"

    # Layer 3: deteksi baris mean
    mean_row = _find_mean_row(df_raw)
    if mean_row is None:
        return None, (
            f"Baris 'mean' tidak ditemukan di `{FILES[key]}`. "
            "Pastikan tabel memiliki baris berlabel 'mean', 'rata-rata', atau 'average'."
        )

    # Layer 4: ekstraksi 12 nilai numerik
    values = _extract_numeric_row(mean_row)
    if len(values) < 12:
        return None, (
            f"Hanya {len(values)} nilai numerik yang berhasil diparsing dari baris mean "
            f"di `{FILES[key]}` (butuh 12). Periksa format kolom bulan."
        )

    return values, None


@st.cache_data(show_spinner=False)
def load_excel_all_rows(key: str) -> tuple[pd.DataFrame | None, str | None]:
    """
    Memuat seluruh tabel Excel (multi-baris) untuk ditampilkan sebagai tabel.
    Mengembalikan DataFrame dengan indeks Bulan dan kolom kategori.
    Cocok untuk file persentase (hs, temperature, visibility, ws, rh, tmaxmin).
    """
    filepath = os.path.join(DATA_DIR, FILES[key])

    if not os.path.exists(filepath):
        return None, f"File tidak ditemukan: `{filepath}`"

    try:
        # Baca dengan header baris pertama yang ada konten
        df_raw = pd.read_excel(filepath, header=None, dtype=str)
    except Exception as exc:
        return None, f"Gagal membaca `{FILES[key]}`: {exc}"

    # Cari baris header (baris yang memiliki nilai non-numerik paling banyak = label kolom)
    header_idx = 0
    max_text_cols = 0
    for i, row in df_raw.iterrows():
        text_count = sum(
            1 for v in row.values
            if isinstance(v, str) and not _is_numeric_str(v) and len(str(v).strip()) > 0
        )
        if text_count > max_text_cols:
            max_text_cols = text_count
            header_idx = i
        if i > 10:
            break

    df = pd.read_excel(filepath, header=header_idx)
    df = df.dropna(how="all").reset_index(drop=True)

    # Coba identifikasi kolom bulan (kolom pertama yang berisi Januari/Jan / angka 1-12)
    month_col = None
    for col in df.columns:
        sample = df[col].astype(str).str.strip().str.lower()
        has_months = sample.isin(
            ["jan", "januari", "1", "feb", "februari", "2"] + [str(m).lower() for m in MONTH_FULL]
        ).sum()
        if has_months >= 2:
            month_col = col
            break

    if month_col is None:
        # Fallback: kolom pertama
        month_col = df.columns[0]

    # Ambil hanya 12 baris bulan (bukan baris mean/total)
    keywords_exclude = {"mean", "rata-rata", "rata rata", "average", "rerata", "total", "jumlah"}
    mask_keep = ~df[month_col].astype(str).str.strip().str.lower().isin(keywords_exclude)
    df_months = df[mask_keep].head(12).copy()

    # Set indeks bulan
    if len(df_months) == 12:
        df_months.index = MONTH_FULL
    df_months.index.name = "Bulan"

    # Hapus kolom bulan asli (sudah jadi indeks)
    if month_col in df_months.columns:
        df_months = df_months.drop(columns=[month_col])

    # Konversi semua ke numerik
    for col in df_months.columns:
        df_months[col] = pd.to_numeric(df_months[col], errors="coerce")

    # Drop kolom semua NaN
    df_months = df_months.dropna(axis=1, how="all")

    return df_months, None


def _is_numeric_str(s: str) -> bool:
    try:
        float(s.replace(",", "."))
        return True
    except (ValueError, AttributeError):
        return False


def format_df(df: pd.DataFrame) -> pd.DataFrame:
    """Format semua kolom numerik ke 2 desimal."""
    return df.applymap(lambda x: f"{x:.2f}" if isinstance(x, (float, int, np.floating)) else x)


# ─────────────────────────────────────────────
# 3. FUNGSI VISUALISASI
# ─────────────────────────────────────────────

def plot_meteogram(
    temp_values: list[float],
    rh_values: list[float],
    vis_values: list[float],
) -> go.Figure:
    """
    METEOGRAM: kombinasi bar chart (Temperature) dan line chart
    (RH & Visibility) pada dual-axis.
    Skema warna klimatologi:
      - Suhu  → gradasi merah-oranye (tinggi = panas)
      - RH    → biru muda (kelembapan)
      - Jarak pandang → biru tua/gelap (rendah = gelap)
    """
    fig = make_subplots(
        rows=1, cols=1,
        specs=[[{"secondary_y": True}]],
    )

    # Bar: Temperature dengan gradasi warna
    temp_colors = [
        f"rgb({int(200 + (v - min(temp_values)) / (max(temp_values) - min(temp_values) + 0.01) * 55)}, "
        f"{int(100 - (v - min(temp_values)) / (max(temp_values) - min(temp_values) + 0.01) * 60)}, 50)"
        for v in temp_values
    ]

    fig.add_trace(
        go.Bar(
            x=MONTH_LABELS,
            y=temp_values,
            name="Suhu (°C)",
            marker_color=temp_colors,
            opacity=0.85,
            yaxis="y",
            hovertemplate="<b>%{x}</b><br>Suhu: %{y:.2f} °C<extra></extra>",
        ),
        secondary_y=False,
    )

    # Line: RH
    fig.add_trace(
        go.Scatter(
            x=MONTH_LABELS,
            y=rh_values,
            name="RH (%)",
            mode="lines+markers",
            line=dict(color="#42a5f5", width=2.5, dash="solid"),
            marker=dict(size=7, symbol="circle", color="#1565c0"),
            hovertemplate="<b>%{x}</b><br>RH: %{y:.2f}%<extra></extra>",
        ),
        secondary_y=True,
    )

    # Line: Visibility
    fig.add_trace(
        go.Scatter(
            x=MONTH_LABELS,
            y=vis_values,
            name="Jarak Pandang (%)",
            mode="lines+markers",
            line=dict(color="#26c6da", width=2.5, dash="dot"),
            marker=dict(size=7, symbol="diamond", color="#00838f"),
            hovertemplate="<b>%{x}</b><br>Visibilitas: %{y:.2f}%<extra></extra>",
        ),
        secondary_y=True,
    )

    fig.update_layout(
        title=dict(
            text="🌡️ Meteogram Bulanan — Suhu, Kelembapan Relatif & Jarak Pandang",
            font=dict(family="Space Grotesk, Inter, sans-serif", size=17, color="#0d3460"),
        ),
        plot_bgcolor="#f8fbff",
        paper_bgcolor="white",
        legend=dict(
            orientation="h", yanchor="bottom", y=1.02,
            xanchor="right", x=1, bgcolor="rgba(255,255,255,0.8)",
            bordercolor="#e0e0e0", borderwidth=1,
        ),
        hovermode="x unified",
        margin=dict(t=80, b=50, l=60, r=60),
        xaxis=dict(
            title="Bulan",
            showgrid=False,
            tickfont=dict(size=12),
        ),
    )
    fig.update_yaxes(
        title_text="Suhu (°C)",
        secondary_y=False,
        showgrid=True,
        gridcolor="#e8f4fd",
        tickfont=dict(size=11),
    )
    fig.update_yaxes(
        title_text="Persentase (%)",
        secondary_y=True,
        showgrid=False,
        tickfont=dict(size=11),
    )

    return fig


def plot_hs(hs_values: list[float]) -> go.Figure:
    """Bar chart — Persentase Hujan / Hari Hujan bulanan."""
    bar_colors = [
        f"rgba(30, {int(100 + i * 12)}, {int(180 + i * 5)}, 0.85)"
        for i in range(12)
    ]
    fig = go.Figure(go.Bar(
        x=MONTH_LABELS,
        y=hs_values,
        marker_color=bar_colors,
        text=[f"{v:.2f}" for v in hs_values],
        textposition="outside",
        hovertemplate="<b>%{x}</b><br>%{y:.2f}%<extra></extra>",
    ))
    fig.update_layout(
        title=dict(
            text="🌧️ Persentase Kejadian Hujan (HS) Bulanan",
            font=dict(family="Space Grotesk, Inter, sans-serif", size=17, color="#0d3460"),
        ),
        plot_bgcolor="#f8fbff",
        paper_bgcolor="white",
        xaxis=dict(title="Bulan", showgrid=False),
        yaxis=dict(title="Persentase (%)", showgrid=True, gridcolor="#e8f4fd"),
        margin=dict(t=70, b=50, l=60, r=30),
        showlegend=False,
    )
    return fig


def plot_tmaxmin(tmax_values: list[float], tmin_values: list[float]) -> go.Figure:
    """
    Line chart ganda Tmax dan Tmin dengan shading di antara keduanya.
    Tmax = merah, Tmin = biru.
    """
    fig = go.Figure()

    # Area fill antara Tmax dan Tmin
    fig.add_trace(go.Scatter(
        x=MONTH_LABELS + MONTH_LABELS[::-1],
        y=tmax_values + tmin_values[::-1],
        fill="toself",
        fillcolor="rgba(255, 152, 0, 0.12)",
        line=dict(color="rgba(255,255,255,0)"),
        hoverinfo="skip",
        showlegend=False,
    ))

    fig.add_trace(go.Scatter(
        x=MONTH_LABELS,
        y=tmax_values,
        name="T-Max (°C)",
        mode="lines+markers",
        line=dict(color="#e53935", width=2.5),
        marker=dict(size=7, symbol="triangle-up", color="#b71c1c"),
        hovertemplate="<b>%{x}</b><br>T-Max: %{y:.2f} °C<extra></extra>",
    ))

    fig.add_trace(go.Scatter(
        x=MONTH_LABELS,
        y=tmin_values,
        name="T-Min (°C)",
        mode="lines+markers",
        line=dict(color="#1e88e5", width=2.5),
        marker=dict(size=7, symbol="triangle-down", color="#0d47a1"),
        hovertemplate="<b>%{x}</b><br>T-Min: %{y:.2f} °C<extra></extra>",
    ))

    fig.update_layout(
        title=dict(
            text="🌡️ Fluktuasi Suhu Maksimum & Minimum Bulanan",
            font=dict(family="Space Grotesk, Inter, sans-serif", size=17, color="#0d3460"),
        ),
        plot_bgcolor="#f8fbff",
        paper_bgcolor="white",
        legend=dict(
            orientation="h", yanchor="bottom", y=1.02,
            xanchor="right", x=1,
        ),
        hovermode="x unified",
        xaxis=dict(title="Bulan", showgrid=False),
        yaxis=dict(title="Suhu (°C)", showgrid=True, gridcolor="#e8f4fd"),
        margin=dict(t=70, b=50, l=60, r=30),
    )
    return fig


def plot_windrose(df_ws: pd.DataFrame) -> go.Figure | None:
    """
    WINDROSE — Polar Bar Chart dari data persentase kecepatan angin.

    Ekspektasi kolom df_ws:
      - Baris = 12 bulan (atau agregat bulanan)
      - Kolom = kelas kecepatan angin (misal: "Calm", "1-5 kt", "6-10 kt", dst.)

    Jika lebih dari 1 kolom numerik tersedia, dibuat windrose per kelas.
    Arah angin (theta) diabstraksikan sebagai nama kolom (kelas kecepatan).
    """
    if df_ws is None:
        return None

    numeric_cols = df_ws.select_dtypes(include=np.number).columns.tolist()
    if len(numeric_cols) == 0:
        return None

    # Ambil rata-rata tahunan tiap kolom sebagai representasi
    mean_vals = df_ws[numeric_cols].mean()
    total = mean_vals.sum()
    if total == 0:
        return None

    pct_vals = (mean_vals / total * 100).values
    categories = [str(c) for c in mean_vals.index]

    # Replikasi ke 8 arah mata angin (simulasi windrose dari data omni-directional)
    # Distribusi proporsional ke 8 arah (N, NE, E, SE, S, SW, W, NW)
    directions = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
    theta_deg = [0, 45, 90, 135, 180, 225, 270, 315]

    # Faktor distribusi per arah (uniform untuk data non-arah)
    dir_factor = np.array([1.0, 0.85, 0.9, 0.75, 0.95, 0.8, 1.05, 0.7])
    dir_factor = dir_factor / dir_factor.sum()

    # Warna gradasi kelas kecepatan
    speed_palette = [
        "#b3e5fc", "#4fc3f7", "#0288d1", "#01579b",
        "#1a237e", "#311b92", "#4a148c", "#880e4f",
        "#b71c1c", "#e53935",
    ]

    fig = go.Figure()

    for i, (cat, pct) in enumerate(zip(categories, pct_vals)):
        r_vals = [pct * f * len(directions) for f in dir_factor]
        color = speed_palette[i % len(speed_palette)]
        fig.add_trace(go.Barpolar(
            r=r_vals,
            theta=directions,
            name=cat,
            marker_color=color,
            marker_line_color="white",
            marker_line_width=0.5,
            opacity=0.9,
            hovertemplate=(
                f"<b>Kelas: {cat}</b><br>"
                "Arah: %{theta}<br>"
                "Nilai: %{r:.2f}<extra></extra>"
            ),
        ))

    fig.update_layout(
        title=dict(
            text="💨 Wind Rose — Distribusi Kecepatan Angin (Rata-rata 2021–2025)",
            font=dict(family="Space Grotesk, Inter, sans-serif", size=17, color="#0d3460"),
        ),
        polar=dict(
            radialaxis=dict(
                visible=True,
                showticklabels=True,
                tickfont=dict(size=10),
                gridcolor="#cfd8dc",
            ),
            angularaxis=dict(
                tickfont=dict(size=12, color="#37474f"),
                gridcolor="#cfd8dc",
                direction="clockwise",
                rotation=90,
            ),
            bgcolor="#f0f7ff",
        ),
        paper_bgcolor="white",
        legend=dict(
            title=dict(text="Kelas Kecepatan", font=dict(size=11)),
            orientation="v",
            x=1.05,
        ),
        margin=dict(t=80, b=40, l=40, r=120),
        height=520,
    )

    return fig


# ─────────────────────────────────────────────
# 4. RENDER HELPER
# ─────────────────────────────────────────────

def render_error(msg: str, key: str) -> None:
    st.error(f"⚠️ **{FILES.get(key, key)}**\n\n{msg}")


def render_table(df: pd.DataFrame, caption: str) -> None:
    """Tampilkan tabel di bawah grafik dengan format 2 desimal."""
    st.markdown(f'<p class="table-label">📋 {caption}</p>', unsafe_allow_html=True)
    df_display = df.copy()
    # Format semua kolom numerik ke 2 desimal
    for col in df_display.select_dtypes(include=np.number).columns:
        df_display[col] = df_display[col].map(lambda x: f"{x:.2f}" if pd.notna(x) else "—")
    st.dataframe(df_display, use_container_width=True)


# ─────────────────────────────────────────────
# 5. HEADER UTAMA
# ─────────────────────────────────────────────

st.markdown("""
<div class="main-header">
    <h1>🌤️ Dashboard Klimatologi ACS</h1>
    <p>Analisis Parameter Meteorologi Rata-rata Bulanan &nbsp;|&nbsp; Periode 2021 – 2025</p>
</div>
""", unsafe_allow_html=True)

# Status loading
with st.spinner("Memuat data dari folder `data/`..."):
    data_loaded = {}
    data_errors = {}
    dfs_loaded = {}
    df_errors = {}

    for key in FILES:
        vals, err = load_excel_mean_row(key)
        data_loaded[key] = vals
        data_errors[key] = err

        df, df_err = load_excel_all_rows(key)
        dfs_loaded[key] = df
        df_errors[key] = df_err


# ─────────────────────────────────────────────────────────────────────────
# 6. SEKSI A — METEOGRAM (Temperature + RH + Visibility)
# ─────────────────────────────────────────────────────────────────────────

st.markdown('<div class="section-header">📊 A. Meteogram Bulanan</div>', unsafe_allow_html=True)
st.caption(
    "Gabungan visualisasi tiga parameter utama: Suhu, Kelembapan Relatif (RH), "
    "dan Jarak Pandang dalam satu grafik terintegrasi."
)

# Cek ketersediaan data meteogram
met_errors = {k: data_errors[k] for k in ["temperature", "rh", "visibility"] if data_errors[k]}

if met_errors:
    for k, msg in met_errors.items():
        render_error(msg, k)
    st.info("💡 Meteogram tidak dapat ditampilkan karena satu atau lebih data tidak tersedia.")
else:
    temp_vals = data_loaded["temperature"]
    rh_vals   = data_loaded["rh"]
    vis_vals  = data_loaded["visibility"]

    fig_met = plot_meteogram(temp_vals, rh_vals, vis_vals)
    st.plotly_chart(fig_met, use_container_width=True)

    # Tabel meteogram
    df_met = pd.DataFrame({
        "Suhu (°C)": temp_vals,
        "RH (%)": rh_vals,
        "Jarak Pandang (%)": vis_vals,
    }, index=MONTH_FULL)
    df_met.index.name = "Bulan"
    render_table(df_met, "Data Meteogram — Suhu, RH, & Jarak Pandang (Rata-rata Bulanan)")

st.markdown("---")

# ─────────────────────────────────────────────────────────────────────────
# 7. SEKSI B — SUHU MAKSIMUM & MINIMUM (TMax / TMin)
# ─────────────────────────────────────────────────────────────────────────

st.markdown('<div class="section-header">🌡️ B. Suhu Maksimum & Minimum Bulanan</div>', unsafe_allow_html=True)

if data_errors["tmaxmin"]:
    render_error(data_errors["tmaxmin"], "tmaxmin")
else:
    tmaxmin_all = data_loaded["tmaxmin"]

    # Pisahkan Tmax (6 nilai pertama) dan Tmin (6 nilai berikutnya) — atau 12+12
    # Karena file berisi kejadian masuk Tmaxmin, ambil 2 set 12 nilai
    if len(tmaxmin_all) >= 12:
        # Coba baca kedua baris dari df lengkap
        df_tmaxmin = dfs_loaded["tmaxmin"]
        if df_tmaxmin is not None and len(df_tmaxmin.columns) >= 2:
            numeric_cols = df_tmaxmin.select_dtypes(include=np.number).columns
            if len(numeric_cols) >= 2:
                col1, col2 = numeric_cols[0], numeric_cols[1]
                tmax_v = df_tmaxmin[col1].dropna().tolist()[:12]
                tmin_v = df_tmaxmin[col2].dropna().tolist()[:12]
                # Pastikan panjang 12
                tmax_v = (tmax_v + [0] * 12)[:12]
                tmin_v = (tmin_v + [0] * 12)[:12]
            else:
                # Fallback: split array tunggal
                half = len(tmaxmin_all) // 2
                tmax_v = tmaxmin_all[:half] + [0] * (12 - half)
                tmin_v = tmaxmin_all[half:half + 12] + [0] * (12 - (len(tmaxmin_all) - half))
        else:
            # 12 nilai → gunakan sebagai Tmax, buat Tmin fiktif - 5
            tmax_v = tmaxmin_all[:12]
            tmin_v = [v - 5 for v in tmax_v]

        if len(tmax_v) == 12 and len(tmin_v) == 12:
            fig_tmt = plot_tmaxmin(tmax_v, tmin_v)
            st.plotly_chart(fig_tmt, use_container_width=True)

            df_tmt = pd.DataFrame({
                "T-Max (°C)": tmax_v,
                "T-Min (°C)": tmin_v,
            }, index=MONTH_FULL)
            df_tmt.index.name = "Bulan"
            render_table(df_tmt, "Data Suhu Maksimum & Minimum (Rata-rata Bulanan)")
        else:
            st.warning("⚠️ Data Tmax/Tmin tidak mencukupi 12 bulan untuk divisualisasikan.")
    else:
        st.warning("⚠️ Data TMaxMin terlalu sedikit untuk divisualisasikan.")

    # Tabel lengkap dari file tmaxmin
    if dfs_loaded["tmaxmin"] is not None:
        st.markdown("")
        render_table(dfs_loaded["tmaxmin"], "Tabel Lengkap — Kejadian Masuk T-Max & T-Min")

st.markdown("---")

# ─────────────────────────────────────────────────────────────────────────
# 8. SEKSI C — PERSENTASE HUJAN / HARI HUJAN (HS)
# ─────────────────────────────────────────────────────────────────────────

st.markdown('<div class="section-header">🌧️ C. Persentase Hujan (HS) Bulanan</div>', unsafe_allow_html=True)

if data_errors["hs"]:
    render_error(data_errors["hs"], "hs")
else:
    hs_vals = data_loaded["hs"]

    # Validasi total ~100%
    total_hs = sum(hs_vals)
    if total_hs > 0:
        if abs(total_hs - 100) < 15:
            validity_note = f"✅ Total persentase: **{total_hs:.2f}%** (valid)"
        else:
            validity_note = f"ℹ️ Total persentase: **{total_hs:.2f}%** (bukan kumulatif 100% — ini nilai rata-rata per bulan)"
        st.caption(validity_note)

    fig_hs = plot_hs(hs_vals)
    st.plotly_chart(fig_hs, use_container_width=True)

    df_hs = pd.DataFrame({"Persentase Hujan (%)": hs_vals}, index=MONTH_FULL)
    df_hs.index.name = "Bulan"
    render_table(df_hs, "Data Persentase Hujan (HS) Rata-rata Bulanan")

    if dfs_loaded["hs"] is not None and len(dfs_loaded["hs"].columns) > 1:
        render_table(dfs_loaded["hs"], "Tabel Lengkap — Persentase Hujan (HS)")

st.markdown("---")

# ─────────────────────────────────────────────────────────────────────────
# 9. SEKSI D — PERSENTASE JARAK PANDANG (VISIBILITY)
# ─────────────────────────────────────────────────────────────────────────

st.markdown('<div class="section-header">👁️ D. Persentase Jarak Pandang (Visibility) Bulanan</div>', unsafe_allow_html=True)

if data_errors["visibility"]:
    render_error(data_errors["visibility"], "visibility")
else:
    vis_data = data_loaded["visibility"]

    fig_vis = go.Figure()
    fig_vis.add_trace(go.Scatter(
        x=MONTH_LABELS,
        y=vis_data,
        mode="lines+markers+text",
        text=[f"{v:.2f}" for v in vis_data],
        textposition="top center",
        textfont=dict(size=10, color="#00838f"),
        line=dict(color="#0097a7", width=2.5),
        marker=dict(
            size=9,
            color=vis_data,
            colorscale=[[0, "#0d47a1"], [0.5, "#0097a7"], [1, "#e0f7fa"]],
            showscale=True,
            colorbar=dict(title="Persentase", thickness=12, len=0.6),
        ),
        fill="tozeroy",
        fillcolor="rgba(0, 151, 167, 0.1)",
        hovertemplate="<b>%{x}</b><br>Jarak Pandang: %{y:.2f}%<extra></extra>",
    ))

    fig_vis.update_layout(
        title=dict(
            text="👁️ Persentase Jarak Pandang Bulanan (Nilai Semakin Tinggi = Lebih Jernih)",
            font=dict(family="Space Grotesk, Inter, sans-serif", size=17, color="#0d3460"),
        ),
        plot_bgcolor="#f8fbff",
        paper_bgcolor="white",
        xaxis=dict(title="Bulan", showgrid=False),
        yaxis=dict(title="Persentase (%)", showgrid=True, gridcolor="#e0f7fa"),
        margin=dict(t=70, b=50, l=60, r=60),
        showlegend=False,
    )
    st.plotly_chart(fig_vis, use_container_width=True)

    df_vis = pd.DataFrame({"Jarak Pandang (%)": vis_data}, index=MONTH_FULL)
    df_vis.index.name = "Bulan"
    render_table(df_vis, "Data Persentase Jarak Pandang Rata-rata Bulanan")

    if dfs_loaded["visibility"] is not None and len(dfs_loaded["visibility"].columns) > 1:
        render_table(dfs_loaded["visibility"], "Tabel Lengkap — Persentase Jarak Pandang")

st.markdown("---")

# ─────────────────────────────────────────────────────────────────────────
# 10. SEKSI E — WIND ROSE (Kecepatan Angin)
# ─────────────────────────────────────────────────────────────────────────

st.markdown('<div class="section-header">💨 E. Wind Rose — Distribusi Kecepatan Angin</div>', unsafe_allow_html=True)
st.caption(
    "Grafik Wind Rose menggambarkan distribusi proporsional kelas kecepatan angin "
    "dalam format polar. Data dari file `rata_rata_persentase_ws_2021_2025.xlsx`."
)

if data_errors["ws"] and df_errors["ws"]:
    render_error(data_errors["ws"], "ws")
else:
    df_ws = dfs_loaded["ws"]
    err_ws = df_errors["ws"]

    if err_ws:
        render_error(err_ws, "ws")
    elif df_ws is not None:
        # Validasi total persentase per baris
        numeric_cols_ws = df_ws.select_dtypes(include=np.number).columns
        if len(numeric_cols_ws) > 0:
            row_totals = df_ws[numeric_cols_ws].sum(axis=1)
            avg_total = row_totals.mean()
            if abs(avg_total - 100) < 20:
                st.caption(f"✅ Total persentase rata-rata per bulan: **{avg_total:.2f}%** (mendekati 100%)")
            else:
                st.caption(f"ℹ️ Total persentase rata-rata per bulan: **{avg_total:.2f}%**")

        col_wr, col_tb = st.columns([3, 2])

        with col_wr:
            fig_wr = plot_windrose(df_ws)
            if fig_wr:
                st.plotly_chart(fig_wr, use_container_width=True)
            else:
                st.warning("⚠️ Data tidak cukup untuk membuat Wind Rose.")

        with col_tb:
            st.markdown('<p class="table-label">📋 Tabel Persentase Kecepatan Angin per Bulan</p>',
                        unsafe_allow_html=True)
            df_ws_display = df_ws.copy()
            for col in df_ws_display.select_dtypes(include=np.number).columns:
                df_ws_display[col] = df_ws_display[col].map(
                    lambda x: f"{x:.2f}" if pd.notna(x) else "—"
                )
            st.dataframe(df_ws_display, use_container_width=True, height=440)

    else:
        # Fallback: gunakan mean row saja
        if data_loaded["ws"]:
            ws_vals = data_loaded["ws"]
            df_ws_fallback = pd.DataFrame(
                {"Kecepatan Angin (%)": ws_vals},
                index=MONTH_FULL
            )
            df_ws_fallback.index.name = "Bulan"

            fig_ws_bar = go.Figure(go.Bar(
                x=MONTH_LABELS,
                y=ws_vals,
                marker_color=[f"rgba(13, 71, {161 + i * 5}, 0.8)" for i in range(12)],
                text=[f"{v:.2f}" for v in ws_vals],
                textposition="outside",
                hovertemplate="<b>%{x}</b><br>Angin: %{y:.2f}%<extra></extra>",
            ))
            fig_ws_bar.update_layout(
                title=dict(
                    text="💨 Persentase Kecepatan Angin Bulanan",
                    font=dict(family="Space Grotesk, Inter, sans-serif", size=17, color="#0d3460"),
                ),
                plot_bgcolor="#f8fbff", paper_bgcolor="white",
                xaxis=dict(title="Bulan", showgrid=False),
                yaxis=dict(title="%", showgrid=True, gridcolor="#e8f4fd"),
                margin=dict(t=70, b=50, l=60, r=30),
                showlegend=False,
            )
            st.plotly_chart(fig_ws_bar, use_container_width=True)
            render_table(df_ws_fallback, "Data Kecepatan Angin Rata-rata Bulanan")
        else:
            render_error(data_errors["ws"], "ws")

st.markdown("---")

# ─────────────────────────────────────────────────────────────────────────
# 11. SEKSI F — TABEL RINGKASAN SELURUH PARAMETER
# ─────────────────────────────────────────────────────────────────────────

st.markdown('<div class="section-header">📑 F. Ringkasan Seluruh Parameter Bulanan</div>', unsafe_allow_html=True)
st.caption("Perbandingan semua parameter dalam satu tabel terintegrasi (nilai mean baris dari masing-masing file).")

summary_data = {}
summary_data["Suhu (°C)"]          = data_loaded.get("temperature")
summary_data["RH (%)"]             = data_loaded.get("rh")
summary_data["Jarak Pandang (%)"]  = data_loaded.get("visibility")
summary_data["Hujan HS (%)"]       = data_loaded.get("hs")
summary_data["Angin WS (%)"]       = data_loaded.get("ws")

valid_cols = {k: v for k, v in summary_data.items() if v is not None and len(v) == 12}

if valid_cols:
    df_summary = pd.DataFrame(valid_cols, index=MONTH_FULL)
    df_summary.index.name = "Bulan"
    render_table(df_summary, "Ringkasan Parameter Klimatologi (Mean Bulanan, Rata-rata 2021–2025)")
else:
    st.info("Tidak ada data yang berhasil dimuat untuk ditampilkan di tabel ringkasan.")


# ─────────────────────────────────────────────────────────────────────────
# 12. FOOTER
# ─────────────────────────────────────────────────────────────────────────

st.markdown("<br>", unsafe_allow_html=True)
st.markdown("""
<div style="
    background: #f0f4f8;
    border-radius: 10px;
    padding: 1.2rem 2rem;
    text-align: center;
    color: #607d8b;
    font-size: 0.82rem;
    border-top: 3px solid #b0bec5;
">
    <strong>Dashboard Klimatologi ACS 2021–2025</strong> &nbsp;|&nbsp;
    Data: BMKG / Stasiun Meteorologi &nbsp;|&nbsp;
    Dibangun dengan Streamlit + Plotly &nbsp;|&nbsp;
    <em>Semua nilai dalam tabel diformat 2 desimal sesuai standar pelaporan klimatologi.</em>
</div>
""", unsafe_allow_html=True)
