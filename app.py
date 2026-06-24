import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import io
import os

# ==============================================================================
# 1. KONFIGURASI HALAMAN & ANTARMUKA (UI) UTAMA
# ==============================================================================
st.set_page_config(
    page_title="Dashboard Meteorologi Interaktif (2021-2025)",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Desain CSS Kustom Minimalis Modern & Rapi
st.markdown("""
    <style>
    .main-title { font-size: 30px; font-weight: 700; color: #1E3A8A; margin-bottom: 2px; }
    .sub-title { font-size: 15px; color: #4B5563; margin-bottom: 25px; }
    div.stMetric { background-color: #F3F4F6; padding: 15px; border-radius: 8px; border: 1px solid #E5E7EB; }
    </style>
""", unsafe_allow_html=True)

MONTHS = [
    'JANUARY', 'FEBRUARY', 'MARCH', 'APRIL', 'MAY', 'JUNE', 
    'JULY', 'AUGUST', 'SEPTEMBER', 'OCTOBER', 'NOVEMBER', 'DECEMBER'
]

# ==============================================================================
# 2. DATA PIPELINE ENGINE (AMAN & AMBISI KUALITAS TINGGI)
# ==============================================================================

def find_file(filename):
    """Mencari lokasi file di direktori utama atau subfolder secara aman"""
    if os.path.exists(filename):
        return filename
    potential_path = os.path.join("data_acsrsn", filename)
    if os.path.exists(potential_path):
        return potential_path
    return filename

def clean_numeric_dataframe(df, exclude_cols=['DATE']):
    """Membersihkan whitespace, menormalisasi desimal, dan konversi ke float tanpa resiko eror"""
    for col in df.columns:
        if col not in exclude_cols:
            df[col] = df[col].astype(str).str.replace(',', '.', regex=False)
            df[col] = df[col].str.replace(r'[^\d\.\-]', '', regex=True)
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0.0)
    return df

@st.cache_data
def load_t_or_rh_data(filename, is_temp=True):
    """Membaca data Suhu/Kelembaban ber-header ganda dengan mekanisme auto-padding"""
    filepath = find_file(filename)
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Berkas '{filename}' tidak ditemukan.")
    
    raw_df = pd.read_csv(filepath, header=None)
    suffix = "TEMPERATURE" if is_temp else "RH"
    clean_cols = ['DATE', '0', '3', '6', '9', '12', '15', '18', '21', 'DAILY MEAN', f'{suffix} MAX', f'{suffix} MIN']
    
    # Auto-padding jika kolom kurang dari 12 akibat kesalahan ekspor CSV
    while raw_df.shape[1] < 12:
        raw_df[raw_df.shape[1]] = pd.NA
        
    data_df = raw_df.iloc[2:].copy()
    data_df = data_df.iloc[:, :12]
    data_df.columns = clean_cols
    
    data_df['DATE'] = data_df['DATE'].astype(str).str.strip().str.upper()
    data_df = data_df[data_df['DATE'].isin(MONTHS)]
    
    return clean_numeric_dataframe(data_df)

