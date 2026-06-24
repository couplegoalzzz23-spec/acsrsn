import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import numpy as np
import io
import os

# ==========================================
# 1. PAGE CONFIGURATION & INITIALIZATION
# ==========================================
st.set_page_config(
    page_title="Dashboard Meteorologi Interaktif (2021-2025)",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Konten CSS Kustom untuk Mempercantik UI
st.markdown("""
    <style>
    .main-title { font-size: 32px; font-weight: bold; color: #1E3A8A; margin-bottom: 5px; }
    .sub-title { font-size: 16px; color: #4B5563; margin-bottom: 20px; }
    </style>
""", unsafe_allow_html=True)

DATA_DIR = "data_acsrsn"
MONTHS = [
    'JANUARY', 'FEBRUARY', 'MARCH', 'APRIL', 'MAY', 'JUNE', 
    'JULY', 'AUGUST', 'SEPTEMBER', 'OCTOBER', 'NOVEMBER', 'DECEMBER'
]

# ==========================================
# 2. ROBUST DATA LOADERS (WITH CACHING)
# ==========================================

def clean_numeric_dataframe(df, exclude_cols=['DATE']):
    """Membersihkan whitespace dan mengonversi format koma/string ke float secara aman"""
    for col in df.columns:
        if col not in exclude_cols:
            df[col] = df[col].astype(str).str.replace(',', '.').str.replace(r'[^\d\.\-]', '', regex=True)
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0.0)
    return df

@st.cache_data
def load_t_or_rh_data(filename, is_temp=True):
    filepath = os.path.join(DATA_DIR, filename)
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"File {filename} tidak ditemukan di folder '{DATA_DIR}'.")
    
    # Membaca data mentah tanpa header terlebih dahulu
    raw_df = pd.read_csv(filepath, header=None)
    suffix = "TEMPERATURE" if is_temp else "RH"
    clean_cols = ['DATE', '0', '3', '6', '9', '12', '15', '18', '21', 'DAILY MEAN', f'{suffix} MAX', f'{suffix} MIN']
    
    # Mengambil baris data utama (asumsi baris 0 dan 1 adalah gabungan header asli)
    data_df = raw_df.iloc[2:].copy()
    
    # Ambil hanya 12 kolom pertama untuk menghindari eror kolom Unnamed ekstra akibat koma gantung
    data_df = data_df.iloc[:, :12]
    data_df.columns = clean_cols
    
    data_df['DATE'] = data_df['DATE'].astype(str).str.strip().str.upper()
    data_df = data_df[data_df['DATE'].isin(MONTHS)]
    
    return clean_numeric_dataframe(data_df)

@st.cache_data
def load_wind_data(filename):
    filepath = os.path.join(DATA_DIR, filename)
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"File {filename} tidak ditemukan di folder '{DATA_DIR}'.")
        
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        lines = f.readlines()
        
    dir_lines = []
    speed_lines = []
    is_speed_section = False
    
    for line in lines:
        if "Kecepatan Angin Bulanan (%)" in line or "Kecepatan Angin Bulanan" in line:
            is_speed_section = True
            continue
        if not is_speed_section:
            dir_lines.append(line)
        else:
            speed_lines.append(line)
            
    # Parsing Tabel Arah Angin (Bagian Atas)
    dir_header_idx = 0
    for i, line in enumerate(dir_lines):
        if 'DATE' in line and 'CALM' in line:
            dir_header_idx = i
            break
    df_dir = pd.read_csv(io.StringIO("".join(dir_lines[dir_header_idx:])))
    df_dir.columns = [c.strip() for c in df_dir.columns]
    
    # Buang kolom sampah Unnamed jika ada
    df_dir = df_dir.loc[:, ~df_dir.columns.str.contains('^Unnamed')]
    df_dir['DATE'] = df_dir['DATE'].astype(str).str.strip().str.upper()
    df_dir = df_dir[df_dir['DATE'].isin(MONTHS)]
    df_dir = clean_numeric_dataframe(df_dir)
    
    # Parsing Tabel Kecepatan Angin (Bagian Bawah)
    speed_header_idx = 0
    for i, line in enumerate(speed_lines):
        if 'DATE' in line and 'CALM' in line:
            speed_header_idx = i
            break
    df_speed = pd.read_csv(io.StringIO("".join(speed_lines[speed_header_idx:])))
    df_speed.columns = [c.strip() for c in df_speed.columns]
    
    # Buang kolom sampah Unnamed jika ada
    df_speed = df_speed.loc[:, ~df_speed.columns.str.contains('^Unnamed')]
    df_speed['DATE'] = df_speed['DATE'].astype(str).str.strip().str.upper()
    df_speed = df_speed[df_speed['DATE'].isin(MONTHS)]
    df_speed = clean_numeric_dataframe(df_speed)
    
    return df_dir, df_speed

