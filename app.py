import streamlit as st
import pandas as pd
import plotly.express as px
import os

# Konfigurasi Halaman Utama
st.set_page_config(
    page_title="Analisis Ketinggian Dasar Awan (HS)",
    page_icon="✈️",
    layout="wide"
)

# Judul Utama Aplikasi
st.title("📊 Dasbor Analisis Ketinggian Dasar Awan (2021-2025)")
st.write("Sistem ini membaca data frekuensi ketinggian pangkalan awan terendah langsung dari framework repositori.")

# Daftar bulan sesuai dengan format penamaan file repositori
BULAN_LIST = [
    "Januari", "Februari", "Maret", "April", "Mei", "Juni",
    "Juli", "Agustus", "September", "Oktober", "November", "Desember"
]

# Sidebar Navigasi & Kontrol Parameter
st.sidebar.header("⚙️ Parameter Navigasi")
bulan_terpilih = st.sidebar.selectbox("Pilih Bulan Analisis:", BULAN_LIST)

# Penentuan jalur file otomatis (Mendukung file di root directory atau di dalam folder 'data')
nama_file = f"HS_2021-2025.xlsx - {bulan_terpilih}.csv"
path_file = nama_file

if not os.path.exists(path_file):
    # Jalur alternatif jika file dimasukkan ke dalam folder data
    path_file = os.path.join("data", nama_file)

@st.cache_data
def muat_data_otomatis(file_path):
    """
    Fungsi untuk memuat dan membersihkan data secara otomatis.
    Menggunakan caching untuk performa cepat dan efisien.
    """
    if not os.path.exists(file_path):
        return None
    try:
        # Definisi kolom secara manual agar struktur data tetap konsisten dan tahan banting
        kolom_kustom = ['TIME (GMT)', 'YEAR', 'HS', '< 150', '< 200', '< 300', '< 500', '< 1000', '< 1500']
        
        # Melewati 5 baris pertama yang berisi informasi judul non-tabel di file CSV
        df = pd.read_csv(file_path, skiprows=5, names=kolom_kustom, header=None)
        
        # Konversi tipe data utama ke numerik dan bersihkan baris kosong
        df['TIME (GMT)'] = pd.to_numeric(df['TIME (GMT)'], errors='coerce')
        df['YEAR'] = pd.to_numeric(df['YEAR'], errors='coerce')
        df = df.dropna(subset=['TIME (GMT)', 'YEAR'])
        
        # Mengubah indeks kolom waktu & tahun menjadi integer
        df['TIME (GMT)'] = df['TIME (GMT)'].astype(int)
        df['YEAR'] = df['YEAR'].astype(int)
        
        # Memastikan seluruh nilai frekuensi dikonversi ke float secara aman
        kolom_frekuensi = ['< 150', '< 200', '< 300', '< 500', '< 1000', '< 1500']
        for col in kolom_frekuensi:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
            
        return df
    except Exception as eks:
        st.error(f"Gagal memproses struktur data internal: {eks}")
        return None

# Proses Pemeriksaan dan Validasi File Data
if os.path.exists(path_file):
    data_aktif = muat_data_otomatis(path_file)
    
    if data_aktif is not None and not data_aktif.empty:
        # Pilihan Filter Multi-Tahun di Sidebar
        tahun_tersedia = sorted(data_aktif['YEAR'].unique())
        tahun_terpilih = st.sidebar.multiselect("Saring Berdasarkan Tahun:", options=tahun_tersedia, default=tahun_tersedia)
        
        # Penyaringan data berdasarkan input pengguna
        df_terfilter = data_aktif[data_aktif['YEAR'].isin(tahun_terpilih)]
        
        # Tampilan Utama Grafik Analisis
        st.subheader(f"📈 Tren Distribusi Frekuensi Ketinggian Dasar Awan — {bulan_terpilih}")
        
        mode_grafik = st.radio(
            "Pilih Mode Analisis Grafik:", 
            ["Rata-rata Distribusi per Jam (GMT)", "Analisis Spesifik Per Tahun"], 
            horizontal=True
        )
        
        kolom_kategori_awan = ['< 150', '< 200', '< 300', '< 500', '< 1000', '< 1500']
        
        if mode_grafik == "Rata-rata Distribusi per Jam (GMT)":
            # Agregasi data rerata berdasarkan waktu GMT
            df_rata_rata = df_terfilter.groupby('TIME (GMT)')[kolom_kategori_awan].mean().reset_index()
            df_panjang = df_rata_rata.melt(id_vars=['TIME (GMT)'], value_vars=kolom_kategori_awan, 
                                           var_name='Ketinggian Dasar Awan (Feet)', value_name='Persentase (%)')
            
            fig = px.line(
                df_panjang, 
                x='TIME (GMT)', 
                y='Persentase (%)', 
                color='Ketinggian Dasar Awan (Feet)',
                markers=True,
                title=f"Rata-rata Persentase Kemunculan Dasar Awan per Jam (GMT) — {bulan_terpilih}",
                labels={'TIME (GMT)': 'Waktu Siklus (GMT)'}
            )
            fig.update_layout(xaxis=dict(tickmode='linear', tick0=0, dtick=1))
            st.plotly_chart(fig, use_container_width=True)
            
        else:
            # Visualisasi detail per tahun terpilih
            tahun_spesifik = st.selectbox("Pilih Tahun Target:", tahun_terpilih)
            df_tahun_tunggal = df_terfilter[df_terfilter['YEAR'] == tahun_spesifik]
            df_panjang_tahun = df_tahun_tunggal.melt(id_vars=['TIME (GMT)'], value_vars=kolom_kategori_awan, 
                                                     var_name='Ketinggian Dasar Awan (Feet)', value_name='Persentase (%)')
            
            fig = px.bar(
                df_panjang_tahun, 
                x='TIME (GMT)', 
                y='Persentase (%)', 
                color='Ketinggian Dasar Awan (Feet)',
                barmode='group',
                title=f"Distribusi Persentase per Jam (GMT) pada Tahun {tahun_spesifik} — {bulan_terpilih}",
                labels={'TIME (GMT)': 'Waktu Siklus (GMT)'}
            )
            fig.update_layout(xaxis=dict(tickmode='linear', tick0=0, dtick=1))
            st.plotly_chart(fig, use_container_width=True)

        # Tabulasi Data Mentah Terfilter
        with st.expander("📄 Tampilkan Lembar Data Tabular"):
            st.dataframe(
                df_terfilter.style.format({col: "{:.2f}%" for col in kolom_kategori_awan}), 
                use_container_width=True
            )
    else:
        st.warning("Struktur data di dalam file kosong atau tidak dapat diuraikan.")
else:
    st.error(f"Berkas data `{nama_file}` tidak dapat ditemukan di root atau folder `data/`.")
    st.info("Pastikan Anda telah menyertakan semua file bulanan dengan penamaan yang tepat di dalam repositori GitHub Anda.")
