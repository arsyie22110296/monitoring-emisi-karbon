"""
APLIKASI MONITORING EMISI KARBON - EMISIKU
Multi-Fuel Support: Solar, Bensin, Kayu, LPG
Skripsi - Ariel Adrienne Setiawan (22110296)
"""

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

# Import modul lokal
from emission_calculator import calculate_emissions, get_emission_summary, FACTORS, FUEL_FACTORS, get_fuel_info
from clustering_engine import EmissionClusterAnalyzer
import visualizer as viz
import report_exporter as rex

# Logo dan Branding
import base64

# ================= KONFIGURASI HALAMAN =================
st.set_page_config(
    page_title="EmisiKu - Monitoring Emisi Karbon UMKM",
    page_icon="emisiku_logo.png",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ================= CUSTOM CSS PREMIUM =================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

* {
    font-family: 'Inter', sans-serif;
}

.stApp {
    background: linear-gradient(135deg, black 30%, dark grey 100%);
}

.metric-card {
    background: white;
    padding: 1.2rem;
    border-radius: 1rem;
    box-shadow: 0 4px 20px rgba(0,0,0,0.08);
    text-align: center;
    transition: transform 0.2s, box-shadow 0.2s;
}
.metric-card:hover {
    transform: translateY(-5px);
    box-shadow: 0 8px 30px rgba(0,0,0,0.12);
}
.metric-value {
    font-size: 2rem;
    font-weight: 800;
    color: #1a472a;
}
.metric-label {
    font-size: 0.8rem;
    color: #666;
    margin-top: 0.3rem;
}

.stButton > button {
    background: linear-gradient(135deg, #2ecc71, #27ae60);
    color: white;
    border: none;
    border-radius: 12px;
    padding: 0.6rem 1.5rem;
    font-weight: 600;
    transition: all 0.3s ease;
}
.stButton > button:hover {
    transform: scale(1.02);
    box-shadow: 0 8px 25px rgba(46,204,113,0.3);
    color: white;
}

div[data-testid="stExpander"]:hover {
    transform: translateX(5px);
    transition: 0.2s;
}

.footer {
    text-align: center;
    padding: 2rem 0 1rem 0;
    color: #888;
    font-size: 0.8rem;
    border-top: 1px solid #ddd;
    margin-top: 2rem;
}
</style>
""", unsafe_allow_html=True)

# ================= SIDEBAR =================
with st.sidebar:
    logo_path = Path("emisiku_logo.png")
    
    if logo_path.exists():
        with open(logo_path, "rb") as f:
            logo_data = base64.b64encode(f.read()).decode()
        
        st.markdown(f"""
        <div style="text-align: center; padding: 1rem 0;">
            <img src="data:image/png;base64,{logo_data}" style="width: 250px; margin-bottom: 10px;">
            <p style="color: white; font-size: 0.8rem;">Carbon Tracking for SMEs</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style="text-align: center; padding: 1rem 0;">
            <div style="font-size: 4rem;">🌿</div>
            <h2 style="margin: 0.5rem 0 0 0; font-size: 2rem; color: white;">EmisiKu</h2>
            <p style="color: white; font-size: 0.8rem;">Carbon Tracking for SMEs</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("""
    <div style="background: DodgerBlue; border-radius: 16px; padding: 1rem; margin: 1rem 0;">
        <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem;">
            <span style="font-size: 0.8rem;">🎯 Target Netral Karbon 2030</span>
            <span style="font-size: 0.8rem; font-weight: bold;">15%</span>
        </div>
        <progress value="15" max="100" style="width:100%; height:8px; border-radius:4px;"></progress>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    st.markdown("### 🔥 Jenis Bahan Bakar")
    
    fuel_type = st.radio(
        "Pilih jenis bahan bakar yang digunakan:",
        options=['solar', 'bensin', 'kayu', 'lpg'],
        format_func=lambda x: f"{FUEL_FACTORS[x]['icon']} {FUEL_FACTORS[x]['sumber'].split()[0]} - {x.upper()}",
        help="Pilih sesuai bahan bakar yang digunakan pabrik Anda"
    )
    
    fuel_info = get_fuel_info(fuel_type)
    st.caption(f"Faktor emisi: {fuel_info['value']} {fuel_info['unit']}")
    
    st.markdown("---")
    
    uploaded_file = st.file_uploader(
        "📂 Upload Data Emisi",
        type=['csv', 'xlsx'],
        help="Upload CSV/Excel dengan kolom: tanggal, listrik_kwh, bahan_bakar_liter/kg, jarak_tempuh_km"
    )
    
    with st.expander("📥 Download Template"):
        template_df = pd.DataFrame({
            'tanggal': ['2026-04-01', '2026-04-02'],
            'listrik_kwh': [150, 160],
            f'bahan_bakar_{fuel_info["unit"]}': [10, 12],
            'jarak_tempuh_km': [50, 55]
        })
        csv_template = template_df.to_csv(index=False)
        st.download_button(
            label="Download Template CSV",
            data=csv_template,
            file_name="template_emisi.csv",
            mime="text/csv"
        )
    
    st.markdown("---")
    st.markdown("### ℹ️ Faktor Emisi")
    
    st.caption(f"""
    {FUEL_FACTORS['listrik']['icon']} Listrik: {FUEL_FACTORS['listrik']['value']} {FUEL_FACTORS['listrik']['unit']}
    {fuel_info['icon']} {fuel_type.upper()}: {fuel_info['value']} {fuel_info['unit']}
    {FUEL_FACTORS['transportasi']['icon']} Transportasi: {FUEL_FACTORS['transportasi']['value']} {FUEL_FACTORS['transportasi']['unit']}
    """)

# ================= MAIN PAGE =================
st.title("🌍 EmisiKu")
st.markdown("*Sistem Monitoring Analisis Pola Emisi Karbon untuk UMKM dengan Menggunakan K-Means Clustering*")

# ================= LOAD DATA =================
if uploaded_file is not None:
    if uploaded_file.name.endswith('.csv'):
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_excel(uploaded_file)
    
    if 'tanggal' in df.columns:
        df['tanggal'] = pd.to_datetime(df['tanggal'])
    
    st.success(f"✅ Data berhasil dimuat: {df.shape[0]} baris, {df.shape[1]} kolom")
    st.caption(f"Jenis bahan bakar yang dipilih: {fuel_info['icon']} {fuel_type.upper()}")
    
    with st.expander("📋 Preview Data", expanded=False):
        st.dataframe(df.head(10), use_container_width=True)
    
    # ================= PERHITUNGAN EMISI =================
    st.subheader("📊 1. Perhitungan Emisi Karbon")
    
    df = calculate_emissions(df, fuel_type=fuel_type)
    emission_summary = get_emission_summary(df)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div style="font-size: 2rem;">🌍</div>
            <div class="metric-value">{emission_summary['total_emisi_kg']:,.0f}</div>
            <div class="metric-label">Total CO₂ (kg)</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <div style="font-size: 2rem;">⚡</div>
            <div class="metric-value">{emission_summary['rata_rata_emisi_per_periode']:.0f}</div>
            <div class="metric-label">Rata-rata/hari (kg)</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <div style="font-size: 2rem;">📈</div>
            <div class="metric-value">{emission_summary['emisi_tertinggi']:.0f}</div>
            <div class="metric-label">Emisi Tertinggi (kg)</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
        <div class="metric-card">
            <div style="font-size: 2rem;">📉</div>
            <div class="metric-value">{emission_summary['emisi_terendah']:.0f}</div>
            <div class="metric-label">Emisi Terendah (kg)</div>
        </div>
        """, unsafe_allow_html=True)
    
    if emission_summary['total_emisi_kg'] < 10000:
        st.markdown("""
        <div style="background: linear-gradient(135deg, #FFD700, #FFA500); border-radius: 20px; padding: 0.6rem 1rem; text-align: center; margin: 1rem 0;">
            🏆 <strong>Green Champion!</strong> Total emisi di bawah 10 ton — Luar biasa!
        </div>
        """, unsafe_allow_html=True)
    
    # ================= CLUSTERING =================
    st.subheader("🎯 2. K-Means Clustering")
    
    n_clusters = st.selectbox("Jumlah Cluster (K)", [2, 3, 4, 5], index=1,
                               help="Default 3: Emisi Tinggi, Sedang, Rendah")
    
    analyzer = EmissionClusterAnalyzer(n_clusters=n_clusters, random_state=42)
    
    if st.button("🔍 Tentukan K Optimal", use_container_width=True):
        with st.spinner("Menghitung Elbow Method..."):
            elbow_result = analyzer.find_optimal_k(df, max_k=10)
            fig_elbow = viz.plot_elbow_curve(
                elbow_result['wss'], 
                elbow_result['k_range'], 
                elbow_result['optimal_k']
            )
            st.plotly_chart(fig_elbow, use_container_width=True)
            st.info(f"💡 Rekomendasi K optimal dari Elbow Method: **{elbow_result['optimal_k']}**")
    
    if st.button("🚀 Jalankan K-Means Clustering", type="primary", use_container_width=True):
        with st.spinner("Sedang melakukan clustering..."):
            df_clustered = analyzer.fit(df)
            metrics = analyzer.get_evaluation_metrics()
            
            st.session_state['df_clustered'] = df_clustered
            st.session_state['cluster_metrics'] = metrics
            st.session_state['clustering_done'] = True
            
            st.success("✅ Clustering selesai!")
            st.balloons()
    
    # ================= TAMPILKAN HASIL CLUSTERING =================
    if st.session_state.get('clustering_done', False):
        df_clustered = st.session_state['df_clustered']
        metrics = st.session_state['cluster_metrics']
        
        st.markdown("#### 📊 Evaluasi Kualitas Cluster")
        col1, col2, col3 = st.columns(3)
        with col1:
            sil_score = metrics.get('silhouette_score', 0)
            st.metric("Silhouette Score", f"{sil_score:.4f}")
        with col2:
            st.metric("Calinski-Harabasz", f"{metrics.get('calinski_harabasz_score', 0):.2f}")
        with col3:
            st.metric("Davies-Bouldin", f"{metrics.get('davies_bouldin_score', 0):.4f}")
        
        st.markdown("#### 📋 Distribusi Cluster")
        cluster_counts = df_clustered['cluster_label'].value_counts()
        for cluster, count in cluster_counts.items():
            emoji = "🟢" if cluster == "Rendah" else ("🟡" if cluster == "Sedang" else "🔴")
            st.write(f"{emoji} **{cluster}**: {count} periode ({(count/len(df_clustered))*100:.1f}%)")
        
        # ================= REKOMENDASI =================
        st.subheader("💡 3. Rekomendasi Pengurangan Emisi")
        
        if 'Tinggi' in cluster_counts.index:
            st.warning("🔴 **Periode Emisi Tinggi Terdeteksi!** Evaluasi aktivitas pada periode tersebut.")
            st.markdown("""
            **Langkah yang bisa dilakukan:**
            - ✅ Periksa jadwal produksi di periode emisi tinggi
            - ✅ Cek apakah ada mesin/alat yang boros energi
            - ✅ Pertimbangkan perawatan rutin peralatan produksi
            """)
        
        if emission_summary['kontribusi_listrik_persen'] > 40:
            st.info("💡 **Sumber emisi terbesar: Listrik**")
            st.markdown("""
            **Rekomendasi hemat listrik:**
            - Ganti lampu ke LED (hemat 60-80%)
            - Matikan peralatan saat tidak digunakan
            - Pertimbangkan penggunaan panel surya untuk kebutuhan siang hari
            """)
        elif emission_summary['kontribusi_bbm_persen'] > 40:
            st.info(f"💡 **Sumber emisi terbesar: {fuel_type.upper()}**")
            st.markdown(f"""
            **Rekomendasi hemat bahan bakar:**
            - Lakukan perawatan rutin mesin 
            - Catat konsumsi {fuel_type} harian untuk evaluasi
            - Jika pakai kayu bakar, pastikan kayu kering (efisiensi lebih tinggi)
            """)
        elif emission_summary['kontribusi_transport_persen'] > 40:
            st.info("💡 **Sumber emisi terbesar: Transportasi**")
            st.markdown("""
            **Rekomendasi efisiensi transportasi:**
            - Optimalisasi rute distribusi
            - Tingkatkan muatan per perjalanan
            - Kelompokkan pelanggan berdasarkan zona
            """)
        
        # ================= VISUALISASI =================
        st.subheader("📈 4. Dashboard Visualisasi")
        
        tab1, tab2, tab3 = st.tabs(["📈 Tren Emisi", "🥧 Kontribusi Sumber", "🎯 Hasil Clustering"])
        
        with tab1:
            fig_trend = viz.plot_emission_trend(df_clustered)
            st.plotly_chart(fig_trend, use_container_width=True)
        
        with tab2:
            fig_pie = viz.plot_emission_breakdown_pie(df_clustered)
            st.plotly_chart(fig_pie, use_container_width=True)
            
            st.markdown(f"""
            📋 **Detail Kontribusi:**
            - ⚡ Listrik: {emission_summary['kontribusi_listrik_persen']:.1f}%
            - {fuel_info['icon']} {fuel_type.upper()}: {emission_summary['kontribusi_bbm_persen']:.1f}%
            - 🚚 Transportasi: {emission_summary['kontribusi_transport_persen']:.1f}%
            """)
        
        with tab3:
            fig_scatter = viz.plot_cluster_scatter(df_clustered)
            st.plotly_chart(fig_scatter, use_container_width=True)
        
        with st.expander("📋 Data Lengkap dengan Label Cluster", expanded=False):
            st.dataframe(df_clustered, use_container_width=True)
        
        # ================= 🔥 EKSPOR LAPORAN (DIPINDAHKAN KE SINI) =================
        st.subheader("📄 5. Ekspor Laporan MRV")

        st.markdown("""
        <style>
        .stDownloadButton button {
            background: linear-gradient(135deg, #28a745, #1e7e34) !important;
            color: white !important;
            border: none !important;
            border-radius: 12px !important;
            padding: 10px 20px !important;
            font-weight: 600 !important;
            font-size: 16px !important;
            width: 100% !important;
            transition: all 0.3s ease !important;
            box-shadow: 0 4px 15px rgba(40, 167, 69, 0.3) !important;
        }

        .stDownloadButton button:hover {
            transform: translateY(-3px) !important;
            box-shadow: 0 8px 25px rgba(40, 167, 69, 0.4) !important;
            background: linear-gradient(135deg, #34ce57, #28a745) !important;
        }
        </style>
        """, unsafe_allow_html=True)

        col1, col2 = st.columns(2)

        with col1:
            excel_data = rex.export_to_excel(df_clustered)
            st.download_button(
                label="📊 Download Laporan Excel",
                data=excel_data,
                file_name=f"laporan_emisi_{datetime.now().strftime('%Y%m%d')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

        with col2:
            html_report = rex.generate_html_report(df_clustered, metrics, emission_summary)
            st.download_button(
                label="🌟 Download Laporan Lengkap MRV",
                data=html_report,
                file_name=f"laporan_mrv_{datetime.now().strftime('%Y%m%d')}.html",
                mime="text/html"
            )

else:
    # Tampilan saat belum upload
    st.info("📂 Silakan upload file data emisi (CSV/Excel) di sidebar kiri")
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
        ### 📝 Format Data yang Diperlukan
        
        File harus memiliki kolom:
        - `tanggal` (YYYY-MM-DD)
        - `listrik_kwh` (kWh)
        - `bahan_bakar_liter` atau `bahan_bakar_kg` (sesuai jenis BBM)
        - `jarak_tempuh_km` (km)
        """)
    
    with col2:
        st.markdown("""
        ### 🚀 Cara Menggunakan
        
        1. Pilih jenis bahan bakar di sidebar
        2. Upload file CSV/Excel
        3. Sistem hitung emisi otomatis
        4. Klik "Jalankan Clustering"
        5. Ekspor laporan untuk MRV
        """)

# ================= FAQ & FOOTER =================
with st.expander("❓ Pertanyaan Umum (FAQ)"):
    st.markdown("""
    **Bagaimana cara mulai menggunakan EmisiKu?**  
    Upload file CSV/Excel dengan format yang benar (tanggal, listrik_kwh, bahan_bakar, jarak_tempuh_km)
    
    **Apakah data saya aman?**  
    Ya, data hanya diproses sementara di browser Anda dan tidak disimpan di server kami.
    
    **Apakah EmisiKu gratis?**  
    Ya, EmisiKu didedikasikan untuk membantu UMKM Indonesia mengurangi jejak karbon.
    
    **Apa itu mekanisme MRV?**  
    MRV (Monitoring, Reporting, Verification) adalah standar internasional untuk pelaporan emisi karbon.
    """)

st.markdown("""
<div style="text-align: center; padding: 2rem 0 1rem 0; color: #888; font-size: 0.8rem; border-top: 1px solid #ddd; margin-top: 2rem;">
    © 2026 EmisiKu • STMIK Mardira Indonesia
</div>
""", unsafe_allow_html=True)