import streamlit as st
import pandas as pd
import plotly.express as px
import os

st.set_page_config(page_title="Dashboard Meteo", layout="wide")

# Fungsi untuk memuat data
def load_data(bulan):
    filename = f"HS_2021-2025.xlsx - {bulan}.csv"
    
    if not os.path.exists(filename):
        st.error(f"File {filename} tidak ditemukan di folder!")
        return None

    # header=4 karena data kolom dimulai dari baris ke-5 (indeks 4)
    df = pd.read_csv(filename, header=4)
    
    # 1. Bersihkan nama kolom agar tidak ada spasi yang tidak terlihat
    df.columns = df.columns.str.strip()
    
    # 2. Rename kolom agar mudah dipanggil (sesuaikan dengan struktur CSV Anda)
    # File Anda memiliki struktur: (GMT), Unnamed: 1 (YEAR), < 150, dst
    df = df.rename(columns={
        '(GMT)': 'TIME', 
        'Unnamed: 1': 'YEAR',
        '< 150': 'C_150', '< 200': 'C_200', '< 300': 'C_300', 
        '< 500': 'C_500', '< 1000': 'C_1000', '< 1500': 'C_1500'
    })
    
    # 3. Ambil kolom yang relevan saja
    cols = ['TIME', 'YEAR', 'C_150', 'C_200', 'C_300', 'C_500', 'C_1000', 'C_1500']
    df = df[cols]
    
    # 4. Paksa konversi ke angka (untuk menghindari error data kotor)
    df = df.apply(pd.to_numeric, errors='coerce').fillna(0)
    
    return df

# UI Streamlit
st.title("Dashboard Meteorologi")

bulan_list = ["Januari", "Februari", "Maret", "April", "Mei", "Juni", 
              "Juli", "Agustus", "September", "Oktober", "November", "Desember"]

bulan_pilihan = st.sidebar.selectbox("Pilih Bulan", bulan_list)

df = load_data(bulan_pilihan)

if df is not None:
    st.write(f"Menampilkan data untuk: {bulan_pilihan}")
    
    # Pilihan filter tahun
    tahun_tersedia = sorted(df['YEAR'].unique().astype(int))
    tahun_pilihan = st.sidebar.multiselect("Pilih Tahun", tahun_tersedia, default=tahun_tersedia)
    
    # Filter data
    df_plot = df[df['YEAR'].isin(tahun_pilihan)]
    
    # Grafik
    fig = px.line(df_plot, x='TIME', y=['C_150', 'C_200', 'C_300', 'C_500', 'C_1000', 'C_1500'], 
                  color='YEAR', title=f"Frekunesi Cloud Base ({bulan_pilihan})")
    st.plotly_chart(fig, use_container_width=True)
    
    st.dataframe(df)
