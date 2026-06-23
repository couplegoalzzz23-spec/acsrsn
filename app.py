import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np
import os

# ==========================================
# KONFIGURASI HALAMAN & UI
# ==========================================
st.set_page_config(page_title="Tactical Weather Dashboard ACS", layout="wide", page_icon="🌤️")
st.title("🌤️ Tactical Weather Dashboard - ACS")
st.markdown("Visualisasi dan Analisis Data Aerodrome Climatological Summary (ACS) Tahun 2021-2025.")
st.markdown("---")

# ==========================================
# ABSOLUTE PATH RESOLUTION (ANTI CRASH DI CLOUD)
# ==========================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")

# ==========================================
# FUNGSI EKSTRAKSI DATA SUPER KETAT
# ==========================================
@st.cache_data
def load_acs_data(filename, categories):
    filepath = os.path.join(DATA_DIR, filename)
    target_months = ['Januari', 'Februari', 'Maret', 'April', 'Mei', 'Juni',
                     'Juli', 'Agustus', 'September', 'Oktober', 'November', 'Desember']
    data = []
    
    if not os.path.exists(filepath):
        return pd.DataFrame(), f"File tidak ditemukan di sistem: {filepath}"

    try:
        xls = pd.ExcelFile(filepath, engine='openpyxl')
        available_sheets = xls.sheet_names
        
        for month in target_months:
            matched_sheet = None
            for sheet in available_sheets:
                if sheet.strip().lower() == month.lower():
                    matched_sheet = sheet
                    break
            
            row_dict = {'Bulan': month}
            
            if matched_sheet:
                df = pd.read_excel(xls, sheet_name=matched_sheet)
                df.columns = df.columns.astype(str).str.strip()
                
                # Cari baris yang memuat kata 'Mean' tanpa peduli kapitalisasi
                mask = df.astype(str).apply(lambda x: x.str.contains(r'(?i)^mean$', na=False)).any(axis=1)
                
                if mask.any():
                    mean_idx = mask.idxmax()
                    mean_row = df.iloc[mean_idx]
                    
                    for cat in categories:
                        val = mean_row.get(cat, np.nan)
                        if isinstance(val, str):
                            val = val.replace(',', '.')
                        try:
                            row_dict[cat] = float(val)
                        except (ValueError, TypeError):
                            row_dict[cat] = np.nan
                else:
                    for cat in categories:
                        row_dict[cat] = np.nan
            else:
                for cat in categories:
                    row_dict[cat] = np.nan
                    
            data.append(row_dict)
            
        return pd.DataFrame(data), None
    except Exception as e:
        return pd.DataFrame(), f"Terjadi kesalahan sistem saat membaca file '{filename}': {str(e)}"

# ==========================================
# FUNGSI RENDER TABEL
# ==========================================
def render_neat_table(df, title):
    st.markdown(f"#### 📊 {title}")
    if df.empty:
        st.warning("Data kosong atau gagal diproses.")
        return
    
    df_display = df.set_index('Bulan')
    styled_df = df_display.style.format(na_rep="-", precision=2)
    st.dataframe(styled_df, use_container_width=True)

# ==========================================
# SIDEBAR NAVIGATION
# ==========================================
st.sidebar.header("Navigasi Parameter")
menu = st.sidebar.radio(
    "Pilih Parameter Cuaca:",
    (
        "1. Rata-rata Persentase Temperatur",
        "2. Rata-rata Persentase Visibility",
        "3. Distribusi Frekuensi Angin",
        "4. Profil Variasi Diurnal RH",
        "5. Profil Variasi Diurnal Temperature",
        "6. Rata-rata Persentase HS"
    )
)

# ==========================================
# LOGIKA MENU & VISUALISASI
# ==========================================

if menu == "1. Rata-rata Persentase Temperatur":
    filename = "rata_rata_persentase_temperature_2021_2025.xlsx"
    categories = ['5 - 0', '0 - 5', '5 - 10', '10 - 15', '15 - 20', '20 - 25', '25 - 30', '30 - 35', '> 35']
    colors = ['red', 'orange', 'yellow', 'darkblue', 'purple', 'brown', 'pink', 'grey', 'blue']
    
    df, error = load_acs_data(filename, categories)
    if error:
        st.error(error)
    else:
        fig = go.Figure()
        for cat, color in zip(categories, colors):
            fig.add_trace(go.Scatter(x=df['Bulan'], y=df[cat], mode='lines+markers', name=cat, line=dict(color=color)))
        fig.update_layout(title="Rata-rata Persentase Temperatur Bulanan", yaxis_title="Persentase Kejadian (%)", hovermode="x unified")
        st.plotly_chart(fig, use_container_width=True)
        render_neat_table(df, "Ringkasan Rata-rata Persentase Temperatur 2021–2025")

