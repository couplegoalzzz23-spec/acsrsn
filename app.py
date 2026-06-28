import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os

# Konfigurasi Halaman Streamlit
st.set_page_config(
    page_title="Dashboard Meteorologi - Cloud Base",
    page_icon="⛅",
    layout="wide"
)

st.title("⛅ Dashboard Meteorologi Profesional")
st.markdown("### Analisis Ketinggian Dasar Awan (Cloud Base Height) 2021-2025")
st.write("Sistem membaca dataset langsung dari repositori. Silakan pilih bulan pada panel di sebelah kiri.")

# Daftar bulan sesuai format penamaan file Anda
BULAN_LIST = [
    "Januari", "Februari", "Maret", "April", "Mei", "Juni",
    "Juli", "Agustus", "September", "Oktober", "November", "Desember"
]

# Sidebar Konfigurasi
with st.sidebar:
    st.header("⚙️ Pengaturan")
    bulan_terpilih = st.selectbox("Pilih Bulan", BULAN_LIST)
    
@st.cache_data
def load_data(bulan):
    """
    Fungsi untuk membaca data secara otomatis berdasarkan bulan yang dipilih.
    Memanfaatkan cache untuk performa maksimal.
    """
    # Menyesuaikan nama file dengan format yang ada di Github
    filename = f"HS_2021-2025.xlsx - {bulan}.csv"
    
    # Cek apakah file ada di root direktori
    if not os.path.exists(filename):
        # Jika Anda menyimpannya di dalam folder (misal: 'data/'), ubah variabel filename di atas
        return None
    
    # Tentukan nama kolom secara eksplisit agar aman jika struktur file berubah sedikit
    cols = ['TIME', 'YEAR', '< 150', '< 200', '< 300', '< 500', '< 1000', '< 1500']
    
    try:
        # skiprows=5 digunakan untuk melewati 5 baris pertama yang bukan bagian tabel metrik
        df = pd.read_csv(filename, skiprows=5, names=cols, header=None)
        
        # Bersihkan baris yang kosong (drop NA)
        df = df.dropna(subset=['TIME', 'YEAR'])
        
        # Konversi kolom identitas ke format angka bulat (integer)
        df['TIME'] = pd.to_numeric(df['TIME'], errors='coerce').astype(int)
        df['YEAR'] = pd.to_numeric(df['YEAR'], errors='coerce').astype(int)
        
        # Konversi kolom frekuensi awan ke float/desimal
        for col in cols[2:]:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
            
        return df
    except Exception as e:
        st.error(f"Error membaca data: {e}")
        return None

# Eksekusi Pemanggilan Data
df = load_data(bulan_terpilih)

if df is not None and not df.empty:
    tahun_tersedia = sorted(df['YEAR'].unique())
    
    # Filter Berdasarkan Tahun
    st.sidebar.subheader("🔍 Filter Data")
    tahun_terpilih = st.sidebar.multiselect("Pilih Tahun Target", options=tahun_tersedia, default=tahun_tersedia)
    
    if not tahun_terpilih:
        st.warning("⚠️ Silakan pilih minimal satu tahun pada panel sebelah kiri.")
        st.stop()
        
    df_filter = df[df['YEAR'].isin(tahun_terpilih)]
    
    # Menghitung Mean Klimatologi
    cols_awan = ['< 150', '< 200', '< 300', '< 500', '< 1000', '< 1500']
    mean_df = df_filter.groupby('TIME')[cols_awan].mean().reset_index()
    
    st.markdown("---")
    st.header(f"📊 Statistik Klimatologi Diurnal - {bulan_terpilih}")
    
    # ✅ Hitung Statistik KPI
    max_val = mean_df[cols_awan].max().max()
    min_val = mean_df[cols_awan].min().min()
    avg_val = mean_df[cols_awan].mean().mean()
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Maksimum Frekuensi (%)", f"{max_val:.2f}%")
    col2.metric("Minimum Frekuensi (%)", f"{min_val:.2f}%")
    col3.metric("Rata-rata Global (%)", f"{avg_val:.2f}%")
    
    st.markdown("---")
    
    # ✅ Multi-line Meteogram menggunakan Plotly
    st.subheader("📉 Multi-line Meteogram Diurnal")
    fig_line = go.Figure()
    for col in cols_awan:
        fig_line.add_trace(go.Scatter(
            x=mean_df['TIME'], y=mean_df[col],
            mode='lines+markers', name=f'Base {col} ft',
            hovertemplate='Jam: %{x} GMT<br>Frekuensi: %{y:.2f}%<extra></extra>'
        ))
    
    fig_line.update_layout(
        xaxis_title="Waktu Pengamatan (GMT)", yaxis_title="Frekuensi Kemunculan (%)",
        xaxis=dict(tickmode='linear', dtick=1),
        hovermode="x unified", margin=dict(l=20, r=20, t=30, b=20)
    )
    st.plotly_chart(fig_line, use_container_width=True, theme="streamlit")
    
    # ✅ Heatmap Distribusi Diurnal
    st.markdown("---")
    st.subheader("🔥 Heatmap Distribusi Diurnal Awan")
    heatmap_data = mean_df.set_index('TIME')[cols_awan].T
    fig_heat = px.imshow(
        heatmap_data,
        labels=dict(x="Waktu Pengamatan (GMT)", y="Ketinggian Dasar Awan (ft)", color="Frekuensi (%)"),
        x=heatmap_data.columns, y=heatmap_data.index,
        aspect="auto", color_continuous_scale="Turbo"
    )
    fig_heat.update_layout(
        xaxis=dict(tickmode='linear', dtick=1),
        margin=dict(l=20, r=20, t=30, b=20)
    )
    st.plotly_chart(fig_heat, use_container_width=True, theme="streamlit")
    
    # ✅ Fitur Download & Tabel Data
    st.markdown("---")
    st.subheader("📥 Unduh Hasil Analisis")
    
    col_dl1, col_dl2 = st.columns(2)
    with col_dl1:
        # Download format CSV
        csv_data = mean_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📄 Download Mean Klimatologi (CSV)",
            data=csv_data, file_name=f"Mean_Klimatologi_{bulan_terpilih}.csv", 
            mime="text/csv", use_container_width=True
        )
    with col_dl2:
        # Notifikasi instruksi download gambar dari Plotly bawaan
        st.info("📸 **Unduh Grafik (PNG):** Arahkan kursor Anda ke sudut kanan atas grafik, lalu klik ikon **Camera**.")
        
    with st.expander("👁️ Tampilkan Data Tabular Lengkap"):
        st.dataframe(mean_df.style.format("{:.2f}", subset=cols_awan).background_gradient(cmap='Blues'), use_container_width=True)

else:
    # Error Handling jika file untuk bulan tersebut tidak tersedia
    st.error(f"❌ Berkas `HS_2021-2025.xlsx - {bulan_terpilih}.csv` tidak ditemukan di direktori utama Github Anda.")
    st.warning("Pastikan kerangka file CSV bulanan telah ter-upload di repository yang sama dengan letak file `app.py`.")
