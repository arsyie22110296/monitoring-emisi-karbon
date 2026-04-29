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

def plot_emission_trend(df: pd.DataFrame):
    """Plot tren emisi karbon dari waktu ke waktu"""
    
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    
    # Bar chart untuk total emisi
    fig.add_trace(
        go.Bar(
            x=df['tanggal'],
            y=df['total_emisi_kgco2'],
            name='Total Emisi (kg CO₂)',
            marker_color='steelblue',
            opacity=0.7
        ),
        secondary_y=False
    )
    
    # Line chart untuk moving average
    ma_7 = df['total_emisi_kgco2'].rolling(window=7, min_periods=1).mean()
    fig.add_trace(
        go.Scatter(
            x=df['tanggal'],
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
    """Plot pie chart kontribusi emisi per sumber"""
    
    sumber_emisi = ['Listrik', 'BBM', 'Transportasi']
    nilai_emisi = [
        df['emisi_listrik_kg'].sum(),
        df['emisi_bbm_kg'].sum(),
        df['emisi_transport_kg'].sum()
    ]
    warna = ['#3498db', '#e74c3c', '#2ecc71']
    
    fig = go.Figure(data=[go.Pie(
        labels=sumber_emisi,
        values=nilai_emisi,
        hole=0.4,
        marker_colors=warna,
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
    """Plot scatter 3D hasil clustering K-Means"""
    
    # Mapping warna untuk cluster
    warna_cluster = {
        'Rendah': 'green',
        'Sedang': 'orange',
        'Tinggi': 'red'
    }
    
    fig = go.Figure()
    
    for cluster_label in df['cluster_label'].unique():
        df_cluster = df[df['cluster_label'] == cluster_label]
        fig.add_trace(go.Scatter(
            x=df_cluster['listrik_kwh'],
            y=df_cluster['total_emisi_kgco2'],
            mode='markers',
            name=f'Cluster {cluster_label}',
            marker=dict(
                size=12,
                color=warna_cluster.get(cluster_label, 'gray'),
                opacity=0.7,
                line=dict(width=1, color='white')
            ),
            text=df_cluster['tanggal'].dt.strftime('%Y-%m-%d'),
            hovertemplate='<b>%{text}</b><br>Listrik: %{x} kWh<br>Total Emisi: %{y:.0f} kg CO₂<extra></extra>'
        ))
    
    fig.update_layout(
        title='🎯 Hasil K-Means Clustering (Listrik vs Total Emisi)',
        xaxis_title='Konsumsi Listrik (kWh)',
        yaxis_title='Total Emisi (kg CO₂)',
        height=500,
        legend_title='Cluster',
        hovermode='closest'
    )
    
    return fig

def plot_cluster_comparison_bar(df: pd.DataFrame):
    """Plot perbandingan karakteristik antar cluster"""
    
    cluster_means = df.groupby('cluster_label')[['listrik_kwh', 'bbm_liter', 'jarak_tempuh_km']].mean()
    
    fig = go.Figure()
    
    fitur = ['listrik_kwh', 'bbm_liter', 'jarak_tempuh_km']
    labels = ['Listrik (kWh)', 'BBM (Liter)', 'Jarak Tempuh (km)']
    warna = ['#3498db', '#e74c3c', '#2ecc71']
    
    for i, (fitur, label, warna) in enumerate(zip(fitur, labels, warna)):
        fig.add_trace(go.Bar(
            name=label,
            x=cluster_means.index,
            y=cluster_means[fitur],
            marker_color=warna,
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
    
    for cluster in df['cluster_label'].unique():
        df_cluster = df[df['cluster_label'] == cluster]
        fig.add_trace(go.Box(
            y=df_cluster['total_emisi_kgco2'],
            name=f'Cluster {cluster}',
            boxmean='sd',
            marker_color=['green', 'orange', 'red'][list(df['cluster_label'].unique()).index(cluster)]
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
    
    df['hari'] = df['tanggal'].dt.day_name()
    urutan_hari = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    df['hari'] = pd.Categorical(df['hari'], categories=urutan_hari, ordered=True)
    
    weekly_emisi = df.groupby('hari')['total_emisi_kgco2'].mean().reset_index()
    
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