@st.cache_data
def load_generic_freq_data(filename):
    filepath = os.path.join(DATA_DIR, filename)
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"File {filename} tidak ditemukan di folder '{DATA_DIR}'.")
    df = pd.read_csv(filepath)
    df.columns = [c.strip() for c in df.columns]
    df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
    df['DATE'] = df['DATE'].astype(str).str.strip().str.upper()
    df = df[df['DATE'].isin(MONTHS)]
    return clean_numeric_dataframe(df)

# ==========================================
# 3. GLOBAL DATA LOADING PIPELINE
# ==========================================
try:
    df_hs = load_generic_freq_data('hs_2021_2025.xlsx - Sheet1.csv')
    df_rh = load_t_or_rh_data('rh_max_min_2021_2025.xlsx - Sheet1.csv', is_temp=False)
    df_t = load_t_or_rh_data('t_max_min_2021_2025.xlsx - Sheet1.csv', is_temp=True)
    df_temp_freq = load_generic_freq_data('temperature_2021_2025.xlsx - Sheet1.csv')
    df_vis = load_generic_freq_data('visibility_2021_2025.xlsx - Sheet1.csv')
    df_wind_dir, df_wind_spd = load_wind_data('wind_2021_2025.xlsx - Sheet1.csv')
    data_loaded_successfully = True
except Exception as e:
    st.error(f"❌ Terjadi kesalahan saat memuat berkas data: {str(e)}")
    st.warning(f"Pastikan folder '{DATA_DIR}' berisi seluruh file CSV asli dari pangkalan data Anda.")
    data_loaded_successfully = False

