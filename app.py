import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import io
import os

# Konfigurasi Halaman Utama Streamlit
st.set_page_config(
    page_title="Interactive Diurnal Meteogram Analysis",
    page_icon="📊",
    layout="wide"
)

st.title("📊 Analisis Pola Diurnal & Meteogram Interaktif")
st.write("Aplikasi ini membaca data frekuensi atmosfer/cuaca bulanan dan menyajikannya dalam bentuk visualisasi pola diurnal (00-23 GMT) secara bersih dan informatif.")

# ==========================================
# FUNCTION: Pembaca Data & Pembersih Tahan Banting
# ==========================================
def load_and_clean_csv(uploaded_file):
    try:
        # Membaca mentah baris awal untuk mencari letak header yang sebenarnya
        bytes_data = uploaded_file.getvalue()
        lines = bytes_data.decode("utf-8").split("\n")
        
        header_idx = 0
        for i, line in enumerate(lines[:10]):
            # Menemukan baris yang mengandung penanda waktu utama
            if "TIME" in line and "YEAR" in line:
                header_idx = i
                break
        
        # Membaca ulang menggunakan pandas dari baris header yang tepat
        uploaded_file.seek(0)
        df = pd.read_csv(uploaded_file, skiprows=header_idx)
        
        # Pembersihan Nama Kolom (menghilangkan spasi/pindah baris tak terlihat)
        df.columns = [str(col).strip().replace('\n', ' ') for col in df.columns]
        
        # Validasi kolom minimum
        if 'TIME' not in df.columns or 'YEAR' not in df.columns:
            st.error(f"Format kolom tidak sesuai pada file: {uploaded_file.name}. Pastikan terdapat kolom 'TIME' dan 'YEAR'.")
            return None
            
        # Rename kolom pertama jika mengandung teks tambahan seperti '(GMT)'
        df.rename(columns={df.columns[0]: 'TIME', df.columns[1]: 'YEAR'}, inplace=True)
        
        # Filter hanya baris yang kolom TIME-nya numerik (0-23)
        df['TIME_clean'] = pd.to_numeric(df['TIME'], errors='coerce')
        df = df.dropna(subset=['TIME_clean'])
        df['TIME'] = df['TIME_clean'].astype(int)
        df.drop(columns=['TIME_clean'], inplace=True)
        
        # Filter jam valid (0-23)
        df = df[df['TIME'].between(0, 23)]
        
        # Konversi semua kolom parameter (kolom ke-3 dst) menjadi numerik & tangani missing values
        value_cols = df.columns[2:]
        for col in value_cols:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0.0)
            
        return df
    except Exception as e:
        st.error(f"Gagal memproses file {uploaded_file.name}: {str(e)}")
        return None

# ==========================================
# SIDEBAR: Unggah File & Kontrol
# ==========================================
st.sidebar.header("📁 Unggah Data & Pengaturan")
uploaded_files = st.sidebar.file_uploader(
    "Unggah File CSV Bulanan (Bisa pilih banyak sekaligus)", 
    type=["csv"], 
    accept_multiple_files=True
)

