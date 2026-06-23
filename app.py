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

elif menu == "2. Rata-rata Persentase Visibility":
    filename = "rata_rata_persentase_visibility_2021_2025.xlsx"
    categories = ['< 200', '< 400', '< 600', '< 800', '< 1500', '< 1800', '< 3000', '< 5000', '< 8000']
    colors = ['blue', 'brown', 'green', 'orange', 'purple', 'red', 'grey', 'black', 'yellow']
    
    df, error = load_acs_data(filename, categories)
    if error:
        st.error(error)
    else:
        fig = go.Figure()
        for cat, color in zip(categories, colors):
            fig.add_trace(go.Scatter(x=df['Bulan'], y=df[cat], mode='lines+markers', name=cat, line=dict(color=color)))
        fig.update_layout(title="Rata-rata Persentase Visibility Bulanan", yaxis_title="Persentase Kejadian (%)", hovermode="x unified")
        st.plotly_chart(fig, use_container_width=True)
        render_neat_table(df, "Ringkasan Rata-rata Persentase Visibility 2021–2025")

elif menu == "3. Distribusi Frekuensi Angin":
    filename = "rata_rata_persentase_ws_2021_2025.xlsx"
    categories = ['1 - 5', '6 - 10', '11 - 15', '16 - 20', '21 - 25', '26 - 30', '31 - 35', '36 - 45', '> 45', 'TOTAL']
    colors = ['red', 'yellow', 'blue', 'darkgreen', 'orange', 'navy', 'purple', 'magenta', 'lightbrown', 'green']
    
    df, error = load_acs_data(filename, categories)
    if error:
        st.error(error)
    else:
        st.markdown("### A. Distribusi Frekuensi Kecepatan Angin")
        fig_polar = go.Figure()
        for cat, color in zip(categories[:-1], colors[:-1]): 
            fig_polar.add_trace(go.Barpolar(r=df[cat].fillna(0), theta=df['Bulan'], name=cat, marker_color=color))
        fig_polar.update_layout(polar=dict(angularaxis=dict(direction="clockwise")), legend=dict(title="Wind Speed (Kts)"))
        st.plotly_chart(fig_polar, use_container_width=True)

        st.markdown("### B. Meteogram Kecepatan Angin")
        fig_line = go.Figure()
        for cat, color in zip(categories, colors):
            fig_line.add_trace(go.Scatter(x=df['Bulan'], y=df[cat], mode='lines+markers', name=cat, line=dict(color=color)))
        fig_line.update_layout(yaxis_title="Persentase Kejadian (%)", hovermode="x unified")
        st.plotly_chart(fig_line, use_container_width=True)
        render_neat_table(df, "Ringkasan Frekuensi Angin 2021–2025")

elif menu == "4. Profil Variasi Diurnal RH":
    filename = "rata_rata_jumlah_kejadian_masuk_rh_2021_2025.xlsx"
    categories = ['0', '3', '6', '9', '12', '15', '18', '21', 'DAILY MEAN', 'RH MAX', 'RH MIN']
    colors = ['navy', 'orange', 'grey', 'magenta', 'darkblue', 'purple', 'brown', 'blue', 'red', 'yellow', 'green']
    
    df, error = load_acs_data(filename, categories)
    if error:
        st.error(error)
    else:
        fig = go.Figure()
        for cat, color in zip(categories, colors):
            fig.add_trace(go.Scatter(x=df['Bulan'], y=df[cat], mode='lines+markers', name=f"{cat} UTC" if cat.isdigit() else cat, line=dict(color=color)))
        fig.update_layout(title="Profil Variasi Diurnal dan Ekstrem RH", yaxis_title="Nilai RH (%)", hovermode="x unified")
        st.plotly_chart(fig, use_container_width=True)
        render_neat_table(df, "Ringkasan Statistik Bulanan RH 2021–2025")

elif menu == "5. Profil Variasi Diurnal Temperature":
    filename = "rata_rata_jumlah_kejadian_masuk_tmaxmin_2021_2025.xlsx"
    categories = ['0', '3', '6', '9', '12', '15', '18', '21', 'DAILY MEAN', 'T MAX', 'T MIN']
    colors = ['navy', 'orange', 'grey', 'magenta', 'black', 'purple', 'brown', 'blue', 'red', 'yellow', 'green']
    
    df, error = load_acs_data(filename, categories)
    if error:
        st.error(error)
    else:
        fig = go.Figure()
        for cat, color in zip(categories, colors):
            fig.add_trace(go.Scatter(x=df['Bulan'], y=df[cat], mode='lines+markers', name=f"{cat} UTC" if cat.isdigit() else cat, line=dict(color=color)))
        fig.update_layout(title="Profil Variasi Diurnal dan Ekstrem Temperature", yaxis_title="Nilai Temperature (°C)", hovermode="x unified")
        st.plotly_chart(fig, use_container_width=True)
        render_neat_table(df, "Ringkasan Statistik Bulanan Temperature 2021–2025")

elif menu == "6. Rata-rata Persentase HS":
    filename = "rata_rata_persentase_hs_2021_2025.xlsx"
    categories = ['< 150', '< 200', '< 300', '< 500', '< 1000', '< 1500']
    colors = ['blue', 'orange', 'green', 'red', 'purple', 'yellow']
    
    df, error = load_acs_data(filename, categories)
    if error:
        st.error(error)
    else:
        fig = go.Figure()
        for cat, color in zip(categories, colors):
            fig.add_trace(go.Scatter(x=df['Bulan'], y=df[cat], mode='lines+markers', name=cat, line=dict(color=color)))
        fig.update_layout(title="Rata-rata Persentase HS Bulanan", yaxis_title="Persentase Kejadian (%)", hovermode="x unified")
        st.plotly_chart(fig, use_container_width=True)
        render_neat_table(df, "Ringkasan Rata-rata Persentase HS 2021–2025")
