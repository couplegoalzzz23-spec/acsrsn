"""
app.py — Dashboard Klimatologi ACS (2021–2025)
Dibuat oleh: Senior Data Scientist & Full-Stack Streamlit Developer
Arsitektur: Robust, Flexible Column Matching, Error-Resilient
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import numpy as np
import os

# ─────────────────────────────────────────────
# 1. KONFIGURASI HALAMAN
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="Dashboard Klimatologi ACS Roesmin Nurjadin",
    page_icon="🌤️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Custom CSS untuk mempercantik tampilan tabel dan spasi baris
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    .main-title { text-align: center; color: #1E3A8A; font-weight: 700; margin-bottom: 2rem; }
    .section-card { background-color: #F8FAFC; padding: 1.5rem; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); margin-bottom: 2.5rem; }
</style>
""", unsafe_allow_html=True)

st.markdown("<h1 class='main-title'>🌤️ Dashboard Terintegrasi Aerodrome Climatological Summary (ACS)</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #64748B;'>Analisis Parameter Cuaca Periode Rata-Rata Tahun 2021 – 2025</p>", unsafe_allow_html=True)

# Daftar Bulan Resmi sesuai nama Sheets di Excel Anda
BULAN_LIST = ["Januari", "Februari", "Maret", "April", "Mei", "Juni", "Juli", "Agustus", "September", "Oktober", "November", "Desember"]

DATA_DIR = "data"

# ─────────────────────────────────────────────
# 2. FUNGSI PEMBACAAN DATA (TAHAN BANTING)
# ─────────────────────────────────────────────
@st.cache_data
def load_acs_data(file_name):
    file_path = os.path.join(DATA_DIR, file_name)
    if not os.path.exists(file_path):
        return None, f"File {file_name} tidak ditemukan di folder 'data/'."
    
    try:
        # Membaca seluruh sheets untuk 12 bulan
        excel_file = pd.ExcelFile(file_path)
        monthly_values = {}
        column_headers = None
        
        for bln in BULAN_LIST:
            # Cari sheet yang cocok (toleran terhadap variasi huruf besar/kecil)
            target_sheet = None
            for sheet in excel_file.sheet_names:
                if sheet.strip().lower() == bln.lower():
                    target_sheet = sheet
                    break
            
            if not target_sheet:
                # Fallback: jika tidak ketemu, gunakan sheet berdasarkan urutan index jika tersedia
                continue
                
            # Baca data sheet tanpa mengunci header terlebih dahulu untuk mencari baris MEAN
            df_raw = pd.read_excel(excel_file, sheet_name=target_sheet, header=None)
            
            # Strategi Tahan Banting: Cari baris yang mengandung kata 'mean' atau baris indeks ke-249 (baris 251 di Excel)
            mean_row_idx = None
            for idx, row in df_raw.iterrows():
                row_str = " ".join(row.astype(str).lower())
                if 'mean' in row_str or 'rata' in row_str:
                    mean_row_idx = idx
                    break
            
            # Jika tidak ketemu teks 'mean', paksa tembak ke baris 249 (indeks Python untuk baris 251 Excel)
            if mean_row_idx is None and len(df_raw) > 249:
                mean_row_idx = 249
            elif mean_row_idx is None:
                mean_row_idx = len(df_raw) - 1 # baris terakhir jika file pendek
                
            # Ambil header kolom dari baris ke-0 atau ke-1
            if column_headers is None:
                column_headers = df_raw.iloc[0].astype(str).tolist()
                # Bersihkan kolom dari karakter kosong/unnamed
                column_headers = [col if 'unnamed' not in col.lower() else f"Kolom_{i}" for i, col in enumerate(column_headers)]
            
            # Ambil baris data mean tersebut
            mean_row_data = df_raw.iloc[mean_row_idx].values
            monthly_values[bln] = mean_row_data
            
        if not monthly_values:
            return None, f"Tidak ada data sheet bulan yang cocok di file {file_name}."
            
        # Bentuk DataFrame Akhir
        df_final = pd.DataFrame.from_dict(monthly_values, orient='index', columns=column_headers)
        
        # Bersihkan kolom pertama (biasanya kolom kategori/text 'MEAN')
        if df_final.shape[1] > 1:
            df_final = df_final.iloc[:, 1:] # Ambil dari kolom ke-2 dan seterusnya (angka persentase)
            
        # Pastikan tipe data float dan bulatkan 2 desimal
        df_final = df_final.apply(pd.to_numeric, errors='coerce').fillna(0).round(2)
        return df_final, None
        
    except Exception as e:
        return None, f"Gagal memproses file {file_name}. Error: {str(e)}"

# ─────────────────────────────────────────────
# 3. PEMROSESAN DAN VISUALISASI DATA
# ─────────────────────────────────────────────