if uploaded_files:
    all_data = {}
    for f in uploaded_files:
        # Ekstrak nama bulan atau identitas dari nama file
        month_name = f.name.split("-")[-1].replace(".csv", "").strip() if "-" in f.name else f.name.replace(".csv", "")
        cleaned_df = load_and_clean_csv(f)
        if cleaned_df is not None:
            all_data[month_name] = cleaned_df

    if all_data:
        st.sidebar.success(f"Berhasil memuat {len(all_data)} file bulan!")
        
        # Pilihan Bulan untuk Analisis
        selected_month = st.sidebar.selectbox("Pilih Bulan Analisis:", list(all_data.keys()))
        df_selected = all_data[selected_month]
        
        # Pilihan Rentang Tahun jika tersedia multi-tahun
        available_years = sorted(df_selected['YEAR'].unique().astype(int).tolist())
        selected_years = st.sidebar.multiselect("Pilih Tahun (Kosongkan untuk Semua Tahun):", available_years, default=available_years)
        
        if selected_years:
            df_filtered = df_selected[df_selected['YEAR'].isin(selected_years)]
        else:
            df_filtered = df_selected

        # Proteksi jika setelah filter data kosong
        if df_filtered.empty:
            st.warning("Data kosong setelah difilter berdasarkan tahun.")
        else:
            # Agregasi Rata-rata Pola Diurnal berdasarkan Jam (00-23)
            diurnal_profile = df_filtered.groupby('TIME').mean().reset_index()
            # Memastikan urutan jam runtut dari 0 sampai 23
            diurnal_profile = diurnal_profile.sort_values('TIME')
            
            # Mendapatkan list parameter/kolom nilai (di luar TIME dan YEAR)
            parameter_cols = [col for col in diurnal_profile.columns if col not in ['TIME', 'YEAR']]
            
            # Pilihan Tipe Tampilan Grafik Meteogram
            chart_type = st.sidebar.radio("Tipe Visualisasi Meteogram:", ["Grafik Area Bertumpuk (Meteogram Standar)", "Grafik Garis (Tren Perbandingan)"])

            # ==========================================
            # MAIN TABS: Visualisasi & Data Mentah
            # ==========================================
            tab1, tab2 = st.tabs(["📊 Meteogram Pola Diurnal", "📋 Data Teragregasi"])
            
            with tab1:
                st.subheader(f"Meteogram Diurnal - Bulan: {selected_month}")
                st.caption(f"Menampilkan rata-rata frekuensi (%) kejadian berdasarkan waktu diurnal (00-23 GMT) untuk tahun {', '.join(map(str, selected_years)) if selected_years else 'Semua Tahun'}")
                
                # Inisialisasi Grafik Plotly
                fig = go.Figure()
                
                # Menambahkan trace untuk setiap kategori/parameter
                for col in parameter_cols:
                    if chart_type == "Grafik Area Bertumpuk (Meteogram Standar)":
                        fig.add_trace(go.Scatter(
                            x=diurnal_profile['TIME'],
                            y=diurnal_profile[col],
                            name=col,
                            mode='lines',
                            stackgroup='one', # Membuat efek bertumpuk (stacked area) khas meteogram
                            hovertemplate=f"<b>Jam %{{x}}:00 GMT</b><br>{col}: %{{y}}%<extra></extra>"
                        ))
                    else:
                        fig.add_trace(go.Scatter(
                            x=diurnal_profile['TIME'],
                            y=diurnal_profile[col],
                            name=col,
                            mode='lines+markers',
                            hovertemplate=f"<b>Jam %{{x}}:00 GMT</b><br>{col}: %{{y}}%<extra></extra>"
                        ))
                
                # Pengaturan Layout Grafik agar Informatif dan Bersih
                fig.update_layout(
                    xaxis=dict(
                        title="Waktu Diurnal (GMT / UTC)",
                        tickmode='array',
                        tickvals=list(range(0, 24)),
                        ticktext=[f"{str(h).zfill(2)}:00" for h in range(0, 24)],
                        gridcolor='rgba(200, 200, 200, 0.2)'
                    ),
                    yaxis=dict(
                        title="Frekuensi Kemunculan (%)",
                        hoverformat=".2f",
                        gridcolor='rgba(200, 200, 200, 0.2)'
                    ),
                    hovermode="x unified",
                    legend=dict(
                        orientation="h",
                        yanchor="bottom",
                        y=1.02,
                        xanchor="right",
                        x=1
                    ),
                    margin=dict(l=40, r=40, t=80, b=40),
                    height=550,
                    template="plotly_white"
                )
                
                # Tampilkan grafik interaktif ke Streamlit
                st.plotly_chart(fig, use_container_width=True)
                
                # Informasi Tambahan / Insight Pembacaan
                st.info("""
                💡 **Cara Membaca Meteogram:**
                * Sumbu-X menunjukkan siklus waktu 24 jam penuh (Format GMT).
                * Setiap warna mewakili batas parameter akumulasi tinggi dasar awan / nilai parameter atmosfer terkait.
                * Arahkan kursor Anda ke grafik untuk melihat detail nilai persentase di jam tertentu secara real-time.
                """)
                
            with tab2:
                st.subheader("Data Rata-rata Pola Diurnal Terhitung")
                st.dataframe(diurnal_profile.set_index('TIME'), use_container_width=True)
                
                # Tombol Unduh Data Hasil Agregasi
                csv_buffer = io.StringIO()
                diurnal_profile.to_csv(csv_buffer, index=False)
                st.download_button(
                    label="📥 Unduh Data Agregasi (CSV)",
                    data=csv_buffer.getvalue(),
                    file_name=f"diurnal_profile_{selected_month}.csv",
                    mime="text/csv"
                )
    else:
        st.info("💡 Silakan unggah satu atau beberapa file CSV di panel sebelah kiri untuk memulai pemrosesan meteogram.")
else:
    st.info("👋 Selamat Datang! Silakan unggah berkas data cuaca Anda melalui sidebar kiri untuk memplot Pola Diurnal secara otomatis.")
