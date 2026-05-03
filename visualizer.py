import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Setting style
plt.style.use('seaborn-v0_8-darkgrid')
sns.set_palette("Set2")

def _detect_bbm_column(df: pd.DataFrame) -> str:
    """
    Mendeteksi nama kolom bahan bakar yang tersedia di DataFrame
    Support berbagai format: bahan_bakar_liter, bahan_bakar_kg, bbm_liter, solar_liter
    """
    bbm_candidates = ['bahan_bakar_liter', 'bahan_bakar_kg', 'bbm_liter', 'solar_liter']
    for col in bbm_candidates:
        if col in df.columns:
            return col
    return None

def plot_emission_trend(df: pd.DataFrame):
    """Plot tren emisi karbon dari waktu ke waktu"""
    
    # 🔥 PERBAIKAN: Cek apakah kolom tanggal ada
    df_temp = df.copy()
    if 'tanggal' not in df_temp.columns:
        # Jika tidak ada kolom tanggal, buat index sebagai pengganti
        df_temp['tanggal'] = df_temp.index
    elif df_temp['tanggal'].dtype == 'datetime64[ns]':
        # Kolom tanggal sudah benar format datetime
        pass
    else:
        # Coba konversi ke datetime
        try:
            df_temp['tanggal'] = pd.to_datetime(df_temp['tanggal'])
        except:
            df_temp['tanggal'] = df_temp.index
    
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    
    # Bar chart untuk total emisi
    fig.add_trace(
        go.Bar(
            x=df_temp['tanggal'],
            y=df_temp['total_emisi_kgco2'],
            name='Total Emisi (kg CO₂)',
            marker_color='steelblue',
            opacity=0.7
        ),
        secondary_y=False
    )
    
    # Line chart untuk moving average
    ma_7 = df_temp['total_emisi_kgco2'].rolling(window=7, min_periods=1).mean()
    fig.add_trace(
        go.Scatter(
            x=df_temp['tanggal'],
            y=ma_7,
            name='Moving Average (7 periode)',
            line=dict(color='red', width=2, dash='dash')
        ),
        secondary_y=False
    )
    
    fig.update_layout(
        title='📈 Tren Emisi Karbon dari Waktu ke Waktu',
        xaxis_title='Periode Waktu',
        yaxis_title='Emisi (kg CO₂)',
        height=450,
        hovermode='x unified'
    )
    
    return fig

def plot_emission_breakdown_pie(df: pd.DataFrame):
    """Plot pie chart kontribusi emisi per sumber (Multi-Fuel Support)"""
    
    # Deteksi kolom BBM yang tersedia
    bbm_col = _detect_bbm_column(df)
    
    # Ambil nilai emisi BBM (coba berbagai kemungkinan nama kolom)
    if 'emisi_bbm_kg' in df.columns:
        nilai_bbm = df['emisi_bbm_kg'].sum()
    elif 'emisi_solar_kg' in df.columns:
        nilai_bbm = df['emisi_solar_kg'].sum()
    else:
        # Hitung manual jika ada kolom bahan bakar
        if bbm_col and 'total_emisi_kgco2' in df.columns and 'emisi_listrik_kg' in df.columns and 'emisi_transport_kg' in df.columns:
            nilai_bbm = df['total_emisi_kgco2'].sum() - df['emisi_listrik_kg'].sum() - df['emisi_transport_kg'].sum()
        else:
            nilai_bbm = 0
    
    sumber_emisi = ['Listrik', 'BBM', 'Transportasi']
    nilai_emisi = [
        df['emisi_listrik_kg'].sum() if 'emisi_listrik_kg' in df.columns else 0,
        nilai_bbm,
        df['emisi_transport_kg'].sum() if 'emisi_transport_kg' in df.columns else 0
    ]
    
    # Filter nilai yang > 0 (supaya pie chart tidak error)
    filtered_data = [(sumber, nilai) for sumber, nilai in zip(sumber_emisi, nilai_emisi) if nilai > 0]
    
    if len(filtered_data) == 0:
        # Fallback: buat figure kosong dengan pesan
        fig = go.Figure()
        fig.add_annotation(text="Tidak ada data emisi", x=0.5, y=0.5, showarrow=False)
        fig.update_layout(title='🌿 Kontribusi Emisi per Sumber', height=400)
        return fig
    
    labels_filtered = [item[0] for item in filtered_data]
    values_filtered = [item[1] for item in filtered_data]
    
    warna = {'Listrik': '#3498db', 'BBM': '#e74c3c', 'Transportasi': '#2ecc71'}
    marker_colors = [warna.get(label, '#95a5a6') for label in labels_filtered]
    
    fig = go.Figure(data=[go.Pie(
        labels=labels_filtered,
        values=values_filtered,
        hole=0.4,
        marker_colors=marker_colors,
        textinfo='label+percent',
        textposition='auto',
        hovertemplate='<b>%{label}</b><br>Emisi: %{value:,.0f} kg CO₂<br>Persentase: %{percent}<extra></extra>'
    )])
    
    fig.update_layout(
        title='🌿 Kontribusi Emisi per Sumber',
        height=400,
        showlegend=True
    )
    
    return fig