# --- A. TEMPERATURE ---
st.markdown("<div class='section-card'>", unsafe_allow_html=True)
st.subheader("📊 Rata-rata Persentase Temperatur Bulanan Tahun 2021-2025")
df_temp, err = load_acs_data("rata_rata_persentase_temperature_2021_2025.xlsx")

if err:
    st.error(err)
else:
    # Plot Grafik Garis Fluktuasi
    fig_temp = go.Figure()
    colors_temp = ['#EF4444', '#F97316', '#FACC15', '#1E293B', '#3B82F6', '#10B981', '#8B5CF6']
    
    for i, col in enumerate(df_temp.columns):
        color = colors_temp[i % len(colors_temp)]
        fig_temp.add_trace(go.Scatter(
            x=df_temp.index, y=df_temp[col],
            mode='lines+markers', name=f"Kategori {col}",
            line=dict(color=color, width=3),
            marker=dict(size=8)
        ))
        
    fig_temp.update_layout(
        xaxis_title="Bulan", yaxis_title="Persentase Kejadian (%)",
        hovermode="x unified", margin=dict(l=40, r=40, t=20, b=40),
        height=450
    )
    st.plotly_chart(fig_temp, use_container_width=True)
    
    # Tabel data di bawah grafik (rapi, renggang, 2 desimal)
    st.markdown("**Tabel Data Persentase Temperatur:**")
    st.dataframe(df_temp.style.format("{:.2f}"), use_container_width=True)
st.markdown("</div>", unsafe_allow_html=True)


# --- B. WIND SPEED & WINDROSE ---
st.markdown("<div class='section-card'>", unsafe_allow_html=True)
st.subheader("💨 Rata-rata Persentase Kecepatan Angin & Analisis Windrose")
df_ws, err_ws = load_acs_data("rata_rata_persentase_ws_2021_2025.xlsx")

if err_ws:
    st.error(err_ws)
else:
    col_g1, col_g2 = st.columns(2)
    
    with col_g1:
        st.markdown("##### Grafik Tren Kecepatan Angin")
        fig_ws = go.Figure()
        for col in df_ws.columns:
            fig_ws.add_trace(go.Scatter(x=df_ws.index, y=df_ws[col], mode='lines+markers', name=col))
        fig_ws.update_layout(xaxis_title="Bulan", yaxis_title="Persentase (%)", height=400)
        st.plotly_chart(fig_ws, use_container_width=True)
        
    with col_g2:
        st.markdown("##### Interpretasi Distribusi Windrose (Polar Chart)")
        # Mentransformasikan data kolom ws menjadi struktur polar bar
        df_wind_melt = df_ws.reset_index().melt(id_vars='index', var_name='Kecepatan', value_name='Persentase')
        df_wind_melt.rename(columns={'index': 'Bulan'}, inplace=True)
        
        fig_rose = px.bar_polar(
            df_wind_melt, r="Persentase", theta="Bulan",
            color="Kecepatan", template="plotly_white",
            color_discrete_sequence=px.colors.sequential.Plasma_r
        )
        fig_rose.update_layout(height=400, margin=dict(t=20, b=20))
        st.plotly_chart(fig_rose, use_container_width=True)
        
    st.markdown("**Tabel Data Kecepatan Angin (WS):**")
    st.dataframe(df_ws.style.format("{:.2f}"), use_container_width=True)
st.markdown("</div>", unsafe_allow_html=True)


# --- C. VISIBILITY ---
st.markdown("<div class='section-card'>", unsafe_allow_html=True)
st.subheader("👁️ Rata-rata Persentase Jarak Pandang (Visibility)")
df_vis, err_vis = load_acs_data("rata_rata_persentase_visibility_2021_2025.xlsx")

if err_vis:
    st.error(err_vis)
else:
    colors_vis = ['#2563EB', '#F97316', '#10B981', '#DC2626', '#7C3AED', '#EAB308']
    fig_vis = go.Figure()
    for i, col in enumerate(df_vis.columns):
        fig_vis.add_trace(go.Scatter(x=df_vis.index, y=df_vis[col], mode='lines+markers', name=col, line=dict(color=colors_vis[i % len(colors_vis)])))
    fig_vis.update_layout(xaxis_title="Bulan", yaxis_title="Persentase (%)", height=400)
    st.plotly_chart(fig_vis, use_container_width=True)
    
    st.markdown("**Tabel Data Jarak Pandang (Visibility):**")
    st.dataframe(df_vis.style.format("{:.2f}"), use_container_width=True)
st.markdown("</div>", unsafe_allow_html=True)

st.markdown("<p style='text-align: center; font-size: 0.8rem; color: #94A3B8;'>Dashboard ACS Terintegrasi v2.0 • Berbasis Streamlit & Plotly</p>", unsafe_allow_html=True)