# ==========================================
# 4. SIDEBAR NAVIGATION & FILTERS
# ==========================================
if data_loaded_successfully:
    st.sidebar.markdown("## 🧭 Navigasi Utama")
    menu = st.sidebar.selectbox(
        "Pilih Menu Tampilan:",
        ["Analisis Multivarian (Meteogram)", "Analisis Angin (Windrose)", "Distribusi Frekuensi Lainnya"]
    )
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("## 📅 Filter Waktu Climatology")
    filter_bulan = st.sidebar.selectbox(
        "Pilih Cakupan Bulan:",
        ["Semua Bulan (Gabungan/Tahunan)"] + MONTHS
    )

    # Header Utama Dashboard
    st.markdown('<div class="main-title">Dashboard Analisis Data Meteorologi (Periode 2021-2025)</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="sub-title">Menampilkan visualisasi terperinci dan interpretasi data historis lokal | Filter saat ini: <b>{filter_bulan}</b></div>', unsafe_allow_html=True)
    st.divider()

    # ==========================================
    # MENU 1: METEOGRAM & TABEL DATA
    # ==========================================
    if menu == "Analisis Multivarian (Meteogram)":
        st.subheader("📊 Meteogram Interaktif Suhu & Kelembaban Relatif (RH)")
        
        hours = ['0', '3', '6', '9', '12', '15', '18', '21']
        fig = go.Figure()
        
        if filter_bulan == "Semua Bulan (Gabungan/Tahunan)":
            fig.add_trace(go.Scatter(x=df_t['DATE'], y=df_t['DAILY MEAN'], name='Suhu Rata-rata (°C)', line=dict(color='red', width=3)))
            fig.add_trace(go.Scatter(x=df_t['DATE'], y=df_t['TEMPERATURE MAX'], name='Suhu Maksimum (°C)', line=dict(color='darkred', dash='dash')))
            fig.add_trace(go.Scatter(x=df_t['DATE'], y=df_t['TEMPERATURE MIN'], name='Suhu Minimum (°C)', line=dict(color='orange', dash='dot')))
            
            fig.add_trace(go.Scatter(x=df_rh['DATE'], y=df_rh['DAILY MEAN'], name='RH Rata-rata (%)', yaxis='y2', line=dict(color='blue', width=3)))
            fig.add_trace(go.Scatter(x=df_rh['DATE'], y=df_rh['RH MAX'], name='RH Maksimum (%)', yaxis='y2', line=dict(color='darkblue', dash='dash')))
            fig.add_trace(go.Scatter(x=df_rh['DATE'], y=df_rh['RH MIN'], name='RH Minimum (%)', yaxis='y2', line=dict(color='skyblue', dash='dot')))
            
            x_label = "Bulan"
            title_text = "Variasi Suhu dan RH Tahunan (Rata-rata 2021-2025)"
        else:
            sub_t = df_t[df_t['DATE'] == filter_bulan].iloc[0]
            sub_rh = df_rh[df_rh['DATE'] == filter_bulan].iloc[0]
            
            t_values = [sub_t[h] for h in hours]
            rh_values = [sub_rh[h] for h in hours]
            time_labels = [f"{h.zfill(2)}:00 UTC" for h in hours]
            
            fig.add_trace(go.Scatter(x=time_labels, y=t_values, name='Suhu Diurnal (°C)', mode='lines+markers', line=dict(color='red', width=3)))
            fig.add_trace(go.Scatter(x=time_labels, y=rh_values, name='RH Diurnal (%)', mode='lines+markers', yaxis='y2', line=dict(color='blue', width=3)))
            
            x_label = "Waktu Pengamatan (Diurnal)"
            title_text = f"Meteogram Diurnal Suhu & RH - Bulan {filter_bulan}"
            
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Suhu Rata-rata Harian", f"{sub_t['DAILY MEAN']:.1f} °C")
            col2.metric("Suhu Maksimum / Minimum", f"{sub_t['TEMPERATURE MAX']:.1f} / {sub_t['TEMPERATURE MIN']:.1f} °C")
            col3.metric("RH Rata-rata Harian", f"{sub_rh['DAILY MEAN']:.1f} %")
            col4.metric("RH Maksimum / Minimum", f"{sub_rh['RH MAX']:.1f} / {sub_rh['RH MIN']:.1f} %")
            st.write("")

        fig.update_layout(
            title=title_text,
            xaxis=dict(title=x_label),
            yaxis=dict(title="Temperatur Udara (°C)", titlefont=dict(color="red"), tickfont=dict(color="red")),
            yaxis2=dict(title="Kelembaban Relatif / RH (%)", titlefont=dict(color="blue"), tickfont=dict(color="blue"), overlaying="y", side="right"),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            hovermode="x unified",
            height=500
        )
        st.plotly_chart(fig, use_container_width=True)
        
        st.markdown("### 📋 Tabel Data Pendukung")
        tab_t, tab_rh = st.tabs(["Data Suhu (Temperature)", "Data Kelembaban (Relative Humidity)"])
        with tab_t:
            st.dataframe(df_t, use_container_width=True, hide_index=True)
        with tab_rh:
            st.dataframe(df_rh, use_container_width=True, hide_index=True)

    # ==========================================
    # MENU 2: PARAMETER ANGIN & WINDROSE
    # ==========================================
    elif menu == "Analisis Angin (Windrose)":
        st.subheader("💨 Analisis Frekuensi Distribusi Kompas Angin (Windrose Summary)")
        
        dir_sectors = [
            '35 - 36 - 01', '02 - 03- 04', '05 - 06 - 07', '08 - 09 - 10', 
            '11 - 12 - 13', '14 - 15 - 16', '17 - 18 - 19', '20 - 21 - 22', 
            '23 - 24 - 25', '26 - 27 - 28', '29 - 30 - 31', '32 - 33 - 34'
        ]
        angles = [0, 30, 60, 90, 120, 150, 180, 210, 240, 270, 300, 330]
        
        if filter_bulan == "Semua Bulan (Gabungan/Tahunan)":
            dir_values = df_wind_dir[dir_sectors].mean().values
            calm_val = df_wind_dir['CALM'].mean()
            speed_df_filtered = df_wind_spd.drop(columns=['DATE'])
            speed_values = speed_df_filtered.mean()
            rose_title = "Windrose Distribusi Arah Angin - Keseluruhan (Tahunan Gabungan)"
        else:
            row_dir = df_wind_dir[df_wind_dir['DATE'] == filter_bulan].iloc[0]
            dir_values = [row_dir[sec] for sec in dir_sectors]
            calm_val = row_dir['CALM']
            row_spd = df_wind_spd[df_wind_spd['DATE'] == filter_bulan].iloc[0]
            speed_values = row_spd.drop(['DATE'])
            rose_title = f"Windrose Distribusi Arah Angin - Bulan {filter_bulan}"

        col1, col2 = st.columns([1, 1])
        
        with col1:
            fig_rose = go.Figure()
            fig_rose.add_trace(go.Barpolar(
                r=dir_values,
                theta=angles,
                name="Frekuensi Sektor Arah Angin",
                marker_color="teal",
                marker_line_color="black",
                marker_line_width=1,
                opacity=0.85
            ))
            fig_rose.update_layout(
                title=rose_title,
                polar=dict(
                    angularaxis=dict(
                        tickmode="array",
                        tickvals=angles,
                        ticktext=['N (Utara)', 'NNE', 'ENE', 'E (Timur)', 'ESE', 'SSE', 'S (Selatan)', 'SSW', 'WSW', 'W (Barat)', 'WNW', 'NNW'],
                        direction="clockwise",
                        period=360
                    )
                ),
                height=500
            )
            st.plotly_chart(fig_rose, use_container_width=True)
            st.info(f"ℹ️ **Kondisi Tenang (CALM):** Frekuensi udara tenang rata-rata bernilai **{calm_val:.2f}%**")

        with col2:
            fig_spd = go.Figure()
            fig_spd.add_trace(go.Bar(
                x=list(speed_values.index),
                y=list(speed_values.values),
                marker_color="royalblue",
                marker=dict(line=dict(color='black', width=1))  # SINTAKS FIXED (Bebas Eror Plotly)
            ))
            fig_spd.update_layout(
                title=f"Distribusi Spektrum Kecepatan Angin ({filter_bulan if filter_bulan != 'Semua Bulan (Gabungan/Tahunan)' else 'Gabungan'})",
                xaxis_title="Rentang Batas Kecepatan (Knot / Satuan Data)",
                yaxis_title="Frekuensi Kemunculan (%)",
                height=500
            )
            st.plotly_chart(fig_spd, use_container_width=True)

        st.markdown("### 📋 Tabel Data Frekuensi Angin")
        tab_dir_t, tab_spd_t = st.tabs(["Tabel Distribusi Arah Kontur", "Tabel Distribusi Tingkat Kecepatan"])
        with tab_dir_t:
            st.dataframe(df_wind_dir, use_container_width=True, hide_index=True)
        with tab_spd_t:
            st.dataframe(df_wind_spd, use_container_width=True, hide_index=True)

    # ==========================================
    # MENU 3: DISTRIBUSI FREKUENSI LAINNYA
    # ==========================================
    elif menu == "Distribusi Frekuensi Lainnya":
        st.subheader("📊 Analisis Distribusi Kluster Frekuensi Lingkungan")
        
        sub_menu = st.radio("Pilih Parameter Frekuensi:", ["Distribusi Rentang Suhu", "Distribusi Jarak Pandang (Visibility)", "Distribusi Ketinggian (Ceiling/Hs)"], orientation="horizontal")
        
        if sub_menu == "Distribusi Rentang Suhu":
            active_df = df_temp_freq
            title_g = "Histogram Distribusi Probabilitas Rentang Suhu Udara"
            x_title_bar = "Rentang Nilai Suhu (°C)"
        elif sub_menu == "Distribusi Jarak Pandang (Visibility)":
            active_df = df_vis
            title_g = "Histogram Distribusi Probabilitas Jarak Pandang (Visibility)"
            x_title_bar = "Rentang Nilai Pandang (Meter)"
        else:
            active_df = df_hs
            title_g = "Histogram Distribusi Probabilitas Batas Ketinggian (Hs)"
            x_title_bar = "Kategori Batas Ketinggian"

        if filter_bulan == "Semua Bulan (Gabungan/Tahunan)":
            plot_series = active_df.drop(columns=['DATE']).mean()
            g_title_final = f"{title_g} - Kompilasi Tahunan"
        else:
            plot_series = active_df[active_df['DATE'] == filter_bulan].drop(columns=['DATE']).iloc[0]
            g_title_final = f"{title_g} - Bulan {filter_bulan}"

        fig_freq = go.Figure()
        fig_freq.add_trace(go.Bar(
            x=list(plot_series.index),
            y=list(plot_series.values),
            marker_color="darkcyan",
            text=[f"{v:.2f}%" for v in plot_series.values],
            textposition='auto',
            marker=dict(line=dict(color='black', width=1))
        ))
        
        fig_freq.update_layout(
            title=g_title_final,
            xaxis_title=x_title_bar,
            yaxis_title="Persentase Frekuensi (%)",
            height=500
        )
        st.plotly_chart(fig_freq, use_container_width=True)

        st.markdown("### 📋 Arsip Data Parameter Lengkap")
        st.dataframe(active_df, use_container_width=True, hide_index=True)