def plot_cluster_scatter(df: pd.DataFrame):
    """Plot scatter 2D hasil clustering K-Means"""
    
    # Mapping warna untuk cluster
    warna_cluster = {
        'Rendah': 'green',
        'Sedang': 'orange',
        'Tinggi': 'red'
    }
    
    # 🔥 PERBAIKAN: Siapkan hover text yang aman
    if 'tanggal' in df.columns:
        if df['tanggal'].dtype == 'datetime64[ns]':
            hover_text = df['tanggal'].dt.strftime('%Y-%m-%d')
        else:
            hover_text = df['tanggal'].astype(str)
    else:
        hover_text = df.index.astype(str)
    
    fig = go.Figure()
    
    for cluster_label in df['cluster_label'].unique():
        df_cluster = df[df['cluster_label'] == cluster_label]
        fig.add_trace(go.Scatter(
            x=df_cluster['listrik_kwh'] if 'listrik_kwh' in df_cluster.columns else df_cluster.index,
            y=df_cluster['total_emisi_kgco2'] if 'total_emisi_kgco2' in df_cluster.columns else range(len(df_cluster)),
            mode='markers',
            name=f'Cluster {cluster_label}',
            marker=dict(
                size=12,
                color=warna_cluster.get(cluster_label, 'gray'),
                opacity=0.7,
                line=dict(width=1, color='white')
            ),
            text=hover_text[df_cluster.index] if isinstance(hover_text, pd.Series) else hover_text,
            hovertemplate='<b>%{text}</b><br>Total Emisi: %{y:.0f} kg CO₂<extra></extra>'
        ))
    
    x_title = 'Konsumsi Listrik (kWh)' if 'listrik_kwh' in df.columns else 'Indeks Data'
    fig.update_layout(
        title='🎯 Hasil K-Means Clustering',
        xaxis_title=x_title,
        yaxis_title='Total Emisi (kg CO₂)',
        height=500,
        legend_title='Cluster',
        hovermode='closest'
    )
    
    return fig

def plot_cluster_comparison_bar(df: pd.DataFrame):
    """Plot perbandingan karakteristik antar cluster (Multi-Fuel Support)"""
    
    # Deteksi kolom BBM
    bbm_col = _detect_bbm_column(df)
    
    # Siapkan fitur yang akan dibandingkan
    fitur_list = ['listrik_kwh']
    labels_list = ['Listrik (kWh)']
    
    if bbm_col:
        fitur_list.append(bbm_col)
        labels_list.append(f'BBM ({bbm_col.split("_")[-1]})')
    
    if 'jarak_tempuh_km' in df.columns:
        fitur_list.append('jarak_tempuh_km')
        labels_list.append('Jarak Tempuh (km)')
    
    if len(fitur_list) == 0:
        fig = go.Figure()
        fig.add_annotation(text="Tidak ada data untuk perbandingan", x=0.5, y=0.5, showarrow=False)
        fig.update_layout(title='📊 Perbandingan Karakteristik Antar Cluster', height=450)
        return fig
    
    # Hitung rata-rata per cluster
    cluster_means = df.groupby('cluster_label')[fitur_list].mean()
    
    fig = go.Figure()
    warna = ['#3498db', '#e74c3c', '#2ecc71', '#9b59b6', '#f39c12']
    
    for i, (fitur, label, color) in enumerate(zip(fitur_list, labels_list, warna)):
        fig.add_trace(go.Bar(
            name=label,
            x=cluster_means.index,
            y=cluster_means[fitur],
            marker_color=color,
            text=cluster_means[fitur].round(1),
            textposition='auto'
        ))
    
    fig.update_layout(
        title='📊 Perbandingan Karakteristik Antar Cluster',
        xaxis_title='Cluster',
        yaxis_title='Rata-rata Konsumsi',
        height=450,
        barmode='group',
        legend_title='Parameter'
    )
    
    return fig

