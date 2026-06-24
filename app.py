import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import os

# --- 1. KONFIGURASI HALAMAN ---
st.set_page_config(page_title="Dashboard Klimatologi", page_icon="🌤️", layout="wide")

# Folder utama sesuai instruksi GitHub Anda
DATA_DIR = "data_acsrsn"

# --- 2. FUNGSI PEMBACAAN & PEMBERSIHAN DATA TAHAN BANTING ---
@st.cache_data
def load_data():
    # Menyesuaikan dengan nama file CSV bersih Anda
    files = {
        "t": "t_max_min_2021_2025.csv",
        "rh": "rh_max_min_2021_2025.csv",
        "vis": "visibility_2021_2025.csv",
        "hs": "hs_2021_2025.csv",
        "wind": "wind_2021_2025.csv",
        "temp_dist": "temperature_2021_2025.csv"
    }
    
    data = {}
    for k, v in files.items():
        filepath = os.path.join(DATA_DIR, v)
        if not os.path.exists(filepath):
            st.error(f"⚠️ SISTEM ERROR: File tidak ditemukan di path '{filepath}'. Pastikan folder '{DATA_DIR}' sudah benar dan file berektensi .csv murni.")
            st.stop()
        
        # Baca sebagai CSV
        data[k] = pd.read_csv(filepath)

    # A. Ekstraksi Suhu & RH (Membongkar baris sub-header)
    df_t = data["t"].iloc[1:].reset_index(drop=True).copy()
    df_t.rename(columns={'DAILY': 'T_Mean', 'TEMPERATURE': 'T_Max', 'Unnamed: 11': 'T_Min'}, inplace=True)
    df_t[['T_Mean', 'T_Max', 'T_Min']] = df_t[['T_Mean', 'T_Max', 'T_Min']].astype(float)
    
    df_rh = data["rh"].iloc[1:].reset_index(drop=True).copy()
    df_rh.rename(columns={'DAILY': 'RH_Mean', 'RH': 'RH_Max', 'Unnamed: 11': 'RH_Min'}, inplace=True)
    df_rh[['RH_Mean', 'RH_Max', 'RH_Min']] = df_rh[['RH_Mean', 'RH_Max', 'RH_Min']].astype(float)

    # B. Ekstraksi Wind (Arah dan Kecepatan dari 1 file CSV)
    wind_raw = data["wind"]
    
    # B1. Arah Angin (Baris 1 s/d 12)
    df_wd = wind_raw.iloc[1:13].copy()
    dir_labels = ['N (360°)', 'NNE (30°)', 'ENE (60°)', 'E (90°)', 'ESE (120°)', 'SSE (150°)', 'S (180°)', 'SSW (210°)', 'WSW (240°)', 'W (270°)', 'WNW (300°)', 'NNW (330°)']
    df_wd.columns = ['DATE', 'CALM'] + dir_labels
    for col in df_wd.columns[1:]:
        df_wd[col] = pd.to_numeric(df_wd[col], errors='coerce').fillna(0)
        
    # B2. Kecepatan Angin (Baris 15 s/d 26, ambil hanya 11 kolom pertama)
    df_ws = wind_raw.iloc[15:27, 0:11].copy()
    spd_labels = ['1 - 5', '6 - 10', '11 - 15', '16 - 20', '21 - 25', '26 - 30', '31 - 35', '36 - 45', '> 45']
    df_ws.columns = ['DATE', 'CALM'] + spd_labels
    for col in df_ws.columns[1:]:
        df_ws[col] = pd.to_numeric(df_ws[col], errors='coerce').fillna(0)
        
    return df_t, df_rh, df_wd, df_ws, dir_labels, spd_labels, data["vis"], data["hs"], data["temp_dist"]

# Panggil load data
df_t, df_rh, df_wd, df_ws, dir_labels, spd_labels, df_vis, df_hs, df_temp_dist = load_data()

# --- 3. UI DASHBOARD ---
st.title("🌤️ Dashboard Klimatologi Udara (2021-2025)")
st.markdown("Visualisasi Data Cuaca Interaktif berdasarkan arsip observasi lapangan.")

tab1, tab2, tab3 = st.tabs(["📈 Meteogram & Suhu", "🧭 Windrose Angin", "📊 Visibility & Awan"])

