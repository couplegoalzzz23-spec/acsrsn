import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import logging

# Setup Logging untuk mendeteksi error di Streamlit Cloud
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Konfigurasi Halaman Streamlit
st.set_page_config(
    page_title="Dashboard Meteorologi | Analisis Cloud Base",
    page_icon="⛅",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS untuk tampilan KPI/Metrik yang rapi
st.markdown("""
    <style>
    .metric-card {
        background-color: #262730;
        padding: 15px;
        border-radius: 10px;
        text-align: center;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.3);
    }
    .st-emotion-cache-1wivap2 {
        padding-top: 2rem;
    }
    </style>
""", unsafe_allow_html=True)

@st.cache_data(show_spinner=False)
def load_and_validate_data(uploaded_files):
    all_data = []
    
    for uploaded_file in uploaded_files:
        try:
            # Identifikasi format (mendukung file Excel multi-sheet dan kumpulan CSV)
            if uploaded_file.name.endswith('.csv'):
                df = pd.read_csv(uploaded_file, header=None)
                sheet_dict = {uploaded_file.name.replace('.csv', ''): df}
            elif uploaded_file.name.endswith(('.xls', '.xlsx')):
                sheet_dict = pd.read_excel(uploaded_file, sheet_name=None, header=None)
            else:
                st.warning(f"Format file {uploaded_file.name} tidak didukung.")
                continue
            
            # Iterasi untuk tiap bulan/sheet
            for sheet_name, df in sheet_dict.items():
                # Pencarian baris dinamis: Cari baris mana saja yang mengandung teks 'TIME'
                header_row_mask = df.apply(lambda r: r.astype(str).str.contains('TIME', case=False, na=False).any(), axis=1)
                
                if not header_row_mask.any():
                    logging.warning(f"Kolom TIME tidak ditemukan di sheet {sheet_name}")
                    continue
                    
                idx = header_row_mask.idxmax()
                col_part1 = df.iloc[idx].fillna("").astype(str)
                col_part2 = df.iloc[idx+1].fillna("").astype(str)
                
                cols = []
                # Penggabungan header multi-level menjadi header tunggal yang bersih
                for c1, c2 in zip(col_part1, col_part2):
                    c1_str = str(c1).strip()
                    c2_str = str(c2).strip()
                    
                    if "TIME" in c1_str:
                        cols.append("TIME")
                    elif "YEAR" in c1_str:
                        cols.append("YEAR")
                    elif "<" in c2_str or ">" in c2_str:
                        cols.append(c2_str)
                    else:
                        cols.append(c2_str if c2_str and c2_str.lower() != 'nan' else c1_str)
                
                # Ekstrak data murni (di bawah baris header)
                data = df.iloc[idx+2:].copy()
                data.columns = [c.strip() for c in cols]
                
                # Buang kolom yang tidak terpakai/kosong
                data = data.loc[:, [bool(c) for c in data.columns]]
                
                if "TIME" not in data.columns or "YEAR" not in data.columns:
                    logging.error(f"Struktur kolom utama (TIME/YEAR) tidak lengkap di {sheet_name}")
                    continue
                
                data["Bulan_Sumber"] = sheet_name
                
                # Konversi menjadi format numerik
                for col in data.columns:
                    if col != "Bulan_Sumber":
                        data[col] = pd.to_numeric(data[col], errors='coerce')
                
                data = data.dropna(subset=['TIME', 'YEAR'])
                all_data.append(data)
                
        except Exception as e:
            logging.error(f"Error pembacaan pada file {uploaded_file.name}: {e}")
            st.error(f"Gagal memproses file {uploaded_file.name}: {e}")
            
    if all_data:
        final_df = pd.concat(all_data, ignore_index=True)
        return final_df
    return pd.DataFrame()

def main():
    st.title("⛅ Dashboard Meteorologi Profesional")
    st.markdown("### Analisis Profil Ketinggian Dasar Awan (Cloud Base Height)")
    
    # --- KONFIGURASI SIDEBAR ---
    with st.sidebar:
        st.header("⚙️ Data Input")
        uploaded_files = st.file_uploader(
            "Unggah Data Pengamatan", 
            type=['xlsx', 'xls', 'csv'], 
            accept_multiple_files=True,
            help="Unggah file utama (contoh: HS_2021-2025.xlsx) yang memuat sheet dari Januari hingga Desember."
        )
        st.markdown("---")
        st.info("💡 **Tips Deployment Cloud:** Aplikasi ini kompatibel dengan Streamlit Community Cloud.")
    
    # --- HALAMAN UTAMA ---
    if uploaded_files:
        with st.spinner('Memvalidasi dan mengolah struktur data...'):
            df = load_and_validate_data(uploaded_files)
            
        if df.empty:
            st.error("❌ Data tidak valid. Pastikan template format pengamatan (terutama baris 'TIME') sesuai.")
            st.stop()
            
        st.success(f"✅ Sistem berhasil mendeteksi dan membersihkan **{len(df)}** baris data harian!")
        
        # Ekstraksi otomatis rentang base awan (contoh: < 150, < 200)
        threshold_cols = [c for c in df.columns if '<' in c or '>' in c]
        
        # --- FILTER DATA BERDASARKAN TAHUN ---
        st.sidebar.subheader("🔍 Filter Analisis")
        available_years = sorted(df['YEAR'].dropna().unique().astype(int).tolist())
        selected_years = st.sidebar.multiselect(
            "Pilih Rentang Tahun", 
            options=available_years, 
            default=available_years
        )
        
        if not selected_years:
            st.warning("⚠️ Mohon centang setidaknya satu tahun pada panel filter (sebelah kiri).")
            st.stop()
            
        filtered_df = df[df['YEAR'].isin(selected_years)]
        
        # --- PERHITUNGAN MEAN KLIMATOLOGI DIURNAL ---
        st.markdown("---")
        st.header("📊 Statistik Klimatologi Diurnal")
        st.markdown(f"Menampilkan agregasi (rata-rata persentase) dasar awan untuk periode tahun **{min(selected_years)} hingga {max(selected_years)}**.")
        
        mean_df = filtered_df.groupby('TIME')[threshold_cols].mean().reset_index()
        
        # --- KOTAK METRIK UTAMA ---
        st.subheader("📈 Rekapitulasi Global (Periode Filter)")
        col1, col2, col3 = st.columns(3)
        max_val = mean_df[threshold_cols].max().max()
        min_val = mean_df[threshold_cols].min().min()
        avg_val = mean_df[threshold_cols].mean().mean()
        
        col1.metric("Frekuensi Maksimum (%)", f"{max_val:.2f}%")
        col2.metric("Frekuensi Minimum (%)", f"{min_val:.2f}%")
        col3.metric("Rata-rata Global (%)", f"{avg_val:.2f}%")

        # --- GRAFIK MULTI-LINE METEOGRAM ---
        st.markdown("---")
        st.subheader("📉 Meteogram Multi-Line: Siklus Frekuensi Dasar Awan")
        
        fig_line = go.Figure()
        for col in threshold_cols:
            fig_line.add_trace(go.Scatter(
                x=mean_df['TIME'], 
                y=mean_df[col], 
                mode='lines+markers',
                name=f'Base {col} ft',
                hovertemplate='Jam (GMT): %{x}<br>Frekuensi: %{y:.2f}%<extra></extra>'
            ))
            
        fig_line.update_layout(
            xaxis_title="Waktu Pengamatan (Jam - GMT)",
            yaxis_title="Frekuensi Kemunculan (%)",
            xaxis=dict(tickmode='linear', tick0=0, dtick=1),
            hovermode="x unified",
            legend_title="Batas Ketinggian",
            margin=dict(l=20, r=20, t=30, b=20)
        )
        
        # theme="streamlit" memastikan grafik menyesuaikan (Dark Mode / Light Mode) dari user preference
        st.plotly_chart(fig_line, theme="streamlit", use_container_width=True)
        
        # --- HEATMAP DISTRIBUSI DIURNAL ---
        st.markdown("---")
        st.subheader("🔥 Heatmap Diurnal Distribusi Ketinggian Awan")
        
        # Pivot (Tidy Format) agar kompatibel dengan parameter imshow (Heatmap)
        heatmap_data = mean_df.set_index('TIME')[threshold_cols].T
        
        fig_heat = px.imshow(
            heatmap_data,
            labels=dict(x="Waktu Pengamatan (GMT)", y="Ketinggian Awan (ft)", color="Frekuensi (%)"),
            x=heatmap_data.columns,
            y=heatmap_data.index,
            aspect="auto",
            color_continuous_scale="Turbo"  # Palet ideal untuk intensitas data cuaca
        )
        fig_heat.update_layout(
            xaxis=dict(tickmode='linear', dtick=1),
            margin=dict(l=20, r=20, t=30, b=20)
        )
        
        st.plotly_chart(fig_heat, theme="streamlit", use_container_width=True)
        
        # --- FITUR DOWNLOAD DATA (CSV & PNG) ---
        st.markdown("---")
        st.subheader("📥 Unduh Hasil Analisis & Data Tabular")
        
        col_dl1, col_dl2 = st.columns(2)
        with col_dl1:
            csv_data = mean_df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📄 Download Nilai Klimatologi (Format CSV)",
                data=csv_data,
                file_name="mean_klimatologi_diurnal.csv",
                mime="text/csv",
                use_container_width=True
            )
            
        with col_dl2:
            st.info("📸 **Unduh Grafik (PNG):** Arahkan kursor Anda ke sudut kanan atas salah satu grafik, lalu klik **ikon kamera**.")
            
        # Preview Tabel Ekstensif
        with st.expander("👁️ Tampilkan Tabel Matriks Klimatologi (Detail)"):
            st.dataframe(
                mean_df.style.format({col: "{:.2f}" for col in threshold_cols})
                       .background_gradient(cmap='Blues', subset=threshold_cols),
                use_container_width=True,
                height=400
            )

    else:
        st.info("👋 **Selamat datang di Dashboard Meteorologi!**")
        st.write("Silakan unggah file `HS_2021-2025.xlsx` pada panel kontrol di menu sebelah kiri untuk memulai visualisasi.")

if __name__ == "__main__":
    main()
