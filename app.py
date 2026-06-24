
Percakapan dengan Gemini
Bertindaklah sebagai Senior Python Developer dan Data Scientist ahli Streamlit. Saya memiliki folder `data_acsrsn` (JANGAN gunakan folder dummy 'data') yang berisi 6 file CSV cuaca murni untuk dibuatkan dashboard interaktif.



Struktur file:

1. `t_max_min_2021_2025.csv`: Suhu. Baris indeks ke-0 adalah sub-header ('MEAN', 'MAX', 'MIN'). Lakukan `df.iloc[1:]`, ubah kolom ['DAILY', 'TEMPERATURE', 'Unnamed: 11'] ke float.

2. `rh_max_min_2021_2025.csv`: Kelembaban. Baris ke-0 adalah sub-header. Lakukan `iloc[1:]`, ubah kolom target ke float.

3. `wind_2021_2025.csv`: Berisi 2 tabel tumpuk. 

   - Arah angin: `iloc[1:13]` (Kolom arah ada di index 2 sampai akhir).

   - Kecepatan angin: `iloc[15:27, 0:11]` (Ambil 11 kolom pertama saja).

4. `visibility_2021_2025.csv`: Normal.

5. `hs_2021_2025.csv`: Tinggi dasar awan, Normal.

6. `temperature_2021_2025.csv`: Distribusi frekuensi suhu.



Buatkan `app.py` dan `requirements.txt` dengan kriteria berikut:

1. Tahan Banting: Gunakan `os.path.exists()` untuk validasi keberadaan file sebelum di-load menggunakan `pd.read_csv()`. Gunakan `@st.cache_data`.

2. UI Bersih: Gunakan `st.set_page_config(layout="wide")` dan `st.tabs`.

3. Tab Meteogram: Buat dual-axis chart dengan Plotly (`make_subplots`). Suhu di Y-primer, RH di Y-sekunder. Tampilkan tabel gabungan (Suhu & RH) di bawahnya.

4. Tab Windrose: Gunakan `px.bar_polar`. Sediakan `st.selectbox` agar user bisa memilih "Windrose Keseluruhan (Tahunan)" atau "Windrose per Bulan". Kalkulasi probabilitas gabungan (Joint Frequency) dari data arah dan kecepatan yang terpisah.

5. Jangan gunakan data dummy sedikit pun. Kode harus langsung siap deploy tanpa error.

File app.py dan requirements.txt Anda telah berhasil disiapkan untuk mendeploy dashboard berbasis Streamlit!
Ikon PY
app
 PY 
Buka
Ikon TXT
requirements
 TXT 
Buka

Sebagai Senior Python Developer dan Data Scientist, saya telah merancang kode ini secara robust (tahan banting) dan persis seperti standar produksi yang Anda inginkan. Berikut adalah rincian fitur dan implementasinya:

Validasi & Caching Tingkat Lanjut: Sistem memvalidasi eksistensi setiap file melalui os.path.exists() ke dalam direktori /data_acsrsn dan menghindari error yang merusak UI. Memori akan dimaksimalkan melalui dekorator @st.cache_data. Tidak ada data dummy yang digunakan.

Slicing DataFrame Akurat:

Suhu: Melakukan slicing df.iloc[1:], lalu mengubah kolom target menjadi float menggunakan pd.to_numeric(errors='coerce') yang jauh lebih aman saat mengonversi raw string.

Angin (wind_2021_2025.csv): Menangani dua tabel tumpuk yang tidak biasa dengan cara diload tanpa header (header=None), lalu diekstrak khusus index baris [1:13] (kolom indeks ke 2 dan seterusnya) untuk arah, dan index baris [15:27] (11 kolom pertama) untuk kecepatan.

Desain Tabular & Tab: Dashboard dipersiapkan menggunakan st.set_page_config(layout="wide") dan dirapikan lewat arsitektur st.tabs.

Dual-Axis Meteogram (Plotly): Di Tab Pertama, make_subplots digunakan untuk menjajarkan Trend Temperatur di Y-primer dan Trend Kelembaban (RH) di Y-sekunder, lengkap dengan styling garis warna yang kontras, serta tabel gabungan warna-gradien (gradient-styled dataframe) yang elegan di bagian bawah grafik.

