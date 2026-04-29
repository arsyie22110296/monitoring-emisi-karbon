import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

# Import modul lokal
from emission_calculator import calculate_emissions, get_emission_summary, FACTORS
from clustering_engine import EmissionClusterAnalyzer
import visualizer as viz
import report_exporter as rex

# ================= KONFIGURASI HALAMAN =================
st.set_page_config(
    page_title="Sistem Monitoring Emisi Karbon",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ================= SIDEBAR =================
with st.sidebar:
    logo_path = "emisiku_logo.png"
    from pathlib import Path
    if Path(logo_path).exists():
        import base64
        with open(logo_path, "rb") as f:
            data = base64.b64encode(f.read()).decode()
        st.markdown(
            f"""
            <div style="display: flex; justify-content: center;">
                <img src="data:image/png;base64,{data}" style="width: 250px; height: auto; border-radius: 12px;">
            </div>
            """,
            unsafe_allow_html=True
        )
    else:
        st.warning("Logo tidak ditemukan")
    
    st.markdown("---")

    # Upload file
    uploaded_file = st.file_uploader(
        "📂 Upload Data Emisi",
        type=['csv', 'xlsx'],
        help="Upload file CSV atau Excel dengan kolom: tanggal, listrik_kwh, bbm_liter, jarak_tempuh_km"
    )
    
    st.markdown("---")
    st.markdown("### ℹ️ Informasi")
    st.caption(f"""
    **Faktor Emisi:**\n
    - Listrik: {FACTORS['electricity']['value']} {FACTORS['electricity']['unit']}\n
    - Solar: {FACTORS['bbm']['value']} {FACTORS['bbm']['unit']}\n
    - Transportasi: {FACTORS['transportation']['value']} {FACTORS['transportation']['unit']}
    """)
    
    st.caption("© 2026 - Skripsi Teknik Informatika")

# ================= MAIN PAGE =================
st.title("🌍 Sistem Analisis Pola Emisi Karbon")
st.markdown("""
Sistem ini membantu UMKM untuk:
- 📊 Menghitung jejak karbon dari aktivitas operasional
- 🔍 Mengelompokkan pola emisi (Tinggi/Sedang/Rendah) dengan **K-Means Clustering**
- 📈 Dashboard visualisasi interaktif
- 📄 Ekspor laporan untuk mekanisme **MRV** (Monitoring, Reporting, Verification)
""")

# ================= LOAD DATA =================
if uploaded_file is not None:
    # Baca file
    if uploaded_file.name.endswith('.csv'):
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_excel(uploaded_file)
    
    # Konversi kolom tanggal jika ada
    if 'tanggal' in df.columns:
        df['tanggal'] = pd.to_datetime(df['tanggal'])
    
    st.success(f"✅ Data berhasil dimuat: {df.shape[0]} baris, {df.shape[1]} kolom")
    
    # Preview data
    with st.expander("📋 Preview Data", expanded=False):
        st.dataframe(df.head(10), use_container_width=True)
    
    # ================= PERHITUNGAN EMISI =================
    st.subheader("📊 1. Perhitungan Emisi Karbon")
    
    # Cek apakah perlu hitung emisi
    if 'total_emisi_kgco2' not in df.columns:
        df = calculate_emissions(df)
        st.info("✅ Perhitungan emisi otomatis selesai menggunakan faktor emisi standar")
    
    # Tampilkan ringkasan emisi
    emission_summary = get_emission_summary(df)
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Emisi", f"{emission_summary['total_emisi_kg']:,.0f} kg CO₂", 
                  f"{emission_summary['total_emisi_ton']:.2f} ton")
    with col2:
        st.metric("Rata-rata per Hari", f"{emission_summary['rata_rata_emisi_per_periode']:.0f} kg CO₂")
    with col3:
        st.metric("Emisi Tertinggi", f"{emission_summary['emisi_tertinggi']:.0f} kg CO₂")
    with col4:
        st.metric("Emisi Terendah", f"{emission_summary['emisi_terendah']:.0f} kg CO₂")
    
    # ================= CLUSTERING =================
    st.subheader("🎯 2. K-Means Clustering")
    
    # Pilihan jumlah cluster
    col1, col2 = st.columns([1, 2])
    with col1:
        n_clusters = st.selectbox("Jumlah Cluster (K)", [2, 3, 4, 5], index=1, 
                                   help="Jumlah cluster untuk K-Means. Default 3 (Tinggi, Sedang, Rendah)")
    
    # Inisialisasi analyzer
    analyzer = EmissionClusterAnalyzer(n_clusters=n_clusters, random_state=42)
    
    # Elbow Method untuk rekomendasi K optimal
    if st.button("🔍 Tentukan K Optimal dengan Elbow Method"):
        with st.spinner("Menghitung Elbow Method..."):
            elbow_result = analyzer.find_optimal_k(df, max_k=10)
            fig_elbow = viz.plot_elbow_curve(
                elbow_result['wss'], 
                elbow_result['k_range'], 
                elbow_result['optimal_k']
            )
            st.plotly_chart(fig_elbow, use_container_width=True)
            st.info(f"💡 Rekomendasi K optimal dari Elbow Method: **{elbow_result['optimal_k']}**")
    
    # Jalankan clustering
    if st.button("🚀 Jalankan K-Means Clustering", type="primary"):
        with st.spinner("Sedang melakukan clustering..."):
            df_clustered = analyzer.fit(df)
            metrics = analyzer.get_evaluation_metrics()
            
            # Simpan ke session state
            st.session_state['df_clustered'] = df_clustered
            st.session_state['cluster_metrics'] = metrics
            st.session_state['clustering_done'] = True
            
            st.success("✅ Clustering selesai!")
    
    # Tampilkan hasil clustering jika sudah dilakukan
    if st.session_state.get('clustering_done', False):
        df_clustered = st.session_state['df_clustered']
        metrics = st.session_state['cluster_metrics']
        
        # Metrik evaluasi
        st.markdown("#### 📊 Evaluasi Kualitas Cluster")
        col1, col2, col3 = st.columns(3)
        with col1:
            sil_score = metrics.get('silhouette_score', 0)
            color = "green" if sil_score >= 0.5 else ("orange" if sil_score >= 0.25 else "red")
            st.metric("Silhouette Score", f"{sil_score:.4f}", 
                      help=">0.5 = Good, 0.25-0.5 = Fair, <0.25 = Poor")
        with col2:
            st.metric("Calinski-Harabasz", f"{metrics.get('calinski_harabasz_score', 0):.2f}")
        with col3:
            st.metric("Davies-Bouldin", f"{metrics.get('davies_bouldin_score', 0):.4f}")
        
        # Tabel distribusi cluster
        st.markdown("#### 📋 Distribusi Cluster")
        cluster_counts = df_clustered['cluster_label'].value_counts()
        
        col1, col2, col3 = st.columns(3)
        warna_cluster = {'Rendah': '🟢', 'Sedang': '🟠', 'Tinggi': '🔴'}
        for i, (cluster, count) in enumerate(cluster_counts.items()):
            color_symbol = warna_cluster.get(cluster, '⚪')
            with [col1, col2, col3][i if i < 3 else 0]:
                st.metric(f"{color_symbol} Cluster {cluster}", f"{count} periode", 
                          f"{(count/len(df_clustered))*100:.1f}%")
        
        # Karakteristik cluster
        st.markdown("#### 📊 Karakteristik Setiap Cluster")
        cluster_char = analyzer.get_cluster_characteristics(df_clustered)
        st.dataframe(cluster_char, use_container_width=True)
        
        # ================= VISUALISASI =================
        st.subheader("📈 3. Dashboard Visualisasi")
        
        # Tab untuk visualisasi
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "📈 Tren Emisi", "🥧 Kontribusi Sumber", "🎯 Hasil Clustering", 
            "📊 Perbandingan Cluster", "📅 Pola Mingguan"
        ])
        
        with tab1:
            fig_trend = viz.plot_emission_trend(df_clustered)
            st.plotly_chart(fig_trend, use_container_width=True)
        
        with tab2:
            col1, col2 = st.columns([1, 1])
            with col1:
                fig_pie = viz.plot_emission_breakdown_pie(df_clustered)
                st.plotly_chart(fig_pie, use_container_width=True)
            with col2:
                st.markdown("##### 📋 Detail Kontribusi")
                st.markdown(f"""
                - 💡 **Listrik:** {emission_summary['kontribusi_listrik_persen']:.1f}% ({df_clustered['emisi_listrik_kg'].sum():.0f} kg CO₂)
                - 🔥 **Solar:** {emission_summary['kontribusi_bbm_persen']:.1f}% ({df_clustered['emisi_bbm_kg'].sum():.0f} kg CO₂)
                - 🚚 **Transportasi:** {emission_summary['kontribusi_transport_persen']:.1f}% ({df_clustered['emisi_transport_kg'].sum():.0f} kg CO₂)
                """)
        
        with tab3:
            fig_scatter = viz.plot_cluster_scatter(df_clustered)
            st.plotly_chart(fig_scatter, use_container_width=True)
            
            # Tambahan boxplot distribusi
            fig_box = viz.plot_emission_distribution(df_clustered)
            st.plotly_chart(fig_box, use_container_width=True)
        
        with tab4:
            fig_comparison = viz.plot_cluster_comparison_bar(df_clustered)
            st.plotly_chart(fig_comparison, use_container_width=True)
        
        with tab5:
            fig_weekly = viz.plot_weekly_pattern(df_clustered)
            st.plotly_chart(fig_weekly, use_container_width=True)
        
        # Tampilkan data lengkap
        with st.expander("📋 Data Lengkap dengan Label Cluster", expanded=False):
            st.dataframe(df_clustered, use_container_width=True)
        
        # ================= EKSPOR LAPORAN MRV =================
        st.subheader("📄 4. Ekspor Laporan MRV")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("📊 Ekspor ke CSV"):
                csv_link = rex.export_to_csv(df_clustered)
                st.markdown(csv_link, unsafe_allow_html=True)
        
        with col2:
            if st.button("📑 Ekspor ke Excel"):
                excel_data = rex.export_to_excel(df_clustered)
                st.download_button(
                    label="📥 Download Excel",
                    data=excel_data,
                    file_name=f"laporan_emisi_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
        
        with col3:
            if st.button("📄 Generate HTML Report"):
                html_report = rex.generate_html_report(df_clustered, metrics, emission_summary)
                st.download_button(
                    label="📥 Download HTML Report",
                    data=html_report,
                    file_name=f"laporan_mrv_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html",
                    mime="text/html"
                )
        
        # Informasi footer
        st.markdown("---")
        st.caption(f"""
        **Informasi Laporan:**
        - Periode data: {df_clustered['tanggal'].min().strftime('%Y-%m-%d')} s/d {df_clustered['tanggal'].max().strftime('%Y-%m-%d')}
        - Total periode: {len(df_clustered)} hari
        - Metode clustering: K-Means (n_clusters={n_clusters})
        - Laporan sesuai mekanisme MRV untuk mendukung Perpres nomor 14 tahun 2024 dan nomor 110 tahun 2025 tentang CCS 
        """)

else:
    # Tampilkan panduan jika belum upload
    st.info("📂 Silakan upload file data emisi (CSV/Excel) di sidebar kiri")
    
    st.markdown("""
    ### 📝 Format Data yang Diperlukan
    
    File harus memiliki kolom berikut:
    - `tanggal` (format: YYYY-MM-DD)
    - `listrik_kwh` (konsumsi listrik dalam kWh)
    - `bbm_liter` (konsumsi bahan bakar dalam liter)
    - `jarak_tempuh_km` (jarak transportasi dalam km)
    
    ### 🚀 Contoh Penggunaan
    
    1. Gunakan file data dengan format .csv 
    2. Upload file di sidebar kiri
    3. Sistem akan otomatis menghitung emisi karbon
    4. Lakukan clustering dan analisis pola
    5. Ekspor laporan untuk kebutuhan MRV
    """)
    
    # Tampilkan contoh data
    st.markdown("### 📋 Contoh Data yang Benar")
    contoh_data = pd.DataFrame({
        'tanggal': ['2026-04-01', '2026-04-02', '2026-04-03'],
        'listrik_kwh': [145.2, 168.5, 132.8],
        'bbm_liter': [9.5, 11.2, 8.7],
        'jarak_tempuh_km': [48.5, 52.3, 45.1]
    })
    st.dataframe(contoh_data, use_container_width=True)
