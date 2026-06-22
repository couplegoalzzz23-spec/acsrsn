import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import os

# ==========================================
# 1. KONFIGURASI HALAMAN
# ==========================================
st.set_page_config(
    page_title="ACS Weather Dashboard",
    page_icon="🌤️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==========================================
# 2. FUNGSI PEMBACAAN & CACHING DATA
# ==========================================
@st.cache_data(show_spinner=False)
def load_excel_data(file_name: str) -> pd.DataFrame:
    """
    Fungsi tahan banting (bulletproof) untuk membaca file Excel.
    Menggunakan try-except untuk mencegah aplikasi crash jika file hilang/korup.
    """
    file_path = os.path.join("data", file_name)
    try:
        # Engine openpyxl wajib dideklarasikan untuk kestabilan dependensi
        df = pd.read_excel(file_path, engine='openpyxl')
        return df
    except FileNotFoundError:
        st.error(f"🚨 File tidak ditemukan: `{file_path}`. Pastikan folder data/ memiliki file ini.")
        return pd.DataFrame()
    except Exception as e:
        st.error(f"⚠️ Terjadi kesalahan saat memproses `{file_name}`: {str(e)}")
        return pd.DataFrame()

def extract_mean_row_to_monthly(df: pd.DataFrame, value_name: str) -> pd.DataFrame:
    """
    Algoritma fleksibel untuk mencari baris 'mean' atau 'rata-rata' secara dinamis.
    Mengekstrak 12 kolom bulan (Jan-Dec) menjadi format vertikal (sebagai index).
    """
    if df.empty:
        return pd.DataFrame()
    
    # Mencari baris yang mengandung kata 'mean', 'rata', atau 'average' di kolom pertama
    first_col = df.iloc[:, 0].astype(str).str.lower()
    mean_row_idx = first_col[first_col.str.contains('mean|rata|average', na=False)].index
    
    if len(mean_row_idx) > 0:
        # Mengambil baris pertama yang cocok
        target_row = df.loc[mean_row_idx[0]]
    else:
        # Fallback: Jika tidak ada label mean, asumsikan baris terakhir (misal baris 251) adalah total/mean
        target_row = df.iloc[-1]
    
    # Asumsi: data bulan berada di 12 kolom berurutan.
    # Kita menggunakan regex sederhana atau mengambil 12 nilai numerik terakhir
    numeric_data = pd.to_numeric(target_row, errors='coerce').dropna()
    
    # Ambil 12 data terakhir dengan asumsi itu adalah Jan-Dec
    if len(numeric_data) >= 12:
        monthly_values = numeric_data.values[-12:]
    else:
        monthly_values = numeric_data.values
        
    months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    
    # Sesuaikan panjang array bulan dengan data yang ditemukan
    months = months[:len(monthly_values)] 
    
    result_df = pd.DataFrame({
        'Bulan': months,
        value_name: monthly_values
    })
    result_df.set_index('Bulan', inplace=True)
    return result_df

# ==========================================
# 3. LOGIKA APLIKASI UTAMA
# ==========================================
def main():
    st.title("🌤️ Aerodrome Climatological Summary (ACS) Dashboard")
    st.markdown("Visualisasi interaktif rata-rata klimatologi Pangkalan Udara (2021-2025).")
    st.markdown("---")

    # Memuat file data utama
    file_temp = "rata_rata_persentase_temperature_2021_2025.xlsx"
    file_rh = "rata_rata_jumlah_kejadian_masuk_rh_2021_2025.xlsx"
    file_vis = "rata_rata_persentase_visibility_2021_2025.xlsx"
    file_ws = "rata_rata_persentase_ws_2021_2025.xlsx"

    with st.spinner("Memuat data klimatologi..."):
        df_temp_raw = load_excel_data(file_temp)
        df_rh_raw = load_excel_data(file_rh)
        df_vis_raw = load_excel_data(file_vis)
        df_ws_raw = load_excel_data(file_ws)

    # Ekstraksi baris mean menjadi data bulanan
    df_temp = extract_mean_row_to_monthly(df_temp_raw, 'Suhu Udara (°C)')
    df_rh = extract_mean_row_to_monthly(df_rh_raw, 'Kelembapan (%)')
    df_vis = extract_mean_row_to_monthly(df_vis_raw, 'Jarak Pandang (Persentase)')

    # Gabungkan data untuk Meteogram
    if not df_temp.empty and not df_rh.empty and not df_vis.empty:
        df_meteogram = pd.concat([df_temp, df_rh, df_vis], axis=1)
        
        st.subheader("📈 1. Meteogram Klimatologi Bulanan")
        st.markdown("Korelasi fluktuasi Suhu, Kelembapan Relatif, dan Jarak Pandang sepanjang tahun.")
        
        # --- PLOTLY METEOGRAM (Stacked Subplots) ---
        fig_met = make_subplots(
            rows=3, cols=1, 
            shared_xaxes=True, 
            vertical_spacing=0.08,
            subplot_titles=("Suhu Udara Rata-rata (°C)", "Kelembapan Relatif (%)", "Persentase Jarak Pandang Kritis")
        )

        # Trace 1: Temperature (Warm Color)
        fig_met.add_trace(go.Scatter(
            x=df_meteogram.index, y=df_meteogram['Suhu Udara (°C)'],
            mode='lines+markers', name='Suhu',
            line=dict(color='firebrick', width=3),
            marker=dict(size=8)
        ), row=1, col=1)

        # Trace 2: RH (Cool Color)
        fig_met.add_trace(go.Scatter(
            x=df_meteogram.index, y=df_meteogram['Kelembapan (%)'],
            mode='lines+markers', name='Kelembapan',
            line=dict(color='royalblue', width=3),
            fill='tozeroy', fillcolor='rgba(65, 105, 225, 0.2)'
        ), row=2, col=1)

        # Trace 3: Visibility (Bar Chart, Dark Color)
        fig_met.add_trace(go.Bar(
            x=df_meteogram.index, y=df_meteogram['Jarak Pandang (Persentase)'],
            name='Jarak Pandang',
            marker_color='slategray'
        ), row=3, col=1)

        fig_met.update_layout(height=700, showlegend=False, hovermode="x unified", margin=dict(t=40, b=40))
        st.plotly_chart(fig_met, use_container_width=True)

        # --- TABEL METEOGRAM ---
        st.markdown("###### Tabel Data Meteogram (Januari - Desember)")
        # Menampilkan tabel 2 angka desimal, indeks (Bulan) terlihat utuh
        st.dataframe(
            df_meteogram.style.format(precision=2), 
            use_container_width=True
        )

    st.markdown("---")

    # --- WINDROSE CHART ---
    st.subheader("🧭 2. Distribusi Arah dan Kecepatan Angin (Windrose)")
    
    if not df_ws_raw.empty:
        # Algoritma Transformasi Data Windrose
        # Karena ACS standar menyajikan baris sebagai Arah (N, NNE, dll) dan kolom sebagai Kelas Kecepatan Angin.
        try:
            # Asumsi: Kolom 1 adalah 'Arah', kolom-kolom berikutnya adalah persentase/kejadian kelas kecepatan.
            # Mengabaikan baris total/mean untuk visualisasi Windrose polar.
            first_col_name = df_ws_raw.columns[0]
            df_wind_clean = df_ws_raw[~df_ws_raw.iloc[:, 0].astype(str).str.contains('mean|rata|total', case=False, na=False)]
            
            # Melt data dari matriks lebar menjadi format panjang (Direction, Speed_Class, Frequency)
            df_melted = df_wind_clean.melt(id_vars=[first_col_name], var_name="Speed_Class", value_name="Frequency")
            df_melted.rename(columns={first_col_name: "Direction"}, inplace=True)
            df_melted['Frequency'] = pd.to_numeric(df_melted['Frequency'], errors='coerce').fillna(0)

            # Plotly Express Polar Bar (Windrose)
            fig_wind = px.bar_polar(
                df_melted, 
                r="Frequency", 
                theta="Direction", 
                color="Speed_Class",
                color_discrete_sequence=px.colors.sequential.Plasma_r,
                template="plotly_white",
                title="Persentase Distribusi Angin Dominan"
            )
            fig_wind.update_layout(height=600)
            st.plotly_chart(fig_wind, use_container_width=True)

            # --- TABEL WINDROSE ---
            st.markdown("###### Tabel Persentase Distribusi Angin Berdasarkan Arah (Un-melted view)")
            
            # Format dataframe ke 2 desimal
            df_wind_clean_indexed = df_wind_clean.set_index(first_col_name)
            # Konversi semua ke numerik untuk proses style
            df_wind_clean_indexed = df_wind_clean_indexed.apply(pd.to_numeric, errors='coerce')
            
            st.dataframe(
                df_wind_clean_indexed.style.format(precision=2), 
                use_container_width=True
            )
            
        except Exception as e:
            st.warning(f"Tidak dapat memetakan data Windrose secara otomatis karena format matriks tidak standar. Error: {e}")
            st.write("Tampilan Data Raw Windrose:")
            st.dataframe(df_ws_raw.style.format(precision=2))

if __name__ == "__main__":
    main()
