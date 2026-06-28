import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os

st.set_page_config(page_title="Dashboard Meteo", layout="wide")

@st.cache_data
def load_data(bulan):
    filename = f"HS_2021-2025.xlsx - {bulan}.csv"
    if not os.path.exists(filename):
        return None
    
    # Membaca dengan skip baris deskripsi dan memastikan header di baris ke-4 (indeks 4)
    df = pd.read_csv(filename, header=4)
    
    # 1. Pembersihan Nama Kolom: Menghapus spasi ekstra atau karakter tak terlihat
    df.columns = df.columns.str.strip()
    
    # 2. Rename kolom agar konsisten
    # Berdasarkan data: (GMT), Unnamed: 1 (ini adalah YEAR), < 150, dst
    df = df.rename(columns={'(GMT)': 'TIME', 'Unnamed: 1': 'YEAR'})
    
    # 3. Filter hanya kolom yang relevan
    cols_to_keep = ['TIME', 'YEAR', '< 150', '< 200', '< 300', '< 500', '< 1000', '< 1500']
    df = df[cols_to_keep]
    
    # 4. Konversi tipe data
    df = df.apply(pd.to_numeric, errors='coerce').fillna(0)
    return df

# Sidebar & Logic
bulan_list = ["Januari", "Februari", "Maret", "April", "Mei", "Juni", 
              "Juli", "Agustus", "September", "Oktober", "November", "Desember"]
bulan_terpilih = st.sidebar.selectbox("Pilih Bulan", bulan_list)

df = load_data(bulan_terpilih)

if df is not None:
    st.title(f"Dashboard Meteorologi: {bulan_terpilih}")
    
    # Filter Tahun
    tahun_tersedia = sorted(df['YEAR'].unique().astype(int))
    tahun_terpilih = st.sidebar.multiselect("Pilih Tahun", tahun_tersedia, default=tahun_tersedia)
    
    df_filtered = df[df['YEAR'].isin(tahun_terpilih)].groupby('TIME').mean().reset_index()
    
    # Meteogram
    fig = go.Figure()
    for col in ['< 150', '< 200', '< 300', '< 500', '< 1000', '< 1500']:
        fig.add_trace(go.Scatter(x=df_filtered['TIME'], y=df_filtered[col], name=col))
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Heatmap
    heatmap_data = df_filtered.set_index('TIME').drop(columns=['YEAR']).T
    st.plotly_chart(px.imshow(heatmap_data, color_continuous_scale='Viridis'), use_container_width=True)
else:
    st.error("File tidak ditemukan atau format tidak sesuai.")