def plot_elbow_curve(wss_values: list, k_range: list, optimal_k: int):
    """Plot elbow curve untuk penentuan K optimal"""
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=k_range,
        y=wss_values,
        mode='lines+markers',
        name='WSS (Inertia)',
        line=dict(color='blue', width=2),
        marker=dict(size=8, color='darkblue')
    ))
    
    # Tandai titik optimal
    fig.add_vline(
        x=optimal_k,
        line_dash="dash",
        line_color="red",
        annotation_text=f"K optimal = {optimal_k}",
        annotation_position="top"
    )
    
    fig.update_layout(
        title='🔍 Elbow Method - Penentuan Jumlah Cluster Optimal',
        xaxis_title='Jumlah Cluster (K)',
        yaxis_title='Within-Cluster Sum of Squares (WSS)',
        height=450
    )
    
    return fig

def plot_emission_distribution(df: pd.DataFrame):
    """Plot distribusi emisi per cluster (boxplot)"""
    
    fig = go.Figure()
    colors = {'Rendah': 'green', 'Sedang': 'orange', 'Tinggi': 'red'}
    
    for cluster in df['cluster_label'].unique():
        df_cluster = df[df['cluster_label'] == cluster]
        fig.add_trace(go.Box(
            y=df_cluster['total_emisi_kgco2'],
            name=f'Cluster {cluster}',
            boxmean='sd',
            marker_color=colors.get(cluster, 'gray')
        ))
    
    fig.update_layout(
        title='📦 Distribusi Emisi per Cluster',
        xaxis_title='Cluster',
        yaxis_title='Total Emisi (kg CO₂)',
        height=450
    )
    
    return fig

def plot_weekly_pattern(df: pd.DataFrame):
    """Plot pola emisi berdasarkan hari dalam seminggu"""
    
    # 🔥 PERBAIKAN: Cek kolom tanggal dengan lebih baik
    if 'tanggal' not in df.columns:
        fig = go.Figure()
        fig.add_annotation(text="Tidak ada data tanggal untuk analisis mingguan", x=0.5, y=0.5, showarrow=False)
        fig.update_layout(title='📅 Pola Emisi Rata-rata per Hari', height=400)
        return fig
    
    # Cek apakah kolom tanggal bisa dijadikan datetime
    try:
        df_temp = df.copy()
        df_temp['tanggal'] = pd.to_datetime(df_temp['tanggal'])
        df_temp['hari'] = df_temp['tanggal'].dt.day_name()
    except:
        fig = go.Figure()
        fig.add_annotation(text="Format tanggal tidak valid", x=0.5, y=0.5, showarrow=False)
        fig.update_layout(title='📅 Pola Emisi Rata-rata per Hari', height=400)
        return fig
    
    urutan_hari = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    df_temp['hari'] = pd.Categorical(df_temp['hari'], categories=urutan_hari, ordered=True)
    
    weekly_emisi = df_temp.groupby('hari', observed=True)['total_emisi_kgco2'].mean().reset_index()
    
    fig = px.bar(
        weekly_emisi,
        x='hari',
        y='total_emisi_kgco2',
        title='📅 Pola Emisi Rata-rata per Hari',
        labels={'hari': 'Hari', 'total_emisi_kgco2': 'Rata-rata Emisi (kg CO₂)'},
        color='total_emisi_kgco2',
        color_continuous_scale='RdYlGn_r'
    )
    
    fig.update_layout(height=400)
    
    return fig