Kalkulasi Windrose (Joint Frequency Probability): Pada Tab Kedua, karena data dipisah (marginal probability), kode akan mengalkulasi Joint Frequency Probability dengan rumus statistika P(D,S)=P(Direction)×P(Speed) per periodenya. Ini akan menghasilkan polar visualisasi px.bar_polar yang dinamis — baik menggunakan integrasi tahunan maupun bulanan via interaksi selectbox.

Ekstra Visualisasi: Tab-tab sisanya telah saya akomodir untuk memvisualisasikan Visibilitas, Tinggi Dasar Awan (Hs), serta Distribusi Suhu sebagai pelengkap dashboard eksekutif meteorologi Anda.

Cara Eksekusi:

Pastikan folder bernama data_acsrsn berada di tempat yang sama dengan lokasi app.py.

Instal pustaka yang dibutuhkan menggunakan perintah: pip install -r requirements.txt

Jalankan aplikasi menggunakan: streamlit run app.py




Gemini adalah AI dan dapat melakukan kesalahan.

Memuat requirements.txt.
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as gr
from plotly.subplots import make_subplots
import os

# 1. PAGE CONFIGURATION
st.set_page_config(
    page_title="Advanced Weather Analytics Dashboard",
    page_icon="⛈️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS to enhance the layout
st.markdown("""
    <style>
    .main-header {
        font-size:28px !important;
        font-weight: bold;
        color: #1E3A8A;
        margin-bottom: 20px;
    }
    .status-box {
        padding: 10px;
        border-radius: 5px;
        margin-bottom: 10px;
    }
    </style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-header">⛈️ Climate & Weather Analytics Dashboard (2021-2025)</div>', unsafe_allow_html=True)

# 2. DATA LOADING & CACHING LAYER WITH EXTRA ROBUSTNESS
DATA_DIR = "data_acsrsn"

@st.cache_data
def load_temperature_extremes():
    file_path = os.path.join(DATA_DIR, "t_max_min_2021_2025.csv")
    if not os.path.exists(file_path):
        return None
    try:
        # Read raw data
        df = pd.read_csv(file_path)
        # Apply user rules: index 0 is subheader, do iloc[1:]
        df_clean = df.iloc[1:].copy().reset_index(drop=True)
        
        # Target columns to convert to float
        target_cols = ['DAILY', 'TEMPERATURE', 'Unnamed: 11']
        for col in target_cols:
            if col in df_clean.columns:
                df_clean[col] = pd.to_numeric(df_clean[col], errors='coerce')
        
        # Rename columns logically if they exist for better readability
        rename_map = {}
        if 'DAILY' in df_clean.columns: rename_map['DAILY'] = 'Mean Temperature (°C)'
        if 'TEMPERATURE' in df_clean.columns: rename_map['TEMPERATURE'] = 'Max Temperature (°C)'
        if 'Unnamed: 11' in df_clean.columns: rename_map['Unnamed: 11'] = 'Min Temperature (°C)'
        df_clean.rename(columns=rename_map, inplace=True)
        
        return df_clean
    except Exception as e:
        st.error(f"Error processing t_max_min_2021_2025.csv: {e}")
        return None

@st.cache_data
def load_humidity_data():
    file_path = os.path.join(DATA_DIR, "rh_max_min_2021_2025.csv")
    if not os.path.exists(file_path):
        return None
    try:
        df = pd.read_csv(file_path)
        df_clean = df.iloc[1:].copy().reset_index(drop=True)
        
        # Convert numeric columns to float (excluding the first column which usually represents the time/month)
        for col in df_clean.columns[1:]:
            df_clean[col] = pd.to_numeric(df_clean[col], errors='coerce')
            
        return df_clean
    except Exception as e:
        st.error(f"Error processing rh_max_min_2021_2025.csv: {e}")
        return None

@st.cache_data
def load_wind_data():
    file_path = os.path.join(DATA_DIR, "wind_2021_2025.csv")
    if not os.path.exists(file_path):
        return None, None
    try:
        # Read without headers to manually slice stacked tables safely
        df = pd.read_csv(file_path, header=None)
        
        # Table 1: Wind Direction (iloc[1:13], columns from index 2 to end)
        # Row 0 contains direction labels (N, NE, E, etc.)
        dir_headers = df.iloc[0, 2:].dropna().tolist()
        dir_months = df.iloc[1:13, 0].values # Month column
        dir_values = df.iloc[1:13, 2:].copy()
        
        df_dir = pd.DataFrame(dir_values.values, columns=dir_headers[:dir_values.shape[1]])
        df_dir.insert(0, 'Month', dir_months)
        for col in df_dir.columns[1:]:
            df_dir[col] = pd.to_numeric(df_dir[col], errors='coerce').fillna(0)
            
        # Table 2: Wind Speed (iloc[15:27, 0:11])
        # Row 14 usually contains speed range headers
        spd_headers = df.iloc[14, 1:11].dropna().tolist()
        spd_months = df.iloc[15:27, 0].values
        spd_values = df.iloc[15:27, 1:11].copy()
        
        df_spd = pd.DataFrame(spd_values.values, columns=spd_headers[:spd_values.shape[1]])
        df_spd.insert(0, 'Month', spd_months)
        for col in df_spd.columns[1:]:
            df_spd[col] = pd.to_numeric(df_spd[col], errors='coerce').fillna(0)
            
        return df_dir, df_spd
    except Exception as e:
        st.error(f"Error processing wind_2021_2025.csv: {e}")
        return None, None

@st.cache_data
def load_normal_file(filename):
    file_path = os.path.join(DATA_DIR, filename)
    if not os.path.exists(file_path):
        return None
    try:
        df = pd.read_csv(file_path)
        for col in df.columns[1:]:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        return df
    except Exception as e:
        st.error(f"Error processing {filename}: {e}")
        return None

# Load all datasets securely
df_temp_ext = load_temperature_extremes()
df_rh = load_humidity_data()
df_wind_dir, df_wind_spd = load_wind_data()
df_visibility = load_normal_file("visibility_2021_2025.csv")
df_hs = load_normal_file("hs_2021_2025.csv")
df_temp_dist = load_normal_file("temperature_2021_2025.csv")

# Sidebar Status Panel
st.sidebar.header("📁 File Status Check")
files_to_check = {
    "t_max_min_2021_2025.csv": df_temp_ext is not None,
    "rh_max_min_2021_2025.csv": df_rh is not None,
    "wind_2021_2025.csv": df_wind_dir is not None and df_wind_spd is not None,
    "visibility_2021_2025.csv": df_visibility is not None,
    "hs_2021_2025.csv": df_hs is not None,
    "temperature_2021_2025.csv": df_temp_dist is not None
}

for file, exists in files_to_check.items():
    if exists:
        st.sidebar.success(f"✔️ {file} Loaded")
    else:
        st.sidebar.error(f"❌ {file} Missing/Error")

# 3. TABS SETUP
tabs = st.tabs(["📊 Meteogram & Data", "💨 Windrose Analysis", "🌫️ Visibility & Cloud Base (Hs)", "🌡️ Temp Distribution"])

# ==========================================
# TAB 1: METEOGRAM (DUAL AXIS CHART)
# ==========================================
with tabs[0]:
    st.subheader("Meteogram Interaktif & Integrasi Data")
    
    if df_temp_ext is not None and df_rh is not None:
        # Determine X-axis (Months or Index labels)
        x_axis_labels = df_temp_ext.iloc[:, 0] if not df_temp_ext.empty else list(range(1, 13))
        
        # Get column names for selection / visualization
        temp_cols = [c for c in df_temp_ext.columns if 'Temperature' in c or c in ['DAILY', 'TEMPERATURE', 'Unnamed: 11']]
        rh_cols = [c for c in df_rh.columns if c != df_rh.columns[0]]
        
        col_sel1, col_sel2 = st.columns(2)
        with col_sel1:
            selected_temp = st.selectbox("Pilih Parameter Suhu (Y-Primer):", temp_cols, index=0)
        with col_sel2:
            selected_rh = st.selectbox("Pilih Parameter Kelembaban / RH (Y-Sekunder):", rh_cols, index=0)
            
        # Create dual-axis subplot
        fig_meteogram = make_subplots(specs=[[{"secondary_y": True}]])
        
        # Primary Y-Axis: Temperature
        fig_meteogram.add_trace(
            gr.Scatter(
                x=x_axis_labels, 
                y=df_temp_ext[selected_temp], 
                name=selected_temp,
                mode='lines+markers',
                line=dict(color='#EF4444', width=3)
            ),
            secondary_y=False,
        )
        
        # Secondary Y-Axis: RH
        fig_meteogram.add_trace(
            gr.Scatter(
                x=x_axis_labels, 
                y=df_rh[selected_rh], 
                name=f"{selected_rh} (RH)",
                mode='lines+markers',
                line=dict(color='#3B82F6', width=3, dash='dash')
            ),
            secondary_y=True,
        )
        
        # Layout tuning
        fig_meteogram.update_layout(
            title_text=f"Meteogram: {selected_temp} vs {selected_rh}",
            hovermode="x unified",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            margin=dict(l=20, r=20, t=60, b=20)
        )
        
        fig_meteogram.update_xaxes(title_text="Periode / Bulan")
        fig_meteogram.update_yaxes(title_text="Suhu (°C)", secondary_y=False)
        fig_meteogram.update_yaxes(title_text="Kelembaban Nisbi / RH (%)", secondary_y=True)
        
        st.plotly_chart(fig_meteogram, use_container_width=True)
        
        # Combined Table Display Below
        st.subheader("Tabel Gabungan Parameter Utama")
        # Merge safely on first column or index
        combined_df = pd.DataFrame({
            'Periode': x_axis_labels,
            selected_temp: df_temp_ext[selected_temp],
            selected_rh: df_rh[selected_rh]
        })
        st.dataframe(combined_df.style.background_gradient(cmap="Blues", subset=[selected_rh])
                                     .background_gradient(cmap="Reds", subset=[selected_temp]), 
                     use_container_width=True)
    else:
        st.warning("Data Suhu atau RH tidak tersedia untuk membuat Meteogram.")

# ==========================================
# TAB 2: WINDROSE ANALYSIS
# ==========================================
with tabs[1]:
    st.subheader("Analisis Windrose (Joint Frequency Probability)")
    
    if df_wind_dir is not None and df_wind_spd is not None:
        mode_windrose = st.selectbox(
            "Pilih Cakupan Analisis Windrose:",
            ["Windrose Keseluruhan (Tahunan)", "Windrose per Bulan"]
        )
        
        # Establish months based on data
        available_months = df_wind_dir['Month'].unique()
        
        if mode_windrose == "Windrose per Bulan":
            selected_month = st.selectbox("Pilih Bulan:", available_months)
            # Filter rows for specific month
            dir_row = df_wind_dir[df_wind_dir['Month'] == selected_month].iloc[0, 1:]
            spd_row = df_wind_spd[df_wind_spd['Month'] == selected_month].iloc[0, 1:]
        else:
            # Average/Sum across the entire period for Annual profile
            dir_row = df_wind_dir.iloc[:, 1:].mean()
            spd_row = df_wind_spd.iloc[:, 1:].mean()
            
        # Normalize weights to derive probabilities P(Direction) and P(Speed)
        total_dir = dir_row.sum() if dir_row.sum() > 0 else 1
        total_spd = spd_row.sum() if spd_row.sum() > 0 else 1
        
        p_dir = dir_row / total_dir
        p_spd = spd_row / total_spd
        
        # Compute Joint Frequency Probability: P(D, S) = P(D) * P(S) * Total Sample Baseline
        # Reconstructing a joint distribution matrix using the marginal distributions
        joint_records = []
        for direction, prob_d in p_dir.items():
            for speed_range, prob_s in p_spd.items():
                # Re-scale back to percentage for presentation
                joint_frequency = prob_d * prob_s * 100 
                joint_records.append({
                    'Direction': direction,
                    'Speed Range': speed_range,
                    'Frequency (%)': round(joint_frequency, 3)
                })
                
        df_joint = pd.DataFrame(joint_records)
        
        # Plotting using px.bar_polar
        fig_windrose = px.bar_polar(
            df_joint,
            r="Frequency (%)",
            theta="Direction",
            color="Speed Range",
            color_discrete_sequence=px.colors.sequential.Plasma_r,
            title=f"Windrose Configuration: {mode_windrose}" + (f" ({selected_month})" if mode_windrose == "Windrose per Bulan" else " (Annual Average)"),
            template="plotly_white"
        )
        
        fig_windrose.update_layout(
            polar=dict(
                radialaxis=dict(ticksuffix="%", angle=45),
                angularaxis=dict(direction="clockwise", period=12) # Setup neat standard compass arrangement
            ),
            margin=dict(l=40, r=40, t=80, b=40)
        )
        
        st.plotly_chart(fig_windrose, use_container_width=True)
        
        # Show breakdown matrix options
        with st.expander("Lihat Detail Matriks Probabilitas Gabungan (Joint Frequency Table)"):
            pivot_joint = df_joint.pivot(index='Direction', columns='Speed Range', values='Frequency (%)')
            st.dataframe(pivot_joint, use_container_width=True)
    else:
        st.warning("Data Arah atau Kecepatan Angin (wind_2021_2025.csv) tidak terdeteksi.")

# ==========================================
# TAB 3: VISIBILITY & CLOUD BASE (HS)
# ==========================================
with tabs[2]:
    st.subheader("Analisis Tren Visibility & Tinggi Dasar Awan (Hs)")
    
    col_v1, col_v2 = st.columns(2)
    
    with col_v1:
        st.markdown("**Sebaran Keterangan Jarak Pandang (Visibility)**")
        if df_visibility is not None:
            lbl_col = df_visibility.columns[0]
            val_cols = df_visibility.columns[1:]
            
            # Line Chart for Visibility Trends across categories
            fig_vis = px.line(
                df_visibility, 
                x=lbl_col, 
                y=val_cols, 
                markers=True,
                title="Tren Distribusi Jarak Pandang (Visibility)",
                labels={lbl_col: "Periode"}
            )
            fig_vis.update_layout(legend=dict(orientation="h", y=-0.2))
            st.plotly_chart(fig_vis, use_container_width=True)
            st.dataframe(df_visibility, use_container_width=True)
        else:
            st.info("File `visibility_2021_2025.csv` tidak ditemukan.")
            
    with col_v2:
        st.markdown("**Analisis Tinggi Dasar Awan (Hs)**")
        if df_hs is not None:
            lbl_col_hs = df_hs.columns[0]
            val_cols_hs = df_hs.columns[1:]
            
            # Stacked Bar Chart for Cloud Base Profile
            fig_hs_chart = px.bar(
                df_hs,
                x=lbl_col_hs,
                y=val_cols_hs,
                title="Distribusi Tinggi Dasar Awan (Hs)",
                labels={lbl_col_hs: "Periode"}
            )
            fig_hs_chart.update_layout(legend=dict(orientation="h", y=-0.2))
            st.plotly_chart(fig_hs_chart, use_container_width=True)
            st.dataframe(df_hs, use_container_width=True)
        else:
            st.info("File `hs_2021_2025.csv` tidak ditemukan.")

# ==========================================
# TAB 4: TEMPERATURE DISTRIBUTION
# ==========================================
with tabs[3]:
    st.subheader("Distribusi Frekuensi Temperatur")
    if df_temp_dist is not None:
        lbl_td = df_temp_dist.columns[0]
        val_td = df_temp_dist.columns[1:]
        
        st.markdown("Visualisasi ini menggambarkan seberapa sering temperatur berada pada rentang tertentu sepanjang tahun.")
        
        # Interactive Multi-line or Area representation for distribution
        fig_dist = px.area(
            df_temp_dist,
            x=lbl_td,
            y=val_td,
            title="Kurva Distribusi Frekuensi Suhu Udara",
            labels={lbl_td: "Kelas Interval Suhu (°C)"},
            line_shape="spline"
        )
        fig_dist.update_layout(hovermode="x unified")
        st.plotly_chart(fig_dist, use_container_width=True)
        
        st.dataframe(df_temp_dist, use_container_width=True)
    else:
        st.info("File `temperature_2021_2025.csv` tidak ditemukan.")
app.py
Menampilkan app.py.
