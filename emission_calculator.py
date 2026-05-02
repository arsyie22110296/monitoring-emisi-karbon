"""
MODUL PERHITUNGAN EMISI KARBON
Multi-Fuel Support: Solar, Bensin, Kayu Bakar, LPG
Sesuai proposal skripsi - Faktor emisi IPCC 2022 & Kementerian LHK
"""

import pandas as pd
import numpy as np

# ================= FAKTOR EMISI PER JENIS BAHAN BAKAR =================
# Sumber: IPCC 2022, Kementerian LHK, PLN Grid Indonesia 2025
FUEL_FACTORS = {
    'solar': {
        'value': 2.68,
        'unit': 'kg CO₂/liter',
        'sumber': 'IPCC 2022',
        'icon': '⛽'
    },
    'bensin': {
        'value': 2.31,
        'unit': 'kg CO₂/liter',
        'sumber': 'IPCC 2022',
        'icon': '⛽'
    },
    'kayu': {
        'value': 1.82,
        'unit': 'kg CO₂/kg',
        'sumber': 'KLHK (biomassa)',
        'icon': '🌲'
    },
    'lpg': {
        'value': 1.51,
        'unit': 'kg CO₂/kg',
        'sumber': 'IPCC 2022',
        'icon': '🛢️'
    },
    'listrik': {
        'value': 0.85,
        'unit': 'kg CO₂/kWh',
        'sumber': 'PLN Grid Average 2025',
        'icon': '⚡'
    },
    'transportasi': {
        'value': 0.27,
        'unit': 'kg CO₂/km',
        'sumber': 'IPCC 2022, Light Duty Vehicle',
        'icon': '🚚'
    }
}

# Faktor Default (untuk kompatibilitas)
FACTORS = {
    'electricity': FUEL_FACTORS['listrik'],
    'bbm': FUEL_FACTORS['solar'],
    'transportation': FUEL_FACTORS['transportasi']
}


def calculate_emissions(df: pd.DataFrame, fuel_type: str = 'solar') -> pd.DataFrame:
    """
    Menghitung emisi karbon dengan jenis bahan bakar fleksibel
    
    Args:
        df: DataFrame dengan kolom 
            - listrik_kwh (wajib)
            - bahan_bakar_liter atau bahan_bakar_kg (wajib)
            - jarak_tempuh_km (wajib)
            - atau kolom lama: solar_liter / bbm_liter untuk kompatibilitas
        fuel_type: 'solar', 'bensin', 'kayu', 'lpg'
    
    Returns:
        DataFrame dengan kolom emisi
    """
    
    df = df.copy()
    
    # ========== 1. Hitung Emisi Listrik ==========
    if 'listrik_kwh' in df.columns:
        df['emisi_listrik_kg'] = (df['listrik_kwh'] * FUEL_FACTORS['listrik']['value']).round(2)
    else:
        df['emisi_listrik_kg'] = 0
    
    # ========== 2. Hitung Emisi Bahan Bakar (Multi-Fuel) ==========
    bbm_value = FUEL_FACTORS[fuel_type]['value']
    
    # Cek berbagai kemungkinan nama kolom
    if 'bahan_bakar_liter' in df.columns:
        df['emisi_bbm_kg'] = (df['bahan_bakar_liter'] * bbm_value).round(2)
        df['satuan_bbm'] = 'liter'
    elif 'bahan_bakar_kg' in df.columns:
        df['emisi_bbm_kg'] = (df['bahan_bakar_kg'] * bbm_value).round(2)
        df['satuan_bbm'] = 'kg'
    elif 'solar_liter' in df.columns:
        df['emisi_bbm_kg'] = (df['solar_liter'] * FUEL_FACTORS['solar']['value']).round(2)
        df['satuan_bbm'] = 'liter'
    elif 'bbm_liter' in df.columns:
        df['emisi_bbm_kg'] = (df['bbm_liter'] * bbm_value).round(2)
        df['satuan_bbm'] = 'liter'
    else:
        df['emisi_bbm_kg'] = 0
        df['satuan_bbm'] = 'unknown'
    
    # Simpan jenis bahan bakar yang digunakan
    df['jenis_bahan_bakar'] = fuel_type
    
    # ========== 3. Hitung Emisi Transportasi ==========
    if 'jarak_tempuh_km' in df.columns:
        df['emisi_transport_kg'] = (df['jarak_tempuh_km'] * FUEL_FACTORS['transportasi']['value']).round(2)
    else:
        df['emisi_transport_kg'] = 0
    
    # ========== 4. Total Emisi ==========
    df['total_emisi_kgco2'] = (df['emisi_listrik_kg'] + df['emisi_bbm_kg'] + df['emisi_transport_kg']).round(2)
    
    return df


def get_emission_summary(df: pd.DataFrame) -> dict:
    """Menghasilkan ringkasan statistik emisi"""
    
    if 'total_emisi_kgco2' not in df.columns:
        df = calculate_emissions(df)
    
    # Handle jika kolom emisi_bbm_kg tidak ada
    if 'emisi_bbm_kg' not in df.columns:
        if 'emisi_solar_kg' in df.columns:
            df['emisi_bbm_kg'] = df['emisi_solar_kg']
        else:
            df['emisi_bbm_kg'] = 0
    
    total = df['total_emisi_kgco2'].sum()
    
    summary = {
        'total_emisi_kg': total,
        'total_emisi_ton': total / 1000,
        'rata_rata_emisi_per_periode': df['total_emisi_kgco2'].mean(),
        'emisi_tertinggi': df['total_emisi_kgco2'].max(),
        'emisi_terendah': df['total_emisi_kgco2'].min(),
        'std_emisi': df['total_emisi_kgco2'].std(),
        'jumlah_periode': len(df),
    }
    
    # Kontribusi per sumber (hindari division by zero)
    if total > 0:
        summary['kontribusi_listrik_persen'] = (df['emisi_listrik_kg'].sum() / total) * 100
        summary['kontribusi_bbm_persen'] = (df['emisi_bbm_kg'].sum() / total) * 100
        summary['kontribusi_transport_persen'] = (df['emisi_transport_kg'].sum() / total) * 100
    else:
        summary['kontribusi_listrik_persen'] = 0
        summary['kontribusi_bbm_persen'] = 0
        summary['kontribusi_transport_persen'] = 0
    
    return summary


def get_fuel_info(fuel_type: str) -> dict:
    """Mendapatkan informasi tentang jenis bahan bakar"""
    return FUEL_FACTORS.get(fuel_type, FUEL_FACTORS['solar'])