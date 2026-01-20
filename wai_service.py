"""
WAI Service - Berechnet den Whale Activity Index
"""
import httpx
import pandas as pd
from typing import List, Dict, Optional
from datetime import datetime
from config import config


class WAIService:
    """Service zur Berechnung des Whale Activity Index"""
    
    DATA_URL = config.DATA_URL
    MEDIAN_WINDOW = config.MEDIAN_WINDOW
    WAI_SMOOTHING_WINDOW = config.WAI_SMOOTHING_WINDOW
    WAI_MIN = config.WAI_MIN
    WAI_MAX = config.WAI_MAX
    BTC_DATA_URL = config.BTC_DATA_URL
    
    def __init__(self):
        self.cached_data: Optional[pd.DataFrame] = None
        self.last_fetch: Optional[datetime] = None
    
    async def fetch_daily_metrics(self) -> pd.DataFrame:
        """Lädt die täglichen Metriken und BTC-Daten von der API"""
        async with httpx.AsyncClient() as client:
            # Whale Activity Daten laden
            response = await client.get(self.DATA_URL, timeout=30.0)
            response.raise_for_status()
            data = response.json()
        
        # JSON in DataFrame konvertieren
        df = pd.DataFrame(data['daily_metrics'])
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date')
        
        # BTC-Daten laden (letzte 180 Tage)
        try:
            async with httpx.AsyncClient() as client:
                params = {
                    'vs_currency': 'usd',
                    'days': '180',
                    'interval': 'daily'
                }
                response = await client.get(self.BTC_DATA_URL, params=params, timeout=30.0)
                response.raise_for_status()
                btc_data = response.json()
            
            # BTC Schlusskurse in DataFrame konvertieren
            prices = btc_data.get('prices', [])
            btc_df = pd.DataFrame(prices, columns=['timestamp', 'btc_close'])
            btc_df['date'] = pd.to_datetime(btc_df['timestamp'], unit='ms').dt.date
            btc_df = btc_df[['date', 'btc_close']].drop_duplicates(subset=['date'])
            
            # 1D-Rendite und 7D-Volatilität berechnen
            btc_df['btc_close'] = btc_df['btc_close'].astype(float)
            btc_df['btc_return_1d'] = btc_df['btc_close'].pct_change()
            btc_df['btc_volatility_7d'] = btc_df['btc_close'].rolling(window=7).std() / btc_df['btc_close'].rolling(window=7).mean()
            btc_df['date'] = pd.to_datetime(btc_df['date'])
            
            # Merge mit Whale-Daten
            df = df.merge(btc_df, on='date', how='left')
        except Exception as e:
            print(f"Warnung: BTC-Daten konnten nicht geladen werden: {e}")
            df['btc_close'] = None
            df['btc_return_1d'] = None
            df['btc_volatility_7d'] = None
        
        return df
    
    def calculate_median_baseline(self, series: pd.Series, window: int) -> pd.Series:
        """
        Berechnet ein rollierendes Median-Fenster als robuste Basislinie.
        
        Median ist robuster gegen Ausreißer als Mittelwert.
        
        Args:
            series: Eingabe-Serie
            window: Fenster-Größe
        
        Returns:
            Series mit Median-Werten
        """
        return series.rolling(window=window, min_periods=1).median()
    
    def calculate_percentile_rank(self, series: pd.Series, window: int = 180) -> pd.Series:
        """
        Berechnet den Percentile Rank (Prozentrang) innerhalb eines rollierenden Fensters.
        
        Der Percentile Rank zeigt, wie viel Prozent der Werte im Fenster <= dem aktuellen Wert sind.
        Resultat liegt im Bereich [0, 1].
        
        Args:
            series: Eingabe-Serie
            window: Fenster-Größe (z.B. 180 Tage)
        
        Returns:
            Series mit Percentile Rank Werten [0, 1]
        """
        def percentile_rank_window(window_values):
            # Der letzte Wert ist der aktuelle Tageswert
            current_value = window_values.iloc[-1]
            # Prozentrang: Wie viel Prozent der Werte sind <= aktueller Wert
            percentile = (window_values <= current_value).sum() / len(window_values)
            return percentile
        
        return series.rolling(window=window, min_periods=1).apply(
            percentile_rank_window, raw=False
        )
    
    def calculate_dynamic_weights(self, 
                                  normalized_tx: pd.Series, 
                                  normalized_vol: pd.Series,
                                  window: int = 30) -> tuple:
        """
        Berechnet volatilitätsabhängige Gewichte für TX-Count und Volume.
        
        Logik:
        ------
        Die Gewichte werden basierend auf der Volatilität (Standardabweichung) 
        der normalisierten Volumen-Serie angepasst:
        
        1. Berechne std(V̂) im rollierenden Fenster
        2. Normalisiere std auf [0, 1] mittels Percentile-Normalisierung
        3. Wende inverse Beziehung an:
           - Hohe V-Volatilität → Volumen ist weniger zuverlässig → TX stärker gewichten
           - Niedrige V-Volatilität → Volumen ist stabil → Volumen stärker gewichten
        
        Gewichtungsformel:
        ──────────────────
        v_std_percentile = PercentileRank(std(V̂), window=window)
        weight_volume = v_std_percentile  # Höhere Volatilität → niedrigeres Gewicht
        weight_tx = 1 - weight_volume     # TX erhält Restgewicht
        
        Args:
            normalized_tx: Normalisierte TX-Count Serie
            normalized_vol: Normalisierte Volume Serie
            window: Fenster-Größe für Volatilitätsberechnung
        
        Returns:
            tuple: (weight_tx_series, weight_volume_series) - beide summieren zu 1.0
        """
        # Berechne rolling std für Volume
        vol_std = normalized_vol.rolling(window=window, min_periods=1).std()
        vol_std = vol_std.fillna(0)  # NaN für erste Tage
        
        # Normalisiere std auf [0, 1] mit Percentile Rank
        def percentile_rank_window(window_values):
            current = window_values.iloc[-1]
            percentile = (window_values <= current).sum() / len(window_values)
            return percentile
        
        vol_std_percentile = vol_std.rolling(window=window, min_periods=1).apply(
            percentile_rank_window, raw=False
        )
        vol_std_percentile = vol_std_percentile.fillna(0.5)  # Default: 50/50 bei fehlenden Daten
        
        # Inverse Beziehung: Höhere V-Volatilität → geringeres V-Gewicht, höheres TX-Gewicht
        weight_volume = 1.0 - vol_std_percentile  # Wenn vol volatil, dann NIEDRIGES Gewicht für Volume
        weight_tx = vol_std_percentile             # Wenn vol volatil, dann HOHES Gewicht für TX (zuverlässiger)
        
        return weight_tx, weight_volume

    def calculate_wai_v1(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Berechnet den ursprünglichen WAI v1 mit statischen 50/50-Gewichten
        und historisch adaptiver Percentile-Skalierung auf 0-100 (180 Tage).
        """
        result = df.copy()
        result['baseline_tx'] = self.calculate_median_baseline(result['whale_tx_count'], self.MEDIAN_WINDOW)
        result['baseline_vol'] = self.calculate_median_baseline(result['whale_tx_volume_btc'], self.MEDIAN_WINDOW)
        result['norm_tx'] = result['whale_tx_count'] / result['baseline_tx']
        result['norm_vol'] = result['whale_tx_volume_btc'] / result['baseline_vol']
        result['wai_v1_raw'] = 0.5 * result['norm_tx'] + 0.5 * result['norm_vol']
        result['wai_v1_percentile'] = self.calculate_percentile_rank(
            result['wai_v1_raw'], window=180
        )
        result['wai_v1'] = (result['wai_v1_percentile'] * 100).round()
        result['wai_v1'] = result['wai_v1'].fillna(0)
        return result
    
    def calculate_wai(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Berechnet den WAI mit volatilitätsabhängigen Gewichten.
        
        Schritte:
        1. Normalisierung durch Median-Basislinie:
           - T_hat = T_d / Median_30(T)
           - V_hat = V_d / Median_30(V)
        
        2. Volatilitätsabhängige Gewichtung:
           - weight_vol = PercentileRank(std(V_hat), window=30)
           - weight_tx = 1 - weight_vol
        
        3. Gewichtete WAI-Berechnung:
           - WAI_raw = weight_tx * T_hat + weight_vol * V_hat
        
        4. Historisch adaptive Skalierung (180-Tage-Fenster):
           - WAI_percentile = PercentileRank(WAI_raw, window=180)
           - WAI_index = round(WAI_percentile * 100)
        """
        # Kopie erstellen
        result = df.copy()
        
        # Basislinie für Transaction Count und Volume berechnen
        # Verwendet Median-Basislinie
        result['sma_transaction_count'] = self.calculate_median_baseline(
            result['whale_tx_count'], 
            self.MEDIAN_WINDOW
        )
        result['sma_total_volume'] = self.calculate_median_baseline(
            result['whale_tx_volume_btc'], 
            self.MEDIAN_WINDOW
        )
        
        # Normalisierung
        result['normalized_transaction_count'] = (
            result['whale_tx_count'] / result['sma_transaction_count']
        )
        result['normalized_volume'] = (
            result['whale_tx_volume_btc'] / result['sma_total_volume']
        )
        
        # Volatilitätsabhängige Gewichte berechnen
        weight_tx, weight_volume = self.calculate_dynamic_weights(
            result['normalized_transaction_count'],
            result['normalized_volume'],
            window=self.MEDIAN_WINDOW
        )
        
        result['weight_tx'] = weight_tx
        result['weight_volume'] = weight_volume
        
        # WAI berechnen mit dynamischen Gewichten
        result['wai_raw'] = (
            result['weight_tx'] * result['normalized_transaction_count'] + 
            result['weight_volume'] * result['normalized_volume']
        )
        
        # Historisch adaptive Skalierung: Percentile Rank über 180-Tage-Fenster
        # Resultat liegt im Bereich [0, 1]
        result['wai_percentile'] = self.calculate_percentile_rank(
            result['wai_raw'],
            window=180  # 180-Tage adaptives Referenzfenster
        )
        
        # Skaliere auf [0, 100] und runde
        result['wai_scaled'] = (result['wai_percentile'] * 100).round()
        
        # Smoothing mit EMA für weniger Ausschläge
        result['wai'] = result['wai_scaled'].ewm(span=self.WAI_SMOOTHING_WINDOW, adjust=False).mean().round()
        
        # NaN-Werte behandeln (für erste Tage ohne vollständigen Fenster)
        result['wai'] = result['wai'].fillna(0)
        
        return result
    
    async def get_wai_data(self, 
                          start_date: Optional[str] = None, 
                          end_date: Optional[str] = None,
                          limit: Optional[int] = None) -> List[Dict]:
        """
        Gibt WAI-Daten für einen bestimmten Zeitraum zurück
        
        Args:
            start_date: Startdatum (YYYY-MM-DD)
            end_date: Enddatum (YYYY-MM-DD)
            limit: Maximale Anzahl der Ergebnisse (neueste zuerst)
        
        Returns:
            Liste mit WAI-Berechnungen
        """
        # Daten laden
        df = await self.fetch_daily_metrics()
        
        # WAI v2 und v1 berechnen
        df_with_wai = self.calculate_wai(df)
        df_v1 = self.calculate_wai_v1(df)
        df_with_wai['wai_v1'] = df_v1['wai_v1']
        
        # Filtern nach Datumsbereich
        if start_date:
            start = pd.to_datetime(start_date)
            df_with_wai = df_with_wai[df_with_wai['date'] >= start]
        
        if end_date:
            end = pd.to_datetime(end_date)
            df_with_wai = df_with_wai[df_with_wai['date'] <= end]
        
        # Sortieren (neueste zuerst)
        df_with_wai = df_with_wai.sort_values('date', ascending=False)
        
        # Limit anwenden
        if limit:
            df_with_wai = df_with_wai.head(limit)
        
        # In Dictionary-Format konvertieren
        result = []
        for _, row in df_with_wai.iterrows():
            btc_close = row.get('btc_close')
            btc_return = row.get('btc_return_1d')
            btc_vol = row.get('btc_volatility_7d')
            
            item = {
                'date': row['date'].strftime('%Y-%m-%d'),
                'wai': int(round(float(row['wai']))),
                'wai_v1': int(round(float(row['wai_v1']))),
                'tx_count': int(row['whale_tx_count']),
                'volume': round(float(row['whale_tx_volume_btc']), 2),
            }
            
            # BTC-Daten hinzufügen wenn verfügbar
            if btc_close is not None:
                item['btc_close'] = round(float(btc_close), 2)
            if btc_return is not None:
                item['btc_return_1d'] = round(float(btc_return), 4)
            if btc_vol is not None:
                item['btc_volatility_7d'] = round(float(btc_vol), 4)
            
            result.append(item)
        
        return result
    
    async def get_latest_wai(self) -> Dict:
        """Gibt den aktuellsten WAI-Wert zurück"""
        data = await self.get_wai_data(limit=1)
        return data[0] if data else {}
    
    async def get_wai_statistics(self, 
                                start_date: Optional[str] = None, 
                                end_date: Optional[str] = None) -> Dict:
        """Berechnet Statistiken über einen optionalen Zeitraum"""
        df = await self.fetch_daily_metrics()
        df_with_wai = self.calculate_wai(df)
        
        # Filtern nach Datumsbereich
        if start_date:
            start = pd.to_datetime(start_date)
            df_with_wai = df_with_wai[df_with_wai['date'] >= start]
        
        if end_date:
            end = pd.to_datetime(end_date)
            df_with_wai = df_with_wai[df_with_wai['date'] <= end]
        
        return {
            'total_days': len(df_with_wai),
            'date_range': {
                'start': df_with_wai['date'].min().strftime('%Y-%m-%d'),
                'end': df_with_wai['date'].max().strftime('%Y-%m-%d')
            },
            'wai_stats': {
                'mean': round(float(df_with_wai['wai'].mean()), 4),
                'median': round(float(df_with_wai['wai'].median()), 4),
                'min': round(float(df_with_wai['wai'].min()), 4),
                'max': round(float(df_with_wai['wai'].max()), 4),
                'std': round(float(df_with_wai['wai'].std()), 4)
            },
            'latest_wai': round(float(df_with_wai.iloc[-1]['wai']), 4),
            'latest_date': df_with_wai.iloc[-1]['date'].strftime('%Y-%m-%d')
        }
    
    async def calculate_wai_comparison(self) -> Dict:
        """
        Vergleicht den alten WAI-Index (linear, 50/50) mit dem neuen WAI-Index v2 (percentile, dynamisch).
        
        Metriken:
        - Anzahl Tage mit Wert = 100
        - Histogramm-Verteilung (5er-Buckets)
        - Sensitivität in Hochaktivitätsphasen (Tage > 75)
        - Korrelation zwischen alt und neu
        """
        # Daten laden
        df = await self.fetch_daily_metrics()
        
        # === ALTES SYSTEM: Linear, 50/50 ===
        df_old = df.copy()
        df_old['baseline_tx'] = self.calculate_median_baseline(df_old['whale_tx_count'], self.MEDIAN_WINDOW)
        df_old['baseline_vol'] = self.calculate_median_baseline(df_old['whale_tx_volume_btc'], self.MEDIAN_WINDOW)
        df_old['norm_tx'] = df_old['whale_tx_count'] / df_old['baseline_tx']
        df_old['norm_vol'] = df_old['whale_tx_volume_btc'] / df_old['baseline_vol']
        df_old['wai_raw'] = 0.5 * df_old['norm_tx'] + 0.5 * df_old['norm_vol']
        df_old['wai_index_old'] = (df_old['wai_raw'] * 100).round()
        
        # === NEUES SYSTEM: Percentile, dynamisch ===
        df_new = self.calculate_wai(df.copy())
        
        # Merge beide Systeme
        df_compare = pd.DataFrame()
        df_compare['date'] = df_old['date']
        df_compare['wai_index_old'] = df_old['wai_index_old']
        df_compare['wai_index_v2'] = df_new['wai']
        df_compare['weight_tx'] = df_new['weight_tx']
        df_compare['weight_vol'] = df_new['weight_volume']
        
        # 1. Anzahl Tage mit Index = 100
        count_100_old = (df_compare['wai_index_old'] == 100).sum()
        count_100_new = (df_compare['wai_index_v2'] == 100).sum()
        
        # 2. Histogramm-Verteilung (5er-Buckets)
        bins = list(range(0, 105, 5))
        hist_old = pd.cut(df_compare['wai_index_old'], bins=bins).value_counts().sort_index()
        hist_new = pd.cut(df_compare['wai_index_v2'], bins=bins).value_counts().sort_index()
        
        histogram = {}
        for interval in hist_old.index:
            bucket = f"{int(interval.left)}-{int(interval.right)}"
            histogram[bucket] = {
                'old': int(hist_old.get(interval, 0)),
                'new': int(hist_new.get(interval, 0))
            }
        
        # 3. Sensitivität in Hochaktivitätsphasen (Index > 75)
        high_activity_threshold = 75
        df_compare['high_activity_old'] = df_compare['wai_index_old'] > high_activity_threshold
        df_compare['high_activity_new'] = df_compare['wai_index_v2'] > high_activity_threshold
        
        days_high_old = df_compare['high_activity_old'].sum()
        days_high_new = df_compare['high_activity_new'].sum()
        
        avg_high_old = df_compare[df_compare['high_activity_old']]['wai_index_old'].mean()
        avg_high_new = df_compare[df_compare['high_activity_new']]['wai_index_v2'].mean()
        
        high_activity_both = df_compare[df_compare['high_activity_old'] | df_compare['high_activity_new']]
        correlation = high_activity_both['wai_index_old'].corr(high_activity_both['wai_index_v2'])
        
        # 4. Statistische Vergleiche
        stats_old = {
            'mean': round(float(df_compare['wai_index_old'].mean()), 2),
            'median': round(float(df_compare['wai_index_old'].median()), 2),
            'std': round(float(df_compare['wai_index_old'].std()), 2),
            'min': int(df_compare['wai_index_old'].min()),
            'max': int(df_compare['wai_index_old'].max()),
            'count_at_100': int(count_100_old),
            'pct_at_100': round(100 * count_100_old / len(df_compare), 2)
        }
        
        stats_new = {
            'mean': round(float(df_compare['wai_index_v2'].mean()), 2),
            'median': round(float(df_compare['wai_index_v2'].median()), 2),
            'std': round(float(df_compare['wai_index_v2'].std()), 2),
            'min': int(df_compare['wai_index_v2'].min()),
            'max': int(df_compare['wai_index_v2'].max()),
            'count_at_100': int(count_100_new),
            'pct_at_100': round(100 * count_100_new / len(df_compare), 2)
        }
        
        # 5. Sensitivitäts-Metriken
        sensitivity_metrics = {
            'high_activity_days_old': int(days_high_old),
            'high_activity_days_new': int(days_high_new),
            'high_activity_change_pct': round(100 * (days_high_new - days_high_old) / days_high_old, 2) if days_high_old > 0 else 0,
            'avg_index_high_activity_old': round(float(avg_high_old), 2),
            'avg_index_high_activity_new': round(float(avg_high_new), 2),
            'correlation_high_activity': round(float(correlation), 4) if not pd.isna(correlation) else 0.0
        }
        
        # 6. Gewichts-Analyse
        weight_stats = {
            'avg_weight_tx': round(float(df_compare['weight_tx'].mean()), 4),
            'avg_weight_vol': round(float(df_compare['weight_vol'].mean()), 4),
            'std_weight_tx': round(float(df_compare['weight_tx'].std()), 4),
            'std_weight_vol': round(float(df_compare['weight_vol'].std()), 4)
        }
        
        return {
            'summary': {
                'total_days': len(df_compare),
                'date_range': {
                    'start': df_compare['date'].min().strftime('%Y-%m-%d'),
                    'end': df_compare['date'].max().strftime('%Y-%m-%d')
                }
            },
            'system_old': {
                'name': 'Linear Scaling (50/50 Static)',
                'description': 'WAI_old = round((0.5 * Ť + 0.5 * V̂) * 100)',
                'statistics': stats_old
            },
            'system_new': {
                'name': 'Percentile + Dynamic Weighting (v2)',
                'description': 'WAI_v2 = round(PercentileRank(w_tx*Ť + w_vol*V̂) * 100)',
                'statistics': stats_new
            },
            'distribution': {
                'histogram_buckets': histogram,
                'buckets_description': 'Anzahl Tage pro 5er-Bucket [old vs new]'
            },
            'sensitivity_analysis': sensitivity_metrics,
            'weight_analysis': weight_stats,
            'key_findings': {
                'higher_dispersion_new': stats_new['std'] > stats_old['std'],
                'more_extreme_values_new': stats_new['max'] > stats_old['max'],
                'better_sensitivity_to_spikes': days_high_new > days_high_old,
                'dynamic_weights_impact': f"TX-Gewicht variiert zwischen {round(df_compare['weight_tx'].min(), 3)} und {round(df_compare['weight_tx'].max(), 3)}"
            }
        }