@st.cache_data
def load_wind_data(filename):
    """Memisahkan dan membaca file CSV gabungan arah dan kecepatan angin secara presisi"""
    filepath = find_file(filename)
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Berkas '{filename}' tidak ditemukan.")
        
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        lines = f.readlines()
        
    dir_lines, speed_lines = [], []
    is_speed_section = False
    
    for line in lines:
        if "kecepatan angin bulanan" in line.lower():
            is_speed_section = True
            continue
        if not is_speed_section:
            dir_lines.append(line)
        else:
            speed_lines.append(line)
            
    # Parsing Bagian 1: Distribusi Arah Angin
    dir_header_idx = next((i for i, l in enumerate(dir_lines) if 'DATE' in l and 'CALM' in l), -1)
    if dir_header_idx != -1:
        df_dir = pd.read_csv(io.StringIO("".join(dir_lines[dir_header_idx:])))
    else:
        df_dir = pd.DataFrame(columns=['DATE', 'CALM'])
        
    df_dir.columns = [c.strip() for c in df_dir.columns]
    df_dir = df_dir.loc[:, ~df_dir.columns.str.contains('^Unnamed')]
    df_dir['DATE'] = df_dir['DATE'].astype(str).str.strip().str.upper()
    df_dir = df_dir[df_dir['DATE'].isin(MONTHS)]
    df_dir = clean_numeric_dataframe(df_dir)
    
    # Parsing Bagian 2: Rentang Kecepatan Angin
    speed_header_idx = next((i for i, l in enumerate(speed_lines) if 'DATE' in l and 'CALM' in l), -1)
    if speed_header_idx != -1:
        df_speed = pd.read_csv(io.StringIO("".join(speed_lines[speed_header_idx:])))
    else:
        df_speed = pd.DataFrame(columns=['DATE', 'CALM'])
        
    df_speed.columns = [c.strip() for c in df_speed.columns]
    df_speed = df_speed.loc[:, ~df_speed.columns.str.contains('^Unnamed')]
    df_speed['DATE'] = df_speed['DATE'].astype(str).str.strip().str.upper()
    df_speed = df_speed[df_speed['DATE'].isin(MONTHS)]
    df_speed = clean_numeric_dataframe(df_speed)
    
    return df_dir, df_speed

@st.cache_data
def load_generic_freq_data(filename):
    """Membaca data distribusi frekuensi standar lingkungan (Suhu, Visibility, Hs)"""
    filepath = find_file(filename)
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Berkas '{filename}' tidak ditemukan.")
    df = pd.read_csv(filepath)
    df.columns = [c.strip() for c in df.columns]
    df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
    df['DATE'] = df['DATE'].astype(str).str.strip().str.upper()
    df = df[df['DATE'].isin(MONTHS)]
    return clean_numeric_dataframe(df)

# ==============================================================================
# 3. EKSEKUSI PEMUATAN DATABASE UTAMA
# ==============================================================================
try:
    df_hs = load_generic_freq_data('hs_2021_2025.xlsx - Sheet1.csv')
    df_rh = load_t_or_rh_data('rh_max_min_2021_2025.xlsx - Sheet1.csv', is_temp=False)
    df_t = load_t_or_rh_data('t_max_min_2021_2025.xlsx - Sheet1.csv', is_temp=True)
    df_temp_freq = load_generic_freq_data('temperature_2021_2025.xlsx - Sheet1.csv')
    df_vis = load_generic_freq_data('visibility_2021_2025.xlsx - Sheet1.csv')
    df_wind_dir, df_wind_spd = load_wind_data('wind_2021_2025.xlsx - Sheet1.csv')
    data_load_error = False
except Exception as e:
    st.error(f"❌ Gagal memuat database cuaca: {str(e)}")
    st.info("💡 Solusi: Pastikan berkas CSV berada satu lokasi dengan file script app.py ini.")
    data_load_error = True

