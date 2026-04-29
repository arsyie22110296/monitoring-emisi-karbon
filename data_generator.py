import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random

# Seed untuk reproducibility (sesuai standar ilmiah)
RANDOM_SEED = 42
np.random.seed(RANDOM_SEED)
random.seed(RANDOM_SEED)

# Faktor Emisi (kg CO2 per unit aktivitas) - Berdasarkan IPCC 2022 & PLN
# Sumber: PLTU batubara rata-rata Indonesia = 0.85 kg CO2/kWh
#        Solar = 2.68 kg CO2/liter
#        Transportasi diesel = 0.27 kg CO2/km (kendaraan angkut barang ringan)
FAKTOR_EMISI = {
    'listrik': 0.85,      # kg CO2 / kWh
    'BBM': 2.68,        # kg CO2 / liter
    'transportasi': 0.27  # kg CO2 / km
}

# Parameter simulasi berdasarkan observasi pabrik tahu di Cibuntu Bandung
PARAMETER_UMKM = {
    'listrik_mean': 150.0,      # kWh/hari
    'listrik_std': 30.0,
    'listrik_min': 80.0,
    'listrik_max': 250.0,
    'bbm_mean': 10.0,         # liter/hari
    'bbm_std': 3.0,
    'bbm_min': 4.0,
    'bbm_max': 20.0,
    'jarak_mean': 50.0,         # km/hari
    'jarak_std': 15.0,
    'jarak_min': 20.0,
    'jarak_max': 100.0
}

def generate_emission_data(n_periods: int = 30, start_date: str = None) -> pd.DataFrame:
    """
    Membangkitkan data emisi karbon untuk UMKM pabrik tahu.
    
    Args:
        n_periods: Jumlah periode waktu (default 30 hari)
        start_date: Tanggal mulai (format 'YYYY-MM-DD'), default 30 hari terakhir
    
    Returns:
        DataFrame dengan kolom:
        - tanggal: periode waktu
        - listrik_kwh: konsumsi listrik dalam kWh
        - bbm_liter: konsumsi solar dalam liter
        - jarak_tempuh_km: jarak transportasi dalam km
        - emisi_listrik_kg: emisi dari listrik
        - emisi_bbm_kg: emisi dari solar
        - emisi_transport_kg: emisi dari transportasi
        - total_emisi_kgco2: total emisi karbon
        - cluster: label cluster (default -1, untuk diisi setelah clustering)
    """
    
    # Set tanggal
    if start_date:
        start = datetime.strptime(start_date, '%Y-%m-%d')
    else:
        end_date = datetime(2026, 4, 30)
        start = end_date - timedelta(days=n_periods - 1)
    
    dates = [start + timedelta(days=i) for i in range(n_periods)]
    
    # Generate data aktivitas dengan variasi musiman (weekend effect)
    listrik_kwh = []
    bbm_liter = []
    jarak_km = []
    
    for i, date in enumerate(dates):
        # Weekend effect: produksi lebih rendah di Sabtu/Minggu
        is_weekend = date.weekday() >= 5
        weekend_factor = 0.7 if is_weekend else 1.0
        
        # Listrik
        l = np.random.normal(
            PARAMETER_UMKM['listrik_mean'] * weekend_factor,
            PARAMETER_UMKM['listrik_std']
        )
        listrik_kwh.append(np.clip(l, PARAMETER_UMKM['listrik_min'], PARAMETER_UMKM['listrik_max']))
        
        # Solar
        s = np.random.normal(
            PARAMETER_UMKM['bbm_mean'] * weekend_factor,
            PARAMETER_UMKM['bbm_std']
        )
        bbm_liter.append(np.clip(s, PARAMETER_UMKM['bbm_min'], PARAMETER_UMKM['bbm_max']))
        
        # Jarak (tidak terlalu terpengaruh weekend)
        j = np.random.normal(PARAMETER_UMKM['jarak_mean'], PARAMETER_UMKM['jarak_std'])
        jarak_km.append(np.clip(j, PARAMETER_UMKM['jarak_min'], PARAMETER_UMKM['jarak_max']))
    
    # Konversi ke numpy array
    listrik_kwh = np.array(listrik_kwh).round(1)
    bbm_liter = np.array(bbm_liter).round(1)
    jarak_km = np.array(jarak_km).round(1)
    
    # Hitung emisi per sumber
    emisi_listrik = listrik_kwh * FAKTOR_EMISI['listrik']
    emisi_solar = bbm_liter * FAKTOR_EMISI['BBM']
    emisi_transport = jarak_km * FAKTOR_EMISI['transportasi']
    
    # Total emisi
    total_emisi = emisi_listrik + emisi_solar + emisi_transport
    
    # Buat DataFrame
    df = pd.DataFrame({
        'tanggal': dates,
        'listrik_kwh': listrik_kwh,
        'bbm_liter': bbm_liter,
        'jarak_tempuh_km': jarak_km,
        'emisi_listrik_kg': emisi_listrik.round(2),
        'emisi_bbm_kg': emisi_solar.round(2),
        'emisi_transport_kg': emisi_transport.round(2),
        'total_emisi_kgco2': total_emisi.round(2),
        'cluster': -1  # placeholder, akan diisi setelah clustering
    })
    
    return df

def save_sample_data(filename: str = "data_emisi_simulasi.csv", n_periods: int = 30):
    """Simpan data simulasi ke file CSV"""
    df = generate_emission_data(n_periods)
    df.to_csv(filename, index=False)
    print(f"✅ Data simulasi berhasil disimpan ke {filename}")
    print(f"📊 Total data: {len(df)} periode")
    print(f"📈 Rentang total emisi: {df['total_emisi_kgco2'].min():.2f} - {df['total_emisi_kgco2'].max():.2f} kg CO2")
    return df

if __name__ == "__main__":
    save_sample_data()
