"""
Aerodrome Climatological Summary (ACS) Dashboard
------------------------------------------------
A production-ready Streamlit application for analyzing diurnal patterns 
of Lowest Cloud Base frequencies. 

Author: Senior Meteorologist & Software Architect (AI)
Target: Streamlit Cloud (Python 3.11+)
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import logging
from pathlib import Path
from typing import List

# =====================================================================
# KONFIGURASI LOGGING & PAGE
# =====================================================================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

st.set_page_config(
    page_title="ACS: Lowest Cloud Base",
    page_icon="☁️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =====================================================================
# KONSTANTA
# =====================================================================
DATA_FILE = Path("hs_2021_2025.xlsx")
EXPECTED_COLUMNS = ["TIME", "YEAR", "<150", "<200", "<300", "<500", "<1000", "<1500"]
CATEGORIES = ["<150", "<200", "<300", "<500", "<1000", "<1500"]


# =====================================================================
# FUNGSI CSS & STYLING
# =====================================================================
def apply_custom_css() -> None:
    st.markdown("""
        <style>
        .main {
            background-color: #FAFAFA;
        }
        .metric-card {
            background-color: white;
            border-radius: 8px;
            padding: 20px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.05);
            text-align: center;
            border-left: 4px solid #1f77b4;
        }
        .metric-title {
            color: #555;
            font-size: 14px;
            font-weight: 600;
            text-transform: uppercase;
        }
        .metric-value {
            color: #1f77b4;
            font-size: 28px;
            font-weight: bold;
            margin-top: 10px;
        }
        h1, h2, h3 {
            color: #2c3e50;
        }
        </style>
    """, unsafe_allow_html=True)


# =====================================================================
# FUNGSI PEMROSESAN DATA (SMART LOADER)
# =====================================================================
@st.cache_data(show_spinner="Memindai, membersihkan, dan memvalidasi struktur data Excel...")
def load_and_validate_data(filepath: Path) -> pd.DataFrame:
    """
    Membaca file excel dengan algoritma Smart Loader: 
    - Mencari letak baris header secara otomatis
    - Memeriksa seluruh sheet
    - Membersihkan spasi tersembunyi pada nama kolom
    """
    try:
        if not filepath.exists():
            raise FileNotFoundError(f"File data '{filepath}' tidak ditemukan di repository.")
            
        xl = pd.ExcelFile(filepath, engine="openpyxl")
        
        df_valid = None
        sheet_terdeteksi = ""
        
        # 1. Iterasi semua sheet untuk mencari yang mengandung format tabel ACS
        for sheet in xl.sheet_names:
            # Baca sampel 15 baris pertama untuk mencari posisi header
            sample_df = pd.read_excel(filepath, sheet_name=sheet, header=None, nrows=15, engine="openpyxl")
            
            header_row = -1
            for idx, row in sample_df.iterrows():
                # Bersihkan setiap sel ke bentuk string uppercase bebas spasi
                row_str = [str(val).strip().upper() for val in row.values]
                if 'TIME' in row_str or '<150' in row_str:
                    header_row = idx
                    break
                    
            if header_row != -1:
                # Baca ulang DataFrame menggunakan index header yang ditemukan
                temp_df = pd.read_excel(filepath, sheet_name=sheet, header=header_row, engine="openpyxl")
                
                # 2. Pembersihan nama kolom (Hapus spasi tersembunyi)
                temp_df.columns = temp_df.columns.astype(str).str.strip()
                
                # 3. Normalisasi Case untuk 'TIME' dan 'YEAR'
                rename_map = {}
                for col in temp_df.columns:
                    if col.upper() == 'TIME': rename_map[col] = 'TIME'
                    if col.upper() == 'YEAR': rename_map[col] = 'YEAR'
                temp_df.rename(columns=rename_map, inplace=True)
                
                # Cek apakah seluruh 8 kolom wajib sudah ada di temp_df
                missing = [c for c in EXPECTED_COLUMNS if c not in temp_df.columns]
                if not missing:
                    df_valid = temp_df
                    sheet_terdeteksi = sheet
                    break # Hentikan pencarian jika menemukan 1 sheet yang memenuhi syarat
                    
        if df_valid is None:
            raise ValueError(f"Sistem tidak dapat menemukan kolom wajib {EXPECTED_COLUMNS} di sheet manapun. Pastikan format tabel di Excel sudah benar.")
            
        logger.info(f"Data valid ditemukan pada sheet: '{sheet_terdeteksi}'")
        
        # Ambil kolom yang diperlukan saja sesuai urutan
        df = df_valid[EXPECTED_COLUMNS].copy()

        # 4. Tangani Missing Value & NaN (Isi dengan 0 untuk frekuensi)
        df.fillna(0, inplace=True)
        
        # 5. Konversi Tipe Data
        df['TIME'] = pd.to_numeric(df['TIME'], errors='coerce')
        df['YEAR'] = pd.to_numeric(df['YEAR'], errors='coerce')
        for cat in CATEGORIES:
            df[cat] = pd.to_numeric(df[cat], errors='coerce')
            
        # 6. Drop baris jika TIME atau YEAR rusak (menjadi NaN setelah coerce)
        df.dropna(subset=['TIME', 'YEAR'], inplace=True)
        
        # Cast TIME dan YEAR ke integer
        df['TIME'] = df['TIME'].astype(int)
        df['YEAR'] = df['YEAR'].astype(int)
        
        # 7. Hapus duplikasi jika ada (TIME dan YEAR yang sama)
        df.drop_duplicates(subset=['TIME', 'YEAR'], keep='last', inplace=True)
        
        # 8. Urutkan berdasarkan YEAR dan TIME
        df.sort_values(by=['YEAR', 'TIME'], inplace=True)
        df.reset_index(drop=True, inplace=True)
        
        return df

    except FileNotFoundError as e:
        logger.error(str(e))
        st.error(f"🚨 Kesalahan Akses File: {str(e)}")
        st.stop()
    except ValueError as e:
        logger.error(str(e))
        st.error(f"🚨 Kesalahan Struktur Data: {str(e)}")
        st.stop()
    except Exception as e:
        logger.error(f"Kesalahan tak terduga saat memuat data: {str(e)}")
        st.error(f"🚨 Terjadi kesalahan kritis: {str(e)}")
        st.stop()


@st.cache_data(show_spinner="Menghitung rata-rata klimatologi...")
def get_climatological_mean(df: pd.DataFrame) -> pd.DataFrame:
    try:
        mean_df = df.groupby('TIME')[CATEGORIES].mean().reset_index()
        mean_df['YEAR'] = "Mean 2021-2025"
        mean_df = mean_df[['TIME', 'YEAR'] + CATEGORIES]
        return mean_df
    except Exception as e:
        logger.error(f"Gagal menghitung klimatologi: {str(e)}")
        st.error("🚨 Terjadi kesalahan saat memproses perhitungan rata-rata.")
        st.stop()


# =====================================================================
# FUNGSI VISUALISASI PLOTLY
# =====================================================================
def plot_meteogram(df: pd.DataFrame, selected_cats: List[str], title_suffix: str) -> go.Figure:
    try:
        fig = go.Figure()
        color_palette = px.colors.qualitative.Prism

        for idx, cat in enumerate(selected_cats):
            fig.add_trace(go.Scatter(
                x=df['TIME'],
                y=df[cat],
                mode='lines+markers',
                name=f"Kategori {cat} ft",
                line=dict(width=3, color=color_palette[idx % len(color_palette)]),
                marker=dict(size=8, symbol='circle'),
                hovertemplate="<b>Jam:</b> %{x}:00 UTC<br><b>Kategori:</b> " + cat + " ft<br><b>Frekuensi:</b> %{y:.2f}%<extra></extra>"
            ))
            
        fig.update_layout(
            title=f"Diurnal Meteogram of Lowest Cloud Base Frequency ({title_suffix})",
            xaxis_title="Hour (UTC)",
            yaxis_title="Frequency (%)",
            xaxis=dict(tickmode='linear', tick0=0, dtick=1, range=[-0.5, 23.5]),
            yaxis=dict(range=[0, max(df[selected_cats].max().max() * 1.1, 1)]),
            hovermode="x unified",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            template="plotly_white",
            margin=dict(l=40, r=40, t=80, b=40)
        )
        return fig
    except Exception as e:
        logger.error(f"Error plotting meteogram: {str(e)}")
        st.error("🚨 Gagal memuat Meteogram.")
        return go.Figure()


def plot_heatmap(df: pd.DataFrame, selected_cats: List[str], title_suffix: str) -> go.Figure:
    try:
        z_data = df[selected_cats].values.T
        
        fig = go.Figure(data=go.Heatmap(
            z=z_data,
            x=df['TIME'],
            y=[f"{cat} ft" for cat in selected_cats],
            colorscale='Turbo',
            colorbar=dict(title="Freq (%)"),
            hovertemplate="<b>Jam:</b> %{x}:00 UTC<br><b>Kategori:</b> %{y}<br><b>Frekuensi:</b> %{z:.2f}%<extra></extra>"
        ))
        
        fig.update_layout(
            title=f"Heatmap Distribusi Frekuensi Basis Awan ({title_suffix})",
            xaxis_title="Hour (UTC)",
            yaxis_title="Cloud Base Categories",
            xaxis=dict(tickmode='linear', tick0=0, dtick=1),
            template="plotly_white",
            margin=dict(l=40, r=40, t=80, b=40)
        )
        return fig
    except Exception as e:
        logger.error(f"Error plotting heatmap: {str(e)}")
        st.error("🚨 Gagal memuat Heatmap.")
        return go.Figure()


# =====================================================================
# FUNGSI STATISTIK & ANALISIS
# =====================================================================
def generate_summary_statistics(df: pd.DataFrame, selected_cats: List[str]) -> pd.DataFrame:
    try:
        stats_list = []
        for cat in selected_cats:
            series = df[cat]
            stats_list.append({
                "Kategori (ft)": cat,
                "Maximum (%)": series.max(),
                "Minimum (%)": series.min(),
                "Mean (%)": series.mean(),
                "Median (%)": series.median(),
                "Standard Deviation": series.std(),
                "Range (%)": series.max() - series.min()
            })
        stats_df = pd.DataFrame(stats_list)
        return stats_df.round(2)
    except Exception as e:
        logger.error(f"Error calculating stats: {str(e)}")
        return pd.DataFrame()


def generate_auto_interpretation(df: pd.DataFrame, selected_cats: List[str], mode: str) -> str:
    try:
        if df.empty or not selected_cats:
            return "Data tidak tersedia untuk memberikan interpretasi."

        all_vals = df[selected_cats].values
        global_max = all_vals.max()
        global_mean = all_vals.mean()
        
        max_loc = df[selected_cats].max().idxmax()
        max_time = df.loc[df[max_loc].idxmax(), 'TIME']
        
        min_loc = df[selected_cats].min().idxmin()
        min_time = df.loc[df[min_loc].idxmin(), 'TIME']
        
        range_val = global_max - all_vals.min()

        interpretation = f"""
        **Interpretasi Klimatologis ({mode}):**
        
        Berdasarkan analisis distribusi temporal frekuensi *Lowest Cloud Base*, kejadian puncak terpantau pada kategori **{max_loc} ft** dengan probabilitas **{global_max:.2f}%** yang terbentuk secara dominan pada jam **{max_time:02d}:00 UTC**. 
        Sebaliknya, frekuensi terendah tercatat pada kategori **{min_loc} ft** di jam **{min_time:02d}:00 UTC**.
        
        Secara agregat, rerata frekuensi basis awan untuk profil yang dianalisis ini berada pada angka **{global_mean:.2f}%** dengan variabilitas rentang (*range*) sebesar **{range_val:.2f}%**. 
        Pola diurnal ini merepresentasikan efek dari variasi siklus pemanasan radiatif lokal di wilayah pangkalan terhadap batas stabilitas atmosfer.
        """
        return interpretation
    except Exception as e:
        logger.error(f"Error generating interpretation: {str(e)}")
        return "Terjadi kesalahan saat memproses interpretasi otomatis."


# =====================================================================
# MAIN APLIKASI
# =====================================================================
def main():
    apply_custom_css()
    
    # 1. Load Data
    raw_df = load_and_validate_data(DATA_FILE)
    mean_df = get_climatological_mean(raw_df)
    
    # 2. Sidebar Configuration
    st.sidebar.title("Aerodrome Climatological Summary")
    st.sidebar.markdown("---")
    
    year_options = ["Mean 2021-2025"] + [str(y) for y in sorted(raw_df['YEAR'].unique())]
    selected_year = st.sidebar.radio("Pilih Periode / Tahun", year_options)
    
    st.sidebar.markdown("---")
    selected_cats = st.sidebar.multiselect(
        "Pilih Kategori Cloud Base (ft)",
        options=CATEGORIES,
        default=CATEGORIES
    )
    
    if not selected_cats:
        st.warning("⚠️ Silakan pilih setidaknya satu kategori di sidebar untuk menampilkan visualisasi.")
        st.stop()
        
    st.sidebar.markdown("---")
    st.sidebar.info(
        "**Info:**\n"
        "Waktu direpresentasikan dalam **UTC**.\n"
        "Nilai adalah probabilitas frekuensi (%)."
    )

    # 3. Filter Data berdasarkan Pilihan Sidebar
    if selected_year == "Mean 2021-2025":
        display_df = mean_df.copy()
        period_title = "Mean Klimatologi (2021-2025)"
        num_years = 5
    else:
        display_df = raw_df[raw_df['YEAR'] == int(selected_year)].copy()
        period_title = f"Tahun {selected_year}"
        num_years = 1
        
    display_df.sort_values('TIME', inplace=True)
    display_df.reset_index(drop=True, inplace=True)

    # 4. Header UI
    st.title("☁️ Aerodrome Climatological Summary")
    st.subheader(f"Analisis Pola Diurnal Lowest Cloud Base ({period_title})")
    st.markdown("""
        Dashboard operasional ini menampilkan distribusi frekuensi kejadian 
        ketinggian dasar awan terendah (*Lowest Cloud Base*) dalam resolusi temporal per jam (UTC).
    """)
    st.markdown("---")
    
    # 5. KPI Cards
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f'<div class="metric-card"><div class="metric-title">Jumlah Tahun</div><div class="metric-value">{num_years}</div></div>', unsafe_allow_html=True)
    with col2:
        st.markdown(f'<div class="metric-card"><div class="metric-title">Jumlah Jam (Grid)</div><div class="metric-value">{len(display_df)}</div></div>', unsafe_allow_html=True)
    with col3:
        st.markdown(f'<div class="metric-card"><div class="metric-title">Kategori Dianalisis</div><div class="metric-value">{len(selected_cats)}</div></div>', unsafe_allow_html=True)
    with col4:
        overall_mean = display_df[selected_cats].values.mean()
        st.markdown(f'<div class="metric-card"><div class="metric-title">Rata-rata Persentase</div><div class="metric-value">{overall_mean:.2f}%</div></div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # 6. Kontainer Grafik Interaktif
    st.markdown("### Visualisasi Interaktif")
    
    tab1, tab2 = st.tabs(["📉 Meteogram (Line Scatter)", "🔲 Heatmap (Distribusi)"])
    
    with tab1:
        fig_meteogram = plot_meteogram(display_df, selected_cats, period_title)
        st.plotly_chart(fig_meteogram, use_container_width=True, config={'displayModeBar': True})
        
        try:
            html_meteogram = fig_meteogram.to_html()
            st.download_button(
                label="📥 Download Meteogram (HTML)",
                data=html_meteogram,
                file_name=f"meteogram_acs_{selected_year.replace(' ', '_')}.html",
                mime="text/html"
            )
        except Exception as e:
            logger.error(f"Error generating plot download: {str(e)}")
            
    with tab2:
        fig_heatmap = plot_heatmap(display_df, selected_cats, period_title)
        st.plotly_chart(fig_heatmap, use_container_width=True, config={'displayModeBar': True})
        
        try:
            html_heatmap = fig_heatmap.to_html()
            st.download_button(
                label="📥 Download Heatmap (HTML)",
                data=html_heatmap,
                file_name=f"heatmap_acs_{selected_year.replace(' ', '_')}.html",
                mime="text/html"
            )
        except Exception as e:
            logger.error(f"Error generating heatmap download: {str(e)}")

    st.markdown("---")

    # 7. Summary Statistics & Auto Interpretation
    col_stat, col_interp = st.columns([1, 1])
    
    with col_stat:
        st.markdown("### Ringkasan Statistik Data")
        stats_df = generate_summary_statistics(display_df, selected_cats)
        st.dataframe(
            stats_df, 
            hide_index=True, 
            use_container_width=True,
            column_config={
                col: st.column_config.NumberColumn(col, format="%.2f") 
                for col in stats_df.columns if col != "Kategori (ft)"
            }
        )
        
        try:
            csv_data = display_df[['TIME'] + selected_cats].to_csv(index=False).encode('utf-8')
            st.download_button(
                label="💾 Download Data Tabel (CSV)",
                data=csv_data,
                file_name=f"acs_data_{selected_year.replace(' ', '_')}.csv",
                mime="text/csv",
                type="primary"
            )
        except Exception as e:
            logger.error(f"Error generating CSV download: {str(e)}")
            
    with col_interp:
        st.markdown("### Sintesis Meteorologis")
        st.info(generate_auto_interpretation(display_df, selected_cats, period_title))


if __name__ == '__main__':
    main()