# ==============================================================================
# 4. KONTROL INTERAKSI & STRUKTUR DASHBOARD
# ==============================================================================
if not data_load_error:
    st.sidebar.markdown("### 🧭 Navigasi Menu")
    menu = st.sidebar.selectbox(
        "Pilih Jenis Analisis:",
        ["Analisis Multivarian (Meteogram)", "Analisis Karakteristik Angin", "Analisis Kluster Frekuensi Lingkungan"]
    )
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📅 Penyaringan Waktu")
    filter_bulan = st.sidebar.selectbox(
        "Pilih Cakupan Bulan (Climatology):",
        ["Semua Bulan (Kompilasi Tahunan)"] + MONTHS
    )

    st.markdown('<div class="main-title">Dashboard Analisis Meteorologi Lokal (Periode 2021-2025)</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="sub-title">Visualisasi data historis terpadu | Filter aktif: <b>{filter_bulan}</b></div>', unsafe_allow_html=True)
    st.divider()

    # --------------------------------------------------------------------------
    # MENU 1: METEOGRAM INTERAKTIF SUHU & RH
    # --------------------------------------------------------------------------
    if menu == "Analisis Multivarian (Meteogram)":
        st.subheader("📊 Tren Variasi Suhu Udara vs Kelembaban Relatif (RH)")
        
        hours = ['0', '3', '6', '9', '12', '15', '18', '21']
        fig = go.Figure()
        
        if filter_bulan == "Semua Bulan (Kompilasi Tahunan)":
            fig.add_trace(go.Scatter(x=df_t['DATE'], y=df_t['DAILY MEAN'], name='Suhu Rata-rata (°C)', line=dict(color='#DC2626', width=3)))
            fig.add_trace(go.Scatter(x=df_t['DATE'], y=df_t['TEMPERATURE MAX'], name='Suhu Maksimum (°C)', line=dict(color='#991B1B', dash='dash')))
            fig.add_trace(go.Scatter(x=df_t['DATE'], y=df_t['TEMPERATURE MIN'], name='Suhu Minimum (°C)', line=dict(color='#F59E0B', dash='dot')))
            
            fig.add_trace(go.Scatter(x=df_rh['DATE'], y=df_rh['DAILY MEAN'], name='RH Rata-rata (%)', yaxis='y2', line=dict(color='#2563EB', width=3)))
            fig.add_trace(go.Scatter(x=df_rh['DATE'], y=df_rh['RH MAX'], name='RH Maksimum (%)', yaxis='y2', line=dict(color='#1E40AF', dash='dash')))
            fig.add_trace(go.Scatter(x=df_rh['DATE'], y=df_rh['RH MIN'], name='RH Minimum (%)', yaxis='y2', line=dict(color='#38BDF8', dash='dot')))
            
            x_label = "Siklus Bulan Dalam Setahun"
            title_text = "Kurva Tren Fluktuasi Suhu dan RH Makro (Kompilasi 2021-2025)"
        else:
            sub_t_df = df_t[df_t['DATE'] == filter_bulan]
            sub_rh_df = df_rh[df_rh['DATE'] == filter_bulan]
            
            # Safe Fallback handling jika data bulan kosong / terhapus sengaja
            sub_t = sub_t_df.iloc[0] if not sub_t_df.empty else pd.Series(0.0, index=df_t.columns)
            sub_rh = sub_rh_df.iloc[0] if not sub_rh_df.empty else pd.Series(0.0, index=df_rh.columns)
            
            t_values = [sub_t[h] for h in hours]
            rh_values = [sub_rh[h] for h in hours]
            time_labels = [f"{h.zfill(2)}:00 UTC" for h in hours]
            
            fig.add_trace(go.Scatter(x=time_labels, y=t_values, name='Suhu Diurnal (°C)', mode='lines+markers', line=dict(color='#DC2626', width=3)))
            fig.add_trace(go.Scatter(x=time_labels, y=rh_values, name='RH Diurnal (%)', mode='lines+markers', yaxis='y2', line=dict(color='#2563EB', width=3)))
            
            x_label = "Jam Pengamatan Udara (Siklus Diurnal)"
            title_text = f"Meteogram Perubahan Diurnal Suhu & RH - Bulan {filter_bulan}"
            
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Suhu Rata-rata", f"{sub_t['DAILY MEAN']:.1f} °C")
            c2.metric("Ekstrem Suhu (Max/Min)", f"{sub_t['TEMPERATURE MAX']:.1f}°C / {sub_t['TEMPERATURE MIN']:.1f}°C")
            c3.metric("RH Rata-rata", f"{sub_rh['DAILY MEAN']:.1f} %")
            c4.metric("Ekstrem Kelembaban (Max/Min)", f"{sub_rh['RH MAX']:.1f}% / {sub_rh['RH MIN']:.1f}%")
            st.write("")

        fig.update_layout(
            title=title_text,
            xaxis=dict(title=x_label, gridcolor='#E5E7EB'),
            yaxis=dict(title="Temperatur Udara (°C)", titlefont=dict(color="#DC2626"), tickfont=dict(color="#DC2626"), gridcolor='#E5E7EB'),
            yaxis2=dict(title="Kelembaban Relatif / RH (%)", titlefont=dict(color="#2563EB"), tickfont=dict(color="#2563EB"), overlaying="y", side="right"),
            legend=dict(orientation="h", yanchor="bottom", y=1.05, xanchor="center", x=0.5),
            hovermode="x unified",
            plot_bgcolor='white',
            height=500
        )
        st.plotly_chart(fig, use_container_width=True)
        
        st.markdown("### 📋 Lembar Basis Data Historis")
        tab_t, tab_rh = st.tabs(["Data Parameter Temperatur", "Data Parameter Kelembaban (RH)"])
        with tab_t:
            st.dataframe(df_t, use_container_width=True, hide_index=True)
        with tab_rh:
            st.dataframe(df_rh, use_container_width=True, hide_index=True)

    # --------------------------------------------------------------------------
    # MENU 2: KONDISI ANGIN & MAWAR ANGIN (WINDROSE METEOROLOGI)
    # --------------------------------------------------------------------------
    elif menu == "Analisis Karakteristik Angin":
        st.subheader("💨 Profil Sebaran Kontur Arah dan Batas Kecepatan Angin")
        
        # Saring sampah kolom secara dinamis
        dir_sectors = [c for c in df_wind_dir.columns if c not in ['DATE', 'CALM'] and not c.startswith('Unnamed')][:12]
        angles = [i * 30 for i in range(len(dir_sectors))]
        sector_labels = ['N (Utara)', 'NNE', 'ENE', 'E (Timur)', 'ESE', 'SSE', 'S (Selatan)', 'SSW', 'WSW', 'W (Barat)', 'WNW', 'NNW']
        tick_texts = sector_labels[:len(dir_sectors)]
        
        speed_cols = [c for c in df_wind_spd.columns if c not in ['DATE', 'CALM'] and not c.startswith('Unnamed')]

        if filter_bulan == "Semua Bulan (Kompilasi Tahunan)":
            dir_values = df_wind_dir[dir_sectors].mean().values if dir_sectors else [0]*len(angles)
            calm_val = df_wind_dir['CALM'].mean() if 'CALM' in df_wind_dir.columns else 0.0
            speed_values = df_wind_spd[speed_cols].mean() if speed_cols else pd.Series()
            rose_title = "Windrose Pola Frekuensi Arah Angin Dominan (Kompilasi Tahunan)"
        else:
            row_dir_df = df_wind_dir[df_wind_dir['DATE'] == filter_bulan]
            if row_dir_df.empty:
                dir_values = [0] * len(dir_sectors)
                calm_val = 0.0
            else:
                row_dir = row_dir_df.iloc[0]
                dir_values = [row_dir[sec] for sec in dir_sectors]
                calm_val = row_dir['CALM'] if 'CALM' in row_dir else 0.0
                
            row_spd_df = df_wind_spd[df_wind_spd['DATE'] == filter_bulan]
            if row_spd_df.empty:
                speed_values = pd.Series(0.0, index=speed_cols)
            else:
                speed_values = row_spd_df.iloc[0][speed_cols]
                
            rose_title = f"Windrose Pola Arah Angin Dominan - Bulan {filter_bulan}"

        col1, col2 = st.columns([1, 1])
        
        with col1:
            fig_rose = go.Figure()
            fig_rose.add_trace(go.Barpolar(
                r=dir_values,
                theta=angles,
                name="Frekuensi Sektor Arah",
                marker_color="#0D9488",
                marker_line_color="#111827",
                marker_line_width=1,
                opacity=0.85
            ))
            fig_rose.update_layout(
                title=rose_title,
                polar=dict(
                    angularaxis=dict(
                        tickmode="array",
                        tickvals=angles,
                        ticktext=tick_texts,
                        direction="clockwise",
                        period=360,
                        rotation=90  # Menempatkan arah Utara tepat di bagian paling ATAS
                    )
                ),
                height=480
            )
            st.plotly_chart(fig_rose, use_container_width=True)
            st.info(f"ℹ️ **Udara Tenang (CALM):** Probabilitas kondisi atmosfer tenang / tanpa angin berkisar di rata-rata **{calm_val:.2f}%**")

        with col2:
            fig_spd = go.Figure()
            fig_spd.add_trace(go.Bar(
                x=list(speed_values.index),
                y=list(speed_values.values),
                marker=dict(
                    color="#3B82F6",
                    line=dict(color='#111827', width=1)
                )
            ))
            fig_spd.update_layout(
                title=f"Distribusi Kluster Tingkat Kecepatan Angin ({filter_bulan})",
                xaxis_title="Rentang Kelas Kecepatan (Knot)",
                yaxis_title="Frekuensi Kemunculan (%)",
                plot_bgcolor='white',
                xaxis=dict(gridcolor='#E5E7EB'),
                yaxis=dict(gridcolor='#E5E7EB'),
                height=480
            )
            st.plotly_chart(fig_spd, use_container_width=True)

        st.markdown("### 📋 Lembar Basis Data Komponen Angin")
        tab_d, tab_s = st.tabs(["Tabel Distribusi Kontur Arah", "Tabel Tingkat Kecepatan Angin"])
        with tab_d:
            st.dataframe(df_wind_dir, use_container_width=True, hide_index=True)
        with tab_s:
            st.dataframe(df_wind_spd, use_container_width=True, hide_index=True)

    # --------------------------------------------------------------------------
    # MENU 3: DISTRIBUSI FREKUENSI VARIABEL LINGKUNGAN LAINNYA
    # --------------------------------------------------------------------------
    elif menu == "Analisis Kluster Frekuensi Lingkungan":
        st.subheader("📊 Analisis Distribusi Kluster Probabilitas Elemen Atmosfer")
        
        sub_menu = st.sidebar.radio(
            "Pilih Parameter Distribusi:", 
            ["Frekuensi Nilai Suhu Udara", "Frekuensi Jarak Pandang (Visibility)", "Frekuensi Batas Ketinggian Awan (Hs/Ceiling)"]
        )
        
        if sub_menu == "Frekuensi Nilai Suhu Udara":
            active_df = df_temp_freq
            title_g = "Histogram Sebaran Rentang Nilai Suhu Aktual"
            x_title_bar = "Kluster Nilai Suhu (°C)"
            color_bar = "#0891B2"
        elif sub_menu == "Frekuensi Jarak Pandang (Visibility)":
            active_df = df_vis
            title_g = "Histogram Sebaran Ambang Batas Jarak Pandang"
            x_title_bar = "Kategori Batas Pandang (Meter)"
            color_bar = "#4F46E5"
        else:
            active_df = df_hs
            title_g = "Histogram Sebaran Batas Ketinggian Dasar Awan (Hs)"
            x_title_bar = "Kategori Batas Ketinggian Kritis (Feet)"
            color_bar = "#059669"

        cols_to_plot = [c for c in active_df.columns if c != 'DATE']

        if filter_bulan == "Semua Bulan (Kompilasi Tahunan)":
            plot_series = active_df[cols_to_plot].mean() if cols_to_plot else pd.Series()
            g_title_final = f"{title_g} - Gabungan Kompilasi Tahunan"
        else:
            sub_df = active_df[active_df['DATE'] == filter_bulan]
            if sub_df.empty:
                plot_series = pd.Series(0.0, index=cols_to_plot)
            else:
                plot_series = sub_df[cols_to_plot].iloc[0]
            g_title_final = f"{title_g} - Bulan {filter_bulan}"

        fig_freq = go.Figure()
        fig_freq.add_trace(go.Bar(
            x=list(plot_series.index),
            y=list(plot_series.values),
            text=[f"{v:.2f}%" for v in plot_series.values],
            textposition='auto',
            marker=dict(
                color=color_bar,
                line=dict(color='#111827', width=1)
            )
        ))
        
        fig_freq.update_layout(
            title=g_title_final,
            xaxis_title=x_title_bar,
            yaxis_title="Persentase Frekuensi (%)",
            plot_bgcolor='white',
            xaxis=dict(gridcolor='#E5E7EB'),
            yaxis=dict(gridcolor='#E5E7EB'),
            height=500
        )
        st.plotly_chart(fig_freq, use_container_width=True)

        st.markdown("### 📋 Arsip Data Mentah Frekuensi Kumulatif")
        st.dataframe(active_df, use_container_width=True, hide_index=True)
