import pandas as pd
import numpy as np

# Faktor Emisi Standar (berdasarkan IPCC 2022 dan data PLN 2025)
# Nilai ini diperoleh dari kajian literatur dan kebijakan nasional
FACTORS = {
    # Sektor energi listrik (grid Indonesia - rata-rata nasional)
    'electricity': {
        'value': 0.85,  # kg CO2/kWh
        'unit': 'kg CO2/kWh',
        'source': 'PLN Grid Average 2025'
    },
    # Bahan bakar solar (untuk boiler/ genset)
    'bbm': {
        'value': 2.68,  # kg CO2/liter
        'unit': 'kg CO2/liter',
        'source': 'IPCC 2022 Default'
    },
    # Transportasi (kendaraan angkut ringan diesel)
    'transportation': {
        'value': 0.27,  # kg CO2/km
        'unit': 'kg CO2/km',
        'source': 'IPCC 2022, Light Duty Diesel Truck'
    }
}

def calculate_emissions(df: pd.DataFrame) -> pd.DataFrame:
    """
    Menghitung emisi karbon dari data aktivitas UMKM.
    
    Args:
        df: DataFrame dengan kolom 'listrik_kwh', 'bbm_liter', 'jarak_tempuh_km'
    
    Returns:
        DataFrame dengan tambahan kolom emisi:
        - emisi_listrik_kg: emisi dari listrik
        - emisi_bbm_kg: emisi dari solar
        - emisi_transport_kg: emisi dari transportasi
        - total_emisi_kgco2: total emisi
    """
    
    df = df.copy()
    
    # Hitung emisi per sumber
    df['emisi_listrik_kg'] = (df['listrik_kwh'] * FACTORS['electricity']['value']).round(2)
    df['emisi_bbm_kg'] = (df['bbm_liter'] * FACTORS['bbm']['value']).round(2)
    df['emisi_transport_kg'] = (df['jarak_tempuh_km'] * FACTORS['transportation']['value']).round(2)
    
    # Total emisi
    df['total_emisi_kgco2'] = (df['emisi_listrik_kg'] + 
                                df['emisi_bbm_kg'] + 
                                df['emisi_transport_kg']).round(2)
    
    return df

def get_emission_summary(df: pd.DataFrame) -> dict:
    """Menghasilkan ringkasan statistik emisi"""
    
    if 'total_emisi_kgco2' not in df.columns:
        df = calculate_emissions(df)
    
    summary = {
        'total_emisi_kg': df['total_emisi_kgco2'].sum(),
        'total_emisi_ton': df['total_emisi_kgco2'].sum() / 1000,
        'rata_rata_emisi_per_periode': df['total_emisi_kgco2'].mean(),
        'emisi_tertinggi': df['total_emisi_kgco2'].max(),
        'emisi_terendah': df['total_emisi_kgco2'].min(),
        'std_emisi': df['total_emisi_kgco2'].std(),
        'kontribusi_listrik_persen': (df['emisi_listrik_kg'].sum() / df['total_emisi_kgco2'].sum()) * 100,
        'kontribusi_bbm_persen': (df['emisi_bbm_kg'].sum() / df['total_emisi_kgco2'].sum()) * 100,
        'kontribusi_transport_persen': (df['emisi_transport_kg'].sum() / df['total_emisi_kgco2'].sum()) * 100,
    }
    
    return summary