# --- TAB 1: METEOGRAM & TABEL ---
with tab1:
    st.subheader("Meteogram: Fluktuasi Suhu vs Kelembaban (RH)")
    
    fig_meteo = make_subplots(specs=[[{"secondary_y": True}]])
    
    # Plot Suhu (Sumbu Y Kiri)
    fig_meteo.add_trace(go.Scatter(x=df_t['DATE'], y=df_t['T_Max'], name='Suhu Max', mode='lines+markers', line=dict(color='#ff6b6b', dash='dash')), secondary_y=False)
    fig_meteo.add_trace(go.Scatter(x=df_t['DATE'], y=df_t['T_Mean'], name='Suhu Mean', mode='lines+markers', line=dict(color='#c0392b', width=3)), secondary_y=False)
    fig_meteo.add_trace(go.Scatter(x=df_t['DATE'], y=df_t['T_Min'], name='Suhu Min', mode='lines+markers', line=dict(color='#f39c12', dash='dash')), secondary_y=False)
    
    # Plot RH (Sumbu Y Kanan)
    fig_meteo.add_trace(go.Scatter(x=df_rh['DATE'], y=df_rh['RH_Max'], name='RH Max', mode='lines', line=dict(color='#74b9ff', dash='dot')), secondary_y=True)
    fig_meteo.add_trace(go.Scatter(x=df_rh['DATE'], y=df_rh['RH_Mean'], name='RH Mean', mode='lines', line=dict(color='#0984e3', width=3)), secondary_y=True)
    fig_meteo.add_trace(go.Scatter(x=df_rh['DATE'], y=df_rh['RH_Min'], name='RH Min', mode='lines', line=dict(color='#00cec9', dash='dot')), secondary_y=True)
    
    fig_meteo.update_layout(height=450, hovermode='x unified', margin=dict(t=30, b=10))
    fig_meteo.update_yaxes(title_text="<b>Suhu (°C)</b>", secondary_y=False)
    fig_meteo.update_yaxes(title_text="<b>Kelembaban Relatif (%)</b>", secondary_y=True)
    
    st.plotly_chart(fig_meteo, use_container_width=True)
    
    # Tabel Data
    st.markdown("#### 📋 Tabel Ringkasan Meteogram")
    df_combined = pd.merge(df_t[['DATE', 'T_Max', 'T_Mean', 'T_Min']], df_rh[['DATE', 'RH_Max', 'RH_Mean', 'RH_Min']], on='DATE')
    st.dataframe(df_combined.style.format(precision=2), use_container_width=True)


# --- TAB 2: WINDROSE ---
with tab2:
    st.subheader("Distribusi Arah dan Kecepatan Angin (Windrose)")
    
    col_w1, col_w2 = st.columns([1, 3])
    with col_w1:
        opsi_waktu = ["Keseluruhan (Tahunan)"] + df_wd['DATE'].tolist()
        pilihan_waktu = st.selectbox("Pilih Periode Pengamatan:", opsi_waktu)
        st.info("Windrose mensimulasikan probabilitas gabungan antara kecepatan dan arah angin bulanan berdasarkan observasi klimatologis.")
    
    def calc_windrose(period):
        if period == "Keseluruhan (Tahunan)":
            d_dir = df_wd[dir_labels].mean()
            d_spd = df_ws[spd_labels].mean()
        else:
            d_dir = df_wd[df_wd['DATE'] == period][dir_labels].iloc[0]
            d_spd = df_ws[df_ws['DATE'] == period][spd_labels].iloc[0]
            
        total_spd = d_spd.sum()
        if total_spd == 0: total_spd = 1
        
        data_plot = []
        for direction in dir_labels:
            prob_dir = d_dir[direction]
            for speed in spd_labels:
                prob_spd = d_spd[speed]
                # Joint frequency (Proporsi Independen)
                joint_freq = prob_dir * (prob_spd / total_spd)
                if joint_freq > 0:
                    data_plot.append({"Arah": direction, "Kecepatan (Knots)": speed, "Frekuensi (%)": joint_freq})
                    
        return pd.DataFrame(data_plot)

    with col_w2:
        df_plot_wind = calc_windrose(pilihan_waktu)
        
        if df_plot_wind.empty:
            st.warning("Data angin tidak tersedia untuk periode ini.")
        else:
            fig_wr = px.bar_polar(
                df_plot_wind,
                r="Frekuensi (%)",
                theta="Arah",
                color="Kecepatan (Knots)",
                color_discrete_sequence=px.colors.sequential.Tealgrn,
                template="plotly_white"
            )
            fig_wr.update_layout(margin=dict(t=20, b=20), height=550)
            st.plotly_chart(fig_wr, use_container_width=True)


# --- TAB 3: VISIBILITY & AWAN ---
with tab3:
    col_v1, col_v2 = st.columns(2)
    
    with col_v1:
        st.subheader("Jarak Pandang (Visibility)")
        vis_melt = df_vis.melt(id_vars=['DATE'], var_name='Range Jarak Pandang', value_name='Frekuensi (%)')
        fig_v = px.bar(vis_melt, x='DATE', y='Frekuensi (%)', color='Range Jarak Pandang', barmode='stack', color_discrete_sequence=px.colors.qualitative.Pastel)
        fig_v.update_layout(xaxis_title="Bulan", yaxis_title="Frekuensi (%)")
        st.plotly_chart(fig_v, use_container_width=True)
        
    with col_v2:
        st.subheader("Tinggi Dasar Awan (Cloud Base)")
        hs_melt = df_hs.melt(id_vars=['DATE'], var_name='Ketinggian Awan', value_name='Frekuensi (%)')
        fig_h = px.bar(hs_melt, x='DATE', y='Frekuensi (%)', color='Ketinggian Awan', barmode='stack', color_discrete_sequence=px.colors.sequential.Purples)
        fig_h.update_layout(xaxis_title="Bulan", yaxis_title="Frekuensi (%)")
        st.plotly_chart(fig_h, use_container_width=True)
