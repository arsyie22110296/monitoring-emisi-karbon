"""
MODUL GENERATOR DATA EMISI KARBON
Multi-Fuel Support: Solar, Bensin, Kayu, LPG
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta

RANDOM_SEED = 42
np.random.seed(RANDOM_SEED)

# Parameter konsumsi per jenis bahan bakar
FUEL_PARAMS = {
    'solar': {'mean': 10.0, 'std': 3.0, 'min': 4.0, 'max': 20.0, 'unit': 'liter', 'label': 'Solar'},
    'bensin': {'mean': 12.0, 'std': 4.0, 'min': 5.0, 'max': 25.0, 'unit': 'liter', 'label': 'Bensin'},
    'kayu': {'mean': 58.0, 'std': 15.0, 'min': 25.0, 'max': 100.0, 'unit': 'kg', 'label': 'Kayu Bakar'},
    'lpg': {'mean': 6.0, 'std': 2.0, 'min': 2.0, 'max': 12.0, 'unit': 'kg', 'label': 'LPG'}
}


def generate_emission_data(n_periods: int = 30, fuel_type: str = 'solar', start_date: str = None) -> pd.DataFrame:
    """
    Membangkitkan data emisi karbon multi-bahan bakar
    
    Args:
        n_periods: Jumlah periode waktu (default 30)
        fuel_type: 'solar', 'bensin', 'kayu', 'lpg'
        start_date: Tanggal mulai (format 'YYYY-MM-DD')
    """
    
    # Set tanggal
    if start_date:
        start = datetime.strptime(start_date, '%Y-%m-%d')
    else:
        end_date = datetime(2026, 4, 30)
        start = end_date - timedelta(days=n_periods - 1)
    
    dates = [start + timedelta(days=i) for i in range(n_periods)]
    
    # Parameter konsumsi
    params = FUEL_PARAMS[fuel_type]
    
    # Generate data dengan efek weekend
    listrik_kwh = []
    bbm_konsumsi = []
    jarak_km = []
    
    for date in dates:
        is_weekend = date.weekday() >= 5
        weekend_factor = 0.7 if is_weekend else 1.0
        
        # Listrik
        l = np.random.normal(150 * weekend_factor, 30)
        listrik_kwh.append(np.clip(l, 80, 250))
        
        # BBM
        b = np.random.normal(params['mean'] * weekend_factor, params['std'])
        bbm_konsumsi.append(np.clip(b, params['min'], params['max']))
        
        # Jarak tempuh
        j = np.random.normal(50, 15)
        jarak_km.append(np.clip(j, 20, 100))
    
    # Bulatkan
    listrik_kwh = np.array(listrik_kwh).round(1)
    bbm_konsumsi = np.array(bbm_konsumsi).round(1)
    jarak_km = np.array(jarak_km).round(1)
    
    # Buat DataFrame dengan kolom universal
    df = pd.DataFrame({
        'tanggal': dates,
        'listrik_kwh': listrik_kwh,
        f'bahan_bakar_{params["unit"]}': bbm_konsumsi,  # dinamis
        'jenis_bahan_bakar': fuel_type,
        'jarak_tempuh_km': jarak_km,
        'cluster': -1
    })
    
    return df


def save_sample_data(filename: str = "data_emisi_simulasi.csv", n_periods: int = 30, fuel_type: str = 'solar'):
    """Simpan data simulasi ke file CSV"""
    df = generate_emission_data(n_periods, fuel_type)
    df.to_csv(filename, index=False)
    
    params = FUEL_PARAMS[fuel_type]
    print(f"✅ Data simulasi berhasil disimpan ke {filename}")
    print(f"📊 Jenis bahan bakar: {params['label']} ({params['unit']})")
    print(f"📈 Total data: {len(df)} periode")
    print(f"📅 Rentang tanggal: {df['tanggal'].min().strftime('%Y-%m-%d')} - {df['tanggal'].max().strftime('%Y-%m-%d')}")
    
    return df


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--fuel', type=str, default='solar', choices=['solar', 'bensin', 'kayu', 'lpg'])
    args = parser.parse_args()
    
    save_sample_data(fuel_type=args.fuel)
    
    # Tampilkan preview
    df = pd.read_csv("data_emisi_simulasi.csv")
    print("\n📋 Preview data:")
    print(df.head())