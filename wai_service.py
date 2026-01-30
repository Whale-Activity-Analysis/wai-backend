"""
WAI Service - Berechnet den Whale Activity Index
"""
import httpx
import pandas as pd
import numpy as np
from typing import List, Dict, Optional
from datetime import datetime
from config import config


class WAIService:
    """Service zur Berechnung des Whale Activity Index und Whale Intent Index"""
    
    DATA_URL = config.DATA_URL
    MEDIAN_WINDOW = config.MEDIAN_WINDOW
    WAI_SMOOTHING_WINDOW = config.WAI_SMOOTHING_WINDOW
    WAI_MIN = config.WAI_MIN
    WAI_MAX = config.WAI_MAX
    WII_SMOOTHING_WINDOW = config.WII_SMOOTHING_WINDOW
    WII_MIN = config.WII_MIN
    WII_MAX = config.WII_MAX
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
    
    def calculate_wii(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Berechnet den Whale Intent Index (WII) - Was wollen die Whales?
        
        Der WII analysiert die Absichten der Whales basierend auf Exchange-Flows:
        - Hoher Inflow zu Exchanges → Verkaufsdruck (negativ)
        - Hoher Outflow von Exchanges → Akkumulation (positiv)
        - Netflow zeigt Richtungsbias
        
        Schritte:
        1. Netflow-Ratio berechnen: (Outflow - Inflow) / (Outflow + Inflow)
           - Werte: [-1, 1]
           - -1 = Nur Inflow (maximaler Verkaufsdruck)
           - +1 = Nur Outflow (maximale Akkumulation)
           - 0 = Ausgeglichen
        
        2. Normalisierung auf [0, 1]:
           - WII_normalized = (netflow_ratio + 1) / 2
        
        3. Historisch adaptive Skalierung (180-Tage-Fenster):
           - WII_percentile = PercentileRank(WII_normalized, window=180)
        
        4. Skalierung auf [0, 100]:
           - WII_index = round(WII_percentile * 100)
        
        5. EMA-Smoothing für Stabilität
        
        Interpretation:
        - WII < 30: Starker Verkaufsdruck (Whales verkaufen)
        - WII 30-70: Neutral / Ausgeglichen
        - WII > 70: Starke Akkumulation (Whales kaufen/hodlen)
        """
        result = df.copy()
        
        # Netflow-Ratio berechnen: (Outflow - Inflow) / Total
        # Handling von Division durch 0 und fehlenden Daten
        total_flow = result['exchange_outflow_btc'] + result['exchange_inflow_btc']

        # Netflow berechnen (bereits vorhanden, aber wir berechnen neu zur Sicherheit)
        result['netflow'] = result['exchange_outflow_btc'] - result['exchange_inflow_btc']

        # Netflow Ratio: [-1, 1]
        # -1 = Nur Inflow, +1 = Nur Outflow
        result['netflow_ratio'] = 0.0  # Default für Tage ohne Exchange-Aktivität
        mask = total_flow > 0
        result.loc[mask, 'netflow_ratio'] = result.loc[mask, 'netflow'] / total_flow[mask]

        # Normalisierung auf [0, 1] für bessere Interpretation
        # 0 = Maximaler Verkaufsdruck, 1 = Maximale Akkumulation
        result['wii_normalized'] = (result['netflow_ratio'] + 1) / 2
        
        # Alternative: Exchange Flow Ratio als zusätzliche Metrik
        # Outflow / Inflow (bereits in Daten als exchange_flow_ratio)
        # > 1 = Mehr Outflow (Akkumulation)
        # < 1 = Mehr Inflow (Verkaufsdruck)
        
        # Historisch adaptive Skalierung: Percentile Rank über 180-Tage-Fenster
        result['wii_percentile'] = self.calculate_percentile_rank(
            result['wii_normalized'],
            window=180
        )

        # Skaliere auf [0, 100] und runde
        result['wii_scaled'] = (result['wii_percentile'] * 100).round()

        # Kein Smoothing: reaktiver WII
        result['wii'] = result['wii_scaled']

        # Neutral setzen, wenn kein Flow vorhanden ist
        zero_flow_mask = total_flow <= 0
        result.loc[zero_flow_mask, 'wii'] = 50
        result.loc[zero_flow_mask, 'wii_scaled'] = 50
        result.loc[zero_flow_mask, 'wii_percentile'] = 0.5
        result.loc[zero_flow_mask, 'wii_normalized'] = 0.5
        result.loc[zero_flow_mask, 'netflow_ratio'] = 0.0
        result.loc[zero_flow_mask, 'netflow'] = 0.0
        
        # NaN-Werte behandeln
        result['wii'] = result['wii'].fillna(50)  # Neutral bei fehlenden Daten
        
        # Zusätzliche Metriken für Interpretation
        result['wii_signal'] = 'neutral'
        result.loc[result['wii'] < 30, 'wii_signal'] = 'selling_pressure'
        result.loc[result['wii'] > 70, 'wii_signal'] = 'accumulation'

        # Sicherstellen, dass Tage ohne Flow neutral bleiben
        result.loc[zero_flow_mask, 'wii_signal'] = 'neutral'
        
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
        
        # WII berechnen (Whale Intent Index)
        df_with_wii = self.calculate_wii(df)
        df_with_wai['wii'] = df_with_wii['wii']
        df_with_wai['wii_signal'] = df_with_wii['wii_signal']
        df_with_wai['netflow_ratio'] = df_with_wii['netflow_ratio']
        
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
                'wii': int(round(float(row['wii']))),
                'wii_signal': str(row['wii_signal']),
                'tx_count': int(row['whale_tx_count']),
                'volume': round(float(row['whale_tx_volume_btc']), 2),
                'exchange_inflow': round(float(row['exchange_inflow_btc']), 2),
                'exchange_outflow': round(float(row['exchange_outflow_btc']), 2),
                'exchange_netflow': round(float(row['exchange_netflow_btc']), 2),
                'netflow_ratio': round(float(row['netflow_ratio']), 4)
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
        """Berechnet Statistiken über einen optionalen Zeitraum für WAI und WII"""
        df = await self.fetch_daily_metrics()
        df_with_wai = self.calculate_wai(df)
        df_with_wii = self.calculate_wii(df)
        
        # Merge WII Daten
        df_with_wai['wii'] = df_with_wii['wii']
        df_with_wai['wii_signal'] = df_with_wii['wii_signal']
        
        # Filtern nach Datumsbereich
        if start_date:
            start = pd.to_datetime(start_date)
            df_with_wai = df_with_wai[df_with_wai['date'] >= start]
        
        if end_date:
            end = pd.to_datetime(end_date)
            df_with_wai = df_with_wai[df_with_wai['date'] <= end]
        
        # WII Signal-Verteilung
        wii_signal_counts = df_with_wai['wii_signal'].value_counts().to_dict()
        
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
            'wii_stats': {
                'mean': round(float(df_with_wai['wii'].mean()), 4),
                'median': round(float(df_with_wai['wii'].median()), 4),
                'min': round(float(df_with_wai['wii'].min()), 4),
                'max': round(float(df_with_wai['wii'].max()), 4),
                'std': round(float(df_with_wai['wii'].std()), 4),
                'signal_distribution': {
                    'selling_pressure': int(wii_signal_counts.get('selling_pressure', 0)),
                    'neutral': int(wii_signal_counts.get('neutral', 0)),
                    'accumulation': int(wii_signal_counts.get('accumulation', 0))
                }
            },
            'latest_wai': round(float(df_with_wai.iloc[-1]['wai']), 4),
            'latest_wii': round(float(df_with_wai.iloc[-1]['wii']), 4),
            'latest_wii_signal': str(df_with_wai.iloc[-1]['wii_signal']),
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
    
    async def calculate_lead_lag_analysis(self, max_lag: int = 7) -> Dict:
        """
        Lead-Lag-Analyse: Folgt der BTC-Preis auf Whale-Flows?
        
        Untersucht zeitverzögerte Korrelationen zwischen:
        - Exchange Inflow/Outflow und BTC-Returns
        - WAI/WII und BTC-Returns
        
        Args:
            max_lag: Maximale Anzahl Tage für Lag-Analyse
        
        Returns:
            Dictionary mit Korrelationsanalysen
        """
        df = await self.fetch_daily_metrics()
        df = df.sort_values('date')
        
        # WAI und WII berechnen
        df_with_wai = self.calculate_wai(df)
        df_with_wii = self.calculate_wii(df)
        
        # Merge
        df_analysis = pd.DataFrame()
        df_analysis['date'] = df['date']
        df_analysis['wai'] = df_with_wai['wai']
        df_analysis['wii'] = df_with_wii['wii']
        df_analysis['exchange_inflow'] = df['exchange_inflow_btc']
        df_analysis['exchange_outflow'] = df['exchange_outflow_btc']
        df_analysis['exchange_netflow'] = df['exchange_netflow_btc']
        df_analysis['btc_return_1d'] = df['btc_return_1d']
        df_analysis['btc_close'] = df['btc_close']
        
        # Entferne NaN-Werte
        df_analysis = df_analysis.dropna()
        
        if len(df_analysis) < max_lag + 10:
            return {"error": "Nicht genug Daten für Lead-Lag-Analyse"}
        
        # === 1. Lead-Lag für Exchange Inflow → BTC Returns ===
        inflow_lead_lag = {}
        for lag in range(max_lag + 1):
            if lag == 0:
                corr = df_analysis['exchange_inflow'].corr(df_analysis['btc_return_1d'])
            else:
                # Inflow führt BTC-Returns um 'lag' Tage voraus
                corr = df_analysis['exchange_inflow'].iloc[:-lag].corr(
                    df_analysis['btc_return_1d'].iloc[lag:]
                )
            inflow_lead_lag[f"lag_{lag}d"] = round(float(corr), 4) if not pd.isna(corr) else 0.0
        
        # === 2. Lead-Lag für Exchange Outflow → BTC Returns ===
        outflow_lead_lag = {}
        for lag in range(max_lag + 1):
            if lag == 0:
                corr = df_analysis['exchange_outflow'].corr(df_analysis['btc_return_1d'])
            else:
                corr = df_analysis['exchange_outflow'].iloc[:-lag].corr(
                    df_analysis['btc_return_1d'].iloc[lag:]
                )
            outflow_lead_lag[f"lag_{lag}d"] = round(float(corr), 4) if not pd.isna(corr) else 0.0
        
        # === 3. Lead-Lag für Netflow → BTC Returns ===
        netflow_lead_lag = {}
        for lag in range(max_lag + 1):
            if lag == 0:
                corr = df_analysis['exchange_netflow'].corr(df_analysis['btc_return_1d'])
            else:
                corr = df_analysis['exchange_netflow'].iloc[:-lag].corr(
                    df_analysis['btc_return_1d'].iloc[lag:]
                )
            netflow_lead_lag[f"lag_{lag}d"] = round(float(corr), 4) if not pd.isna(corr) else 0.0
        
        # === 4. Lead-Lag für WII → BTC Returns ===
        wii_lead_lag = {}
        for lag in range(max_lag + 1):
            if lag == 0:
                corr = df_analysis['wii'].corr(df_analysis['btc_return_1d'])
            else:
                corr = df_analysis['wii'].iloc[:-lag].corr(
                    df_analysis['btc_return_1d'].iloc[lag:]
                )
            wii_lead_lag[f"lag_{lag}d"] = round(float(corr), 4) if not pd.isna(corr) else 0.0
        
        # === 5. Lead-Lag für WAI → BTC Returns ===
        wai_lead_lag = {}
        for lag in range(max_lag + 1):
            if lag == 0:
                corr = df_analysis['wai'].corr(df_analysis['btc_return_1d'])
            else:
                corr = df_analysis['wai'].iloc[:-lag].corr(
                    df_analysis['btc_return_1d'].iloc[lag:]
                )
            wai_lead_lag[f"lag_{lag}d"] = round(float(corr), 4) if not pd.isna(corr) else 0.0
        
        # Finde optimales Lag (höchste absolute Korrelation)
        best_inflow_lag = max(inflow_lead_lag.items(), key=lambda x: abs(x[1]))
        best_outflow_lag = max(outflow_lead_lag.items(), key=lambda x: abs(x[1]))
        best_netflow_lag = max(netflow_lead_lag.items(), key=lambda x: abs(x[1]))
        best_wii_lag = max(wii_lead_lag.items(), key=lambda x: abs(x[1]))
        best_wai_lag = max(wai_lead_lag.items(), key=lambda x: abs(x[1]))
        
        return {
            'description': 'Lead-Lag-Analyse: Zeitverzögerte Korrelationen zwischen Whale-Flows und BTC-Returns',
            'sample_size': len(df_analysis),
            'max_lag_days': max_lag,
            'exchange_inflow_to_btc_returns': {
                'correlations': inflow_lead_lag,
                'best_lag': best_inflow_lag[0],
                'best_correlation': best_inflow_lag[1],
                'interpretation': 'Negativ = Inflow ist bearish (Verkaufsdruck)'
            },
            'exchange_outflow_to_btc_returns': {
                'correlations': outflow_lead_lag,
                'best_lag': best_outflow_lag[0],
                'best_correlation': best_outflow_lag[1],
                'interpretation': 'Positiv = Outflow ist bullish (Akkumulation)'
            },
            'netflow_to_btc_returns': {
                'correlations': netflow_lead_lag,
                'best_lag': best_netflow_lag[0],
                'best_correlation': best_netflow_lag[1],
                'interpretation': 'Positiv = Netflow korreliert mit Preissteigerung'
            },
            'wii_to_btc_returns': {
                'correlations': wii_lead_lag,
                'best_lag': best_wii_lag[0],
                'best_correlation': best_wii_lag[1],
                'interpretation': 'WII (Intent) als Preisindikator'
            },
            'wai_to_btc_returns': {
                'correlations': wai_lead_lag,
                'best_lag': best_wai_lag[0],
                'best_correlation': best_wai_lag[1],
                'interpretation': 'WAI (Activity) als Preisindikator'
            },
            'key_findings': {
                'inflow_bearish': best_inflow_lag[1] < -0.1,
                'outflow_bullish': best_outflow_lag[1] > 0.1,
                'wii_predictive': abs(best_wii_lag[1]) > 0.15,
                'best_predictor': max([
                    ('Inflow', abs(best_inflow_lag[1])),
                    ('Outflow', abs(best_outflow_lag[1])),
                    ('Netflow', abs(best_netflow_lag[1])),
                    ('WII', abs(best_wii_lag[1])),
                    ('WAI', abs(best_wai_lag[1]))
                ], key=lambda x: x[1])[0]
            }
        }
    
    async def calculate_regime_detection(self) -> Dict:
        """
        Regime Detection: Identifiziert verschiedene Marktphasen
        
        Verwendet K-Means Clustering auf:
        - WAI (Aktivität)
        - WII (Intent)
        - BTC Volatilität
        
        Returns:
            Dictionary mit Regime-Klassifizierung
        """
        df = await self.fetch_daily_metrics()
        df = df.sort_values('date')
        
        # WAI und WII berechnen
        df_with_wai = self.calculate_wai(df)
        df_with_wii = self.calculate_wii(df)
        
        # Merge
        df_regime = pd.DataFrame()
        df_regime['date'] = df['date']
        df_regime['wai'] = df_with_wai['wai']
        df_regime['wii'] = df_with_wii['wii']
        df_regime['btc_volatility'] = df['btc_volatility_7d']
        df_regime['btc_return'] = df['btc_return_1d']
        df_regime['btc_close'] = df['btc_close']
        
        # Entferne NaN
        df_regime = df_regime.dropna()
        
        if len(df_regime) < 20:
            return {"error": "Nicht genug Daten für Regime Detection"}
        
        # Normalisiere Features für Clustering
        from sklearn.preprocessing import StandardScaler
        from sklearn.cluster import KMeans
        
        features = df_regime[['wai', 'wii', 'btc_volatility']].values
        scaler = StandardScaler()
        features_scaled = scaler.fit_transform(features)
        
        # K-Means mit 4 Regimes
        n_regimes = 4
        kmeans = KMeans(n_clusters=n_regimes, random_state=42, n_init=10)
        df_regime['regime'] = kmeans.fit_predict(features_scaled)
        
        # Regime-Charakteristiken
        regime_stats = []
        for regime_id in range(n_regimes):
            regime_data = df_regime[df_regime['regime'] == regime_id]
            
            # Durchschnittliche Returns in diesem Regime
            avg_return = regime_data['btc_return'].mean()
            
            regime_stats.append({
                'regime_id': int(regime_id),
                'count': len(regime_data),
                'percentage': round(100 * len(regime_data) / len(df_regime), 2),
                'characteristics': {
                    'avg_wai': round(float(regime_data['wai'].mean()), 2),
                    'avg_wii': round(float(regime_data['wii'].mean()), 2),
                    'avg_volatility': round(float(regime_data['btc_volatility'].mean()), 4),
                    'avg_btc_return': round(float(avg_return), 4)
                },
                'interpretation': self._interpret_regime(
                    regime_data['wai'].mean(),
                    regime_data['wii'].mean(),
                    regime_data['btc_volatility'].mean(),
                    avg_return
                )
            })
        
        # Sortiere nach Häufigkeit
        regime_stats = sorted(regime_stats, key=lambda x: x['count'], reverse=True)
        
        # Aktuelles Regime
        current_regime = int(df_regime.iloc[-1]['regime'])
        current_regime_stats = next(r for r in regime_stats if r['regime_id'] == current_regime)
        
        return {
            'description': 'Regime Detection: Identifiziert Marktphasen basierend auf WAI, WII und Volatilität',
            'n_regimes': n_regimes,
            'total_days': len(df_regime),
            'regimes': regime_stats,
            'current_regime': current_regime_stats,
            'latest_date': df_regime.iloc[-1]['date'].strftime('%Y-%m-%d')
        }
    
    def _interpret_regime(self, wai: float, wii: float, vol: float, ret: float) -> str:
        """Interpretiert ein Regime basierend auf Charakteristiken"""
        if wai > 65 and wii > 65:
            return "Bull Market - Hohe Aktivität + Akkumulation"
        elif wai > 65 and wii < 35:
            return "Distribution Phase - Hohe Aktivität + Verkaufsdruck"
        elif wai < 35 and wii > 65:
            return "Stealth Accumulation - Niedrige Aktivität + Akkumulation"
        elif wai < 35 and wii < 35:
            return "Capitulation/Apathy - Niedrige Aktivität + Verkaufsdruck"
        elif vol > 0.03:
            return "High Volatility Phase - Unsicherheit"
        elif ret > 0.01:
            return "Uptrend - Positive Returns"
        elif ret < -0.01:
            return "Downtrend - Negative Returns"
        else:
            return "Consolidation - Seitwärtsbewegung"
    
    async def calculate_conditional_volatility(self) -> Dict:
        """
        Conditional Volatility: Volatilität abhängig von Whale-Flows
        
        Untersucht, ob hohe Inflows/Outflows mit höherer Volatilität korrelieren
        
        Returns:
            Dictionary mit Volatilitätsanalysen
        """
        df = await self.fetch_daily_metrics()
        df = df.sort_values('date')
        
        # WII berechnen
        df_with_wii = self.calculate_wii(df)
        
        # Merge
        df_vol = pd.DataFrame()
        df_vol['date'] = df['date']
        df_vol['wii'] = df_with_wii['wii']
        df_vol['wii_signal'] = df_with_wii['wii_signal']
        df_vol['exchange_inflow'] = df['exchange_inflow_btc']
        df_vol['exchange_outflow'] = df['exchange_outflow_btc']
        df_vol['btc_volatility'] = df['btc_volatility_7d']
        df_vol['btc_return'] = df['btc_return_1d']
        
        # Entferne NaN
        df_vol = df_vol.dropna()
        
        if len(df_vol) < 20:
            return {"error": "Nicht genug Daten für Conditional Volatility"}
        
        # === 1. Volatilität nach WII-Signal ===
        vol_by_signal = {}
        for signal in ['selling_pressure', 'neutral', 'accumulation']:
            signal_data = df_vol[df_vol['wii_signal'] == signal]
            if len(signal_data) > 0:
                vol_by_signal[signal] = {
                    'count': len(signal_data),
                    'avg_volatility': round(float(signal_data['btc_volatility'].mean()), 6),
                    'avg_return': round(float(signal_data['btc_return'].mean()), 6)
                }
        
        # === 2. Volatilität bei hohen Inflows vs. Outflows ===
        high_inflow_threshold = df_vol['exchange_inflow'].quantile(0.75)
        high_outflow_threshold = df_vol['exchange_outflow'].quantile(0.75)
        
        high_inflow_data = df_vol[df_vol['exchange_inflow'] > high_inflow_threshold]
        high_outflow_data = df_vol[df_vol['exchange_outflow'] > high_outflow_threshold]
        low_activity_data = df_vol[
            (df_vol['exchange_inflow'] < df_vol['exchange_inflow'].quantile(0.25)) &
            (df_vol['exchange_outflow'] < df_vol['exchange_outflow'].quantile(0.25))
        ]
        
        flow_volatility = {
            'high_inflow': {
                'count': len(high_inflow_data),
                'avg_volatility': round(float(high_inflow_data['btc_volatility'].mean()), 6),
                'avg_return': round(float(high_inflow_data['btc_return'].mean()), 6)
            },
            'high_outflow': {
                'count': len(high_outflow_data),
                'avg_volatility': round(float(high_outflow_data['btc_volatility'].mean()), 6),
                'avg_return': round(float(high_outflow_data['btc_return'].mean()), 6)
            },
            'low_activity': {
                'count': len(low_activity_data),
                'avg_volatility': round(float(low_activity_data['btc_volatility'].mean()), 6) if len(low_activity_data) > 0 else 0.0,
                'avg_return': round(float(low_activity_data['btc_return'].mean()), 6) if len(low_activity_data) > 0 else 0.0
            }
        }
        
        # === 3. Korrelation zwischen Flows und Volatilität ===
        inflow_vol_corr = df_vol['exchange_inflow'].corr(df_vol['btc_volatility'])
        outflow_vol_corr = df_vol['exchange_outflow'].corr(df_vol['btc_volatility'])
        
        return {
            'description': 'Conditional Volatility: Volatilität abhängig von Whale-Flows',
            'sample_size': len(df_vol),
            'volatility_by_wii_signal': vol_by_signal,
            'volatility_by_flow_intensity': flow_volatility,
            'correlations': {
                'inflow_to_volatility': round(float(inflow_vol_corr), 4) if not pd.isna(inflow_vol_corr) else 0.0,
                'outflow_to_volatility': round(float(outflow_vol_corr), 4) if not pd.isna(outflow_vol_corr) else 0.0
            },
            'key_findings': {
                'high_inflow_increases_volatility': flow_volatility['high_inflow']['avg_volatility'] > flow_volatility['low_activity']['avg_volatility'] if len(low_activity_data) > 0 else False,
                'selling_pressure_more_volatile': vol_by_signal.get('selling_pressure', {}).get('avg_volatility', 0) > vol_by_signal.get('accumulation', {}).get('avg_volatility', 0),
                'inflow_bearish_confirmed': flow_volatility['high_inflow']['avg_return'] < 0
            }
        }
    
    async def get_wii_validation_stats(self, lookback_days: list = None) -> Dict:
        """
        Gibt aktuelle WII-Daten zurück.
        Validierungen werden vom wii_validation.py Script durchgeführt.
        """
        df = await self.fetch_daily_metrics()
        df = df.reset_index(drop=True)
        df = self.calculate_wii(df)
        
        if len(df) > 0:
            latest = df.iloc[-1]
            return {
                'latest_wii': latest.get('wii'),
                'latest_date': latest.get('date').strftime('%Y-%m-%d') if latest.get('date') else None,
                'data_point': 'Detaillierte Validierungsstatistiken: python analysis/wii_validation.py'
            }
        
        return {'error': 'Nicht genug Daten'}
