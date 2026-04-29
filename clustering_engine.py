import pandas as pd
import numpy as np
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import silhouette_score, calinski_harabasz_score, davies_bouldin_score
import warnings
warnings.filterwarnings('ignore')

class EmissionClusterAnalyzer:
    """
    Analisis clustering untuk data emisi karbon menggunakan K-Means.
    """
    
    def __init__(self, n_clusters: int = 3, random_state: int = 42):
        """
        Args:
            n_clusters: Jumlah cluster yang diinginkan (default 3: Tinggi, Sedang, Rendah)
            random_state: Seed untuk reproducibility
        """
        self.n_clusters = n_clusters
        self.random_state = random_state
        self.kmeans = None
        self.scaler = StandardScaler()
        self.scaled_data = None
        self.silhouette_score = None
        self.ch_score = None
        self.db_score = None
        
    def prepare_features(self, df: pd.DataFrame, feature_cols: list = None) -> np.ndarray:
        """
        Menyiapkan fitur untuk clustering.
        
        Args:
            df: DataFrame dengan data aktivitas
            feature_cols: Kolom fitur yang digunakan (default: listrik, solar, jarak)
        
        Returns:
            Array fitur yang sudah dinormalisasi
        """
        if feature_cols is None:
            feature_cols = ['listrik_kwh', 'bbm_liter', 'jarak_tempuh_km']
        
        # Pastikan kolom tersedia
        available_cols = [col for col in feature_cols if col in df.columns]
        
        if 'total_emisi_kgco2' in df.columns and len(available_cols) < 2:
            # Fallback ke total emisi jika fitur lain tidak tersedia
            features = df[['total_emisi_kgco2']].values
        else:
            features = df[available_cols].values
        
        # Normalisasi data (StandardScaler)
        self.scaled_data = self.scaler.fit_transform(features)
        
        return self.scaled_data
    
    def find_optimal_k(self, df: pd.DataFrame, max_k: int = 10, feature_cols: list = None) -> dict:
        """
        Menentukan jumlah cluster optimal menggunakan Elbow Method.
        
        Returns:
            Dictionary dengan: 'wss' (list of inertia), 'optimal_k' (rekomendasi)
        """
        self.prepare_features(df, feature_cols)
        
        wss = []  # Within-Cluster Sum of Squares (inertia)
        k_range = range(1, max_k + 1)
        
        for k in k_range:
            kmeans = KMeans(n_clusters=k, random_state=self.random_state, n_init=10)
            kmeans.fit(self.scaled_data)
            wss.append(kmeans.inertia_)
        
        # Deteksi 'elbow' atau siku (rekomendasi K optimal)
        # Menggunakan metode perbedaan persentase
        if len(wss) >= 3:
            # Hitung penurunan relatif dari WSS
            differences = np.diff(wss)
            # Cari titik di mana penurunan mulai melandai
            # Metode sederhana: ambil K di mana penurunan pertama kali < 10% dari penurunan terbesar
            max_diff = max(differences) if len(differences) > 0 else 0
            optimal_k = 2  # default minimal
            for i, diff in enumerate(differences[1:], start=2):
                if diff < 0.1 * max_diff:
                    optimal_k = i
                    break
            else:
                optimal_k = 3  # default jika tidak terdeteksi
        else:
            optimal_k = 3
        
        return {
            'wss': wss,
            'k_range': list(k_range),
            'optimal_k': optimal_k
        }
    
    def fit(self, df: pd.DataFrame, feature_cols: list = None) -> pd.DataFrame:
        """
        Melakukan clustering K-Means pada data emisi.
        
        Args:
            df: DataFrame dengan data aktivitas
            feature_cols: Kolom fitur yang digunakan
        
        Returns:
            DataFrame dengan kolom cluster ditambahkan
        """
        # Siapkan fitur
        self.prepare_features(df, feature_cols)
        
        # Lakukan K-Means
        self.kmeans = KMeans(
            n_clusters=self.n_clusters,
            random_state=self.random_state,
            n_init=10,
            max_iter=300
        )
        clusters = self.kmeans.fit_predict(self.scaled_data)
        
        # Evaluasi kualitas cluster
        if self.n_clusters >= 2:
            self.silhouette_score = silhouette_score(self.scaled_data, clusters)
            self.ch_score = calinski_harabasz_score(self.scaled_data, clusters)
            self.db_score = davies_bouldin_score(self.scaled_data, clusters)
        
        # Tambahkan ke DataFrame
        df_result = df.copy()
        df_result['cluster'] = clusters
        
        # Mapping cluster ke label (Tinggi, Sedang, Rendah)
        # Cluster dengan centroid tertinggi = emisi tinggi
        cluster_means = df_result.groupby('cluster')['total_emisi_kgco2'].mean().sort_values()
        cluster_mapping = {
            cluster_means.index[0]: 'Rendah',
            cluster_means.index[1]: 'Sedang'
        }
        if len(cluster_means) > 2:
            cluster_mapping[cluster_means.index[2]] = 'Tinggi'
        
        df_result['cluster_label'] = df_result['cluster'].map(cluster_mapping)
        
        # Simpan informasi centroid
        self.centroids = self.kmeans.cluster_centers_
        self.cluster_mapping = cluster_mapping
        
        return df_result
    
    def get_evaluation_metrics(self) -> dict:
        """Mendapatkan metrik evaluasi clustering"""
        return {
            'silhouette_score': self.silhouette_score,
            'calinski_harabasz_score': self.ch_score,
            'davies_bouldin_score': self.db_score,
            'n_clusters': self.n_clusters,
            'n_iterations': self.kmeans.n_iter_ if self.kmeans else None,
            'inertia': self.kmeans.inertia_ if self.kmeans else None
        }
    
    def get_cluster_characteristics(self, df: pd.DataFrame, cluster_col: str = 'cluster') -> pd.DataFrame:
        """Mendapatkan karakteristik setiap cluster"""
        
        if cluster_col not in df.columns:
            raise ValueError(f"Kolom '{cluster_col}' tidak ditemukan dalam DataFrame")
        
        # Kolom numerik untuk analisis
        numeric_cols = ['listrik_kwh', 'bbm_liter', 'jarak_tempuh_km', 'total_emisi_kgco2']
        available_cols = [col for col in numeric_cols if col in df.columns]
        
        characteristics = df.groupby(cluster_col)[available_cols].agg(['mean', 'std', 'min', 'max'])
        
        # Tambahkan jumlah data per cluster
        characteristics['count'] = df.groupby(cluster_col).size()
        
        return characteristics
