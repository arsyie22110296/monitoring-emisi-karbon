import streamlit as st
import pandas as pd
import io
import base64
from datetime import datetime

def export_to_csv(df: pd.DataFrame, filename: str = None) -> str:
    """Ekspor data ke CSV"""
    if filename is None:
        filename = f"laporan_emisi_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    
    csv = df.to_csv(index=False)
    b64 = base64.b64encode(csv.encode()).decode()
    href = f'<a href="data:file/csv;base64,{b64}" download="{filename}">📥 Download CSV</a>'
    return href

def export_to_excel(df: pd.DataFrame, filename: str = None) -> bytes:
    """Ekspor data ke Excel dengan multiple sheets"""
    if filename is None:
        filename = f"laporan_emisi_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        # Sheet 1: Data lengkap
        df.to_excel(writer, sheet_name='Data Emisi', index=False)
        
        # Sheet 2: Ringkasan statistik
        if 'cluster_label' in df.columns:
            summary = df.groupby('cluster_label').agg({
                'total_emisi_kgco2': ['count', 'mean', 'std', 'min', 'max'],
                'listrik_kwh': 'mean',
                'solar_liter': 'mean',
                'jarak_tempuh_km': 'mean'
            }).round(2)
            summary.to_excel(writer, sheet_name='Ringkasan Cluster')
    
    return output.getvalue()

def generate_html_report(df: pd.DataFrame, cluster_metrics: dict, emission_summary: dict) -> str:
    """Generate laporan HTML untuk MRV"""
    
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # Hitung distribusi cluster
    if 'cluster_label' in df.columns:
        cluster_dist = df['cluster_label'].value_counts().to_dict()
    else:
        cluster_dist = {}
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Laporan Monitoring Emisi Karbon - MRV</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; }}
            h1 {{ color: #2c3e50; border-bottom: 2px solid #3498db; }}
            h2 {{ color: #34495e; margin-top: 30px; }}
            table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
            th, td {{ border: 1px solid #ddd; padding: 10px; text-align: left; }}
            th {{ background-color: #3498db; color: white; }}
            .summary {{ background-color: #ecf0f1; padding: 15px; border-radius: 8px; margin: 20px 0; }}
            .footer {{ margin-top: 50px; font-size: 12px; color: #7f8c8d; text-align: center; border-top: 1px solid #ddd; padding-top: 20px; }}
            .badge-low {{ background-color: #27ae60; color: white; padding: 3px 8px; border-radius: 4px; }}
            .badge-mid {{ background-color: #f39c12; color: white; padding: 3px 8px; border-radius: 4px; }}
            .badge-high {{ background-color: #e74c3c; color: white; padding: 3px 8px; border-radius: 4px; }}
        </style>
    </head>
    <body>
        <h1>🌿 Laporan Monitoring Emisi Karbon</h1>
        <p><strong>Tanggal Laporan:</strong> {now}</p>
        <p><strong>Periode Data:</strong> {df['tanggal'].min()} s/d {df['tanggal'].max()}</p>
        <p><strong>Jumlah Periode:</strong> {len(df)} hari</p>
        
        <h2>📊 Ringkasan Emisi</h2>
        <div class="summary">
            <table>
                <tr><th>Metrik</th><th>Nilai</th></tr>
                <tr><td>Total Emisi</td><td><strong>{emission_summary['total_emisi_kg']:,.2f} kg CO₂</strong> ({emission_summary['total_emisi_ton']:.2f} ton)</td></tr>
                <tr><td>Rata-rata Emisi per Hari</td><td>{emission_summary['rata_rata_emisi_per_periode']:.2f} kg CO₂</td></tr>
                <tr><td>Emisi Tertinggi</td><td>{emission_summary['emisi_tertinggi']:.2f} kg CO₂</td></tr>
                <tr><td>Emisi Terendah</td><td>{emission_summary['emisi_terendah']:.2f} kg CO₂</td></tr>
                <tr><td>Standar Deviasi</td><td>{emission_summary['std_emisi']:.2f} kg CO₂</td></tr>
            </table>
        </div>
        
        <h2>🔍 Kontribusi per Sumber</h2>
        <div class="summary">
            <table>
                <tr><th>Sumber</th><th>Kontribusi</th></tr>
                <tr><td>Listrik</td><td>{emission_summary['kontribusi_listrik_persen']:.1f}%</td></tr>
                <tr><td>Solar</td><td>{emission_summary['kontribusi_solar_persen']:.1f}%</td></tr>
                <tr><td>Transportasi</td><td>{emission_summary['kontribusi_transport_persen']:.1f}%</td></tr>
            </table>
        </div>
        
        <h2>🎯 Hasil Clustering K-Means</h2>
        <div class="summary">
            <table>
                <tr><th>Metrik</th><th>Nilai</th></tr>
                <tr><td>Jumlah Cluster</td><td>{cluster_metrics.get('n_clusters', 'N/A')}</td></tr>
                <tr><td>Silhouette Score</td><td>{cluster_metrics.get('silhouette_score', 'N/A'):.4f}</td></tr>
                <tr><td>Calinski-Harabasz Score</td><td>{cluster_metrics.get('calinski_harabasz_score', 'N/A'):.2f}</td></tr>
                <tr><td>Davies-Bouldin Score</td><td>{cluster_metrics.get('davies_bouldin_score', 'N/A'):.4f}</td></tr>
            </table>
        </div>
        
        <h2>📋 Distribusi Cluster</h2>
        <div class="summary">
            <table>
                <tr><th>Cluster</th><th>Jumlah Periode</th><th>Persentase</th></tr>
    """
    
    total = sum(cluster_dist.values())
    for cluster, count in cluster_dist.items():
        badge_class = "badge-low" if cluster == "Rendah" else ("badge-mid" if cluster == "Sedang" else "badge-high")
        html += f"""
        <tr>
            <td><span class="{badge_class}">{cluster}</span></td>
            <td>{count}</td>
            <td>{(count/total)*100:.1f}%</td>
        </tr>
        """
    
    html += f"""
            </table>
        </div>
        
        <h2>💡 Rekomendasi Mitigasi</h2>
        <div class="summary">
            <ul>
                <li>Periode dengan emisi <strong>Tinggi</strong> perlu dievaluasi efisiensi energi</li>
                <li>Pertimbangkan penggunaan peralatan listrik yang lebih hemat energi</li>
                <li>Optimasi rute distribusi untuk mengurangi emisi transportasi</li>
                <li>Lakukan monitoring rutin untuk mempertahankan pola emisi Rendah</li>
            </ul>
        </div>
        
        <div class="footer">
            <p>Laporan ini dihasilkan oleh Sistem Monitoring Emisi Karbon - Universitas Mardira Indonesia</p>
            <p>Sesuai dengan mekanisme MRV (Monitoring, Reporting, Verification) untuk mendukung Perpres CCS 2025</p>
        </div>
    </body>
    </html>
    """
    
    return html

def get_excel_download_link(df: pd.DataFrame, filename: str = None) -> str:
    """Mendapatkan link download Excel"""
    excel_data = export_to_excel(df, filename)
    b64 = base64.b64encode(excel_data).decode()
    return f'<a href="data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{b64}" download="{filename or "laporan_emisi.xlsx"}">📥 Download Laporan Excel</a>'
